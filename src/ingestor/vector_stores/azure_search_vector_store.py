"""Azure AI Search vector store implementation.

This module wraps the existing SearchUploader class to implement the
VectorStore interface, maintaining backward compatibility while enabling
the pluggable architecture.
"""

from typing import Optional

from ..vector_store import VectorStore
from ..search_uploader import SearchUploader
from ..config import SearchConfig
from ..models import ChunkDocument


class AzureSearchVectorStore(VectorStore):
    """Azure AI Search vector store implementation.

    This class wraps the existing SearchUploader to provide the VectorStore
    interface while maintaining all existing functionality including:
    - Batch uploads with concurrency control
    - Integrated vectorization support (server-side embeddings)
    - Merge or upload idempotency
    - Error handling and retry logic
    """

    def __init__(self, config: SearchConfig, max_batch_concurrency: int = 5):
        """Initialize Azure Search vector store.

        Args:
            config: Azure Search configuration
            max_batch_concurrency: Maximum number of concurrent batch uploads
        """
        self._uploader = SearchUploader(config, max_batch_concurrency=max_batch_concurrency)
        self._config = config
        # Default dimensions for ada-002, can be overridden by first upload
        self._dimensions = 1536

    async def upload_documents(
        self,
        chunk_docs: list[ChunkDocument],
        include_embeddings: bool = True
    ) -> int:
        """Upload documents to Azure AI Search.

        Args:
            chunk_docs: List of chunk documents to upload
            include_embeddings: Whether to include embedding vectors.
                              Set to False for integrated vectorization (server-side)

        Returns:
            Number of documents successfully uploaded
        """
        # Delegate to existing SearchUploader
        return await self._uploader.upload_documents(chunk_docs, include_embeddings)

    async def delete_documents_by_filename(self, filename: str) -> int:
        """Delete all documents associated with a filename.

        Args:
            filename: The source filename to match

        Returns:
            Number of documents deleted
        """
        # Delegate to existing SearchUploader
        await self._uploader.delete_documents_by_filename(filename)
        # SearchUploader doesn't return count, return 0
        return 0

    async def delete_all_documents(self) -> int:
        """Delete all documents from Azure AI Search index.

        Returns:
            Number of documents deleted
        """
        # Delegate to existing SearchUploader
        await self._uploader.delete_all_documents()
        # SearchUploader doesn't return count, return 0
        return 0

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """Search for similar documents.

        Note: This method is not currently implemented in SearchUploader.
        For search operations, use Azure AI Search SDK directly or implement
        a separate search interface.

        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional OData filter dictionary

        Raises:
            NotImplementedError: Search is not implemented in this version
        """
        raise NotImplementedError(
            "Search functionality is not implemented in AzureSearchVectorStore. "
            "Use Azure AI Search SDK directly for search operations."
        )

    def get_dimensions(self) -> int:
        """Get expected embedding dimensions for Azure Search.

        Returns:
            Number of dimensions (default: 1536 for ada-002)
        """
        return self._dimensions

    async def close(self):
        """Close Azure Search client connections.

        Note: SearchUploader manages its own client lifecycle.
        """
        # SearchUploader doesn't have explicit cleanup
        pass
