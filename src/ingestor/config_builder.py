"""Fluent configuration builder for programmatic setup."""

from typing import Optional
from pathlib import Path

from .config import (
    PipelineConfig,
    SearchConfig,
    DocumentIntelligenceConfig,
    OfficeExtractorConfig,
    AzureOpenAIConfig,
    InputConfig,
    ArtifactsConfig,
    ChunkingConfig,
    PerformanceConfig,
    AzureCredentials,
    KeyVaultConfig,
    ContentUnderstandingConfig,
    InputMode,
    ArtifactsMode,
    MediaDescriberMode,
    TableRenderMode,
    DocumentAction,
    OfficeExtractorMode,
)


class ConfigBuilder:
    """Fluent builder for PipelineConfig.

    Makes it easy to create configurations programmatically without environment variables.
    Provides sensible defaults and a chainable API.

    Example:
        >>> config = (
        ...     ConfigBuilder()
        ...     .with_local_files("docs/*.pdf")
        ...     .with_search("my-service", "my-index", "key123")
        ...     .with_document_intelligence("https://my-di.cognitiveservices.azure.com", "key456")
        ...     .with_azure_openai("https://my-openai.openai.azure.com", "key789", "text-embedding-ada-002")
        ...     .build()
        ... )
    """

    def __init__(self):
        """Initialize builder with default values."""
        # Initialize with sensible defaults
        self._search = SearchConfig(endpoint=None, index_name=None, api_key=None)
        self._document_intelligence = DocumentIntelligenceConfig(endpoint=None, key=None, max_concurrency=3)
        self._office_extractor = OfficeExtractorConfig()  # Has defaults
        self._azure_openai = AzureOpenAIConfig(endpoint=None, api_key=None, emb_deployment=None)
        self._input = InputConfig(mode=InputMode.LOCAL)
        self._artifacts = ArtifactsConfig(mode=ArtifactsMode.LOCAL, local_dir="./artifacts")
        self._azure_credentials = AzureCredentials()
        self._key_vault = KeyVaultConfig()
        self._chunking = ChunkingConfig()  # Has defaults
        self._performance = PerformanceConfig()  # Has defaults
        self._content_understanding: Optional[ContentUnderstandingConfig] = None

        # Processing options
        self._media_describer_mode = MediaDescriberMode.GPT4O
        self._table_render_mode = TableRenderMode.PLAIN
        self._generate_table_summaries = False
        self._use_integrated_vectorization = False
        self._document_action = DocumentAction.ADD

    def with_search(
        self,
        service_name: str,
        index_name: str,
        api_key: Optional[str] = None
    ) -> "ConfigBuilder":
        """Configure Azure AI Search.

        Args:
            service_name: Search service name (constructs endpoint automatically)
            index_name: Index name
            api_key: API key (optional if using managed identity)

        Returns:
            Self for chaining
        """
        endpoint = f"https://{service_name}.search.windows.net"
        self._search = SearchConfig(
            endpoint=endpoint,
            index_name=index_name,
            api_key=api_key,
            service_name=service_name
        )
        return self

    def with_search_endpoint(
        self,
        endpoint: str,
        index_name: str,
        api_key: Optional[str] = None
    ) -> "ConfigBuilder":
        """Configure Azure AI Search with full endpoint URL.

        Args:
            endpoint: Full search endpoint URL
            index_name: Index name
            api_key: API key (optional if using managed identity)

        Returns:
            Self for chaining
        """
        self._search = SearchConfig(
            endpoint=endpoint,
            index_name=index_name,
            api_key=api_key
        )
        return self

    def with_document_intelligence(
        self,
        endpoint: str,
        key: Optional[str] = None,
        max_concurrency: int = 3
    ) -> "ConfigBuilder":
        """Configure Azure Document Intelligence.

        Args:
            endpoint: Document Intelligence endpoint
            key: API key (optional if using managed identity)
            max_concurrency: Max concurrent requests

        Returns:
            Self for chaining
        """
        self._document_intelligence = DocumentIntelligenceConfig(
            endpoint=endpoint,
            key=key,
            max_concurrency=max_concurrency
        )
        return self

    def with_office_extractor_mode(
        self,
        mode: OfficeExtractorMode = OfficeExtractorMode.HYBRID,
        offline_fallback: bool = True,
        equation_extraction: bool = False
    ) -> "ConfigBuilder":
        """Configure document extraction mode.

        Args:
            mode: Extraction mode (azure_di, markitdown, or hybrid)
            offline_fallback: Enable offline fallback (hybrid mode only)
            equation_extraction: Enable equation extraction

        Returns:
            Self for chaining
        """
        self._office_extractor.mode = mode
        self._office_extractor.offline_fallback = offline_fallback
        self._office_extractor.equation_extraction = equation_extraction
        return self

    def with_azure_openai(
        self,
        endpoint: str,
        api_key: str,
        embedding_deployment: str,
        embedding_model: str = "text-embedding-ada-002",
        embedding_dimensions: Optional[int] = None,
        chat_deployment: Optional[str] = None,
        max_concurrency: int = 5
    ) -> "ConfigBuilder":
        """Configure Azure OpenAI.

        Args:
            endpoint: OpenAI endpoint URL
            api_key: API key
            embedding_deployment: Embedding deployment name
            embedding_model: Embedding model name
            embedding_dimensions: Custom dimensions for text-embedding-3-* models
            chat_deployment: Chat deployment name (for media descriptions)
            max_concurrency: Max concurrent requests

        Returns:
            Self for chaining
        """
        self._azure_openai = AzureOpenAIConfig(
            endpoint=endpoint,
            api_key=api_key,
            emb_deployment=embedding_deployment,
            emb_model_name=embedding_model,
            emb_dimensions=embedding_dimensions,
            chat_deployment=chat_deployment,
            max_concurrency=max_concurrency
        )
        return self

    def with_local_files(
        self,
        glob_pattern: str,
        artifacts_dir: str = "./artifacts"
    ) -> "ConfigBuilder":
        """Configure local file input.

        Args:
            glob_pattern: Glob pattern for input files (e.g., "docs/*.pdf")
            artifacts_dir: Directory for artifacts storage

        Returns:
            Self for chaining
        """
        self._input = InputConfig(
            mode=InputMode.LOCAL,
            local_glob=glob_pattern
        )
        self._artifacts = ArtifactsConfig(
            mode=ArtifactsMode.LOCAL,
            local_dir=artifacts_dir
        )
        return self

    def with_blob_input(
        self,
        account_url: str,
        container_in: str,
        prefix: str = "",
        account_key: Optional[str] = None,
        connection_string: Optional[str] = None
    ) -> "ConfigBuilder":
        """Configure Azure Blob Storage input.

        Args:
            account_url: Storage account URL
            container_in: Input container name
            prefix: Blob prefix filter
            account_key: Storage account key
            connection_string: Connection string (alternative to account_key)

        Returns:
            Self for chaining
        """
        self._input = InputConfig(
            mode=InputMode.BLOB,
            blob_account_url=account_url,
            blob_container_in=container_in,
            blob_prefix=prefix,
            blob_key=account_key,
            blob_connection_string=connection_string
        )
        return self

    def with_blob_artifacts(
        self,
        account_url: str,
        container_pages: str,
        container_chunks: str,
        container_images: Optional[str] = None,
        container_citations: Optional[str] = None,
        account_key: Optional[str] = None,
        connection_string: Optional[str] = None
    ) -> "ConfigBuilder":
        """Configure Azure Blob Storage for artifacts.

        Args:
            account_url: Storage account URL
            container_pages: Container for page artifacts
            container_chunks: Container for chunk artifacts
            container_images: Container for extracted images
            container_citations: Container for per-page PDFs
            account_key: Storage account key
            connection_string: Connection string (alternative to account_key)

        Returns:
            Self for chaining
        """
        self._artifacts = ArtifactsConfig(
            mode=ArtifactsMode.BLOB,
            blob_account_url=account_url,
            blob_container_pages=container_pages,
            blob_container_chunks=container_chunks,
            blob_container_images=container_images,
            blob_container_citations=container_citations,
            blob_key=account_key,
            blob_connection_string=connection_string
        )
        return self

    def with_chunking(
        self,
        max_tokens: int = 500,
        max_chars: int = 1000,
        overlap_percent: int = 10,
        cross_page_overlap: bool = False,
        disable_char_limit: bool = False
    ) -> "ConfigBuilder":
        """Configure text chunking.

        Args:
            max_tokens: Maximum tokens per chunk
            max_chars: Maximum characters per chunk
            overlap_percent: Overlap percentage between chunks
            cross_page_overlap: Allow overlap across page boundaries
            disable_char_limit: Disable character limit

        Returns:
            Self for chaining
        """
        self._chunking = ChunkingConfig(
            max_tokens=max_tokens,
            max_chars=max_chars,
            overlap_percent=overlap_percent,
            cross_page_overlap=cross_page_overlap,
            disable_char_limit=disable_char_limit
        )
        return self

    def with_performance(
        self,
        max_workers: int = 4,
        embed_batch_size: int = 128,
        upload_batch_size: int = 1000
    ) -> "ConfigBuilder":
        """Configure performance settings.

        Args:
            max_workers: Maximum parallel workers
            embed_batch_size: Embedding batch size
            upload_batch_size: Upload batch size

        Returns:
            Self for chaining
        """
        self._performance = PerformanceConfig(
            max_workers=max_workers,
            embed_batch_size=embed_batch_size,
            upload_batch_size=upload_batch_size,
            inner_analyze_workers=self._performance.inner_analyze_workers,
            upload_delay=self._performance.upload_delay
        )
        return self

    def with_media_descriptions(
        self,
        mode: MediaDescriberMode = MediaDescriberMode.GPT4O
    ) -> "ConfigBuilder":
        """Configure media description mode.

        Args:
            mode: Media describer mode (gpt4o, content_understanding, or disabled)

        Returns:
            Self for chaining
        """
        self._media_describer_mode = mode
        return self

    def with_table_rendering(
        self,
        mode: TableRenderMode = TableRenderMode.MARKDOWN,
        generate_summaries: bool = False
    ) -> "ConfigBuilder":
        """Configure table rendering.

        Args:
            mode: Table render mode (plain, markdown, or html)
            generate_summaries: Generate AI summaries for tables

        Returns:
            Self for chaining
        """
        self._table_render_mode = mode
        self._generate_table_summaries = generate_summaries
        return self

    def with_integrated_vectorization(
        self,
        enabled: bool = True
    ) -> "ConfigBuilder":
        """Use Azure Search integrated vectorization instead of client-side embeddings.

        Args:
            enabled: Enable integrated vectorization

        Returns:
            Self for chaining
        """
        self._use_integrated_vectorization = enabled
        return self

    def with_document_action(
        self,
        action: DocumentAction = DocumentAction.ADD
    ) -> "ConfigBuilder":
        """Set document processing action.

        Args:
            action: Document action (add, remove, or removeall)

        Returns:
            Self for chaining
        """
        self._document_action = action
        return self

    def build(self) -> PipelineConfig:
        """Build the final PipelineConfig.

        Returns:
            Configured PipelineConfig instance

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not self._search.endpoint:
            raise ValueError("Search endpoint is required. Use with_search() or with_search_endpoint()")
        if not self._search.index_name:
            raise ValueError("Search index name is required. Use with_search() or with_search_endpoint()")

        # Document Intelligence is optional in offline mode
        if self._office_extractor.mode != OfficeExtractorMode.MARKITDOWN:
            if not self._document_intelligence.endpoint:
                raise ValueError(
                    "Document Intelligence endpoint is required for azure_di and hybrid modes. "
                    "Use with_document_intelligence() or switch to markitdown mode with "
                    "with_office_extractor_mode(OfficeExtractorMode.MARKITDOWN)"
                )

        # Azure OpenAI is optional if using integrated vectorization
        if not self._use_integrated_vectorization:
            if not self._azure_openai.endpoint:
                raise ValueError(
                    "Azure OpenAI endpoint is required for client-side embeddings. "
                    "Use with_azure_openai() or enable integrated vectorization with "
                    "with_integrated_vectorization(True)"
                )
            if not self._azure_openai.emb_deployment:
                raise ValueError(
                    "Azure OpenAI embedding deployment is required. "
                    "Use with_azure_openai() or enable integrated vectorization"
                )

        # Input configuration
        if self._input.mode == InputMode.LOCAL:
            if not self._input.local_glob:
                raise ValueError("Local glob pattern is required. Use with_local_files()")
        else:
            if not self._input.blob_account_url and not self._input.blob_connection_string:
                raise ValueError("Blob account URL or connection string is required. Use with_blob_input()")
            if not self._input.blob_container_in:
                raise ValueError("Blob input container is required. Use with_blob_input()")

        return PipelineConfig(
            search=self._search,
            document_intelligence=self._document_intelligence,
            office_extractor=self._office_extractor,
            azure_openai=self._azure_openai,
            input=self._input,
            artifacts=self._artifacts,
            azure_credentials=self._azure_credentials,
            key_vault=self._key_vault,
            chunking=self._chunking,
            performance=self._performance,
            content_understanding=self._content_understanding,
            media_describer_mode=self._media_describer_mode,
            table_render_mode=self._table_render_mode,
            generate_table_summaries=self._generate_table_summaries,
            use_integrated_vectorization=self._use_integrated_vectorization,
            document_action=self._document_action
        )
