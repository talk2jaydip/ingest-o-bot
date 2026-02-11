"""OpenAI embeddings provider implementation.

This module implements embeddings using OpenAI's native API (non-Azure),
for users who want to use OpenAI directly.
"""

from typing import Optional

from ..embeddings_provider import EmbeddingsProvider

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIEmbeddingsProvider(EmbeddingsProvider):
    """OpenAI embeddings API provider (non-Azure).

    Similar to Azure OpenAI but uses the native OpenAI API.
    Supports OpenAI's latest embedding models including text-embedding-3.
    """

    # Model dimension mapping
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-3-small",
        dimensions: Optional[int] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """Initialize OpenAI embeddings provider.

        Args:
            api_key: OpenAI API key
            model_name: OpenAI model name
            dimensions: Custom dimensions for text-embedding-3-* models
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds

        Raises:
            ImportError: If openai package is not installed
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai is required. Install with: pip install openai"
            )

        self.model_name = model_name
        self.dimensions = dimensions

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout
        )

        # Determine dimensions
        if dimensions:
            self._dimensions = dimensions
        else:
            self._dimensions = self.MODEL_DIMENSIONS.get(model_name, 1536)

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as list of floats
        """
        kwargs = {}
        if self.dimensions and self.model_name.startswith("text-embedding-3"):
            kwargs["dimensions"] = self.dimensions

        response = await self.client.embeddings.create(
            model=self.model_name,
            input=text,
            **kwargs
        )
        return response.data[0].embedding

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors, one for each input text
        """
        kwargs = {}
        if self.dimensions and self.model_name.startswith("text-embedding-3"):
            kwargs["dimensions"] = self.dimensions

        response = await self.client.embeddings.create(
            model=self.model_name,
            input=texts,
            **kwargs
        )

        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def get_dimensions(self) -> int:
        """Get embedding dimensions.

        Returns:
            Number of dimensions in embedding vectors
        """
        return self._dimensions

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name/identifier
        """
        return self.model_name

    async def close(self):
        """Cleanup resources.

        Closes the OpenAI API client connection.
        """
        await self.client.close()
