# Pluggable Vector Database & Embeddings Architecture

## Context

The ingest-o-bot pipeline currently has a **tightly-coupled architecture** that only supports:
- **Vector Database:** Azure AI Search
- **Embeddings:** Azure OpenAI (text-embedding-ada-002, text-embedding-3-small/large)

This limits users who want to:
- Use **ChromaDB** for local/offline vector storage
- Use **Hugging Face** models for embeddings (multilingual, domain-specific, cost-free)
- Use **Cohere** embeddings for better semantic search
- Run the pipeline in air-gapped or cost-sensitive environments
- Experiment with different vector DB and embedding combinations

### Current Implementation Issues

1. **SearchUploader** ([search_uploader.py](c:\Work\ingest-o-bot\src\ingestor\search_uploader.py)) directly uses Azure Search SDK
2. **EmbeddingsGenerator** ([embeddings.py](c:\Work\ingest-o-bot\src\ingestor\embeddings.py)) only supports Azure OpenAI
3. **Configuration** ([config.py](c:\Work\ingest-o-bot\src\ingestor\config.py):621-624) hardcodes `search: SearchConfig` and `azure_openai: AzureOpenAIConfig`
4. **Pipeline** ([pipeline.py](c:\Work\ingest-o-bot\src\ingestor\pipeline.py):408-424) initializes components with specific implementations
5. **Data Model** ([models.py](c:\Work\ingest-o-bot\src\ingestor\models.py):235-279) has Azure-specific `to_search_document()` method

### Goal

Design and implement a **pluggable, extensible architecture** that:
- Supports multiple vector databases (Azure Search, ChromaDB, and extensible to Pinecone, Weaviate, etc.)
- Supports multiple embedding providers (Azure OpenAI, Hugging Face, Cohere, OpenAI, and extensible)
- Maintains **100% backward compatibility** with existing configurations
- Follows existing patterns (ABC, factory functions, configuration-driven)
- Enables users to mix and match components (e.g., ChromaDB + Azure OpenAI, Azure Search + Hugging Face)

---

## Proposed Architecture

### Phase 0: Architecture Proposal (Separate Approval Phase)

Create architectural design documents with:
- Abstract base class (ABC) interfaces for `VectorStore` and `EmbeddingsProvider`
- Configuration schema changes with enums and union types
- Factory function patterns
- Backward compatibility strategy
- Data model changes for generic serialization

**Deliverables:**
- Architecture design document (this plan)
- Interface specifications with method signatures
- Configuration examples for all supported combinations
- Migration strategy from current to new architecture

### Phase 1: Core Abstractions (No Breaking Changes)

Refactor existing code into abstract interfaces while keeping everything working.

#### 1.1 Vector Store Abstraction

**Create:** [src/ingestor/vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_store.py)

```python
from abc import ABC, abstractmethod
from typing import Optional

class VectorStore(ABC):
    """Abstract base class for vector database implementations."""

    @abstractmethod
    async def upload_documents(
        self,
        chunk_docs: list[ChunkDocument],
        include_embeddings: bool = True
    ) -> int:
        """Upload documents to vector store.

        Args:
            chunk_docs: List of chunk documents to upload
            include_embeddings: Whether to include embedding vectors
                              (False for server-side vectorization)

        Returns:
            Number of documents successfully uploaded
        """
        pass

    @abstractmethod
    async def delete_documents_by_filename(self, filename: str) -> int:
        """Delete all documents associated with a filename."""
        pass

    @abstractmethod
    async def delete_all_documents() -> int:
        """Delete all documents from the vector store."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """Search for similar documents."""
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get expected embedding dimensions for this store."""
        pass

    async def close(self):
        """Close connections and cleanup resources."""
        pass
```

**Create:** [src/ingestor/vector_stores/\_\_init\_\_.py](c:\Work\ingest-o-bot\src\ingestor\vector_stores\__init__.py)

**Create:** [src/ingestor/vector_stores/azure_search_vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_stores\azure_search_vector_store.py)

Wrap existing `SearchUploader` implementation:
```python
class AzureSearchVectorStore(VectorStore):
    def __init__(self, config: SearchConfig, max_batch_concurrency: int = 5):
        self._uploader = SearchUploader(config, max_batch_concurrency)
        self._dimensions = 1536  # Default for ada-002

    async def upload_documents(self, chunk_docs, include_embeddings=True):
        return await self._uploader.upload_documents(chunk_docs, include_embeddings)

    # ... delegate all methods to _uploader
```

#### 1.2 Embeddings Provider Abstraction

**Create:** [src/ingestor/embeddings_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_provider.py)

```python
from abc import ABC, abstractmethod

class EmbeddingsProvider(ABC):
    """Abstract base class for embedding generation."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch."""
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get embedding vector dimensions."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name/identifier."""
        pass

    async def close(self):
        """Close connections and cleanup resources."""
        pass
```

**Create:** [src/ingestor/embeddings_providers/\_\_init\_\_.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\__init__.py)

**Create:** [src/ingestor/embeddings_providers/azure_openai_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\azure_openai_provider.py)

Wrap existing `EmbeddingsGenerator`:
```python
class AzureOpenAIEmbeddingsProvider(EmbeddingsProvider):
    def __init__(self, config: AzureOpenAIConfig, **kwargs):
        self._generator = EmbeddingsGenerator(config, **kwargs)
        self._dimensions = config.emb_dimensions or 1536
        self._model_name = config.emb_model_name

    async def generate_embedding(self, text: str):
        return await self._generator.generate_embedding(text)

    # ... delegate to _generator
```

#### 1.3 Configuration Changes

**Modify:** [src/ingestor/config.py](c:\Work\ingest-o-bot\src\ingestor\config.py)

Add enums:
```python
class VectorStoreMode(str, Enum):
    AZURE_SEARCH = "azure_search"
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"

class EmbeddingsMode(str, Enum):
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    OPENAI = "openai"
```

Add new config dataclasses (details in Phase 2-3).

Update `PipelineConfig` (lines 618-716) to support both old and new patterns:
```python
@dataclass
class PipelineConfig:
    # Legacy fields (keep for backward compatibility)
    search: Optional[SearchConfig] = None
    azure_openai: Optional[AzureOpenAIConfig] = None

    # New fields
    vector_store_mode: Optional[VectorStoreMode] = None
    vector_store_config: Optional[Any] = None  # Union type
    embeddings_mode: Optional[EmbeddingsMode] = None
    embeddings_config: Optional[Any] = None  # Union type

    # ... rest of config unchanged
```

Backward compatibility logic in `from_env()`:
```python
@classmethod
def from_env(cls, env_path: Optional[str] = None) -> "PipelineConfig":
    # Load legacy config
    search = SearchConfig.from_env()
    azure_openai = AzureOpenAIConfig.from_env()

    # Auto-detect mode from environment
    if os.getenv("VECTOR_STORE_MODE"):
        vector_store_mode = VectorStoreMode(os.getenv("VECTOR_STORE_MODE"))
    elif search.endpoint:  # Legacy Azure Search config present
        vector_store_mode = VectorStoreMode.AZURE_SEARCH
    else:
        vector_store_mode = None

    # Similar logic for embeddings_mode
    # ...

    return cls(
        search=search,  # Keep legacy
        azure_openai=azure_openai,  # Keep legacy
        vector_store_mode=vector_store_mode,
        # ...
    )
```

#### 1.4 Pipeline Integration

**Modify:** [src/ingestor/pipeline.py](c:\Work\ingest-o-bot\src\ingestor\pipeline.py)

Update component initialization (lines 408-424):
```python
async def _initialize_components(self):
    # ... existing code ...

    # Initialize embeddings provider (backward compatible)
    if self.embeddings_provider is None and not self.config.use_integrated_vectorization:
        logger.info("Initializing embeddings provider")

        # Determine mode
        if self.config.embeddings_mode:
            mode = self.config.embeddings_mode
            config = self.config.embeddings_config
        else:
            # Legacy: default to Azure OpenAI
            mode = EmbeddingsMode.AZURE_OPENAI
            config = self.config.azure_openai

        self.embeddings_provider = create_embeddings_provider(mode, config)
        logger.info(f"  Mode: {mode}")
        logger.info(f"  Model: {self.embeddings_provider.get_model_name()}")
        logger.info(f"  Dimensions: {self.embeddings_provider.get_dimensions()}")

    # Initialize vector store (backward compatible)
    if self.vector_store is None:
        logger.info("Initializing vector store")

        # Determine mode
        if self.config.vector_store_mode:
            mode = self.config.vector_store_mode
            config = self.config.vector_store_config
        else:
            # Legacy: default to Azure Search
            mode = VectorStoreMode.AZURE_SEARCH
            config = self.config.search

        self.vector_store = create_vector_store(mode, config, ...)
        logger.info(f"  Mode: {mode}")
```

Update method calls (lines 1594-1636):
```python
async def embed_chunks(self, chunk_docs: list[ChunkDocument]):
    # Replace: self.embeddings_gen
    # With: self.embeddings_provider
    embeddings = await self.embeddings_provider.generate_embeddings_batch(texts)

async def index_chunks(self, chunk_docs: list[ChunkDocument]) -> int:
    # Replace: self.search_uploader
    # With: self.vector_store
    count = await self.vector_store.upload_documents(chunk_docs, include_embeddings)
```

#### 1.5 Data Model Changes

**Modify:** [src/ingestor/models.py](c:\Work\ingest-o-bot\src\ingestor\models.py)

Add generic serialization method (after line 279):
```python
def to_vector_document(self, include_embeddings: bool = True) -> dict:
    """Convert to generic vector document format.

    This provides a standardized format that can be adapted by each
    vector store implementation. Azure Search uses to_search_document(),
    while other stores should use this method.
    """
    return {
        "id": self.chunk.chunk_id,
        "text": self.chunk.text,
        "embedding": self.chunk.embedding if include_embeddings else None,
        "metadata": {
            "sourcefile": self.document.sourcefile,
            "sourcepage": self.page.sourcepage,
            "page_number": self.page.page_num,
            "storage_url": self.page.page_blob_url or self.document.storage_url,
            "document_url": self.document.storage_url,
            "chunk_index": self.chunk.chunk_index_on_page,
            "title": self.chunk.title,
            "token_count": self.chunk.token_count,
            "has_figures": len(self.figures) > 0,
            "has_tables": len(self.tables) > 0,
            "figure_urls": [f.url for f in self.figures if f.url],
        }
    }
```

#### 1.6 Factory Functions

**In:** [src/ingestor/vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_store.py)
```python
def create_vector_store(
    mode: VectorStoreMode,
    config: Any,
    **kwargs
) -> VectorStore:
    """Factory function for vector stores."""
    if mode == VectorStoreMode.AZURE_SEARCH:
        from .vector_stores.azure_search_vector_store import AzureSearchVectorStore
        return AzureSearchVectorStore(config, **kwargs)
    # Phase 2+: Add ChromaDB, etc.
    else:
        raise ValueError(f"Unsupported vector store: {mode}")
```

**In:** [src/ingestor/embeddings_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_provider.py)
```python
def create_embeddings_provider(
    mode: EmbeddingsMode,
    config: Any,
    **kwargs
) -> EmbeddingsProvider:
    """Factory function for embeddings providers."""
    if mode == EmbeddingsMode.AZURE_OPENAI:
        from .embeddings_providers.azure_openai_provider import AzureOpenAIEmbeddingsProvider
        return AzureOpenAIEmbeddingsProvider(config, **kwargs)
    # Phase 3+: Add HuggingFace, Cohere, etc.
    else:
        raise ValueError(f"Unsupported embeddings mode: {mode}")
```

**Testing Phase 1:**
- All existing tests must pass unchanged
- Existing `.env` files must work without modification
- Pipeline runs with Azure Search + Azure OpenAI using new abstractions
- No functional changes, only architectural refactoring

---

### Phase 2: ChromaDB Vector Store Support

Add ChromaDB as an alternative vector database with support for all deployment modes.

#### 2.1 ChromaDB Configuration

**Modify:** [src/ingestor/config.py](c:\Work\ingest-o-bot\src\ingestor\config.py)

```python
@dataclass
class ChromaDBConfig:
    """Configuration for ChromaDB vector store.

    Supports three modes:
    1. Persistent: Local disk storage (persist_directory set)
    2. In-memory: Ephemeral storage (persist_directory=None, host=None)
    3. Client/server: Remote ChromaDB server (host and port set)
    """
    collection_name: str = "documents"

    # Local persistent or in-memory mode
    persist_directory: Optional[str] = None  # None = in-memory

    # Client/server mode
    host: Optional[str] = None
    port: Optional[int] = None

    # Optional: Authentication for client/server mode
    auth_token: Optional[str] = None

    # Performance tuning
    batch_size: int = 1000

    @classmethod
    def from_env(cls) -> "ChromaDBConfig":
        """Load from environment variables.

        Environment variables:
            CHROMADB_COLLECTION_NAME: Collection name (default: "documents")
            CHROMADB_PERSIST_DIR: Local storage directory (optional)
            CHROMADB_HOST: Server host for client/server mode (optional)
            CHROMADB_PORT: Server port (default: 8000)
            CHROMADB_AUTH_TOKEN: Authentication token (optional)
            CHROMADB_BATCH_SIZE: Upload batch size (default: 1000)
        """
        collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "documents")
        persist_directory = os.getenv("CHROMADB_PERSIST_DIR")
        host = os.getenv("CHROMADB_HOST")
        port_str = os.getenv("CHROMADB_PORT")
        port = int(port_str) if port_str else None
        auth_token = os.getenv("CHROMADB_AUTH_TOKEN")
        batch_size = int(os.getenv("CHROMADB_BATCH_SIZE", "1000"))

        return cls(
            collection_name=collection_name,
            persist_directory=persist_directory,
            host=host,
            port=port,
            auth_token=auth_token,
            batch_size=batch_size
        )
```

Update `PipelineConfig.from_env()`:
```python
# Auto-detect ChromaDB if environment variables present
if os.getenv("CHROMADB_COLLECTION_NAME") or os.getenv("CHROMADB_HOST"):
    vector_store_mode = VectorStoreMode.CHROMADB
    vector_store_config = ChromaDBConfig.from_env()
```

#### 2.2 ChromaDB Implementation

**Create:** [src/ingestor/vector_stores/chromadb_vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_stores\chromadb_vector_store.py)

```python
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
    1. Persistent local storage
    2. In-memory storage
    3. Client/server mode
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
        elif persist_directory:
            # Persistent local storage
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            # In-memory (ephemeral)
            self.client = chromadb.EphemeralClient()

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

        Note: ChromaDB requires client-side embeddings. If include_embeddings=False,
        this will raise an error.
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

            ids.append(doc_dict["id"])
            embeddings.append(doc_dict["embedding"])
            documents.append(doc_dict["text"])
            metadatas.append(doc_dict["metadata"])

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
        """Delete all documents with matching sourcefile metadata."""
        # ChromaDB uses where filters
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.collection.delete,
            None,  # ids
            {"sourcefile": filename}  # where filter
        )
        return 0  # ChromaDB doesn't return delete count

    async def delete_all_documents(self) -> int:
        """Delete all documents by deleting and recreating collection."""
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

        Note: This requires query embeddings to be generated externally.
        """
        raise NotImplementedError("Search requires query embedding generation")

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        if self._dimensions is None:
            raise ValueError("Dimensions not yet inferred. Upload documents first.")
        return self._dimensions

    async def close(self):
        """Cleanup resources."""
        # ChromaDB client doesn't require explicit cleanup
        pass
```

#### 2.3 Factory Function Update

**Modify:** [src/ingestor/vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_store.py)

```python
def create_vector_store(mode: VectorStoreMode, config: Any, **kwargs) -> VectorStore:
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
            auth_token=config.auth_token,
            batch_size=config.batch_size
        )

    else:
        raise ValueError(f"Unsupported vector store: {mode}")
```

#### 2.4 Optional Dependencies

**Create:** [requirements-chromadb.txt](c:\Work\ingest-o-bot\requirements-chromadb.txt)
```txt
# ChromaDB vector store support
chromadb>=0.4.22
```

**Update:** [README.md](c:\Work\ingest-o-bot\README.md) with installation instructions:
```bash
# For ChromaDB support
pip install -r requirements-chromadb.txt
```

#### 2.5 Configuration Examples

**Persistent ChromaDB (local disk):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=my-documents
CHROMADB_PERSIST_DIR=./chroma_db
```

**In-memory ChromaDB (temporary):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=temp-documents
# No CHROMADB_PERSIST_DIR = in-memory mode
```

**Client/Server ChromaDB:**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=shared-documents
CHROMADB_HOST=chromadb.example.com
CHROMADB_PORT=8000
CHROMADB_AUTH_TOKEN=secret-token-here
```

**Testing Phase 2:**
- Test persistent mode with disk storage
- Test in-memory mode (data lost on restart)
- Test client/server mode with remote ChromaDB
- Verify batch uploads with large document sets
- Test delete operations
- Ensure dimension compatibility checks work

---

### Phase 3: Multi-Model Embeddings Support

Add support for Hugging Face (with latest multilingual models), Cohere, and OpenAI embeddings.

#### 3.1 Hugging Face Embeddings Configuration

**Modify:** [src/ingestor/config.py](c:\Work\ingest-o-bot\src\ingestor\config.py)

```python
@dataclass
class HuggingFaceEmbeddingsConfig:
    """Configuration for Hugging Face embeddings using sentence-transformers.

    Supports local model execution (CPU/GPU) with various multilingual and
    specialized models.
    """
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"  # "cpu", "cuda", "mps" (Apple Silicon)
    batch_size: int = 32
    normalize_embeddings: bool = True
    max_seq_length: Optional[int] = None  # None = use model default
    trust_remote_code: bool = False  # Required for some custom models

    # Popular model options:
    # - "sentence-transformers/all-MiniLM-L6-v2" (384 dims, fast, English)
    # - "sentence-transformers/all-mpnet-base-v2" (768 dims, quality, English)
    # - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" (384 dims, multilingual)
    # - "sentence-transformers/paraphrase-multilingual-mpnet-base-v2" (768 dims, multilingual)
    # - "intfloat/multilingual-e5-large" (1024 dims, SOTA multilingual)
    # - "BAAI/bge-large-en-v1.5" (1024 dims, SOTA English)

    @classmethod
    def from_env(cls) -> "HuggingFaceEmbeddingsConfig":
        """Load from environment variables.

        Environment variables:
            HUGGINGFACE_MODEL_NAME: Model identifier from HuggingFace Hub
            HUGGINGFACE_DEVICE: Device to run on (cpu/cuda/mps)
            HUGGINGFACE_BATCH_SIZE: Batch size for encoding (default: 32)
            HUGGINGFACE_NORMALIZE: Normalize embeddings (default: true)
            HUGGINGFACE_MAX_SEQ_LENGTH: Max sequence length (optional)
            HUGGINGFACE_TRUST_REMOTE_CODE: Trust remote code (default: false)
        """
        model_name = os.getenv(
            "HUGGINGFACE_MODEL_NAME",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # Latest multilingual default
        )
        device = os.getenv("HUGGINGFACE_DEVICE", "cpu")
        batch_size = int(os.getenv("HUGGINGFACE_BATCH_SIZE", "32"))
        normalize = os.getenv("HUGGINGFACE_NORMALIZE", "true").lower() == "true"
        max_seq_str = os.getenv("HUGGINGFACE_MAX_SEQ_LENGTH")
        max_seq_length = int(max_seq_str) if max_seq_str else None
        trust_remote_code = os.getenv("HUGGINGFACE_TRUST_REMOTE_CODE", "false").lower() == "true"

        return cls(
            model_name=model_name,
            device=device,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            max_seq_length=max_seq_length,
            trust_remote_code=trust_remote_code
        )
```

#### 3.2 Cohere Embeddings Configuration

```python
@dataclass
class CohereEmbeddingsConfig:
    """Configuration for Cohere embeddings API.

    Cohere provides high-quality embeddings optimized for semantic search.
    """
    api_key: str
    model_name: str = "embed-multilingual-v3.0"  # Latest multilingual model
    input_type: str = "search_document"  # "search_document" or "search_query"
    truncate: str = "END"  # "NONE", "START", "END"

    # Model options:
    # - "embed-english-v3.0" (1024 dims, English only)
    # - "embed-multilingual-v3.0" (1024 dims, 100+ languages)
    # - "embed-english-light-v3.0" (384 dims, faster)
    # - "embed-multilingual-light-v3.0" (384 dims, faster, multilingual)

    @classmethod
    def from_env(cls) -> "CohereEmbeddingsConfig":
        """Load from environment variables.

        Environment variables:
            COHERE_API_KEY: Cohere API key (required)
            COHERE_MODEL_NAME: Model name (default: embed-multilingual-v3.0)
            COHERE_INPUT_TYPE: Input type (default: search_document)
            COHERE_TRUNCATE: Truncation strategy (default: END)
        """
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable required")

        model_name = os.getenv("COHERE_MODEL_NAME", "embed-multilingual-v3.0")
        input_type = os.getenv("COHERE_INPUT_TYPE", "search_document")
        truncate = os.getenv("COHERE_TRUNCATE", "END")

        return cls(
            api_key=api_key,
            model_name=model_name,
            input_type=input_type,
            truncate=truncate
        )
```

#### 3.3 OpenAI Embeddings Configuration

```python
@dataclass
class OpenAIEmbeddingsConfig:
    """Configuration for OpenAI embeddings API (non-Azure).

    For users who want to use OpenAI directly instead of Azure OpenAI.
    """
    api_key: str
    model_name: str = "text-embedding-3-small"
    dimensions: Optional[int] = None  # Optional for text-embedding-3-* models
    max_retries: int = 3
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "OpenAIEmbeddingsConfig":
        """Load from environment variables.

        Environment variables:
            OPENAI_API_KEY: OpenAI API key (required)
            OPENAI_EMBEDDING_MODEL: Model name (default: text-embedding-3-small)
            OPENAI_EMBEDDING_DIMENSIONS: Dimensions for v3 models (optional)
            OPENAI_MAX_RETRIES: Max retries (default: 3)
            OPENAI_TIMEOUT: Request timeout in seconds (default: 60)
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        dimensions_str = os.getenv("OPENAI_EMBEDDING_DIMENSIONS")
        dimensions = int(dimensions_str) if dimensions_str else None
        max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        timeout = int(os.getenv("OPENAI_TIMEOUT", "60"))

        return cls(
            api_key=api_key,
            model_name=model_name,
            dimensions=dimensions,
            max_retries=max_retries,
            timeout=timeout
        )
```

Update `PipelineConfig.from_env()` to auto-detect all modes:
```python
# Auto-detect embeddings mode
if os.getenv("EMBEDDINGS_MODE"):
    embeddings_mode = EmbeddingsMode(os.getenv("EMBEDDINGS_MODE"))
elif os.getenv("HUGGINGFACE_MODEL_NAME"):
    embeddings_mode = EmbeddingsMode.HUGGINGFACE
    embeddings_config = HuggingFaceEmbeddingsConfig.from_env()
elif os.getenv("COHERE_API_KEY"):
    embeddings_mode = EmbeddingsMode.COHERE
    embeddings_config = CohereEmbeddingsConfig.from_env()
elif os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_ENDPOINT"):
    embeddings_mode = EmbeddingsMode.OPENAI
    embeddings_config = OpenAIEmbeddingsConfig.from_env()
elif azure_openai.endpoint:
    # Legacy Azure OpenAI
    embeddings_mode = EmbeddingsMode.AZURE_OPENAI
    embeddings_config = azure_openai
```

#### 3.4 Hugging Face Implementation

**Create:** [src/ingestor/embeddings_providers/huggingface_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\huggingface_provider.py)

```python
from typing import Optional
import asyncio
from ..embeddings_provider import EmbeddingsProvider

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class HuggingFaceEmbeddingsProvider(EmbeddingsProvider):
    """Hugging Face embeddings using sentence-transformers.

    Supports local model execution with CPU/GPU acceleration and various
    multilingual and specialized models.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        max_seq_length: Optional[int] = None,
        trust_remote_code: bool = False
    ):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for Hugging Face embeddings. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings

        # Load model (downloads if not cached)
        self.model = SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=trust_remote_code
        )

        # Set max sequence length if specified
        if max_seq_length:
            self.model.max_seq_length = max_seq_length

        # Get dimensions from model
        self._dimensions = self.model.get_sentence_embedding_dimension()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        # sentence-transformers is CPU-bound, run in executor
        embedding = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.encode(
                text,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )
        )
        return embedding.tolist()

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.

        Automatically handles batching based on configured batch_size.
        """
        # Process all texts at once - model handles batching internally
        embeddings = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100  # Show progress for large batches
            )
        )
        return embeddings.tolist()

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name

    async def close(self):
        """Cleanup resources."""
        # Clear model from memory if needed
        if hasattr(self, 'model'):
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
```

#### 3.5 Cohere Implementation

**Create:** [src/ingestor/embeddings_providers/cohere_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\cohere_provider.py)

```python
from typing import Optional
import asyncio
from ..embeddings_provider import EmbeddingsProvider

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

class CohereEmbeddingsProvider(EmbeddingsProvider):
    """Cohere embeddings API provider."""

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
        """Generate embedding for a single text."""
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
        """Get embedding dimensions."""
        return self._dimensions

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name

    async def close(self):
        """Cleanup resources."""
        await self.client.close()
```

#### 3.6 OpenAI Implementation

**Create:** [src/ingestor/embeddings_providers/openai_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\openai_provider.py)

```python
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
        """Generate embedding for a single text."""
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
        """Generate embeddings for multiple texts."""
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
        """Get embedding dimensions."""
        return self._dimensions

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name

    async def close(self):
        """Cleanup resources."""
        await self.client.close()
```

#### 3.7 Factory Function Update

**Modify:** [src/ingestor/embeddings_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_provider.py)

```python
def create_embeddings_provider(mode: EmbeddingsMode, config: Any, **kwargs) -> EmbeddingsProvider:
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
            max_seq_length=config.max_seq_length,
            trust_remote_code=config.trust_remote_code
        )

    elif mode == EmbeddingsMode.COHERE:
        from .embeddings_providers.cohere_provider import CohereEmbeddingsProvider
        return CohereEmbeddingsProvider(
            api_key=config.api_key,
            model_name=config.model_name,
            input_type=config.input_type,
            truncate=config.truncate
        )

    elif mode == EmbeddingsMode.OPENAI:
        from .embeddings_providers.openai_provider import OpenAIEmbeddingsProvider
        return OpenAIEmbeddingsProvider(
            api_key=config.api_key,
            model_name=config.model_name,
            dimensions=config.dimensions,
            max_retries=config.max_retries,
            timeout=config.timeout
        )

    else:
        raise ValueError(f"Unsupported embeddings mode: {mode}")
```

#### 3.8 Optional Dependencies

**Create:** [requirements-embeddings.txt](c:\Work\ingest-o-bot\requirements-embeddings.txt)
```txt
# Hugging Face embeddings
sentence-transformers>=2.3.0
torch>=2.0.0

# Cohere embeddings
cohere>=5.0.0

# OpenAI embeddings (already included in base requirements)
# openai>=1.10.0
```

**Update:** [README.md](c:\Work\ingest-o-bot\README.md):
```bash
# For Hugging Face embeddings (local models)
pip install -r requirements-embeddings.txt

# For Cohere embeddings only
pip install cohere
```

#### 3.9 Configuration Examples

**Hugging Face (latest multilingual):**
```bash
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda  # or cpu or mps
HUGGINGFACE_BATCH_SIZE=32
```

**Cohere (multilingual v3):**
```bash
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-api-key
COHERE_MODEL_NAME=embed-multilingual-v3.0
```

**OpenAI (direct API):**
```bash
EMBEDDINGS_MODE=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_EMBEDDING_DIMENSIONS=1024
```

**Mix and Match:**
```bash
# ChromaDB + Hugging Face (fully offline)
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db

EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=BAAI/bge-large-en-v1.5

# Azure Search + Cohere
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_ENDPOINT=https://...

EMBEDDINGS_MODE=cohere
COHERE_API_KEY=...
```

**Testing Phase 3:**
- Test each embeddings provider independently
- Test with different models (multilingual, English, domain-specific)
- Verify dimension compatibility with vector stores
- Performance benchmarks (speed, quality, cost)
- Test all combinations (4 embeddings × 2 vector stores = 8 configs)

---

### Phase 4: Documentation & Examples

Comprehensive documentation for all configurations and use cases.

#### 4.1 Documentation Files to Create

**Create:** [docs/vector_stores.md](c:\Work\ingest-o-bot\docs\vector_stores.md)
- Overview of vector store abstraction
- Azure AI Search guide (existing functionality)
- ChromaDB guide (all three modes with examples)
- Comparison table (features, performance, cost)
- When to use which vector store

**Create:** [docs/embeddings_providers.md](c:\Work\ingest-o-bot\docs\embeddings_providers.md)
- Overview of embeddings abstraction
- Azure OpenAI guide (existing functionality)
- Hugging Face guide (model selection, GPU setup)
- Cohere guide (API setup, pricing)
- OpenAI guide (direct API usage)
- Model comparison table (dimensions, languages, quality, speed, cost)
- Multilingual best practices

**Create:** [docs/configuration_guide.md](c:\Work\ingest-o-bot\docs\configuration_guide.md)
- Complete environment variable reference
- Configuration file examples
- Mix-and-match scenarios
- Backward compatibility notes
- Troubleshooting guide

**Create:** [docs/migration_guide.md](c:\Work\ingest-o-bot\docs\migration_guide.md)
- Migrating from legacy configuration
- Step-by-step migration examples
- Breaking changes (if any)
- Deprecation timeline

**Update:** [README.md](c:\Work\ingest-o-bot\README.md)
- Add "Vector Stores" section
- Add "Embeddings Providers" section
- Update installation instructions
- Update quick start examples

#### 4.2 Example Scripts to Create

**Create:** [examples/chromadb_persistent.py](c:\Work\ingest-o-bot\examples\chromadb_persistent.py)
```python
"""Example: Using ChromaDB with persistent storage and Hugging Face embeddings."""
import asyncio
from ingestor import ConfigBuilder, Pipeline

async def main():
    # Configure pipeline with ChromaDB + Hugging Face
    config = (
        ConfigBuilder()
        .with_local_files("docs/*.pdf")
        .with_chromadb(
            collection_name="my-documents",
            persist_directory="./chroma_db"
        )
        .with_huggingface_embeddings(
            model_name="intfloat/multilingual-e5-large",
            device="cpu"
        )
        .with_local_artifacts("./artifacts")
        .build()
    )

    # Run pipeline
    pipeline = Pipeline(config)
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Create:** [examples/cohere_azure_search.py](c:\Work\ingest-o-bot\examples\cohere_azure_search.py)
```python
"""Example: Using Cohere embeddings with Azure AI Search."""
import asyncio
from ingestor import ConfigBuilder, Pipeline

async def main():
    # Mix Cohere embeddings with Azure Search
    config = (
        ConfigBuilder()
        .with_blob_input(
            container_name="documents",
            connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        )
        .with_azure_search(
            service_name="my-search",
            index_name="documents",
            api_key=os.getenv("AZURE_SEARCH_KEY")
        )
        .with_cohere_embeddings(
            api_key=os.getenv("COHERE_API_KEY"),
            model_name="embed-multilingual-v3.0"
        )
        .with_blob_artifacts(
            container_name="artifacts",
            connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        )
        .build()
    )

    pipeline = Pipeline(config)
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Create:** [examples/offline_setup.py](c:\Work\ingest-o-bot\examples\offline_setup.py)
```python
"""Example: Fully offline setup with ChromaDB + Hugging Face (no cloud services)."""
import asyncio
from ingestor import ConfigBuilder, Pipeline

async def main():
    # Completely offline configuration
    config = (
        ConfigBuilder()
        .with_local_files("documents/*.pdf")
        .with_chromadb(
            collection_name="offline-docs",
            persist_directory="./vector_db"
        )
        .with_huggingface_embeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        .with_local_artifacts("./artifacts")
        .with_markitdown_extractor()  # Local extraction, no Azure DI
        .build()
    )

    pipeline = Pipeline(config)
    await pipeline.run()
    print("Pipeline completed successfully - all data stored locally!")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 4.3 ConfigBuilder Extensions

**Modify:** [src/ingestor/config_builder.py](c:\Work\ingest-o-bot\src\ingestor\config_builder.py)

Add new fluent methods:
```python
class ConfigBuilder:
    # Existing methods...

    def with_chromadb(
        self,
        collection_name: str = "documents",
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
    ) -> "ConfigBuilder":
        """Configure ChromaDB vector store."""
        self._vector_store_mode = VectorStoreMode.CHROMADB
        self._vector_store_config = ChromaDBConfig(
            collection_name=collection_name,
            persist_directory=persist_directory,
            host=host,
            port=port
        )
        return self

    def with_huggingface_embeddings(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32
    ) -> "ConfigBuilder":
        """Configure Hugging Face embeddings."""
        self._embeddings_mode = EmbeddingsMode.HUGGINGFACE
        self._embeddings_config = HuggingFaceEmbeddingsConfig(
            model_name=model_name,
            device=device,
            batch_size=batch_size
        )
        return self

    def with_cohere_embeddings(
        self,
        api_key: str,
        model_name: str = "embed-multilingual-v3.0"
    ) -> "ConfigBuilder":
        """Configure Cohere embeddings."""
        self._embeddings_mode = EmbeddingsMode.COHERE
        self._embeddings_config = CohereEmbeddingsConfig(
            api_key=api_key,
            model_name=model_name
        )
        return self

    def with_openai_embeddings(
        self,
        api_key: str,
        model_name: str = "text-embedding-3-small",
        dimensions: Optional[int] = None
    ) -> "ConfigBuilder":
        """Configure OpenAI embeddings."""
        self._embeddings_mode = EmbeddingsMode.OPENAI
        self._embeddings_config = OpenAIEmbeddingsConfig(
            api_key=api_key,
            model_name=model_name,
            dimensions=dimensions
        )
        return self
```

#### 4.4 Testing Documentation

**Create:** [tests/README_TESTING.md](c:\Work\ingest-o-bot\tests\README_TESTING.md)

Document testing strategies:
- Unit tests for each implementation
- Integration tests for each combination
- Performance benchmarks
- Dimension compatibility tests
- Error handling tests

---

## Critical Files Summary

### Files to Create (New)

1. **[src/ingestor/vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_store.py)** - VectorStore ABC and factory
2. **[src/ingestor/embeddings_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_provider.py)** - EmbeddingsProvider ABC and factory
3. **[src/ingestor/vector_stores/azure_search_vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_stores\azure_search_vector_store.py)** - Azure Search wrapper
4. **[src/ingestor/vector_stores/chromadb_vector_store.py](c:\Work\ingest-o-bot\src\ingestor\vector_stores\chromadb_vector_store.py)** - ChromaDB implementation
5. **[src/ingestor/embeddings_providers/azure_openai_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\azure_openai_provider.py)** - Azure OpenAI wrapper
6. **[src/ingestor/embeddings_providers/huggingface_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\huggingface_provider.py)** - Hugging Face implementation
7. **[src/ingestor/embeddings_providers/cohere_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\cohere_provider.py)** - Cohere implementation
8. **[src/ingestor/embeddings_providers/openai_provider.py](c:\Work\ingest-o-bot\src\ingestor\embeddings_providers\openai_provider.py)** - OpenAI implementation

### Files to Modify (Existing)

1. **[src/ingestor/config.py](c:\Work\ingest-o-bot\src\ingestor\config.py)** - Add enums, configs, backward compatibility (lines 618-716)
2. **[src/ingestor/pipeline.py](c:\Work\ingest-o-bot\src\ingestor\pipeline.py)** - Update initialization and method calls (lines 408-424, 1594-1636)
3. **[src/ingestor/models.py](c:\Work\ingest-o-bot\src\ingestor\models.py)** - Add `to_vector_document()` method (after line 279)
4. **[src/ingestor/config_builder.py](c:\Work\ingest-o-bot\src\ingestor\config_builder.py)** - Add fluent methods for new configs

---

## Verification Plan

### Phase 1 Verification (Refactor)
```bash
# Existing configuration should work unchanged
python -m pytest tests/

# Pipeline with Azure Search + Azure OpenAI
python src/ingestor/cli.py --validate
python src/ingestor/cli.py --env .env
```

### Phase 2 Verification (ChromaDB)
```bash
# Test ChromaDB persistent mode
VECTOR_STORE_MODE=chromadb CHROMADB_PERSIST_DIR=./test_db python -m pytest tests/test_chromadb.py

# Test ChromaDB in-memory mode
VECTOR_STORE_MODE=chromadb python examples/chromadb_persistent.py

# Verify data persists across runs
ls -la ./chroma_db/
```

### Phase 3 Verification (Embeddings)
```bash
# Test Hugging Face embeddings
EMBEDDINGS_MODE=huggingface HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2 python tests/test_embeddings.py

# Test Cohere embeddings
EMBEDDINGS_MODE=cohere COHERE_API_KEY=xxx python tests/test_embeddings.py

# Test mix: ChromaDB + Hugging Face (fully offline)
python examples/offline_setup.py

# Test mix: Azure Search + Cohere
python examples/cohere_azure_search.py
```

### End-to-End Verification
```bash
# Process real documents with each combination
for vector_store in azure_search chromadb; do
  for embeddings in azure_openai huggingface cohere openai; do
    echo "Testing: $vector_store + $embeddings"
    # Run pipeline with specific configuration
    python run_pipeline.py --vector-store=$vector_store --embeddings=$embeddings
  done
done
```

---

## Timeline Estimate

- **Phase 0 (Architecture):** Already complete (this document)
- **Phase 1 (Refactor):** 3-4 days
- **Phase 2 (ChromaDB):** 2-3 days
- **Phase 3 (Embeddings):** 3-4 days
- **Phase 4 (Documentation):** 1-2 days

**Total:** ~2 weeks for complete implementation

---

## Success Criteria

✅ **Backward Compatibility:** All existing configurations work unchanged
✅ **Extensibility:** New vector stores and embeddings providers can be added easily
✅ **Mix & Match:** Any combination of vector store + embeddings works
✅ **Documentation:** Complete guides for all configurations
✅ **Examples:** Working examples for common use cases
✅ **Testing:** Comprehensive test coverage for all combinations
✅ **Performance:** No degradation compared to current implementation
✅ **User Choice:** Support for latest multilingual models and multiple providers

---

## Next Steps

1. **Review this plan** and approve architecture
2. **Confirm priorities:** Which phase to start with?
3. **Environment setup:** Install optional dependencies for testing
4. **Begin Phase 1:** Create abstractions and wrappers
5. **Iterate:** Test each phase before moving to next
