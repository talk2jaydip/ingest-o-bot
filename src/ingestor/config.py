"""Configuration management for ingestor."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
            raise ValueError("AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE is required")
        if not index_name:
            raise ValueError("AZURE_SEARCH_INDEX is required")
        
        return cls(
            endpoint=endpoint,
            index_name=index_name,
            api_key=api_key
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

        if not endpoint:
            raise ValueError("AZURE_DOC_INT_ENDPOINT is required")

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
        # Phase 2: All three modes supported (azure_di, markitdown, hybrid)
        mode_str = os.getenv("AZURE_OFFICE_EXTRACTOR_MODE", "hybrid")
        mode = OfficeExtractorMode(mode_str)

        # Phase 2: Fallback flag (only applies to HYBRID mode)
        offline_fallback = os.getenv("AZURE_OFFICE_OFFLINE_FALLBACK", "true").lower() == "true"
        libreoffice_path = os.getenv("AZURE_OFFICE_LIBREOFFICE_PATH")

        # Phase 3: Equation extraction (now active)
        equation_extraction = os.getenv("AZURE_OFFICE_EQUATION_EXTRACTION", "false").lower() == "true"

        max_file_size_mb = int(os.getenv("AZURE_OFFICE_MAX_FILE_SIZE_MB", "100"))

        # Verbose logging for debugging
        verbose = os.getenv("AZURE_OFFICE_VERBOSE", "false").lower() == "true"

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
        
        max_concurrency = int(os.getenv("AZURE_OPENAI_MAX_CONCURRENCY", "5"))
        max_retries = int(os.getenv("AZURE_OPENAI_MAX_RETRIES", "3"))
        
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        if not api_key:
            raise ValueError("AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY is required")
        if not emb_deployment:
            raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT is required")
        
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            emb_deployment=emb_deployment,
            emb_model_name=emb_model_name,
            emb_dimensions=emb_dimensions,
            chat_deployment=chat_deployment,
            chat_model_name=chat_model_name,
            max_concurrency=max_concurrency,
            max_retries=max_retries
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
        mode_str = os.getenv("AZURE_INPUT_MODE", "local").lower()
        mode = InputMode(mode_str)
        
        if mode == InputMode.LOCAL:
            local_glob = os.getenv("AZURE_LOCAL_GLOB")
            if not local_glob:
                raise ValueError("AZURE_LOCAL_GLOB is required when AZURE_INPUT_MODE=local")
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
                raise ValueError("AZURE_STORAGE_ACCOUNT is required when AZURE_INPUT_MODE=blob")
            if not blob_container_in:
                raise ValueError("AZURE_BLOB_CONTAINER_IN or AZURE_STORAGE_CONTAINER is required when AZURE_INPUT_MODE=blob")
            
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
    blob_container_prefix: Optional[str] = None  # Prefix for all blob container names
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

        SIMPLIFIED Logic:
        1. If AZURE_ARTIFACTS_DIR is set → LOCAL storage at that directory
           (Overrides input_mode - useful for debugging blob inputs locally)
        2. Otherwise → Follow input_mode (local input → local artifacts, blob input → blob artifacts)
        3. Default → LOCAL if no input_mode provided

        Deprecated flags (backwards compatibility, but prefer AZURE_ARTIFACTS_DIR):
        - AZURE_ARTIFACTS_MODE: Still supported for explicit control
        - AZURE_STORE_ARTIFACTS_TO_BLOB: Still supported but redundant with input_mode
        """
        # Check if AZURE_ARTIFACTS_DIR is explicitly set (HIGHEST PRIORITY - OVERRIDE)
        artifacts_dir = os.getenv("AZURE_ARTIFACTS_DIR")

        if artifacts_dir:
            # AZURE_ARTIFACTS_DIR explicitly set - use local storage
            mode = ArtifactsMode.LOCAL
            get_logger(__name__).info(
                f"Using local artifacts storage: {artifacts_dir} "
                f"(overrides input_mode={input_mode.value if input_mode else 'not set'})"
            )
        else:
            # Check deprecated flags for backwards compatibility
            mode_str = os.getenv("AZURE_ARTIFACTS_MODE")
            force_blob = os.getenv("AZURE_STORE_ARTIFACTS_TO_BLOB", "").lower() == "true"

            if mode_str:
                # Explicit mode set (deprecated but supported)
                mode = ArtifactsMode(mode_str.lower())
                get_logger(__name__).info(f"Using AZURE_ARTIFACTS_MODE={mode.value} (deprecated, prefer removing this flag)")
            elif force_blob:
                # Override flag set (deprecated but supported)
                mode = ArtifactsMode.BLOB
                get_logger(__name__).info("Using AZURE_STORE_ARTIFACTS_TO_BLOB=true (deprecated, prefer removing this flag)")
            elif input_mode:
                # Follow input mode (RECOMMENDED approach)
                mode = ArtifactsMode.BLOB if input_mode == InputMode.BLOB else ArtifactsMode.LOCAL
                get_logger(__name__).info(f"Artifacts storage follows input mode: {mode.value}")
            else:
                # Default to local
                mode = ArtifactsMode.LOCAL
                get_logger(__name__).info("Using default: local artifacts storage")

        if mode == ArtifactsMode.LOCAL:
            local_dir = os.getenv("AZURE_ARTIFACTS_DIR", "./artifacts")
            return cls(mode=mode, local_dir=local_dir)
        else:
            storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
            if storage_account:
                blob_account_url = f"https://{storage_account}.blob.core.windows.net"
            else:
                blob_account_url = os.getenv("AZURE_BLOB_ACCOUNT_URL")
            
            # Container prefix (e.g., "myproject")
            blob_container_prefix = os.getenv("AZURE_BLOB_CONTAINER_PREFIX", "")

            # Base container names (will be prefixed if AZURE_BLOB_CONTAINER_PREFIX is set)
            base_pages = os.getenv("AZURE_BLOB_CONTAINER_OUT_PAGES")
            base_chunks = os.getenv("AZURE_BLOB_CONTAINER_OUT_CHUNKS")
            base_images = os.getenv("AZURE_BLOB_CONTAINER_OUT_IMAGES")
            base_citations = os.getenv("AZURE_BLOB_CONTAINER_CITATIONS")

            # Fallback to AZURE_STORAGE_CONTAINER with -output suffix if specific containers not set
            if not base_pages and not base_chunks:
                base_container = os.getenv("AZURE_STORAGE_CONTAINER")
                if base_container:
                    base_pages = "pages"
                    base_chunks = "chunks"
                    base_images = "images"
                    base_citations = "citations"
                    blob_container_prefix = base_container  # Use AZURE_STORAGE_CONTAINER as prefix
                    get_logger(__name__).info(f"Using AZURE_STORAGE_CONTAINER as prefix for output containers: {base_container}")

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

            if not blob_account_url and not blob_connection_string:
                raise ValueError("AZURE_STORAGE_ACCOUNT is required when AZURE_ARTIFACTS_MODE=blob")
            if not blob_container_pages:
                raise ValueError("AZURE_BLOB_CONTAINER_OUT_PAGES or AZURE_STORAGE_CONTAINER is required when AZURE_ARTIFACTS_MODE=blob")
            if not blob_container_chunks:
                raise ValueError("AZURE_BLOB_CONTAINER_OUT_CHUNKS or AZURE_STORAGE_CONTAINER is required when AZURE_ARTIFACTS_MODE=blob")
            
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
    
    @classmethod
    def from_env(cls) -> "ChunkingConfig":
        """Load from environment variables."""
        max_chars = int(os.getenv("AZURE_CHUNKING_MAX_CHARS", "1000"))
        max_tokens = int(os.getenv("AZURE_CHUNKING_MAX_TOKENS", "500"))
        overlap_percent = int(os.getenv("AZURE_CHUNKING_OVERLAP_PERCENT", "10"))
        cross_page_overlap = os.getenv("AZURE_CHUNKING_CROSS_PAGE_OVERLAP", "false").lower() == "true"
        disable_char_limit = os.getenv("AZURE_CHUNKING_DISABLE_CHAR_LIMIT", "false").lower() == "true"
        
        return cls(
            max_chars=max_chars,
            max_tokens=max_tokens,
            overlap_percent=overlap_percent,
            cross_page_overlap=cross_page_overlap,
            disable_char_limit=disable_char_limit
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
        max_workers = int(os.getenv("AZURE_MAX_WORKERS", "4"))
        inner_analyze_workers = int(os.getenv("AZURE_INNER_ANALYZE_WORKERS", "1"))
        upload_delay = float(os.getenv("AZURE_UPLOAD_DELAY", "0.5"))
        embed_batch_size = int(os.getenv("AZURE_EMBED_BATCH_SIZE", "128"))
        upload_batch_size = int(os.getenv("AZURE_UPLOAD_BATCH_SIZE", "1000"))

        # Parallelization settings
        max_image_concurrency = int(os.getenv("AZURE_MAX_IMAGE_CONCURRENCY", "8"))
        max_figure_concurrency = int(os.getenv("AZURE_MAX_FIGURE_CONCURRENCY", "5"))
        max_batch_upload_concurrency = int(os.getenv("AZURE_MAX_BATCH_UPLOAD_CONCURRENCY", "5"))

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
    
    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "PipelineConfig":
        """Load complete configuration from environment variables.

        Args:
            env_path: Optional path to .env file. If not provided, searches for .env
                     in current directory and parent directories.

        Returns:
            Configured PipelineConfig instance

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

        search = SearchConfig.from_env()
        document_intelligence = DocumentIntelligenceConfig.from_env()
        office_extractor = OfficeExtractorConfig.from_env()
        azure_openai = AzureOpenAIConfig.from_env()
        input_config = InputConfig.from_env()
        # Pass input mode to enable auto-detection of artifacts mode
        artifacts = ArtifactsConfig.from_env(input_mode=input_config.mode)
        azure_credentials = AzureCredentials.from_env()
        key_vault = KeyVaultConfig.from_env()
        chunking = ChunkingConfig.from_env()
        performance = PerformanceConfig.from_env()
        logging_config = LoggingConfig.from_env()
        content_understanding = ContentUnderstandingConfig.from_env()

        # Processing options
        media_describer_str = os.getenv("AZURE_MEDIA_DESCRIBER", "gpt4o").lower()
        media_describer_mode = MediaDescriberMode(media_describer_str)

        table_render_str = os.getenv("AZURE_TABLE_RENDER", "plain").lower()
        table_render_mode = TableRenderMode(table_render_str)

        generate_table_summaries = os.getenv("AZURE_TABLE_SUMMARIES", "false").lower() == "true"
        use_integrated_vectorization = os.getenv("AZURE_USE_INTEGRATED_VECTORIZATION", "false").lower() == "true"

        # Document action mode
        document_action_str = os.getenv("AZURE_DOCUMENT_ACTION", "add").lower()
        document_action = DocumentAction(document_action_str)

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
            document_action=document_action
        )


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

