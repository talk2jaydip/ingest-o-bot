"""Azure OpenAI embeddings provider implementation.

This module wraps the existing EmbeddingsGenerator class to implement the
EmbeddingsProvider interface, maintaining backward compatibility while enabling
the pluggable architecture.
"""

from ..embeddings_provider import EmbeddingsProvider
from ..embeddings import EmbeddingsGenerator
from ..config import AzureOpenAIConfig


class AzureOpenAIEmbeddingsProvider(EmbeddingsProvider):
    """Azure OpenAI embeddings provider implementation.

    This class wraps the existing EmbeddingsGenerator to provide the
    EmbeddingsProvider interface while maintaining all existing functionality including:
    - Token-aware batching (8100 tokens, 16 items max per batch)
    - Retry logic with exponential backoff
    - Concurrency control via semaphore
    - Support for custom dimensions (text-embedding-3-* models)
    """

    def __init__(
        self,
        config: AzureOpenAIConfig,
        disable_batch: bool = False,
        max_retries: int = None
    ):
        """Initialize Azure OpenAI embeddings provider.

        Args:
            config: Azure OpenAI configuration
            disable_batch: Disable batch processing (default: False)
            max_retries: Maximum number of retries (default: from config or 3)
        """
        # Create the underlying EmbeddingsGenerator
        self._generator = EmbeddingsGenerator(
            config,
            disable_batch=disable_batch,
            max_retries=max_retries
        )

        # Store configuration for metadata
        self._config = config
        self._model_name = config.emb_model_name
        self._dimensions = config.emb_dimensions or 1536  # Default for ada-002

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as list of floats
        """
        # Delegate to existing EmbeddingsGenerator
        return await self._generator.generate_embedding(text)

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.

        Automatically handles token-aware batching:
        - Max 8100 tokens per batch
        - Max 16 items per batch
        - Respects rate limits with retry logic

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors, one for each input text
        """
        # Delegate to existing EmbeddingsGenerator
        return await self._generator.generate_embeddings_batch(texts)

    def get_dimensions(self) -> int:
        """Get embedding vector dimensions.

        Returns:
            Number of dimensions (1536 for ada-002, custom for text-embedding-3-*)
        """
        return self._dimensions

    def get_model_name(self) -> str:
        """Get the model name/identifier.

        Returns:
            Model name string (e.g., "text-embedding-ada-002")
        """
        return self._model_name

    def get_max_seq_length(self) -> int:
        """Get maximum sequence length for Azure OpenAI embedding models.

        Azure OpenAI embedding models support up to 8191 tokens per text.
        The batch limit is 8100 tokens total, but individual texts can be up to 8191.

        Returns:
            Maximum sequence length (8191 tokens)
        """
        return 8191

    async def close(self):
        """Close Azure OpenAI client connections.

        Note: EmbeddingsGenerator manages its own client lifecycle via AsyncAzureOpenAI.
        """
        # EmbeddingsGenerator doesn't have explicit cleanup
        pass
