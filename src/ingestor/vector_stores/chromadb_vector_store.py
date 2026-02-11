"""ChromaDB vector store implementation.

This module implements the VectorStore interface for ChromaDB, supporting
three deployment modes: persistent local storage, in-memory, and client/server.
"""

from typing import Optional
import asyncio

from ..vector_store import VectorStore
from ..models import ChunkDocument

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class ChromaDBVectorStore(VectorStore):
    """ChromaDB vector store implementation.

    Supports three deployment modes:
    1. Persistent local storage (persist_directory set)
    2. In-memory storage (persist_directory=None, host=None)
    3. Client/server mode (host and port set)

    Note: ChromaDB requires client-side embeddings and does not support
    server-side vectorization like Azure Search.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        auth_token: Optional[str] = None,
        batch_size: int = 1000
    ):
        """Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for persistent storage (None = in-memory)
            host: Server host for client/server mode
            port: Server port for client/server mode
            auth_token: Authentication token for client/server mode
            batch_size: Batch size for uploads

        Raises:
            ImportError: If chromadb package is not installed
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is required for ChromaDB vector store. "
                "Install with: pip install chromadb"
            )

        self.collection_name = collection_name
        self.batch_size = batch_size
        self._dimensions = None  # Inferred from first upload

        # Initialize ChromaDB client based on mode
        if host and port:
            # Client/server mode
            settings = Settings(
                chroma_api_impl="rest",
                chroma_server_host=host,
                chroma_server_http_port=port
            )
            if auth_token:
                settings.chroma_client_auth_provider = "token"
                settings.chroma_client_auth_credentials = auth_token

            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=settings
            )
            self.mode = "client/server"
        elif persist_directory:
            # Persistent local storage
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.mode = "persistent"
        else:
            # In-memory (ephemeral)
            self.client = chromadb.EphemeralClient()
            self.mode = "in-memory"

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Document chunks with embeddings"}
        )

    async def upload_documents(
        self,
        chunk_docs: list[ChunkDocument],
        include_embeddings: bool = True
    ) -> int:
        """Upload documents to ChromaDB.

        ChromaDB requires client-side embeddings. If include_embeddings=False,
        this will raise an error.

        Args:
            chunk_docs: List of chunk documents to upload
            include_embeddings: Must be True for ChromaDB

        Returns:
            Number of documents successfully uploaded

        Raises:
            ValueError: If include_embeddings=False or embeddings are missing
        """
        if not include_embeddings:
            raise ValueError(
                "ChromaDB requires client-side embeddings. "
                "Set use_integrated_vectorization=False or choose a different vector store."
            )

        # Convert to ChromaDB format
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for chunk_doc in chunk_docs:
            if chunk_doc.chunk.embedding is None:
                raise ValueError(
                    f"Chunk {chunk_doc.chunk.chunk_id} missing embedding. "
                    "Ensure embeddings are generated before upload."
                )

            # Use generic format from to_vector_document()
            doc_dict = chunk_doc.to_vector_document(include_embeddings=True)

            # ChromaDB doesn't accept empty lists in metadata - filter them out
            clean_metadata = {}
            for key, value in doc_dict["metadata"].items():
                if isinstance(value, list) and len(value) == 0:
                    # Skip empty lists - ChromaDB validation rejects them
                    continue
                clean_metadata[key] = value

            ids.append(doc_dict["id"])
            embeddings.append(doc_dict["embedding"])
            documents.append(doc_dict["text"])
            metadatas.append(clean_metadata)

        # Infer dimensions from first embedding
        if self._dimensions is None and embeddings:
            self._dimensions = len(embeddings[0])

        # Upload in batches (ChromaDB handles batching internally, but we control size)
        total_uploaded = 0
        for i in range(0, len(ids), self.batch_size):
            batch_ids = ids[i:i + self.batch_size]
            batch_embeddings = embeddings[i:i + self.batch_size]
            batch_documents = documents[i:i + self.batch_size]
            batch_metadatas = metadatas[i:i + self.batch_size]

            # ChromaDB is sync, run in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.collection.upsert,
                batch_ids,
                batch_embeddings,
                batch_metadatas,
                batch_documents
            )

            total_uploaded += len(batch_ids)

        return total_uploaded

    async def delete_documents_by_filename(self, filename: str) -> int:
        """Delete all documents with matching sourcefile metadata.

        Args:
            filename: The source filename to match

        Returns:
            Number of documents deleted (ChromaDB doesn't return count, returns 0)
        """
        # ChromaDB uses where filters
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.collection.delete,
            None,  # ids
            {"sourcefile": filename}  # where filter
        )
        return 0  # ChromaDB doesn't return delete count

    async def delete_all_documents(self) -> int:
        """Delete all documents by deleting and recreating collection.

        Returns:
            Number of documents deleted (returns 0 as ChromaDB doesn't report count)

        Raises:
            RuntimeError: If deletion or recreation fails
        """
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.client.delete_collection,
            self.collection_name
        )

        self.collection = await asyncio.get_event_loop().run_in_executor(
            None,
            self.client.create_collection,
            self.collection_name,
            {"description": "Document chunks with embeddings"}
        )
        return 0

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """Search for similar documents.

        Note: This requires query embeddings to be generated externally
        and is not currently implemented.

        Args:
            query: Search query text (requires external embedding generation)
            top_k: Number of results to return
            filters: Optional filter dictionary

        Raises:
            NotImplementedError: Search requires query embedding generation
        """
        raise NotImplementedError(
            "Search requires query embedding generation. "
            "This will be implemented in a future version."
        )

    def get_dimensions(self) -> int:
        """Get embedding dimensions.

        Returns:
            Number of dimensions in embedding vectors

        Raises:
            ValueError: If dimensions not yet inferred (no uploads yet)
        """
        if self._dimensions is None:
            raise ValueError("Dimensions not yet inferred. Upload documents first.")
        return self._dimensions

    async def close(self):
        """Cleanup resources.

        ChromaDB client doesn't require explicit cleanup, but this method
        is provided for consistency with the VectorStore interface.
        """
        # ChromaDB client doesn't require explicit cleanup
        pass
