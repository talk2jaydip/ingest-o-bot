"""Abstract base class for embeddings generation.

This module provides the EmbeddingsProvider ABC that defines the interface for all
embedding generation implementations. Implementations include Azure OpenAI,
Hugging Face, Cohere, OpenAI, and potentially others.
"""

from abc import ABC, abstractmethod


class EmbeddingsProvider(ABC):
    """Abstract base class for embedding generation.

    This class defines the interface that all embeddings provider implementations
    must follow. Implementations should handle their own API clients, batching,
    retry logic, and error handling.
    """

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as list of floats

        Raises:
            RuntimeError: If embedding generation fails after retries
            ValueError: If text is empty or invalid
        """
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.

        This method should handle batching internally based on provider limits
        and return embeddings in the same order as input texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors, one for each input text

        Raises:
            RuntimeError: If embedding generation fails after retries
            ValueError: If texts list is empty or contains invalid entries
        """
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get embedding vector dimensions.

        Returns:
            Number of dimensions in embedding vectors

        Example:
            - Azure OpenAI ada-002: 1536
            - Hugging Face MiniLM: 384
            - Cohere v3: 1024
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name/identifier.

        Returns:
            Model name string

        Example:
            - "text-embedding-ada-002"
            - "sentence-transformers/all-MiniLM-L6-v2"
            - "embed-multilingual-v3.0"
        """
        pass

    async def close(self):
        """Close connections and cleanup resources.

        Override this method if your implementation needs cleanup
        (e.g., closing API clients, freeing model memory).
        Default implementation does nothing.
        """
        pass


def create_embeddings_provider(
    mode: "EmbeddingsMode",
    config,
    **kwargs
) -> EmbeddingsProvider:
    """Factory function for creating embeddings provider instances.

    Args:
        mode: EmbeddingsMode enum value indicating which implementation to use
        config: Configuration object for the specific embeddings provider
        **kwargs: Additional arguments passed to the implementation constructor

    Returns:
        Configured EmbeddingsProvider instance

    Raises:
        ValueError: If mode is not supported
        ImportError: If required dependencies are not installed

    Example:
        >>> from ingestor.config import EmbeddingsMode, AzureOpenAIConfig
        >>> config = AzureOpenAIConfig.from_env()
        >>> provider = create_embeddings_provider(
        ...     EmbeddingsMode.AZURE_OPENAI,
        ...     config,
        ...     disable_batch=False
        ... )
    """
    # Import here to avoid circular dependencies
    from .config import EmbeddingsMode

    if mode == EmbeddingsMode.AZURE_OPENAI:
        from .embeddings_providers.azure_openai_provider import AzureOpenAIEmbeddingsProvider
        return AzureOpenAIEmbeddingsProvider(config, **kwargs)

    elif mode == EmbeddingsMode.HUGGINGFACE:
        from .embeddings_providers.huggingface_provider import HuggingFaceEmbeddingsProvider
        return HuggingFaceEmbeddingsProvider(
            model_name=config.model_name,
            device=config.device,
            batch_size=config.batch_size,
            normalize_embeddings=config.normalize_embeddings,
            max_seq_length=getattr(config, 'max_seq_length', None),
            trust_remote_code=getattr(config, 'trust_remote_code', False)
        )

    elif mode == EmbeddingsMode.COHERE:
        from .embeddings_providers.cohere_provider import CohereEmbeddingsProvider
        return CohereEmbeddingsProvider(
            api_key=config.api_key,
            model_name=config.model_name,
            input_type=getattr(config, 'input_type', 'search_document'),
            truncate=getattr(config, 'truncate', 'END')
        )

    elif mode == EmbeddingsMode.OPENAI:
        from .embeddings_providers.openai_provider import OpenAIEmbeddingsProvider
        return OpenAIEmbeddingsProvider(
            api_key=config.api_key,
            model_name=config.model_name,
            dimensions=getattr(config, 'dimensions', None),
            max_retries=getattr(config, 'max_retries', 3),
            timeout=getattr(config, 'timeout', 60)
        )

    else:
        raise ValueError(
            f"Unsupported embeddings mode: {mode}. "
            f"Supported modes: {[m.value for m in EmbeddingsMode]}"
        )
