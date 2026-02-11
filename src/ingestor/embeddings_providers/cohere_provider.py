"""Cohere embeddings provider implementation.

This module implements embeddings using Cohere's API, supporting their
latest v3 multilingual models optimized for semantic search.
"""

from ..embeddings_provider import EmbeddingsProvider

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


class CohereEmbeddingsProvider(EmbeddingsProvider):
    """Cohere embeddings API provider.

    Supports Cohere's latest embedding models including v3 multilingual
    models optimized for semantic search across 100+ languages.
    """

    # Dimension mapping for Cohere models
    MODEL_DIMENSIONS = {
        "embed-english-v3.0": 1024,
        "embed-multilingual-v3.0": 1024,
        "embed-english-light-v3.0": 384,
        "embed-multilingual-light-v3.0": 384,
        "embed-english-v2.0": 4096,
        "embed-multilingual-v2.0": 768,
    }

    def __init__(
        self,
        api_key: str,
        model_name: str = "embed-multilingual-v3.0",
        input_type: str = "search_document",
        truncate: str = "END"
    ):
        """Initialize Cohere embeddings provider.

        Args:
            api_key: Cohere API key
            model_name: Cohere model name
            input_type: Input type ("search_document" or "search_query")
            truncate: Truncation strategy ("NONE", "START", "END")

        Raises:
            ImportError: If cohere package is not installed
            ValueError: If model_name is not recognized
        """
        if not COHERE_AVAILABLE:
            raise ImportError(
                "cohere is required for Cohere embeddings. "
                "Install with: pip install cohere"
            )

        self.model_name = model_name
        self.input_type = input_type
        self.truncate = truncate

        # Initialize Cohere client
        self.client = cohere.AsyncClient(api_key)

        # Get dimensions for model
        self._dimensions = self.MODEL_DIMENSIONS.get(model_name)
        if not self._dimensions:
            raise ValueError(
                f"Unknown model {model_name}. "
                f"Supported models: {list(self.MODEL_DIMENSIONS.keys())}"
            )

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as list of floats
        """
        response = await self.client.embed(
            texts=[text],
            model=self.model_name,
            input_type=self.input_type,
            truncate=self.truncate
        )
        return response.embeddings[0]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Cohere API supports up to 96 texts per request, automatically batches larger requests.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors, one for each input text
        """
        # Cohere supports up to 96 texts per request
        MAX_BATCH_SIZE = 96

        all_embeddings = []

        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            response = await self.client.embed(
                texts=batch,
                model=self.model_name,
                input_type=self.input_type,
                truncate=self.truncate
            )
            all_embeddings.extend(response.embeddings)

        return all_embeddings

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

        Closes the Cohere API client connection.
        """
        await self.client.close()
