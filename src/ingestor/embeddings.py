"""Azure OpenAI embeddings generation with proper batching, retry logic, and dimensions support.

This module provides token-aware batching for efficient Azure OpenAI embedding generation:
- Respects token limits (8100) and batch size limits (16 items) per API call
- Supports custom dimensions for text-embedding-3-* models
- Includes retry logic with exponential backoff for rate limit handling
- Properly handles concurrency with semaphore-based throttling
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

import tiktoken
from openai import AsyncAzureOpenAI, RateLimitError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from typing_extensions import TypedDict

from .config import AzureOpenAIConfig
from .logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class EmbeddingBatch:
    """Represents a batch of text that is going to be embedded.

    Attributes:
        texts: List of text strings to embed
        token_length: Total token count for the batch
    """
    texts: list[str]
    token_length: int


class ExtraArgs(TypedDict, total=False):
    """Extra arguments for embedding API calls."""
    dimensions: int


class EmbeddingsGenerator:
    """Generates embeddings using Azure OpenAI with proper batching, retries, and dimensions support.

    This class handles:
    - Token-aware batching to optimize API calls
    - Retry logic with exponential backoff for rate limiting
    - Custom dimensions support for text-embedding-3-* models
    - Concurrency control with semaphores
    """

    # Model capabilities for batching
    SUPPORTED_BATCH_MODELS = {
        "text-embedding-ada-002": {"token_limit": 8100, "max_batch_size": 16},
        "text-embedding-3-small": {"token_limit": 8100, "max_batch_size": 16},
        "text-embedding-3-large": {"token_limit": 8100, "max_batch_size": 16},
    }

    # Models that support custom dimensions
    SUPPORTED_DIMENSIONS_MODELS = {
        "text-embedding-ada-002": False,
        "text-embedding-3-small": True,
        "text-embedding-3-large": True,
    }

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_MIN_WAIT = 15
    DEFAULT_RETRY_MAX_WAIT = 60

    def __init__(
        self,
        config: AzureOpenAIConfig,
        disable_batch: bool = False,
        max_retries: int = None
    ):
        """Initialize embeddings generator.

        Args:
            config: Azure OpenAI configuration with endpoint, API key, deployment name, etc.
            disable_batch: If True, disable batching and use single embedding calls
            max_retries: Maximum number of retry attempts (overrides config value)
        """
        self.config = config
        self.disable_batch = disable_batch
        self.max_retries = max_retries or config.max_retries or self.DEFAULT_MAX_RETRIES

        # Create Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.endpoint,
            api_version=config.api_version
        )

        self.deployment = config.emb_deployment
        self.model_name = config.emb_model_name
        self.dimensions = config.emb_dimensions

        # Initialize tokenizer for the model
        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            # Fallback to cl100k_base for newer models
            logger.debug(f"No encoding found for {self.model_name}, using cl100k_base")
            self.encoding = tiktoken.get_encoding("cl100k_base")

        self._semaphore: Optional[asyncio.Semaphore] = None

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrency)
        return self._semaphore

    def _calculate_token_length(self, text: str) -> int:
        """Calculate token count for text.

        Args:
            text: Text to tokenize

        Returns:
            Number of tokens in the text
        """
        return len(self.encoding.encode(text))

    def _get_dimensions_args(self) -> ExtraArgs:
        """Get dimensions argument if supported by the model.

        Returns:
            Dictionary with dimensions key if model supports it, empty dict otherwise
        """
        if self.dimensions and self.SUPPORTED_DIMENSIONS_MODELS.get(self.model_name, False):
            return {"dimensions": self.dimensions}
        return {}

    def _before_retry_sleep(self, retry_state):
        """Log retry attempts.

        Args:
            retry_state: Tenacity retry state object
        """
        logger.info(
            f"Rate limited on embeddings API (attempt {retry_state.attempt_number}/{self.max_retries}), "
            f"sleeping before retrying..."
        )

    def split_text_into_batches(self, texts: list[str]) -> list[EmbeddingBatch]:
        """Split texts into batches respecting token limits and batch size.

        Uses token-aware batching to optimize API calls:
        - Batches texts up to 8100 tokens or 16 items (whichever comes first)
        - Ensures no batch exceeds model limits

        Args:
            texts: List of text strings to batch

        Returns:
            List of EmbeddingBatch objects with optimized batching
        """
        batch_info = self.SUPPORTED_BATCH_MODELS.get(self.model_name)
        if not batch_info:
            # Unsupported model - return each text as separate batch
            logger.warning(
                f"Model {self.model_name} not in supported batch models, using single-item batches"
            )
            return [
                EmbeddingBatch(texts=[text], token_length=self._calculate_token_length(text))
                for text in texts
            ]

        batch_token_limit = batch_info["token_limit"]
        batch_max_size = batch_info["max_batch_size"]

        batches: list[EmbeddingBatch] = []
        current_batch: list[str] = []
        current_token_length = 0

        for text in texts:
            text_token_length = self._calculate_token_length(text)

            # Check if adding this text would exceed limits
            if current_token_length + text_token_length >= batch_token_limit and len(current_batch) > 0:
                # Flush current batch
                batches.append(EmbeddingBatch(texts=current_batch, token_length=current_token_length))
                current_batch = []
                current_token_length = 0

            # Add text to current batch
            current_batch.append(text)
            current_token_length += text_token_length

            # Check if batch is full
            if len(current_batch) == batch_max_size:
                batches.append(EmbeddingBatch(texts=current_batch, token_length=current_token_length))
                current_batch = []
                current_token_length = 0

        # Don't forget the last batch
        if len(current_batch) > 0:
            batches.append(EmbeddingBatch(texts=current_batch, token_length=current_token_length))

        return batches

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text with retry logic.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            RuntimeError: If embedding generation fails after retries
        """
        semaphore = self._get_semaphore()
        dimensions_args = self._get_dimensions_args()

        async with semaphore:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(RateLimitError),
                wait=wait_random_exponential(min=self.DEFAULT_RETRY_MIN_WAIT, max=self.DEFAULT_RETRY_MAX_WAIT),
                stop=stop_after_attempt(self.max_retries),
                before_sleep=self._before_retry_sleep
            ):
                with attempt:
                    response = await self.client.embeddings.create(
                        model=self.deployment,
                        input=text,
                        **dimensions_args
                    )
                    logger.debug(f"Generated embedding for text ({len(text)} chars)")
                    return response.data[0].embedding

        # This should not be reached due to tenacity, but for safety
        raise RuntimeError("Failed to generate embedding after retries")

    async def _generate_batch_embeddings(self, batch: EmbeddingBatch) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            batch: EmbeddingBatch with texts and token count

        Returns:
            List of embedding vectors

        Raises:
            RuntimeError: If batch embedding generation fails after retries
        """
        semaphore = self._get_semaphore()
        dimensions_args = self._get_dimensions_args()

        async with semaphore:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(RateLimitError),
                wait=wait_random_exponential(min=self.DEFAULT_RETRY_MIN_WAIT, max=self.DEFAULT_RETRY_MAX_WAIT),
                stop=stop_after_attempt(self.max_retries),
                before_sleep=self._before_retry_sleep
            ):
                with attempt:
                    response = await self.client.embeddings.create(
                        model=self.deployment,
                        input=batch.texts,
                        **dimensions_args
                    )
                    embeddings = [data.embedding for data in response.data]
                    logger.info(
                        f"Computed embeddings batch. Size: {len(batch.texts)}, Tokens: {batch.token_length}"
                    )
                    return embeddings

        raise RuntimeError("Failed to generate batch embeddings after retries")

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts with proper batching.

        Uses token-aware batching to optimize API calls:
        - Batches texts up to 8100 tokens or 16 items (whichever comes first)
        - Supports custom dimensions for text-embedding-3-* models
        - Includes retry logic with exponential backoff

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts")

        # Check if batching is supported and enabled
        if self.disable_batch or self.model_name not in self.SUPPORTED_BATCH_MODELS:
            # Fall back to single embeddings
            logger.info("Batch mode disabled or unsupported, using single embedding calls")
            embeddings = []
            for text in texts:
                emb = await self.generate_embedding(text)
                embeddings.append(emb)
            return embeddings

        # Split into optimal batches
        batches = self.split_text_into_batches(texts)
        logger.info(f"Split into {len(batches)} batches")

        # Process batches
        all_embeddings: list[list[float]] = []
        for i, batch in enumerate(batches):
            logger.debug(f"Processing batch {i + 1}/{len(batches)} ({len(batch.texts)} texts)")
            batch_embeddings = await self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)

        logger.info(f"Generated {len(all_embeddings)} embeddings total")
        return all_embeddings

    def get_dimensions(self) -> int:
        """Get embedding dimensions based on model and config.

        Returns:
            Number of dimensions in the embedding vector
        """
        if self.dimensions:
            return self.dimensions

        # Default dimensions for known models
        if "ada-002" in self.model_name:
            return 1536
        elif "3-small" in self.model_name:
            return 1536  # Default for 3-small
        elif "3-large" in self.model_name:
            return 3072  # Default for 3-large

        # Fallback
        return 1536

    def get_model_name(self) -> str:
        """Get the model name.

        Returns:
            Model name string
        """
        return self.model_name

    async def close(self):
        """Close the OpenAI client and cleanup resources."""
        await self.client.close()


def create_embeddings_generator(
    config: AzureOpenAIConfig,
    disable_batch: bool = False,
    max_retries: int = None
) -> EmbeddingsGenerator:
    """Factory function to create embeddings generator.

    Args:
        config: Azure OpenAI configuration
        disable_batch: If True, disable batching and use single embedding calls
        max_retries: Maximum number of retry attempts (overrides config value)

    Returns:
        Configured EmbeddingsGenerator instance
    """
    return EmbeddingsGenerator(config, disable_batch=disable_batch, max_retries=max_retries)
