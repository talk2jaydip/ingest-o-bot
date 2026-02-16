"""Configuration management for ingestor."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ingestor.logging_utils import get_logger


class InputMode(str, Enum):
    """Input source mode."""
    LOCAL = "local"
    BLOB = "blob"


class ArtifactsMode(str, Enum):
    """Artifacts storage mode."""
    LOCAL = "local"
    BLOB = "blob"


class MediaDescriberMode(str, Enum):
    """Media description service."""
    GPT4O = "gpt4o"
    CONTENT_UNDERSTANDING = "content_understanding"
    DISABLED = "disabled"


class TableRenderMode(str, Enum):
    """Table rendering format."""
    PLAIN = "plain"
    MARKDOWN = "markdown"
    HTML = "html"  # Render as HTML (best for frontend display)


class DocumentAction(str, Enum):
    """Document processing action mode."""
    ADD = "add"           # Add/update documents (default)
    REMOVE = "remove"     # Remove specific documents by filename
    REMOVE_ALL = "removeall"  # Remove all documents from index


class OfficeExtractorMode(str, Enum):
    """Office document extraction mode."""
    AZURE_DI = "azure_di"      # Azure Document Intelligence only (DOCX/PPTX only, DOC fails)
    MARKITDOWN = "markitdown"  # MarkItDown only (fully offline, all formats)
    HYBRID = "hybrid"          # Azure DI first, fallback to MarkItDown (recommended)


class VectorStoreMode(str, Enum):
    """Vector database mode."""
    AZURE_SEARCH = "azure_search"  # Azure AI Search (default)
    CHROMADB = "chromadb"          # ChromaDB (local/cloud)
    PINECONE = "pinecone"          # Pinecone (cloud-based)
    WEAVIATE = "weaviate"          # Weaviate
    QDRANT = "qdrant"              # Qdrant


class EmbeddingsMode(str, Enum):
    """Embeddings provider mode."""
    AZURE_OPENAI = "azure_openai"  # Azure OpenAI (default)
    HUGGINGFACE = "huggingface"    # Hugging Face sentence-transformers (local)
    COHERE = "cohere"              # Cohere embeddings API
    OPENAI = "openai"              # OpenAI embeddings API (non-Azure)


@dataclass
class AzureCredentials:
    """Azure Service Principal credentials for Key Vault and other services."""
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "AzureCredentials":
        """Load from environment variables."""
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )


@dataclass
class KeyVaultConfig:
    """Azure Key Vault configuration."""
    uri: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "KeyVaultConfig":
        """Load from environment variables."""
        uri = os.getenv("KEY_VAULT_URI")
        return cls(uri=uri)


@dataclass
class SearchConfig:
    """Azure AI Search configuration."""
    endpoint: Optional[str] = None
    index_name: Optional[str] = None
    api_key: Optional[str] = None
    service_name: Optional[str] = None  # Helper field for programmatic config
    
    @classmethod
    def from_env(cls) -> "SearchConfig":
        """Load from environment variables."""
        search_service = os.getenv("AZURE_SEARCH_SERVICE")
        if search_service:
            endpoint = f"https://{search_service}.search.windows.net"
        else:
            endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")

        index_name = os.getenv("AZURE_SEARCH_INDEX")
        api_key = os.getenv("AZURE_SEARCH_KEY")

        if not endpoint:
            raise ValueError(
                "Azure AI Search configuration is incomplete.\n"
                "  Missing: AZURE_SEARCH_SERVICE or AZURE_SEARCH_ENDPOINT\n"
                "  \n"
                "  Set one of:\n"
                "    AZURE_SEARCH_SERVICE=your-search-service\n"
                "    OR\n"
                "    AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net\n"
                "  \n"
                "  If using ChromaDB instead, set:\n"
                "    VECTOR_STORE_MODE=chromadb\n"
                "  \n"
                "  See: envs/.env.example or envs/.env.chromadb.example"
            )
        if not index_name:
            raise ValueError(
                "Azure AI Search index name is required.\n"
                "  Missing: AZURE_SEARCH_INDEX\n"
                "  \n"
                "  Set in your .env file:\n"
                "    AZURE_SEARCH_INDEX=your-index-name\n"
            )

        return cls(
            endpoint=endpoint,
            index_name=index_name,
            api_key=api_key
        )


@dataclass
class ChromaDBConfig:
    """ChromaDB vector store configuration.

    Supports three deployment modes:
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


@dataclass
class DocumentIntelligenceConfig:
    """Azure Document Intelligence configuration."""
    endpoint: Optional[str] = None
    key: Optional[str] = None
    max_concurrency: int = 3

    @classmethod
    def from_env(cls) -> "DocumentIntelligenceConfig":
        """Load from environment variables."""
        endpoint = os.getenv("AZURE_DOC_INT_ENDPOINT") or os.getenv("AZURE_DOC_INT_ENDOINT")
        key = os.getenv("AZURE_DOC_INT_KEY")
        max_concurrency = int(os.getenv("AZURE_DI_MAX_CONCURRENCY", "3"))

        # Check if Document Intelligence is actually needed
        office_mode = os.getenv("EXTRACTION_MODE") or os.getenv("AZURE_OFFICE_EXTRACTOR_MODE", "hybrid")

        if not endpoint:
            if office_mode == "markitdown":
                # DI not needed for markitdown-only mode
                return cls(endpoint=None, key=None, max_concurrency=max_concurrency)
            else:
                raise ValueError(
                    "Azure Document Intelligence configuration is required.\n"
                    "  Missing: AZURE_DOC_INT_ENDPOINT\n"
                    "  \n"
                    "  Options:\n"
                    "  1. Use Azure Document Intelligence (recommended):\n"
                    "       AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/\n"
                    "       AZURE_DOC_INT_KEY=your-key\n"
                    "       EXTRACTION_MODE=hybrid (or azure_di)\n"
                    "  \n"
                    "  2. Use offline processing only (no Azure DI):\n"
                    "       EXTRACTION_MODE=markitdown\n"
                    "       (No AZURE_DOC_INT_ENDPOINT needed)\n"
                    "  \n"
                    "  See: envs/.env.scenarios.example for configuration examples"
                )

        return cls(
            endpoint=endpoint,
            key=key,
            max_concurrency=max_concurrency
        )


@dataclass
class OfficeExtractorConfig:
    """Document extraction configuration for ALL document types (PDF + Office).

    IMPORTANT: This mode applies to the ENTIRE pipeline, not just Office documents!

    Three modes:
    - azure_di: Azure DI for ALL documents (PDF, DOCX, PPTX) - no fallback
    - markitdown: Offline for ALL documents (PDF uses pypdf/pymupdf, Office uses MarkItDown) - fully offline
    - hybrid: Try Azure DI first for all documents, fallback to offline processing (recommended)
    """
    mode: OfficeExtractorMode = OfficeExtractorMode.HYBRID  # Default: hybrid mode
    offline_fallback: bool = True  # Only applies to HYBRID mode: enable MarkItDown fallback
    equation_extraction: bool = False  # Phase 3: Premium equation/formula extraction
    max_file_size_mb: int = 100
    libreoffice_path: Optional[str] = None  # Phase 2: For DOC conversion via LibreOffice
    verbose: bool = False  # Enable detailed debug logging for troubleshooting

    @classmethod
    def from_env(cls) -> "OfficeExtractorConfig":
        """Load from environment variables.

        Modes:
        - azure_di: Azure DI only, no fallback (offline_fallback ignored)
        - markitdown: MarkItDown only, no Azure DI (offline_fallback ignored)
        - hybrid: Try Azure DI first, fallback based on offline_fallback flag (default)
        """
        logger = get_logger(__name__)

        # EXTRACTION_MODE (formerly AZURE_OFFICE_EXTRACTOR_MODE)
        mode_str = os.getenv("EXTRACTION_MODE") or os.getenv("AZURE_OFFICE_EXTRACTOR_MODE", "hybrid")
        if os.getenv("AZURE_OFFICE_EXTRACTOR_MODE") and not os.getenv("EXTRACTION_MODE"):
            logger.warning(
                "AZURE_OFFICE_EXTRACTOR_MODE is deprecated. Use EXTRACTION_MODE instead. "
                "Support for AZURE_OFFICE_EXTRACTOR_MODE will be removed in v2.0."
            )
        mode = OfficeExtractorMode(mode_str)

        # EXTRACTION_OFFLINE_FALLBACK (formerly AZURE_OFFICE_OFFLINE_FALLBACK)
        fallback_str = os.getenv("EXTRACTION_OFFLINE_FALLBACK") or os.getenv("AZURE_OFFICE_OFFLINE_FALLBACK", "true")
        if os.getenv("AZURE_OFFICE_OFFLINE_FALLBACK") and not os.getenv("EXTRACTION_OFFLINE_FALLBACK"):
            logger.warning(
                "AZURE_OFFICE_OFFLINE_FALLBACK is deprecated. Use EXTRACTION_OFFLINE_FALLBACK instead. "
                "Support for AZURE_OFFICE_OFFLINE_FALLBACK will be removed in v2.0."
            )
        offline_fallback = fallback_str.lower() == "true"

        # EXTRACTION_LIBREOFFICE_PATH (formerly AZURE_OFFICE_LIBREOFFICE_PATH)
        libreoffice_path = os.getenv("EXTRACTION_LIBREOFFICE_PATH") or os.getenv("AZURE_OFFICE_LIBREOFFICE_PATH")
        if os.getenv("AZURE_OFFICE_LIBREOFFICE_PATH") and not os.getenv("EXTRACTION_LIBREOFFICE_PATH"):
            logger.warning(
                "AZURE_OFFICE_LIBREOFFICE_PATH is deprecated. Use EXTRACTION_LIBREOFFICE_PATH instead. "
                "Support for AZURE_OFFICE_LIBREOFFICE_PATH will be removed in v2.0."
            )

        # EXTRACTION_EQUATIONS_ENABLED (formerly AZURE_OFFICE_EQUATION_EXTRACTION)
        equation_str = os.getenv("EXTRACTION_EQUATIONS_ENABLED") or os.getenv("AZURE_OFFICE_EQUATION_EXTRACTION", "false")
        if os.getenv("AZURE_OFFICE_EQUATION_EXTRACTION") and not os.getenv("EXTRACTION_EQUATIONS_ENABLED"):
            logger.warning(
                "AZURE_OFFICE_EQUATION_EXTRACTION is deprecated. Use EXTRACTION_EQUATIONS_ENABLED instead. "
                "Support for AZURE_OFFICE_EQUATION_EXTRACTION will be removed in v2.0."
            )
        equation_extraction = equation_str.lower() == "true"

        # EXTRACTION_MAX_FILE_SIZE_MB (formerly AZURE_OFFICE_MAX_FILE_SIZE_MB)
        max_size_str = os.getenv("EXTRACTION_MAX_FILE_SIZE_MB") or os.getenv("AZURE_OFFICE_MAX_FILE_SIZE_MB", "100")
        if os.getenv("AZURE_OFFICE_MAX_FILE_SIZE_MB") and not os.getenv("EXTRACTION_MAX_FILE_SIZE_MB"):
            logger.warning(
                "AZURE_OFFICE_MAX_FILE_SIZE_MB is deprecated. Use EXTRACTION_MAX_FILE_SIZE_MB instead. "
                "Support for AZURE_OFFICE_MAX_FILE_SIZE_MB will be removed in v2.0."
            )
        max_file_size_mb = int(max_size_str)

        # EXTRACTION_VERBOSE (formerly AZURE_OFFICE_VERBOSE)
        verbose_str = os.getenv("EXTRACTION_VERBOSE") or os.getenv("AZURE_OFFICE_VERBOSE", "false")
        if os.getenv("AZURE_OFFICE_VERBOSE") and not os.getenv("EXTRACTION_VERBOSE"):
            logger.warning(
                "AZURE_OFFICE_VERBOSE is deprecated. Use EXTRACTION_VERBOSE instead. "
                "Support for AZURE_OFFICE_VERBOSE will be removed in v2.0."
            )
        verbose = verbose_str.lower() == "true"

        return cls(
            mode=mode,
            offline_fallback=offline_fallback,
            equation_extraction=equation_extraction,
            max_file_size_mb=max_file_size_mb,
            libreoffice_path=libreoffice_path,
            verbose=verbose
        )

    def log_configuration(self, logger) -> None:
        """Log the current configuration for debugging.

        Always logs mode and key settings at INFO level.
        Logs detailed configuration at INFO level only if verbose=True.
        """
        # Always log the active mode prominently
        mode_emoji = {
            OfficeExtractorMode.AZURE_DI: "☁️",
            OfficeExtractorMode.MARKITDOWN: "📝",
            OfficeExtractorMode.HYBRID: "🔄"
        }
        emoji = mode_emoji.get(self.mode, "")

        logger.info("=" * 80)
        logger.info(f"{emoji} DOCUMENT PROCESSING MODE (ALL TYPES): {self.mode.value.upper()} {emoji}")
        logger.info("=" * 80)

        # Log mode-specific behavior
        if self.mode == OfficeExtractorMode.AZURE_DI:
            logger.info("  📋 Strategy: Azure Document Intelligence for ALL documents")
            logger.info("  ✅ PDF: Azure DI")
            logger.info("  ✅ DOCX/PPTX: Azure DI")

            # DOC support status based on offline_fallback flag
            if self.offline_fallback:
                logger.info("  ✅ DOC: MarkItDown (fallback enabled)")
                logger.info("  🔧 AZURE_OFFICE_OFFLINE_FALLBACK: Enabled (DOC files use MarkItDown)")
            else:
                logger.info("  ❌ DOC: NOT supported (will fail)")
                logger.info("  🔧 AZURE_OFFICE_OFFLINE_FALLBACK: Disabled (DOC files will fail)")

            logger.info("  💻 Offline capability: Partial (DOC only, if fallback enabled)")
        elif self.mode == OfficeExtractorMode.MARKITDOWN:
            logger.info("  📋 Strategy: Offline processing for ALL documents")
            logger.info("  ✅ PDF: MarkItDown (offline)")
            logger.info("  ✅ DOCX/PPTX/DOC: MarkItDown (offline)")
            logger.info("  💻 Azure DI: NOT used")
            logger.info("  🔧 Fallback: Not applicable")
            logger.info("  💻 Offline: YES - fully offline, no Azure services")
        elif self.mode == OfficeExtractorMode.HYBRID:
            logger.info("  📋 Strategy: Azure DI first, offline fallback for ALL documents")
            logger.info("  ✅ PDF: Azure DI → MarkItDown (if fallback enabled)")
            logger.info("  ✅ DOCX/PPTX: Azure DI → MarkItDown (if fallback enabled)")
            logger.info("  ✅ DOC: MarkItDown only (Azure DI doesn't support)")
            logger.info(f"  🔧 Fallback: {'Enabled' if self.offline_fallback else 'Disabled'}")
            if self.offline_fallback:
                logger.info("     → Falls back to offline processing if Azure DI fails")
            else:
                logger.info("     → Fails if Azure DI unavailable (strict mode)")

        # Log other key settings
        logger.info(f"  📐 Max file size: {self.max_file_size_mb}MB")
        logger.info(f"  🧮 Equation extraction: {'Enabled' if self.equation_extraction else 'Disabled'}")

        if self.libreoffice_path:
            logger.info(f"  📄 LibreOffice path: {self.libreoffice_path}")

        # Detailed configuration only if verbose
        if self.verbose:
            logger.info("")
            logger.info("  🔍 VERBOSE MODE ENABLED - Detailed logging active")
            logger.info(f"     → offline_fallback: {self.offline_fallback}")
            logger.info(f"     → equation_extraction: {self.equation_extraction}")
            logger.info(f"     → max_file_size_mb: {self.max_file_size_mb}")
            logger.info(f"     → libreoffice_path: {self.libreoffice_path or 'Not set'}")

        logger.info("=" * 80)


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI configuration."""
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_version: str = "2024-12-01-preview"
    emb_deployment: Optional[str] = None
    emb_model_name: str = "text-embedding-ada-002"
    emb_dimensions: Optional[int] = None  # Custom dimensions for text-embedding-3-* models
    chat_deployment: Optional[str] = None
    chat_model_name: Optional[str] = None
    vision_deployment: Optional[str] = None  # For GPT-4o vision (media describer)
    vision_model_name: Optional[str] = None
    vision_api_version: Optional[str] = None  # Separate API version for vision (optional)
    max_concurrency: int = 5
    max_retries: int = 3  # Retry attempts for API calls
    
    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """Load from environment variables."""
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        emb_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        emb_model_name = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL") or os.getenv("AZURE_OPENAI_EMBEDDING_NAME", "text-embedding-ada-002")

        # Embedding dimensions for text-embedding-3-* models (optional)
        emb_dimensions_str = os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS")
        emb_dimensions = int(emb_dimensions_str) if emb_dimensions_str else None

        chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        chat_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME") or os.getenv("AZURE_OPENAI_MODEL")

        # Vision model for media describer (GPT-4o with vision capability)
        vision_deployment = os.getenv("AZURE_OPENAI_VISION_DEPLOYMENT")
        vision_model_name = os.getenv("AZURE_OPENAI_VISION_MODEL")
        vision_api_version = os.getenv("AZURE_OPENAI_VISION_API_VERSION")  # Optional separate API version for vision

        max_concurrency = int(os.getenv("AZURE_OPENAI_MAX_CONCURRENCY", "5"))
        max_retries = int(os.getenv("AZURE_OPENAI_MAX_RETRIES", "3"))

        # Check if Azure OpenAI is actually needed
        embeddings_mode = os.getenv("EMBEDDINGS_MODE", "azure_openai").lower()
        use_integrated = os.getenv("AZURE_USE_INTEGRATED_VECTORIZATION", "false").lower() == "true"

        if not endpoint:
            if embeddings_mode in ["huggingface", "cohere", "openai"]:
                # Azure OpenAI not needed for alternative embeddings
                return cls(
                    endpoint=None,
                    api_key=None,
                    emb_deployment=None,
                    emb_model_name=emb_model_name,
                    emb_dimensions=emb_dimensions,
                    chat_deployment=chat_deployment,
                    chat_model_name=chat_model_name,
                    vision_deployment=vision_deployment,
                    vision_model_name=vision_model_name,
                    vision_api_version=vision_api_version,
                    max_concurrency=max_concurrency,
                    max_retries=max_retries
                )
            else:
                raise ValueError(
                    "Azure OpenAI configuration is required.\n"
                    "  Missing: AZURE_OPENAI_ENDPOINT\n"
                    "  \n"
                    "  Options:\n"
                    "  1. Use Azure OpenAI for embeddings (default):\n"
                    "       AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/\n"
                    "       AZURE_OPENAI_KEY=your-key\n"
                    "       AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002\n"
                    "  \n"
                    "  2. Use alternative embeddings provider:\n"
                    "       EMBEDDINGS_MODE=huggingface (local, free)\n"
                    "       OR\n"
                    "       EMBEDDINGS_MODE=cohere (cloud API)\n"
                    "       COHERE_API_KEY=your-key\n"
                    "  \n"
                    "  See: envs/.env.chromadb.example (offline with HuggingFace)\n"
                    "       envs/.env.cohere.example (Cohere embeddings)"
                )

        if not api_key:
            raise ValueError(
                "Azure OpenAI API key is required.\n"
                "  Missing: AZURE_OPENAI_KEY (or AZURE_OPENAI_API_KEY)\n"
                "  \n"
                "  Set in your .env file:\n"
                "    AZURE_OPENAI_KEY=your-api-key\n"
            )

        if not emb_deployment and not use_integrated and embeddings_mode == "azure_openai":
            raise ValueError(
                "Azure OpenAI embedding deployment is required.\n"
                "  Missing: AZURE_OPENAI_EMBEDDING_DEPLOYMENT\n"
                "  \n"
                "  Set in your .env file:\n"
                "    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002\n"
                "  \n"
                "  Or use integrated vectorization:\n"
                "    AZURE_USE_INTEGRATED_VECTORIZATION=true\n"
            )

        return cls(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            emb_deployment=emb_deployment,
            emb_model_name=emb_model_name,
            emb_dimensions=emb_dimensions,
            chat_deployment=chat_deployment,
            chat_model_name=chat_model_name,
            vision_deployment=vision_deployment,
            vision_model_name=vision_model_name,
            vision_api_version=vision_api_version,
            max_concurrency=max_concurrency,
            max_retries=max_retries
        )


@dataclass
class HuggingFaceEmbeddingsConfig:
    """Hugging Face embeddings configuration using sentence-transformers.

    Supports local model execution (CPU/GPU) with various multilingual and
    specialized models.
    """
    model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # Latest multilingual default
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
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
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


@dataclass
class CohereEmbeddingsConfig:
    """Cohere embeddings API configuration.

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


@dataclass
class OpenAIEmbeddingsConfig:
    """OpenAI embeddings API configuration (non-Azure).

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


@dataclass
class ContentUnderstandingConfig:
    """Azure Content Understanding configuration."""
    endpoint: str
    tenant_id: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> Optional["ContentUnderstandingConfig"]:
        """Load from environment variables."""
        endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
        if not endpoint:
            return None
        
        tenant_id = os.getenv("AZURE_CONTENT_UNDERSTANDING_TENANT_ID")
        return cls(endpoint=endpoint, tenant_id=tenant_id)


@dataclass
class InputConfig:
    """Input source configuration."""
    mode: InputMode = InputMode.LOCAL
    # Local mode
    local_glob: Optional[str] = None
    # Blob mode
    blob_account_url: Optional[str] = None
    blob_container_in: Optional[str] = None
    blob_prefix: Optional[str] = None
    blob_key: Optional[str] = None
    blob_connection_string: Optional[str] = None

    @classmethod
    def from_env(cls) -> "InputConfig":
        """Load from environment variables."""
        logger = get_logger(__name__)

        # INPUT_MODE (formerly AZURE_INPUT_MODE)
        mode_str = os.getenv("INPUT_MODE") or os.getenv("AZURE_INPUT_MODE", "local")
        if os.getenv("AZURE_INPUT_MODE") and not os.getenv("INPUT_MODE"):
            logger.warning(
                "AZURE_INPUT_MODE is deprecated. Use INPUT_MODE instead. "
                "Support for AZURE_INPUT_MODE will be removed in v2.0."
            )
        mode = InputMode(mode_str.lower())

        if mode == InputMode.LOCAL:
            # LOCAL_INPUT_GLOB (formerly AZURE_LOCAL_GLOB)
            local_glob = os.getenv("LOCAL_INPUT_GLOB") or os.getenv("AZURE_LOCAL_GLOB")
            if os.getenv("AZURE_LOCAL_GLOB") and not os.getenv("LOCAL_INPUT_GLOB"):
                logger.warning(
                    "AZURE_LOCAL_GLOB is deprecated. Use LOCAL_INPUT_GLOB instead. "
                    "Support for AZURE_LOCAL_GLOB will be removed in v2.0."
                )
            # Note: local_glob can be None here - it will be validated later
            # in the CLI after checking if --glob or --pdf was provided
            return cls(mode=mode, local_glob=local_glob)
        else:
            storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
            if storage_account:
                blob_account_url = f"https://{storage_account}.blob.core.windows.net"
            else:
                blob_account_url = os.getenv("AZURE_BLOB_ACCOUNT_URL")

            # Input container name (with backward compatibility and auto-suffix)
            # Priority: AZURE_BLOB_CONTAINER_IN > AZURE_STORAGE_CONTAINER > AZURE_STORAGE_CONTAINER + "-input"
            blob_container_in = os.getenv("AZURE_BLOB_CONTAINER_IN")
            if not blob_container_in:
                base_container = os.getenv("AZURE_STORAGE_CONTAINER")
                if base_container:
                    blob_container_in = f"{base_container}-input"
                    get_logger(__name__).info(f"Using AZURE_STORAGE_CONTAINER with -input suffix: {blob_container_in}")

            blob_prefix = os.getenv("AZURE_BLOB_PREFIX", "")
            blob_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            blob_connection_string = os.getenv("AZURE_CONNECTION_STRING")

            if not blob_account_url and not blob_connection_string:
                raise ValueError(
                    "Azure Storage Account configuration is incomplete.\n"
                    "  Missing: AZURE_STORAGE_ACCOUNT (or AZURE_CONNECTION_STRING)\n"
                    "  \n"
                    "  Set in your .env file:\n"
                    "    AZURE_STORAGE_ACCOUNT=your-storage-account\n"
                    "    AZURE_STORAGE_ACCOUNT_KEY=your-key\n"
                    "  OR\n"
                    "    AZURE_CONNECTION_STRING=your-connection-string\n"
                    "  \n"
                    "  For local development, use local input instead:\n"
                    "    AZURE_INPUT_MODE=local\n"
                )
            if not blob_container_in:
                raise ValueError(
                    "Azure Blob Storage input container is required.\n"
                    "  Missing: AZURE_BLOB_CONTAINER_IN (or AZURE_STORAGE_CONTAINER)\n"
                    "  \n"
                    "  Set in your .env file:\n"
                    "    AZURE_BLOB_CONTAINER_IN=documents-input\n"
                    "  OR (simple approach):\n"
                    "    AZURE_STORAGE_CONTAINER=documents\n"
                    "    (Auto-creates: documents-input, documents-pages, etc.)\n"
                    "  \n"
                    "  IMPORTANT: You must create the input container first:\n"
                    "    az storage container create --name documents-input \\\n"
                    "      --account-name your-storage-account\n"
                )

            return cls(
                mode=mode,
                blob_account_url=blob_account_url,
                blob_container_in=blob_container_in,
                blob_prefix=blob_prefix,
                blob_key=blob_key,
                blob_connection_string=blob_connection_string
            )


@dataclass
class ArtifactsConfig:
    """Artifacts storage configuration."""
    mode: ArtifactsMode = ArtifactsMode.LOCAL
    # Local mode
    local_dir: str = "./artifacts"
    # Blob mode
    blob_account_url: Optional[str] = None
    blob_container_prefix: Optional[str] = None  # Base name from AZURE_STORAGE_CONTAINER (used as prefix for container names)
    blob_container_pages: Optional[str] = None
    blob_container_chunks: Optional[str] = None
    blob_container_images: Optional[str] = None
    blob_container_citations: Optional[str] = None  # Separate container for per-page PDFs (citations)
    blob_key: Optional[str] = None
    blob_connection_string: Optional[str] = None

    @classmethod
    def from_env(cls, input_mode: Optional[InputMode] = None) -> "ArtifactsConfig":
        """Load from environment variables.

        Args:
            input_mode: Optional input mode to auto-detect artifacts mode from.

        STANDARD Logic:
        1. Determine mode (priority order):
           a. ARTIFACTS_MODE (explicit mode setting) - HIGHEST PRIORITY
           b. STORE_ARTIFACTS_TO_BLOB (legacy override flag)
           c. Follow input_mode (local input → local artifacts, blob input → blob artifacts)
           d. Default → LOCAL if no input_mode provided
        2. Configure storage based on mode:
           - LOCAL mode: Use LOCAL_ARTIFACTS_DIR (or default ./artifacts)
           - BLOB mode: Use blob storage configuration

        Deprecated flags (backwards compatibility):
        - AZURE_ARTIFACTS_DIR: Still supported (renamed to LOCAL_ARTIFACTS_DIR)
        - AZURE_ARTIFACTS_MODE: Still supported (renamed to ARTIFACTS_MODE)
        - AZURE_STORE_ARTIFACTS_TO_BLOB: Still supported but redundant with ARTIFACTS_MODE
        """
        logger = get_logger(__name__)

        # STEP 1: Determine the mode (ARTIFACTS_MODE has highest priority)
        # ARTIFACTS_MODE (formerly AZURE_ARTIFACTS_MODE)
        mode_str = os.getenv("ARTIFACTS_MODE") or os.getenv("AZURE_ARTIFACTS_MODE")
        if os.getenv("AZURE_ARTIFACTS_MODE") and not os.getenv("ARTIFACTS_MODE"):
            logger.warning(
                "AZURE_ARTIFACTS_MODE is deprecated. Use ARTIFACTS_MODE instead. "
                "Support for AZURE_ARTIFACTS_MODE will be removed in v2.0."
            )

        # STORE_ARTIFACTS_TO_BLOB (formerly AZURE_STORE_ARTIFACTS_TO_BLOB)
        force_blob_str = os.getenv("STORE_ARTIFACTS_TO_BLOB") or os.getenv("AZURE_STORE_ARTIFACTS_TO_BLOB", "")
        if os.getenv("AZURE_STORE_ARTIFACTS_TO_BLOB") and not os.getenv("STORE_ARTIFACTS_TO_BLOB"):
            logger.warning(
                "AZURE_STORE_ARTIFACTS_TO_BLOB is deprecated. Use STORE_ARTIFACTS_TO_BLOB instead. "
                "Support for AZURE_STORE_ARTIFACTS_TO_BLOB will be removed in v2.0."
            )
        force_blob = force_blob_str.lower() == "true"

        if mode_str:
            # Explicit mode set - HIGHEST PRIORITY
            mode = ArtifactsMode(mode_str.lower())
            logger.info(f"Using ARTIFACTS_MODE={mode.value} (explicit mode setting)")
        elif force_blob:
            # Override flag set (deprecated but supported)
            mode = ArtifactsMode.BLOB
            logger.info("Using STORE_ARTIFACTS_TO_BLOB=true (deprecated, prefer ARTIFACTS_MODE=blob)")
        elif input_mode:
            # Follow input mode (RECOMMENDED approach)
            mode = ArtifactsMode.BLOB if input_mode == InputMode.BLOB else ArtifactsMode.LOCAL
            logger.info(f"Artifacts storage follows input mode: {mode.value}")
        else:
            # Default to local
            mode = ArtifactsMode.LOCAL
            logger.info("Using default: local artifacts storage")

        # STEP 2: Configure storage based on determined mode
        if mode == ArtifactsMode.LOCAL:
            # LOCAL_ARTIFACTS_DIR (formerly AZURE_ARTIFACTS_DIR) - only used in LOCAL mode
            local_dir = os.getenv("LOCAL_ARTIFACTS_DIR") or os.getenv("AZURE_ARTIFACTS_DIR", "./artifacts")
            if os.getenv("AZURE_ARTIFACTS_DIR") and not os.getenv("LOCAL_ARTIFACTS_DIR"):
                logger.warning(
                    "AZURE_ARTIFACTS_DIR is deprecated. Use LOCAL_ARTIFACTS_DIR instead. "
                    "Support for AZURE_ARTIFACTS_DIR will be removed in v2.0."
                )
            logger.info(f"Local artifacts directory: {local_dir}")
            return cls(mode=mode, local_dir=local_dir)
        else:
            storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
            if storage_account:
                blob_account_url = f"https://{storage_account}.blob.core.windows.net"
            else:
                blob_account_url = os.getenv("AZURE_BLOB_ACCOUNT_URL")

            # Container prefix for naming all blob containers
            # Primary: AZURE_BLOB_CONTAINER_PREFIX (recommended)
            # Fallback: BLOB_CONTAINER_PREFIX (deprecated alias)
            blob_container_prefix = os.getenv("AZURE_BLOB_CONTAINER_PREFIX") or os.getenv("BLOB_CONTAINER_PREFIX", "")

            # Show deprecation warning for alias
            if os.getenv("BLOB_CONTAINER_PREFIX") and not os.getenv("AZURE_BLOB_CONTAINER_PREFIX"):
                logger.warning(
                    "BLOB_CONTAINER_PREFIX is deprecated. Use AZURE_BLOB_CONTAINER_PREFIX instead. "
                    "Support for BLOB_CONTAINER_PREFIX will be removed in v2.0."
                )

            # Base container names (will be prefixed if BLOB_CONTAINER_PREFIX is set)
            base_pages = os.getenv("AZURE_BLOB_CONTAINER_OUT_PAGES")
            base_chunks = os.getenv("AZURE_BLOB_CONTAINER_OUT_CHUNKS")
            base_images = os.getenv("AZURE_BLOB_CONTAINER_OUT_IMAGES")
            base_citations = os.getenv("AZURE_BLOB_CONTAINER_CITATIONS")

            # Determine base container names with fallback logic
            if not base_pages and not base_chunks:
                # No explicit container names set - use prefix with default base names
                if blob_container_prefix:
                    # Use prefix with default base names (pages, chunks, images, citations)
                    base_pages = "pages"
                    base_chunks = "chunks"
                    base_images = "images"
                    base_citations = "citations"

                    # Log which variable was used
                    if os.getenv("AZURE_BLOB_CONTAINER_PREFIX"):
                        logger.info(f"Using AZURE_BLOB_CONTAINER_PREFIX: {blob_container_prefix}")
                    else:
                        logger.info(f"Using BLOB_CONTAINER_PREFIX (deprecated): {blob_container_prefix}")

            # Apply prefix if configured
            if blob_container_prefix:
                blob_container_pages = f"{blob_container_prefix}-{base_pages}" if base_pages else None
                blob_container_chunks = f"{blob_container_prefix}-{base_chunks}" if base_chunks else None
                blob_container_images = f"{blob_container_prefix}-{base_images}" if base_images else None
                blob_container_citations = f"{blob_container_prefix}-{base_citations}" if base_citations else None
            else:
                blob_container_pages = base_pages
                blob_container_chunks = base_chunks
                blob_container_images = base_images
                blob_container_citations = base_citations

            blob_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            blob_connection_string = os.getenv("AZURE_CONNECTION_STRING")

            # Validation
            if not blob_account_url and not blob_connection_string:
                raise ValueError(
                    "Azure Storage Account configuration is required when ARTIFACTS_MODE=blob\n"
                    "  Missing: AZURE_STORAGE_ACCOUNT or AZURE_CONNECTION_STRING\n"
                    "  Set in your .env file:\n"
                    "    AZURE_STORAGE_ACCOUNT=your-storage-account\n"
                    "    AZURE_STORAGE_ACCOUNT_KEY=your-key"
                )
            if not blob_container_pages:
                raise ValueError(
                    "Blob container configuration is incomplete when ARTIFACTS_MODE=blob\n"
                    "  \n"
                    "  You must configure container naming. Choose one approach:\n"
                    "  \n"
                    "  APPROACH 1 - Prefix (Recommended):\n"
                    "    AZURE_BLOB_CONTAINER_PREFIX=myproject\n"
                    "    → Auto-creates: myproject-pages, myproject-chunks, myproject-images, myproject-citations\n"
                    "  \n"
                    "  APPROACH 2 - Explicit (Advanced):\n"
                    "    AZURE_BLOB_CONTAINER_OUT_PAGES=pages\n"
                    "    AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks\n"
                    "    AZURE_BLOB_CONTAINER_OUT_IMAGES=images\n"
                    "    AZURE_BLOB_CONTAINER_CITATIONS=citations\n"
                    "  \n"
                    "  Example .env configuration:\n"
                    "    AZURE_STORAGE_ACCOUNT=mystorageaccount\n"
                    "    AZURE_BLOB_CONTAINER_PREFIX=myproject"
                )
            if not blob_container_chunks:
                raise ValueError(
                    "Blob container configuration is incomplete when ARTIFACTS_MODE=blob\n"
                    "  Missing chunks container. Use one of these approaches:\n"
                    "  \n"
                    "    AZURE_BLOB_CONTAINER_PREFIX=myproject  (Recommended)\n"
                    "    OR\n"
                    "    AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks  (Explicit)"
                )
            
            return cls(
                mode=mode,
                blob_account_url=blob_account_url,
                blob_container_prefix=blob_container_prefix,
                blob_container_pages=blob_container_pages,
                blob_container_chunks=blob_container_chunks,
                blob_container_images=blob_container_images,
                blob_container_citations=blob_container_citations,
                blob_key=blob_key,
                blob_connection_string=blob_connection_string
            )


@dataclass
class ChunkingConfig:
    """Text chunking configuration.

    These parameters control how documents are split into searchable chunks.
    Defaults match the original prepdocslib implementation.
    """
    max_chars: int = 1000  # Soft char guideline for overlap sizing; can be disabled
    max_tokens: int = 500  # Maximum tokens per chunk
    overlap_percent: int = 10  # Percent overlap between chunks for semantic continuity
    cross_page_overlap: bool = False  # If True, allow overlap across page boundaries for text-only chunks
    disable_char_limit: bool = False  # If True, ignore char limit during chunking
    table_legend_buffer: int = 100  # Buffer for table legend/caption context (characters)
    absolute_max_tokens: int = 8000  # Absolute maximum tokens per chunk (safety limit)

    @classmethod
    def from_env(cls) -> "ChunkingConfig":
        """Load from environment variables."""
        logger = get_logger(__name__)

        # CHUNKING_MAX_CHARS (formerly AZURE_CHUNKING_MAX_CHARS)
        max_chars_str = os.getenv("CHUNKING_MAX_CHARS") or os.getenv("AZURE_CHUNKING_MAX_CHARS", "1000")
        if os.getenv("AZURE_CHUNKING_MAX_CHARS") and not os.getenv("CHUNKING_MAX_CHARS"):
            logger.warning(
                "AZURE_CHUNKING_MAX_CHARS is deprecated. Use CHUNKING_MAX_CHARS instead. "
                "Support for AZURE_CHUNKING_MAX_CHARS will be removed in v2.0."
            )
        max_chars = int(max_chars_str)

        # CHUNKING_MAX_TOKENS (formerly AZURE_CHUNKING_MAX_TOKENS)
        max_tokens_str = os.getenv("CHUNKING_MAX_TOKENS") or os.getenv("AZURE_CHUNKING_MAX_TOKENS", "500")
        if os.getenv("AZURE_CHUNKING_MAX_TOKENS") and not os.getenv("CHUNKING_MAX_TOKENS"):
            logger.warning(
                "AZURE_CHUNKING_MAX_TOKENS is deprecated. Use CHUNKING_MAX_TOKENS instead. "
                "Support for AZURE_CHUNKING_MAX_TOKENS will be removed in v2.0."
            )
        max_tokens = int(max_tokens_str)

        # CHUNKING_OVERLAP_PERCENT (formerly AZURE_CHUNKING_OVERLAP_PERCENT)
        overlap_percent_str = os.getenv("CHUNKING_OVERLAP_PERCENT") or os.getenv("AZURE_CHUNKING_OVERLAP_PERCENT", "10")
        if os.getenv("AZURE_CHUNKING_OVERLAP_PERCENT") and not os.getenv("CHUNKING_OVERLAP_PERCENT"):
            logger.warning(
                "AZURE_CHUNKING_OVERLAP_PERCENT is deprecated. Use CHUNKING_OVERLAP_PERCENT instead. "
                "Support for AZURE_CHUNKING_OVERLAP_PERCENT will be removed in v2.0."
            )
        overlap_percent = int(overlap_percent_str)

        # CHUNKING_CROSS_PAGE_OVERLAP (formerly AZURE_CHUNKING_CROSS_PAGE_OVERLAP)
        cross_page_str = os.getenv("CHUNKING_CROSS_PAGE_OVERLAP") or os.getenv("AZURE_CHUNKING_CROSS_PAGE_OVERLAP", "false")
        if os.getenv("AZURE_CHUNKING_CROSS_PAGE_OVERLAP") and not os.getenv("CHUNKING_CROSS_PAGE_OVERLAP"):
            logger.warning(
                "AZURE_CHUNKING_CROSS_PAGE_OVERLAP is deprecated. Use CHUNKING_CROSS_PAGE_OVERLAP instead. "
                "Support for AZURE_CHUNKING_CROSS_PAGE_OVERLAP will be removed in v2.0."
            )
        cross_page_overlap = cross_page_str.lower() == "true"

        # CHUNKING_DISABLE_CHAR_LIMIT (formerly AZURE_CHUNKING_DISABLE_CHAR_LIMIT)
        disable_char_str = os.getenv("CHUNKING_DISABLE_CHAR_LIMIT") or os.getenv("AZURE_CHUNKING_DISABLE_CHAR_LIMIT", "false")
        if os.getenv("AZURE_CHUNKING_DISABLE_CHAR_LIMIT") and not os.getenv("CHUNKING_DISABLE_CHAR_LIMIT"):
            logger.warning(
                "AZURE_CHUNKING_DISABLE_CHAR_LIMIT is deprecated. Use CHUNKING_DISABLE_CHAR_LIMIT instead. "
                "Support for AZURE_CHUNKING_DISABLE_CHAR_LIMIT will be removed in v2.0."
            )
        disable_char_limit = disable_char_str.lower() == "true"

        # CHUNKING_TABLE_LEGEND_BUFFER (formerly AZURE_CHUNKING_TABLE_LEGEND_BUFFER)
        table_legend_str = os.getenv("CHUNKING_TABLE_LEGEND_BUFFER") or os.getenv("AZURE_CHUNKING_TABLE_LEGEND_BUFFER", "100")
        if os.getenv("AZURE_CHUNKING_TABLE_LEGEND_BUFFER") and not os.getenv("CHUNKING_TABLE_LEGEND_BUFFER"):
            logger.warning(
                "AZURE_CHUNKING_TABLE_LEGEND_BUFFER is deprecated. Use CHUNKING_TABLE_LEGEND_BUFFER instead. "
                "Support for AZURE_CHUNKING_TABLE_LEGEND_BUFFER will be removed in v2.0."
            )
        table_legend_buffer = int(table_legend_str)

        # CHUNKING_ABSOLUTE_MAX_TOKENS (formerly AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS)
        absolute_max_str = os.getenv("CHUNKING_ABSOLUTE_MAX_TOKENS") or os.getenv("AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS", "8000")
        if os.getenv("AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS") and not os.getenv("CHUNKING_ABSOLUTE_MAX_TOKENS"):
            logger.warning(
                "AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS is deprecated. Use CHUNKING_ABSOLUTE_MAX_TOKENS instead. "
                "Support for AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS will be removed in v2.0."
            )
        absolute_max_tokens = int(absolute_max_str)

        return cls(
            max_chars=max_chars,
            max_tokens=max_tokens,
            overlap_percent=overlap_percent,
            cross_page_overlap=cross_page_overlap,
            disable_char_limit=disable_char_limit,
            table_legend_buffer=table_legend_buffer,
            absolute_max_tokens=absolute_max_tokens
        )


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""
    max_workers: int = 4
    inner_analyze_workers: int = 1
    upload_delay: float = 0.5
    embed_batch_size: int = 128
    upload_batch_size: int = 1000

    # Parallelization settings for I/O operations
    max_image_concurrency: int = 8      # Parallel image descriptions/uploads
    max_figure_concurrency: int = 5     # Parallel figure extractions
    max_batch_upload_concurrency: int = 5  # Parallel search batch uploads

    @classmethod
    def from_env(cls) -> "PerformanceConfig":
        """Load from environment variables."""
        logger = get_logger(__name__)

        # MAX_WORKERS (formerly AZURE_MAX_WORKERS)
        max_workers_str = os.getenv("MAX_WORKERS") or os.getenv("AZURE_MAX_WORKERS", "4")
        if os.getenv("AZURE_MAX_WORKERS") and not os.getenv("MAX_WORKERS"):
            logger.warning(
                "AZURE_MAX_WORKERS is deprecated. Use MAX_WORKERS instead. "
                "Support for AZURE_MAX_WORKERS will be removed in v2.0."
            )
        max_workers = int(max_workers_str)

        # INNER_ANALYZE_WORKERS (formerly AZURE_INNER_ANALYZE_WORKERS)
        inner_workers_str = os.getenv("INNER_ANALYZE_WORKERS") or os.getenv("AZURE_INNER_ANALYZE_WORKERS", "1")
        if os.getenv("AZURE_INNER_ANALYZE_WORKERS") and not os.getenv("INNER_ANALYZE_WORKERS"):
            logger.warning(
                "AZURE_INNER_ANALYZE_WORKERS is deprecated. Use INNER_ANALYZE_WORKERS instead. "
                "Support for AZURE_INNER_ANALYZE_WORKERS will be removed in v2.0."
            )
        inner_analyze_workers = int(inner_workers_str)

        # UPLOAD_DELAY (formerly AZURE_UPLOAD_DELAY)
        upload_delay_str = os.getenv("UPLOAD_DELAY") or os.getenv("AZURE_UPLOAD_DELAY", "0.5")
        if os.getenv("AZURE_UPLOAD_DELAY") and not os.getenv("UPLOAD_DELAY"):
            logger.warning(
                "AZURE_UPLOAD_DELAY is deprecated. Use UPLOAD_DELAY instead. "
                "Support for AZURE_UPLOAD_DELAY will be removed in v2.0."
            )
        upload_delay = float(upload_delay_str)

        # EMBEDDING_BATCH_SIZE (formerly AZURE_EMBED_BATCH_SIZE)
        embed_batch_str = os.getenv("EMBEDDING_BATCH_SIZE") or os.getenv("AZURE_EMBED_BATCH_SIZE", "128")
        if os.getenv("AZURE_EMBED_BATCH_SIZE") and not os.getenv("EMBEDDING_BATCH_SIZE"):
            logger.warning(
                "AZURE_EMBED_BATCH_SIZE is deprecated. Use EMBEDDING_BATCH_SIZE instead. "
                "Support for AZURE_EMBED_BATCH_SIZE will be removed in v2.0."
            )
        embed_batch_size = int(embed_batch_str)

        # UPLOAD_BATCH_SIZE (formerly AZURE_UPLOAD_BATCH_SIZE)
        upload_batch_str = os.getenv("UPLOAD_BATCH_SIZE") or os.getenv("AZURE_UPLOAD_BATCH_SIZE", "1000")
        if os.getenv("AZURE_UPLOAD_BATCH_SIZE") and not os.getenv("UPLOAD_BATCH_SIZE"):
            logger.warning(
                "AZURE_UPLOAD_BATCH_SIZE is deprecated. Use UPLOAD_BATCH_SIZE instead. "
                "Support for AZURE_UPLOAD_BATCH_SIZE will be removed in v2.0."
            )
        upload_batch_size = int(upload_batch_str)

        # MAX_IMAGE_CONCURRENCY (formerly AZURE_MAX_IMAGE_CONCURRENCY)
        max_img_str = os.getenv("MAX_IMAGE_CONCURRENCY") or os.getenv("AZURE_MAX_IMAGE_CONCURRENCY", "8")
        if os.getenv("AZURE_MAX_IMAGE_CONCURRENCY") and not os.getenv("MAX_IMAGE_CONCURRENCY"):
            logger.warning(
                "AZURE_MAX_IMAGE_CONCURRENCY is deprecated. Use MAX_IMAGE_CONCURRENCY instead. "
                "Support for AZURE_MAX_IMAGE_CONCURRENCY will be removed in v2.0."
            )
        max_image_concurrency = int(max_img_str)

        # MAX_FIGURE_CONCURRENCY (formerly AZURE_MAX_FIGURE_CONCURRENCY)
        max_fig_str = os.getenv("MAX_FIGURE_CONCURRENCY") or os.getenv("AZURE_MAX_FIGURE_CONCURRENCY", "5")
        if os.getenv("AZURE_MAX_FIGURE_CONCURRENCY") and not os.getenv("MAX_FIGURE_CONCURRENCY"):
            logger.warning(
                "AZURE_MAX_FIGURE_CONCURRENCY is deprecated. Use MAX_FIGURE_CONCURRENCY instead. "
                "Support for AZURE_MAX_FIGURE_CONCURRENCY will be removed in v2.0."
            )
        max_figure_concurrency = int(max_fig_str)

        # MAX_BATCH_UPLOAD_CONCURRENCY (formerly AZURE_MAX_BATCH_UPLOAD_CONCURRENCY)
        max_batch_str = os.getenv("MAX_BATCH_UPLOAD_CONCURRENCY") or os.getenv("AZURE_MAX_BATCH_UPLOAD_CONCURRENCY", "5")
        if os.getenv("AZURE_MAX_BATCH_UPLOAD_CONCURRENCY") and not os.getenv("MAX_BATCH_UPLOAD_CONCURRENCY"):
            logger.warning(
                "AZURE_MAX_BATCH_UPLOAD_CONCURRENCY is deprecated. Use MAX_BATCH_UPLOAD_CONCURRENCY instead. "
                "Support for AZURE_MAX_BATCH_UPLOAD_CONCURRENCY will be removed in v2.0."
            )
        max_batch_upload_concurrency = int(max_batch_str)

        return cls(
            max_workers=max_workers,
            inner_analyze_workers=inner_analyze_workers,
            upload_delay=upload_delay,
            embed_batch_size=embed_batch_size,
            upload_batch_size=upload_batch_size,
            max_image_concurrency=max_image_concurrency,
            max_figure_concurrency=max_figure_concurrency,
            max_batch_upload_concurrency=max_batch_upload_concurrency
        )


@dataclass
class LoggingConfig:
    """Logging configuration for production vs development."""
    console_level: str = "INFO"      # Console log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    file_level: str = "DEBUG"        # File log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    write_artifacts: bool = True     # Write detailed artifact logs (DI, chunking, tables, figures)
    use_colors: bool = True          # Enable colorful console logging with ANSI colors

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load from environment variables."""
        console_level = os.getenv("LOG_LEVEL", "INFO").upper()
        file_level = os.getenv("LOG_FILE_LEVEL", "DEBUG").upper()
        write_artifacts = os.getenv("LOG_ARTIFACTS", "true").lower() == "true"
        use_colors = os.getenv("LOG_USE_COLORS", "true").lower() == "true"

        return cls(
            console_level=console_level,
            file_level=file_level,
            write_artifacts=write_artifacts,
            use_colors=use_colors
        )


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    search: SearchConfig
    document_intelligence: DocumentIntelligenceConfig
    office_extractor: OfficeExtractorConfig
    azure_openai: AzureOpenAIConfig
    input: InputConfig
    artifacts: ArtifactsConfig
    azure_credentials: AzureCredentials
    key_vault: KeyVaultConfig
    chunking: ChunkingConfig
    performance: PerformanceConfig
    logging: LoggingConfig
    content_understanding: Optional[ContentUnderstandingConfig] = None

    # Processing options
    media_describer_mode: MediaDescriberMode = MediaDescriberMode.GPT4O
    table_render_mode: TableRenderMode = TableRenderMode.PLAIN
    generate_table_summaries: bool = False
    use_integrated_vectorization: bool = False  # If True, skip client-side embeddings and let Azure Search generate them
    document_action: DocumentAction = DocumentAction.ADD  # Document processing action mode
    auto_validate: bool = True  # Run validation before processing (default: true for safety)

    # New pluggable architecture fields (optional for backward compatibility)
    vector_store_mode: Optional[VectorStoreMode] = None  # Auto-detected from environment or legacy config
    vector_store_config: Optional[Any] = None  # Union of SearchConfig, ChromaDBConfig, etc.
    embeddings_mode: Optional[EmbeddingsMode] = None  # Auto-detected from environment or legacy config
    embeddings_config: Optional[Any] = None  # Union of AzureOpenAIConfig, HuggingFaceConfig, etc.
    
    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "PipelineConfig":
        """Load complete configuration from environment variables.

        Args:
            env_path: Optional path to .env file. If not provided, searches for .env
                     in current directory and parent directories.

        Returns:
            Configured PipelineConfig instance

        Raises:
            ValueError: If required configuration is missing or invalid

        Example:
            >>> # Load from default .env file
            >>> config = PipelineConfig.from_env()
            >>>
            >>> # Load from specific environment file
            >>> config = PipelineConfig.from_env(".env.production")
        """
        # Load .env file if path specified or if dotenv is available
        if env_path:
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=env_path, override=True)
            except ImportError:
                get_logger(__name__).warning(
                    f"python-dotenv not installed, cannot load {env_path}. "
                    "Install with: pip install python-dotenv"
                )

        # Wrap configuration loading with better error context
        try:
            search = SearchConfig.from_env()
        except ValueError as e:
            raise ValueError(
                f"Azure AI Search configuration error:\n{str(e)}\n\n"
                "Need help? Run: python -m ingestor.scenario_validator"
            ) from e

        try:
            document_intelligence = DocumentIntelligenceConfig.from_env()
        except ValueError as e:
            raise ValueError(
                f"Document Intelligence configuration error:\n{str(e)}\n\n"
                "Need help? Run: python -m ingestor.scenario_validator"
            ) from e

        office_extractor = OfficeExtractorConfig.from_env()

        try:
            azure_openai = AzureOpenAIConfig.from_env()
        except ValueError as e:
            raise ValueError(
                f"Azure OpenAI configuration error:\n{str(e)}\n\n"
                "Need help? Run: python -m ingestor.scenario_validator"
            ) from e

        try:
            input_config = InputConfig.from_env()
        except ValueError as e:
            raise ValueError(
                f"Input source configuration error:\n{str(e)}\n\n"
                "Need help? Run: python -m ingestor.scenario_validator"
            ) from e

        # Pass input mode to enable auto-detection of artifacts mode
        artifacts = ArtifactsConfig.from_env(input_mode=input_config.mode)
        azure_credentials = AzureCredentials.from_env()
        key_vault = KeyVaultConfig.from_env()
        chunking = ChunkingConfig.from_env()
        performance = PerformanceConfig.from_env()
        logging_config = LoggingConfig.from_env()
        content_understanding = ContentUnderstandingConfig.from_env()

        # Processing options
        logger = get_logger(__name__)

        # MEDIA_DESCRIBER_MODE (formerly AZURE_MEDIA_DESCRIBER)
        media_describer_str = os.getenv("MEDIA_DESCRIBER_MODE") or os.getenv("AZURE_MEDIA_DESCRIBER", "gpt4o")
        if os.getenv("AZURE_MEDIA_DESCRIBER") and not os.getenv("MEDIA_DESCRIBER_MODE"):
            logger.warning(
                "AZURE_MEDIA_DESCRIBER is deprecated. Use MEDIA_DESCRIBER_MODE instead. "
                "Support for AZURE_MEDIA_DESCRIBER will be removed in v2.0."
            )
        media_describer_mode = MediaDescriberMode(media_describer_str.lower())

        # TABLE_RENDER_FORMAT (formerly AZURE_TABLE_RENDER)
        table_render_str = os.getenv("TABLE_RENDER_FORMAT") or os.getenv("AZURE_TABLE_RENDER", "plain")
        if os.getenv("AZURE_TABLE_RENDER") and not os.getenv("TABLE_RENDER_FORMAT"):
            logger.warning(
                "AZURE_TABLE_RENDER is deprecated. Use TABLE_RENDER_FORMAT instead. "
                "Support for AZURE_TABLE_RENDER will be removed in v2.0."
            )
        table_render_mode = TableRenderMode(table_render_str.lower())

        # TABLE_SUMMARIES_ENABLED (formerly AZURE_TABLE_SUMMARIES)
        table_summaries_str = os.getenv("TABLE_SUMMARIES_ENABLED") or os.getenv("AZURE_TABLE_SUMMARIES", "false")
        if os.getenv("AZURE_TABLE_SUMMARIES") and not os.getenv("TABLE_SUMMARIES_ENABLED"):
            logger.warning(
                "AZURE_TABLE_SUMMARIES is deprecated. Use TABLE_SUMMARIES_ENABLED instead. "
                "Support for AZURE_TABLE_SUMMARIES will be removed in v2.0."
            )
        generate_table_summaries = table_summaries_str.lower() == "true"

        # GENERATE_PAGE_PDFS (formerly AZURE_GENERATE_PAGE_PDFS) - not currently in the code, but adding for completeness
        # This will be used when the feature is implemented
        # generate_page_pdfs_str = os.getenv("GENERATE_PAGE_PDFS") or os.getenv("AZURE_GENERATE_PAGE_PDFS", "false")
        # if os.getenv("AZURE_GENERATE_PAGE_PDFS") and not os.getenv("GENERATE_PAGE_PDFS"):
        #     logger.warning(
        #         "AZURE_GENERATE_PAGE_PDFS is deprecated. Use GENERATE_PAGE_PDFS instead. "
        #         "Support for AZURE_GENERATE_PAGE_PDFS will be removed in v2.0."
        #     )
        # generate_page_pdfs = generate_page_pdfs_str.lower() == "true"

        use_integrated_vectorization = os.getenv("AZURE_USE_INTEGRATED_VECTORIZATION", "false").lower() == "true"

        # DOCUMENT_ACTION (formerly AZURE_DOCUMENT_ACTION)
        document_action_str = os.getenv("DOCUMENT_ACTION") or os.getenv("AZURE_DOCUMENT_ACTION", "add")
        if os.getenv("AZURE_DOCUMENT_ACTION") and not os.getenv("DOCUMENT_ACTION"):
            logger.warning(
                "AZURE_DOCUMENT_ACTION is deprecated. Use DOCUMENT_ACTION instead. "
                "Support for AZURE_DOCUMENT_ACTION will be removed in v2.0."
            )
        document_action = DocumentAction(document_action_str.lower())

        # AUTO_VALIDATE: Run validation before processing
        auto_validate = os.getenv("AUTO_VALIDATE", "true").lower() == "true"

        # Auto-detect vector store mode (backward compatible)
        vector_store_mode = None
        vector_store_config = None
        if os.getenv("VECTOR_STORE_MODE"):
            # Explicit mode specified
            vector_store_mode = VectorStoreMode(os.getenv("VECTOR_STORE_MODE"))
            if vector_store_mode == VectorStoreMode.AZURE_SEARCH:
                vector_store_config = search
            elif vector_store_mode == VectorStoreMode.CHROMADB:
                vector_store_config = ChromaDBConfig.from_env()
            # Other modes (Pinecone, Weaviate, etc.) will be added in future phases
        elif os.getenv("CHROMADB_COLLECTION_NAME") or os.getenv("CHROMADB_HOST") or os.getenv("CHROMADB_PERSIST_DIR"):
            # ChromaDB environment variables present, use ChromaDB
            vector_store_mode = VectorStoreMode.CHROMADB
            vector_store_config = ChromaDBConfig.from_env()
        elif search.endpoint:
            # Legacy: Azure Search config present, use it by default
            vector_store_mode = VectorStoreMode.AZURE_SEARCH
            vector_store_config = search

        # Auto-detect embeddings mode (backward compatible)
        embeddings_mode = None
        embeddings_config = None
        if os.getenv("EMBEDDINGS_MODE"):
            # Explicit mode specified
            embeddings_mode = EmbeddingsMode(os.getenv("EMBEDDINGS_MODE"))
            if embeddings_mode == EmbeddingsMode.AZURE_OPENAI:
                embeddings_config = azure_openai
            elif embeddings_mode == EmbeddingsMode.HUGGINGFACE:
                embeddings_config = HuggingFaceEmbeddingsConfig.from_env()
            elif embeddings_mode == EmbeddingsMode.COHERE:
                embeddings_config = CohereEmbeddingsConfig.from_env()
            elif embeddings_mode == EmbeddingsMode.OPENAI:
                embeddings_config = OpenAIEmbeddingsConfig.from_env()
        elif os.getenv("HUGGINGFACE_MODEL_NAME"):
            # Hugging Face environment variables present
            embeddings_mode = EmbeddingsMode.HUGGINGFACE
            embeddings_config = HuggingFaceEmbeddingsConfig.from_env()
        elif os.getenv("COHERE_API_KEY"):
            # Cohere environment variables present
            embeddings_mode = EmbeddingsMode.COHERE
            embeddings_config = CohereEmbeddingsConfig.from_env()
        elif os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_ENDPOINT"):
            # OpenAI (non-Azure) environment variables present
            embeddings_mode = EmbeddingsMode.OPENAI
            embeddings_config = OpenAIEmbeddingsConfig.from_env()
        elif azure_openai.endpoint:
            # Legacy: Azure OpenAI config present, use it by default
            embeddings_mode = EmbeddingsMode.AZURE_OPENAI
            embeddings_config = azure_openai

        return cls(
            search=search,
            document_intelligence=document_intelligence,
            office_extractor=office_extractor,
            azure_openai=azure_openai,
            input=input_config,
            artifacts=artifacts,
            azure_credentials=azure_credentials,
            key_vault=key_vault,
            chunking=chunking,
            performance=performance,
            logging=logging_config,
            content_understanding=content_understanding,
            media_describer_mode=media_describer_mode,
            table_render_mode=table_render_mode,
            generate_table_summaries=generate_table_summaries,
            use_integrated_vectorization=use_integrated_vectorization,
            document_action=document_action,
            auto_validate=auto_validate,
            vector_store_mode=vector_store_mode,
            vector_store_config=vector_store_config,
            embeddings_mode=embeddings_mode,
            embeddings_config=embeddings_config
        )


def validate_media_describer_config(
    media_describer_mode: MediaDescriberMode,
    azure_openai_config: AzureOpenAIConfig,
    content_understanding_config: Optional[ContentUnderstandingConfig]
) -> list[str]:
    """Validate media describer configuration and return list of errors.

    Args:
        media_describer_mode: Selected media describer mode
        azure_openai_config: Azure OpenAI configuration
        content_understanding_config: Content Understanding configuration (optional)

    Returns:
        List of configuration error messages (empty if valid)
    """
    errors = []

    if media_describer_mode == MediaDescriberMode.DISABLED:
        # No validation needed for disabled mode
        return errors

    elif media_describer_mode == MediaDescriberMode.GPT4O:
        # Validate Azure OpenAI configuration for GPT-4o vision
        if not azure_openai_config.endpoint:
            errors.append(
                "MEDIA_DESCRIBER_MODE=gpt4o requires AZURE_OPENAI_ENDPOINT.\n"
                "  Set: AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/"
            )

        if not azure_openai_config.api_key:
            errors.append(
                "MEDIA_DESCRIBER_MODE=gpt4o requires AZURE_OPENAI_KEY.\n"
                "  Set: AZURE_OPENAI_KEY=your-api-key"
            )

        if not azure_openai_config.vision_deployment:
            errors.append(
                "MEDIA_DESCRIBER_MODE=gpt4o requires AZURE_OPENAI_VISION_DEPLOYMENT.\n"
                "  Set: AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o\n"
                "  Tip: Use gpt-4o-mini for 5x lower cost"
            )

        if not azure_openai_config.vision_model_name:
            errors.append(
                "MEDIA_DESCRIBER_MODE=gpt4o requires AZURE_OPENAI_VISION_MODEL.\n"
                "  Set: AZURE_OPENAI_VISION_MODEL=gpt-4o"
            )

    elif media_describer_mode == MediaDescriberMode.CONTENT_UNDERSTANDING:
        # Validate Content Understanding configuration
        if not content_understanding_config or not content_understanding_config.endpoint:
            errors.append(
                "MEDIA_DESCRIBER_MODE=content_understanding requires AZURE_CONTENT_UNDERSTANDING_ENDPOINT.\n"
                "  NOTE: This mode is not yet fully implemented.\n"
                "  Alternative: Use MEDIA_DESCRIBER_MODE=gpt4o"
            )

    return errors


def validate_embeddings_config(
    embeddings_mode: EmbeddingsMode,
    embeddings_config: Optional[Any]
) -> list[str]:
    """Validate embeddings configuration and return list of errors.

    Only validates the selected embeddings mode's required variables.
    Other embeddings configurations are ignored (override precedence).

    Args:
        embeddings_mode: Selected embeddings mode
        embeddings_config: Embeddings configuration for the selected mode

    Returns:
        List of configuration error messages (empty if valid)
    """
    errors = []

    if embeddings_mode == EmbeddingsMode.AZURE_OPENAI:
        # Validate Azure OpenAI embeddings configuration
        if not embeddings_config:
            errors.append(
                "EMBEDDINGS_MODE=azure_openai requires Azure OpenAI configuration.\n"
                "  Missing: Azure OpenAI config"
            )
            return errors

        # Check required fields for embeddings
        if not embeddings_config.endpoint:
            errors.append(
                "EMBEDDINGS_MODE=azure_openai requires AZURE_OPENAI_ENDPOINT.\n"
                "  Set: AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/"
            )

        if not embeddings_config.api_key:
            errors.append(
                "EMBEDDINGS_MODE=azure_openai requires AZURE_OPENAI_KEY.\n"
                "  Set: AZURE_OPENAI_KEY=your-api-key"
            )

        if not embeddings_config.emb_deployment:
            errors.append(
                "EMBEDDINGS_MODE=azure_openai requires AZURE_OPENAI_EMBEDDING_DEPLOYMENT.\n"
                "  Set: AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002\n"
                "  Tip: Use text-embedding-3-small for better quality at lower cost"
            )

        if not embeddings_config.emb_model_name:
            errors.append(
                "EMBEDDINGS_MODE=azure_openai requires AZURE_OPENAI_EMBEDDING_MODEL.\n"
                "  Set: AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002"
            )

    elif embeddings_mode == EmbeddingsMode.HUGGINGFACE:
        # Validate HuggingFace embeddings configuration
        if not embeddings_config:
            errors.append(
                "EMBEDDINGS_MODE=huggingface requires HuggingFace configuration.\n"
                "  Missing: HuggingFace config"
            )
            return errors

        # HuggingFace only requires model_name (other fields have defaults)
        if not embeddings_config.model_name:
            errors.append(
                "EMBEDDINGS_MODE=huggingface requires HUGGINGFACE_MODEL_NAME.\n"
                "  Set: HUGGINGFACE_MODEL_NAME=BAAI/bge-large-en-v1.5\n"
                "  Popular options:\n"
                "    - BAAI/bge-large-en-v1.5 (1024 dims, SOTA English)\n"
                "    - sentence-transformers/all-MiniLM-L6-v2 (384 dims, fast)\n"
                "    - intfloat/multilingual-e5-large (1024 dims, multilingual)"
            )

    elif embeddings_mode == EmbeddingsMode.COHERE:
        # Validate Cohere embeddings configuration
        if not embeddings_config:
            errors.append(
                "EMBEDDINGS_MODE=cohere requires Cohere configuration.\n"
                "  Missing: Cohere config"
            )
            return errors

        if not embeddings_config.api_key:
            errors.append(
                "EMBEDDINGS_MODE=cohere requires COHERE_API_KEY.\n"
                "  Set: COHERE_API_KEY=your-cohere-api-key\n"
                "  Get API key: https://dashboard.cohere.com/api-keys"
            )

        if not embeddings_config.model_name:
            errors.append(
                "EMBEDDINGS_MODE=cohere requires COHERE_MODEL_NAME.\n"
                "  Set: COHERE_MODEL_NAME=embed-multilingual-v3.0\n"
                "  Options: embed-english-v3.0 | embed-multilingual-v3.0"
            )

    elif embeddings_mode == EmbeddingsMode.OPENAI:
        # Validate OpenAI embeddings configuration
        if not embeddings_config:
            errors.append(
                "EMBEDDINGS_MODE=openai requires OpenAI configuration.\n"
                "  Missing: OpenAI config"
            )
            return errors

        if not embeddings_config.api_key:
            errors.append(
                "EMBEDDINGS_MODE=openai requires OPENAI_API_KEY.\n"
                "  Set: OPENAI_API_KEY=sk-your-openai-api-key\n"
                "  Get API key: https://platform.openai.com/api-keys"
            )

        if not embeddings_config.model_name:
            errors.append(
                "EMBEDDINGS_MODE=openai requires OPENAI_EMBEDDING_MODEL.\n"
                "  Set: OPENAI_EMBEDDING_MODEL=text-embedding-3-small\n"
                "  Options: text-embedding-3-small | text-embedding-3-large"
            )

    return errors


def load_config(env_path: Optional[str] = None) -> PipelineConfig:
    """Load configuration from environment variables.

    Args:
        env_path: Optional path to .env file. If not provided, searches for .env
                 in current directory and parent directories.

    Returns:
        Configured PipelineConfig instance

    Example:
        >>> config = load_config()  # Load from .env
        >>> config = load_config(".env.staging")  # Load from specific file
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True) if env_path else load_dotenv()
    except ImportError:
        pass

    return PipelineConfig.from_env(env_path=env_path)

