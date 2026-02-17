"""Abstract base class for vector database implementations.

This module provides the VectorStore ABC that defines the interface for all
vector database implementations. Implementations include Azure AI Search,
ChromaDB, and potentially others like Pinecone, Weaviate, or Qdrant.
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ChunkDocument


class VectorStore(ABC):
    """Abstract base class for vector database implementations.

    This class defines the interface that all vector store implementations
    must follow. Implementations should handle their own connection management,
    batching, error handling, and retry logic.
    """

    @abstractmethod
    async def upload_documents(
        self,
        chunk_docs: list["ChunkDocument"],
        include_embeddings: bool = True
    ) -> int:
        """Upload documents to vector store.

        Args:
            chunk_docs: List of chunk documents to upload
            include_embeddings: Whether to include embedding vectors
                              (False for server-side vectorization like Azure Search integrated mode)

        Returns:
            Number of documents successfully uploaded

        Raises:
            ValueError: If embeddings are required but missing
            RuntimeError: If upload fails after retries
        """
        pass

    @abstractmethod
    async def delete_documents_by_filename(self, filename: str) -> int:
        """Delete all documents associated with a filename.

        Args:
            filename: The source filename to match

        Returns:
            Number of documents deleted (0 if not supported by implementation)
        """
        pass

    @abstractmethod
    async def delete_all_documents(self) -> int:
        """Delete all documents from the vector store.

        Returns:
            Number of documents deleted (0 if not supported by implementation)

        Raises:
            RuntimeError: If deletion fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """Search for similar documents.

        Args:
            query: Search query text (or embedding if pre-computed)
            top_k: Number of results to return
            filters: Optional filter dictionary (implementation-specific format)

        Returns:
            List of matching documents with scores

        Note:
            This method may require query embeddings to be generated externally
            depending on the implementation.
        """
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get expected embedding dimensions for this store.

        Returns:
            Number of dimensions (e.g., 1536 for ada-002, 384 for MiniLM)

        Raises:
            ValueError: If dimensions not yet determined
        """
        pass

    async def close(self):
        """Close connections and cleanup resources.

        Override this method if your implementation needs cleanup.
        Default implementation does nothing.
        """
        pass


def create_vector_store(
    mode: "VectorStoreMode",
    config,
    **kwargs
) -> VectorStore:
    """Factory function for creating vector store instances.

    Supports both built-in and plugin vector stores.

    Args:
        mode: VectorStoreMode enum value indicating which implementation to use
        config: Configuration object for the specific vector store
        **kwargs: Additional arguments passed to the implementation constructor

    Returns:
        Configured VectorStore instance

    Raises:
        ValueError: If mode is not supported
        ImportError: If required dependencies are not installed

    Example:
        >>> from ingestor.config import VectorStoreMode, SearchConfig
        >>> config = SearchConfig.from_env()
        >>> store = create_vector_store(
        ...     VectorStoreMode.AZURE_SEARCH,
        ...     config,
        ...     max_batch_concurrency=5
        ... )
    """
    # Import here to avoid circular dependencies
    from .config import VectorStoreMode
    from .plugin_registry import get_vector_store_class, list_vector_stores

    # Try built-in implementations first
    if mode == VectorStoreMode.AZURE_SEARCH:
        from .vector_stores.azure_search_vector_store import AzureSearchVectorStore
        return AzureSearchVectorStore(config, **kwargs)

    elif mode == VectorStoreMode.CHROMADB:
        from .vector_stores.chromadb_vector_store import ChromaDBVectorStore
        return ChromaDBVectorStore(
            collection_name=config.collection_name,
            persist_directory=config.persist_directory,
            host=config.host,
            port=config.port,
            auth_token=getattr(config, 'auth_token', None),
            batch_size=getattr(config, 'batch_size', 1000)
        )

    else:
        # Try plugin registry
        try:
            plugin_class = get_vector_store_class(mode.value)
            return plugin_class(config, **kwargs)
        except ValueError:
            raise ValueError(
                f"Unsupported vector store mode: {mode}. "
                f"Built-in: [AZURE_SEARCH, CHROMADB]. "
                f"Plugins: {list_vector_stores()}"
            )
