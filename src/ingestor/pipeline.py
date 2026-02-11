"""Main pipeline orchestrator."""

import asyncio
import hashlib
from ingestor.di_extractor import ExtractedImage
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .artifact_storage import ArtifactStorage, BlobArtifactStorage, create_artifact_storage
from .config import ArtifactsMode, DocumentAction, VectorStoreMode, EmbeddingsMode
from .chunker import LayoutAwareChunker, TextChunk, create_chunker
from .config import PipelineConfig
from .di_extractor import DocumentIntelligenceExtractor, ExtractedPage
from .office_extractor import OfficeExtractor
from .embeddings import EmbeddingsGenerator, create_embeddings_generator
from .embeddings_provider import EmbeddingsProvider, create_embeddings_provider
from .input_source import InputSource, create_input_source
from .logging_utils import (
    get_logger,
    log_chunking_process,
    log_di_response,
    log_di_summary,
    log_figure_processing,
    log_pipeline_summary,
    log_table_processing,
)
from .media_describer import MediaDescriber, create_media_describer
from .models import (
    ChunkArtifact,
    ChunkDocument,
    ChunkMetadata,
    DocumentMetadata,
    FigureReference,
    IngestionResult,
    PageMetadata,
    PipelineStatus,
    TableReference,
)
from .page_splitter import PagePdfSplitter
from .search_uploader import SearchUploader, create_search_uploader
from .table_renderer import TableRenderer, create_table_renderer
from .validator import PipelineValidator
from .vector_store import VectorStore, create_vector_store

logger = get_logger(__name__)


class Pipeline:
    """Main document ingestion pipeline.

    BLOB URL REQUIREMENTS:
    ======================
    This pipeline requires blob storage to be configured (AZURE_STORAGE_ACCOUNT, etc.)
    because both storage_url and citation URLs MUST be blob URLs (https://...), never file:// URIs.

    Behavior by file type:
    - **PDFs**:
        1. Full document uploaded to blob → storage_url
        2. Split into per-page PDFs → uploaded to citations container → citation URLs
        3. sourcepage format: "docname/page-0001.pdf#page=1"

    - **PPTX** (presentations):
        1. Full document uploaded to blob → storage_url
        2. No per-slide files created (PPTX doesn't support page extraction)
        3. sourcepage format: "presentation.pptx#slide=3"

    - **DOCX** (Word documents):
        1. Full document uploaded to blob → storage_url
        2. No per-page files created
        3. sourcepage format: "document.docx#page=5"

    - **Text files** (MD, TXT, JSON, CSV, HTML):
        1. Full file uploaded to blob → storage_url
        2. No per-page files created
        3. sourcepage format: "file.md#page=2"

    All files must be uploaded to blob storage even if input source is already blob,
    to ensure storage_url is always a valid blob URL for the search index.
    """

    def __init__(self, config: PipelineConfig, log_dir: Optional[Path] = None, clean_artifacts: bool = False, validate_only: bool = False):
        self.config = config
        self.log_dir = log_dir or Path("./logs")
        self.clean_artifacts = clean_artifacts
        self.validate_only = validate_only
        self.write_artifacts = config.logging.write_artifacts  # Control artifact log writing

        # Initialize components
        self.input_source: Optional[InputSource] = None
        self.artifact_storage: Optional[ArtifactStorage] = None
        self.di_extractor: Optional[DocumentIntelligenceExtractor] = None
        self.office_extractor: Optional[OfficeExtractor] = None
        self.table_renderer: Optional[TableRenderer] = None
        self.media_describer: Optional[MediaDescriber] = None
        self.chunker: Optional[LayoutAwareChunker] = None

        # Legacy components (still supported for backward compatibility)
        self.embeddings_gen: Optional[EmbeddingsGenerator] = None
        self.search_uploader: Optional[SearchUploader] = None

        # New pluggable components
        self.embeddings_provider: Optional[EmbeddingsProvider] = None
        self.vector_store: Optional[VectorStore] = None

        self.page_splitter: Optional[PagePdfSplitter] = None

        # Track page PDF URLs for citations (blob URLs to per-page PDFs)
        self.page_pdf_urls: dict[tuple[str, int], str] = {}
        # Track full document URLs (blob URLs to complete documents)
        self.full_document_urls: dict[str, str] = {}
    
    def _get_blob_url_for_document(self, filename: str) -> str:
        """Construct blob URL for a document when artifacts are stored in blob storage.

        Args:
            filename: Document filename (with extension)

        Returns:
            Blob URL pointing to where the document would be stored/accessible
        """
        if self.artifact_storage is None:
            # Ensure artifact storage is initialized
            self._initialize_components()

        if not isinstance(self.artifact_storage, BlobArtifactStorage):
            # Fallback - shouldn't happen if artifacts mode is BLOB
            logger.warning(f"Artifact storage is not BlobArtifactStorage, using fallback URL for {filename}")
            return f"https://unknown.blob.core.windows.net/unknown/{filename}"

        # Use citations container if available (for full documents), otherwise pages container
        container = self.artifact_storage.citations_container or self.artifact_storage.pages_container
        account_url = self.artifact_storage.account_url

        # Sanitize filename for blob storage and preserve extension
        # (matches write_full_document behavior)
        safe_name = self.artifact_storage._sanitize_doc_name(filename)
        original_ext = Path(filename).suffix.lower()
        if not Path(safe_name).suffix and original_ext:
            blob_name = f"{safe_name}{original_ext}"
        else:
            blob_name = safe_name

        # Construct blob URL: https://account.blob.core.windows.net/container/filename.ext
        blob_url = f"{account_url}/{container}/{blob_name}"

        logger.debug(f"Constructed blob URL for {filename}: {blob_url}")
        return blob_url

    def _construct_blob_url_from_config(self, filename: str) -> Optional[str]:
        """Construct blob URL from environment configuration without BlobArtifactStorage.

        This allows generating blob URLs even when artifacts are stored locally,
        as long as the blob storage configuration exists in environment variables.

        Args:
            filename: Document filename (with extension)

        Returns:
            Constructed blob URL, or None if configuration is missing
        """
        import os
        import re

        # Get storage account from environment
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        if not storage_account:
            logger.debug("AZURE_STORAGE_ACCOUNT not set, cannot construct blob URL")
            return None

        # Construct account URL
        account_url = f"https://{storage_account}.blob.core.windows.net"

        # Get container configuration (prefer citations container for full documents)
        # Priority: AZURE_BLOB_CONTAINER_CITATIONS > AZURE_STORAGE_CONTAINER-citations
        citations_container = os.getenv("AZURE_BLOB_CONTAINER_CITATIONS")
        if not citations_container:
            # Try to construct from base container name
            base_container = os.getenv("AZURE_STORAGE_CONTAINER")
            container_prefix = os.getenv("AZURE_BLOB_CONTAINER_PREFIX")

            if container_prefix:
                citations_container = f"{container_prefix}-citations"
            elif base_container:
                citations_container = f"{base_container}-citations"

        if not citations_container:
            logger.debug("No blob container configuration found, cannot construct blob URL")
            return None

        # Sanitize filename (mimic BlobArtifactStorage._sanitize_doc_name behavior)
        # Remove any directory separators and special characters
        safe_name = Path(filename).name  # Get just the filename
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', safe_name)  # Replace invalid blob chars
        safe_name = safe_name.replace(' ', '_')  # Replace spaces with underscores

        # Preserve file extension
        original_ext = Path(filename).suffix.lower()
        if not Path(safe_name).suffix and original_ext:
            blob_name = f"{safe_name}{original_ext}"
        else:
            blob_name = safe_name

        # Construct base URL
        blob_url = f"{account_url}/{citations_container}/{blob_name}"

        # Optionally append SAS token if configured
        # Note: For production, you should generate SAS tokens dynamically with limited expiry
        # This is a simple approach using a pre-generated SAS token from environment
        sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
        if sas_token:
            # Remove leading '?' if present
            sas_token = sas_token.lstrip('?')
            blob_url = f"{blob_url}?{sas_token}"
            logger.debug(f"Constructed blob URL with SAS token from config: {blob_url[:80]}...")
        else:
            logger.debug(f"Constructed blob URL from config (no SAS): {blob_url}")

        return blob_url

    def _construct_page_pdf_url_from_config(self, filename: str, page_num: int) -> Optional[str]:
        """Construct per-page PDF blob URL from environment configuration.

        Mimics the naming convention used by BlobArtifactStorage.write_page_pdf():
        {sanitized_name}_page_{page_num_1based:04d}.pdf

        Args:
            filename: Document filename (with extension)
            page_num: Page number (0-indexed, will be converted to 1-based)

        Returns:
            Constructed blob URL for the page PDF, or None if configuration is missing
        """
        import os
        import re

        # Get storage account from environment
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        if not storage_account:
            return None

        # Construct account URL
        account_url = f"https://{storage_account}.blob.core.windows.net"

        # Get pages container configuration
        pages_container = os.getenv("AZURE_BLOB_CONTAINER_OUT_PAGES")
        if not pages_container:
            # Try to construct from base container name
            base_container = os.getenv("AZURE_STORAGE_CONTAINER")
            container_prefix = os.getenv("AZURE_BLOB_CONTAINER_PREFIX")

            if container_prefix:
                pages_container = f"{container_prefix}-pages"
            elif base_container:
                pages_container = f"{base_container}-pages"

        if not pages_container:
            return None

        # Sanitize filename (remove extension and sanitize)
        safe_name = Path(filename).stem  # Remove extension
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', safe_name)  # Replace invalid blob chars
        safe_name = safe_name.replace(' ', '_')  # Replace spaces with underscores

        # Construct page PDF name using 1-based page numbering
        # Format: {safe_name}_page_{page_num_1based:04d}.pdf
        page_num_1based = page_num + 1
        blob_name = f"{safe_name}_page_{page_num_1based:04d}.pdf"

        # Construct base URL
        blob_url = f"{account_url}/{pages_container}/{blob_name}"

        # Optionally append SAS token if configured
        sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
        if sas_token:
            # Remove leading '?' if present
            sas_token = sas_token.lstrip('?')
            blob_url = f"{blob_url}?{sas_token}"

        return blob_url

    def _construct_image_url_from_config(self, filename: str, page_num: int, figure_idx: int) -> Optional[str]:
        """Construct image blob URL from environment configuration.

        Mimics the naming convention used by BlobArtifactStorage.write_image():
        {sanitized_name}/page_{page_num_1based:02d}_fig_{fig_num_1based:02d}.png

        Args:
            filename: Document filename (with extension)
            page_num: Page number (0-indexed, will be converted to 1-based)
            figure_idx: Figure index on page (0-indexed, will be converted to 1-based)

        Returns:
            Constructed blob URL for the image, or None if configuration is missing
        """
        import os
        import re

        # Get storage account from environment
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        if not storage_account:
            return None

        # Construct account URL
        account_url = f"https://{storage_account}.blob.core.windows.net"

        # Get images container configuration
        images_container = os.getenv("AZURE_BLOB_CONTAINER_OUT_IMAGES")
        if not images_container:
            # Try to construct from base container name
            base_container = os.getenv("AZURE_STORAGE_CONTAINER")
            container_prefix = os.getenv("AZURE_BLOB_CONTAINER_PREFIX")

            if container_prefix:
                images_container = f"{container_prefix}-images"
            elif base_container:
                images_container = f"{base_container}-images"

        if not images_container:
            return None

        # Sanitize filename (remove extension and sanitize)
        safe_name = Path(filename).stem  # Remove extension
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', safe_name)  # Replace invalid blob chars
        safe_name = safe_name.replace(' ', '_')  # Replace spaces with underscores

        # Construct image name using 1-based numbering
        # Format: {safe_name}/page_{page_num_1based:02d}_fig_{fig_num_1based:02d}.png
        page_num_1based = page_num + 1
        fig_num_1based = figure_idx + 1
        blob_name = f"{safe_name}/page_{page_num_1based:02d}_fig_{fig_num_1based:02d}.png"

        # Construct base URL
        blob_url = f"{account_url}/{images_container}/{blob_name}"

        # Optionally append SAS token if configured
        sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
        if sas_token:
            # Remove leading '?' if present
            sas_token = sas_token.lstrip('?')
            blob_url = f"{blob_url}?{sas_token}"

        return blob_url

    async def _initialize_components(self):
        """Lazy initialization of pipeline components."""
        if self.input_source is None:
            self.input_source = create_input_source(self.config.input)

        if self.artifact_storage is None:
            self.artifact_storage = create_artifact_storage(self.config.artifacts)
            # Ensure containers exist if using blob storage
            await self.artifact_storage.ensure_containers_exist()

            # IMPORTANT: Validate blob storage configuration
            # storage_url and citation URLs REQUIRE blob storage
            if not isinstance(self.artifact_storage, BlobArtifactStorage):
                logger.warning("=" * 80)
                logger.warning("⚠️  LOCAL ARTIFACTS MODE - Azure AI Search requires blob storage")
                logger.warning("=" * 80)
                logger.warning("Why this matters:")
                logger.warning("  • Azure AI Search requires https:// blob URLs")
                logger.warning("  • Local artifacts use file:// URIs that won't work in the index")
                logger.warning("  • Users won't be able to access document citations")
                logger.warning("")
                logger.warning("To fix - Choose ONE option:")
                logger.warning("")
                logger.warning("  OPTION 1 (Recommended): Use blob input → blob artifacts")
                logger.warning("    Set: AZURE_INPUT_MODE=blob")
                logger.warning("    Remove: AZURE_ARTIFACTS_DIR (if set)")
                logger.warning("    Result: Artifacts automatically go to blob storage")
                logger.warning("")
                logger.warning("  OPTION 2: Keep local input, override to blob artifacts")
                logger.warning("    Keep: AZURE_INPUT_MODE=local")
                logger.warning("    Remove: AZURE_ARTIFACTS_DIR (if set)")
                logger.warning("    Add: AZURE_STORE_ARTIFACTS_TO_BLOB=true")
                logger.warning("=" * 80)
                logger.warning("")
        
        if self.table_renderer is None:
            self.table_renderer = create_table_renderer(self.config.table_render_mode)
        
        if self.di_extractor is None:
            # Pass table_renderer to extractor for in-place table rendering
            self.di_extractor = DocumentIntelligenceExtractor(
                self.config.document_intelligence,
                table_renderer=self.table_renderer,
                max_figure_concurrency=self.config.performance.max_figure_concurrency
            )

        if self.office_extractor is None:
            # Initialize Office document extractor (DOCX/PPTX)
            self.office_extractor = OfficeExtractor(
                di_config=self.config.document_intelligence,
                office_config=self.config.office_extractor,
                table_renderer=self.table_renderer
            )

        if self.media_describer is None:
            self.media_describer = create_media_describer(
                self.config.media_describer_mode,
                self.config.azure_openai,
                self.config.content_understanding
            )
        
        if self.chunker is None:
            self.chunker = create_chunker(
                max_chars=self.config.chunking.max_chars,
                max_tokens=self.config.chunking.max_tokens,
                overlap_percent=self.config.chunking.overlap_percent,
                cross_page_overlap=self.config.chunking.cross_page_overlap,
                disable_char_limit=self.config.chunking.disable_char_limit,
                table_renderer=self.table_renderer
            )
        
        # Initialize embeddings provider (new pluggable architecture)
        # Only initialize if using client-side embeddings
        if self.embeddings_provider is None and not self.config.use_integrated_vectorization:
            logger.info("Initializing embeddings provider")

            # Determine mode (backward compatible)
            if self.config.embeddings_mode:
                mode = self.config.embeddings_mode
                config = self.config.embeddings_config
            else:
                # Legacy: default to Azure OpenAI
                mode = EmbeddingsMode.AZURE_OPENAI
                config = self.config.azure_openai

            logger.info(f"  Mode: {mode.value}")

            # Create provider
            self.embeddings_provider = create_embeddings_provider(mode, config)

            # Log details
            logger.info(f"  Model: {self.embeddings_provider.get_model_name()}")
            logger.info(f"  Dimensions: {self.embeddings_provider.get_dimensions()}")

            # For backward compatibility: Also set embeddings_gen to the same instance if Azure OpenAI
            if mode == EmbeddingsMode.AZURE_OPENAI and self.embeddings_gen is None:
                # Extract the underlying generator from the wrapper
                self.embeddings_gen = self.embeddings_provider._generator

        # Initialize vector store (new pluggable architecture)
        if self.vector_store is None:
            logger.info("Initializing vector store")

            # Determine mode (backward compatible)
            if self.config.vector_store_mode:
                mode = self.config.vector_store_mode
                config = self.config.vector_store_config
            else:
                # Legacy: default to Azure Search
                mode = VectorStoreMode.AZURE_SEARCH
                config = self.config.search

            logger.info(f"  Mode: {mode.value}")

            # Create vector store
            self.vector_store = create_vector_store(
                mode,
                config,
                max_batch_concurrency=self.config.performance.max_batch_upload_concurrency
            )

            # For backward compatibility: Also set search_uploader to the same instance if Azure Search
            if mode == VectorStoreMode.AZURE_SEARCH and self.search_uploader is None:
                # Extract the underlying uploader from the wrapper
                self.search_uploader = self.vector_store._uploader

        # Initialize page splitter for per-page PDF citations (ALWAYS for PDFs)
        # Per-page PDFs are stored in blob storage for citation URLs
        if self.page_splitter is None:
            try:
                self.page_splitter = PagePdfSplitter()
                logger.info("Page splitter initialized for per-page PDF citations")
            except ImportError:
                logger.warning("pypdf not available - per-page PDF splitting disabled")
                self.page_splitter = None
    
    async def validate(self) -> bool:
        """Run pre-check validation on configuration and environment.

        Returns:
            True if all validations passed, False otherwise

        Raises:
            RuntimeError: If validation fails with details about what's wrong
        """
        validator = PipelineValidator(self.config)
        success = await validator.validate_all()

        if not success:
            failed_checks = [r for r in validator.results if not r.passed]
            error_msg = (
                f"\n\nValidation failed with {len(failed_checks)} error(s). "
                f"Please fix the issues above and try again."
            )
            raise RuntimeError(error_msg)

        logger.info("")
        logger.info("✅ All validation checks passed! Pipeline is ready to run.")
        logger.info("")
        return True

    async def run(self) -> Optional[PipelineStatus]:
        """Run the pipeline based on document action mode.

        Supports three actions:
        - ADD: Extract, chunk, embed, and index documents (default)
        - REMOVE: Remove specific documents from the index
        - REMOVE_ALL: Remove ALL documents from the index

        If validate_only is True, only runs validation and exits.

        Returns:
            PipelineStatus for ADD action, None for REMOVE/REMOVE_ALL actions
        """
        # Run validation if validate_only is enabled
        if self.validate_only:
            await self.validate()
            logger.info("✅ Validation complete. Exiting without processing documents.")
            return None

        logger.info(f"Starting document ingestion pipeline (action: {self.config.document_action.value})")
        await self._initialize_components()

        try:
            if self.config.document_action == DocumentAction.REMOVE_ALL:
                # Remove all documents from index
                await self.remove_all_documents()
                return None

            elif self.config.document_action == DocumentAction.REMOVE:
                # Remove specific documents
                await self.remove_documents(clean_artifacts=self.clean_artifacts)
                return None

            # Default: ADD action - process and index documents
            return await self._run_add_pipeline()

        finally:
            await self.close()
    
    async def _run_add_pipeline(self) -> PipelineStatus:
        """Run the ADD pipeline: delete existing → extract → chunk → embed → index.

        Processes documents in parallel based on max_workers configuration.
        Default behavior: Delete existing document chunks first, then add new ones (full replace).

        Returns:
            PipelineStatus with execution results
        """
        # Initialize pipeline status tracker
        pipeline_status = PipelineStatus()

        # Collect all files first (needed for parallel processing)
        logger.info("Collecting files from input source...")
        files = []
        async for filename, file_bytes, source_url in self.input_source.list_files():
            files.append((filename, file_bytes, source_url))

        # Validate that we found files to process
        if len(files) == 0:
            logger.error("No files found in input source. Check your configuration:")
            if self.config.input.mode.value == "local":
                logger.error(f"  - AZURE_INPUT_MODE=local")
                logger.error(f"  - AZURE_LOCAL_GLOB={self.config.input.local_glob}")
                logger.error(f"  Ensure files exist matching the glob pattern")
            else:
                logger.error(f"  - AZURE_INPUT_MODE=blob")
                logger.error(f"  - AZURE_BLOB_CONTAINER_IN={self.config.input.blob_container_in}")
                logger.error(f"  - AZURE_BLOB_PREFIX={self.config.input.blob_prefix or '(none)'}")
                logger.error(f"  Ensure the container exists and contains files")
            raise ValueError("No files found to process")

        logger.info(f"Found {len(files)} files to process")

        # Process documents in parallel (respecting max_workers)
        max_workers = self.config.performance.max_workers
        logger.info(f"Processing up to {max_workers} documents in parallel")

        # Create semaphore for document-level parallelism
        doc_semaphore = asyncio.Semaphore(max_workers)

        async def process_with_semaphore(file_info):
            """Process a single document with semaphore control."""
            async with doc_semaphore:
                return await self._process_single_document(*file_info)

        # Process all documents in parallel
        results = await asyncio.gather(*[
            process_with_semaphore(file_info)
            for file_info in files
        ], return_exceptions=True)

        # Collect results
        for result in results:
            if isinstance(result, Exception):
                # This shouldn't happen since _process_single_document catches exceptions
                logger.error(f"Unexpected exception during parallel processing: {result}", exc_info=result)
            elif result is not None:
                pipeline_status.add_result(result)

        # Log pipeline summary
        self._log_pipeline_status(pipeline_status)

        # Save status to artifact storage (async operation)
        await self._save_pipeline_status(pipeline_status)

        return pipeline_status

    async def _process_image(
        self,
        page_num: int,
        idx: int,
        image: ExtractedImage,
        filename: str
    ) -> tuple[int, int, ExtractedImage]:
        """Process a single image: describe and upload.

        Args:
            page_num: Page number (0-indexed)
            idx: Image index on the page
            image: ExtractedImage object to process
            filename: Document filename

        Returns:
            Tuple of (page_num, idx, processed_image) for logging
        """
        try:
            # Describe image
            if self.media_describer:
                logger.info(f"Generating description for figure {image.figure_id} on page {page_num + 1}")
                image.description = await self.media_describer.describe_image(image.image_bytes)

                # Log figure processing
                log_figure_processing(
                    self.log_dir, filename, page_num, idx, image, image.description
                )

            # Upload image or construct URL from config
            if isinstance(self.artifact_storage, BlobArtifactStorage):
                # Actually upload to blob storage
                image.url = await self.artifact_storage.write_image(
                    filename,
                    image.page_num,
                    image.filename,
                    image.image_bytes,
                    figure_idx=idx  # Pass figure index on page to prevent naming collisions
                )
            else:
                # Construct URL from config without uploading
                image.url = self._construct_image_url_from_config(filename, image.page_num, idx)
                if not image.url:
                    logger.warning(f"Could not construct image URL for {filename} page {image.page_num} figure {idx}")

            return (page_num, idx, image)

        except Exception as e:
            logger.error(f"Failed to process image {image.figure_id} on page {page_num + 1}: {e}")
            # Return the image with error logged, don't fail entire document
            return (page_num, idx, image)

    async def _process_single_document(
        self,
        filename: str,
        file_bytes: bytes,
        source_url: str
    ) -> IngestionResult:
        """Process a single document end-to-end.

        Returns IngestionResult (success or failure).
        This method is called in parallel for multiple documents.
        """
        logger.info(f"Processing document: {filename}")
        start_time = time.time()

        try:
            # Step 0: Delete existing chunks and artifacts in parallel
            logger.info(f"Checking for existing chunks and artifacts of {filename}")

            # Collect deletion tasks
            delete_tasks = []
            # Use pluggable vector store if available, otherwise use legacy search_uploader
            if self.vector_store:
                delete_tasks.append(self.vector_store.delete_documents_by_filename(filename))
            elif self.search_uploader:
                delete_tasks.append(self.search_uploader.delete_documents_by_filename(filename))

            if self.clean_artifacts and isinstance(self.artifact_storage, BlobArtifactStorage):
                delete_tasks.append(self.artifact_storage.delete_document_artifacts(filename))

            # Execute deletions in parallel
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)

            # Process results
            deleted_count = 0
            artifacts_deleted = 0

            if len(results) > 0:
                if isinstance(results[0], Exception):
                    logger.error(f"Failed to delete chunks: {results[0]}")
                else:
                    deleted_count = results[0]
                    if deleted_count > 0:
                        logger.info(f"Deleted {deleted_count} existing chunks for {filename}")
                    else:
                        logger.info(f"No existing chunks found for {filename}")

            if len(results) > 1:
                if isinstance(results[1], Exception):
                    logger.error(f"Failed to delete artifacts: {results[1]}")
                else:
                    artifacts_deleted = results[1]
                    if artifacts_deleted > 0:
                        logger.info(f"Deleted {artifacts_deleted} old artifact blobs for {filename}")
                    else:
                        logger.info(f"No old artifacts found for {filename}")

            # Check file type and process accordingly
            file_ext = Path(filename).suffix.lower()

            if file_ext == '.pdf':
                # ALWAYS ensure full document is in blob storage (storage_url requires blob URL)
                await self.upload_full_document(filename, file_bytes, source_url)

                # ALWAYS split PDF into per-page PDFs for citations (citation URLs require blob URLs)
                if self.page_splitter:
                    await self.split_and_store_page_pdfs(filename, file_bytes)
                else:
                    logger.warning(f"⚠️  Page splitter not available - skipping per-page PDF generation for {filename}")

                # Extract based on mode
                from .config import OfficeExtractorMode
                office_mode = self.config.office_extractor.mode

                if office_mode == OfficeExtractorMode.MARKITDOWN:
                    logger.info(f"📝 [MARKITDOWN MODE - PDF] Processing offline: {filename}")
                    pages = await self.extract_pdf_offline(filename, file_bytes)
                elif office_mode == OfficeExtractorMode.HYBRID:
                    try:
                        logger.info(f"🔄 [HYBRID MODE - PDF] Attempting Azure DI: {filename}")
                        pages = await self.extract_document(filename, file_bytes, source_url)
                    except Exception as e:
                        if self.config.office_extractor.offline_fallback:
                            logger.warning(
                                f"⚠️  [HYBRID MODE - PDF] Azure DI failed: {e.__class__.__name__}. "
                                f"Falling back to offline extraction..."
                            )
                            pages = await self.extract_pdf_offline(filename, file_bytes)
                        else:
                            logger.error(f"❌ [HYBRID MODE - PDF] Azure DI failed and fallback disabled")
                            raise
                else:
                    logger.info(f"☁️  [AZURE_DI MODE - PDF] Processing with Azure DI: {filename}")
                    pages = await self.extract_document(filename, file_bytes, source_url)

            elif file_ext in ['.docx', '.pptx', '.doc']:
                # Office documents: ALWAYS ensure in blob storage
                await self.upload_full_document(filename, file_bytes, source_url)
                pages = await self.extract_office_document(filename, file_bytes, source_url)

            else:
                # Text files (MD, TXT, JSON, CSV, HTML): ALWAYS ensure in blob storage
                await self.upload_full_document(filename, file_bytes, source_url)
                pages = await self._extract_text_file(filename, file_bytes, source_url)

            if not pages:
                error_msg = f"No pages extracted from {filename}"
                logger.warning(error_msg)
                processing_time = time.time() - start_time
                return IngestionResult(
                    filename=filename,
                    success=False,
                    chunks_indexed=0,
                    error_message=error_msg,
                    processing_time_seconds=processing_time
                )

            # Chunk
            chunks = await self.chunk_document(filename, pages, source_url)

            # Embed (if using client-side embeddings)
            if not self.config.use_integrated_vectorization:
                logger.info("=" * 60)
                logger.info("EMBEDDING MODE: Client-Side (Manual)")
                logger.info("=" * 60)
                await self.embed_chunks(chunks)
            else:
                logger.info("=" * 60)
                logger.info("EMBEDDING MODE: Integrated Vectorization (Azure Search)")
                logger.info("=" * 60)
                logger.info("Embeddings will be generated by Azure AI Search")
                logger.info("No client-side embedding generation needed")

            # Index
            chunks_indexed = await self.index_chunks(chunks)

            # Record success
            processing_time = time.time() - start_time
            result = IngestionResult(
                filename=filename,
                success=True,
                chunks_indexed=chunks_indexed,
                error_message=None,
                processing_time_seconds=processing_time
            )

            logger.info(f"✓ Successfully processed {filename}: {len(chunks)} chunks indexed in {processing_time:.2f}s")
            return result

        except Exception as e:
            # Record failure
            processing_time = time.time() - start_time
            error_msg = str(e)
            result = IngestionResult(
                filename=filename,
                success=False,
                chunks_indexed=0,
                error_message=error_msg,
                processing_time_seconds=processing_time
            )

            logger.error(f"✗ Failed to process {filename}: {e}", exc_info=True)
            return result

    def _log_pipeline_status(self, status: PipelineStatus):
        """Log pipeline execution status summary."""
        logger.info("=" * 80)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)

        summary = status.get_summary()
        logger.info(f"Total documents processed: {summary['total_documents']}")
        logger.info(f"✓ Successful ingestions: {summary['successful_documents']}")
        logger.info(f"✗ Failed ingestions: {summary['failed_documents']}")
        logger.info(f"Total chunks indexed: {summary['total_chunks_indexed']}")
        logger.info(f"Success rate: {summary['success_rate']}")

        # Log details of failed documents
        if status.failed_documents > 0:
            logger.info("")
            logger.info("Failed Documents:")
            logger.info("-" * 80)
            for result in status.results:
                if not result.success:
                    logger.error(f"  ✗ {result.filename}: {result.error_message}")

        # Log details of successful documents
        if status.successful_documents > 0:
            logger.info("")
            logger.info("Successful Documents:")
            logger.info("-" * 80)
            for result in status.results:
                if result.success:
                    logger.info(f"  ✓ {result.filename}: {result.chunks_indexed} chunks ({result.processing_time_seconds:.2f}s)")

        logger.info("=" * 80)

    async def _save_pipeline_status(self, status: PipelineStatus):
        """Save pipeline execution status to artifact storage for audit trail."""
        try:
            # Create status document
            status_doc = {
                "pipeline_run_timestamp": datetime.utcnow().isoformat() + "Z",
                "action": self.config.document_action.value,
                "summary": status.get_summary(),
                "results": [
                    {
                        "filename": r.filename,
                        "success": r.success,
                        "chunks_indexed": r.chunks_indexed,
                        "error_message": r.error_message,
                        "processing_time_seconds": r.processing_time_seconds
                    }
                    for r in status.results
                ]
            }

            # Save to artifact storage as a status JSON file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            await self.artifact_storage.write_status_json(
                f"pipeline_status_{timestamp}",
                status_doc
            )

            logger.info(f"Pipeline status saved to artifact storage: pipeline_status_{timestamp}.json")

        except Exception as e:
            # Don't fail the pipeline if status save fails
            logger.warning(f"Failed to save pipeline status to artifact storage: {e}")

    async def remove_documents(self, clean_artifacts: bool = False):
        """Remove specific documents from the search index.

        Uses input source to list filenames to remove.

        Args:
            clean_artifacts: If True, also delete blob artifacts for the documents
        """
        logger.info("Starting document removal")

        total_removed = 0
        total_artifacts_deleted = 0
        files_found = 0

        async for filename, _, _ in self.input_source.list_files():
            files_found += 1
            logger.info(f"Removing document: {filename}")
            try:
                # Delete chunks and artifacts in parallel
                delete_tasks = []
                # Use pluggable vector store if available, otherwise use legacy search_uploader
                if self.vector_store:
                    delete_tasks.append(self.vector_store.delete_documents_by_filename(filename))
                elif self.search_uploader:
                    delete_tasks.append(self.search_uploader.delete_documents_by_filename(filename))

                if clean_artifacts and isinstance(self.artifact_storage, BlobArtifactStorage):
                    delete_tasks.append(self.artifact_storage.delete_document_artifacts(filename))

                # Execute deletions in parallel
                results = await asyncio.gather(*delete_tasks, return_exceptions=True)

                # Process results
                count = 0
                deleted = 0

                if len(results) > 0:
                    if isinstance(results[0], Exception):
                        logger.error(f"Failed to delete chunks: {results[0]}")
                    else:
                        count = results[0]
                        total_removed += count
                        logger.info(f"Removed {count} chunks for {filename}")

                if len(results) > 1:
                    if isinstance(results[1], Exception):
                        logger.error(f"Failed to delete artifacts: {results[1]}")
                    else:
                        deleted = results[1]
                        total_artifacts_deleted += deleted
                        logger.info(f"Deleted {deleted} artifact blobs")

            except Exception as e:
                logger.error(f"Error removing {filename}: {e}", exc_info=True)

        # Validate that we found files to remove
        if files_found == 0:
            logger.error("No files found in input source to remove. Check your configuration:")
            if self.config.input.mode.value == "local":
                logger.error(f"  - AZURE_INPUT_MODE=local")
                logger.error(f"  - AZURE_LOCAL_GLOB={self.config.input.local_glob}")
            else:
                logger.error(f"  - AZURE_INPUT_MODE=blob")
                logger.error(f"  - AZURE_BLOB_CONTAINER_IN={self.config.input.blob_container_in}")
                logger.error(f"  - AZURE_BLOB_PREFIX={self.config.input.blob_prefix or '(none)'}")
            raise ValueError("No files found to remove")

        logger.info(f"Total removed: {total_removed} documents")
        if clean_artifacts:
            logger.info(f"Total artifacts deleted: {total_artifacts_deleted} blobs")
    
    async def remove_all_documents(self):
        """Remove ALL documents from the search index.
        
        WARNING: This will delete ALL documents in the index!
        """
        logger.warning("Removing ALL documents from search index")
        # Use pluggable vector store if available, otherwise use legacy search_uploader
        if self.vector_store:
            count = await self.vector_store.delete_all_documents()
        elif self.search_uploader:
            count = await self.search_uploader.delete_all_documents()
        else:
            raise RuntimeError("No vector store configured!")
        logger.info(f"Removed {count} documents from index")
    
    async def _extract_text_file(
        self,
        filename: str,
        file_bytes: bytes,
        source_url: str
    ) -> list[ExtractedPage]:
        """Extract content from text-based files (TXT, MD, HTML, JSON, CSV).
        
        Creates simple page structures from text content.
        """
        file_ext = Path(filename).suffix.lower()
        logger.info(f"Extracting text content from {file_ext} file: {filename}")
        
        try:
            # Decode text content
            text_content = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_content = file_bytes.decode('latin-1')
            except Exception as e:
                logger.error(f"Failed to decode {filename}: {e}")
                return []
        
        # Handle different file types
        if file_ext == '.json':
            # For JSON, pretty-print for better chunking
            try:
                import json
                data = json.loads(text_content)
                text_content = json.dumps(data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {filename}: {e}, using raw content")
        
        elif file_ext == '.csv':
            # For CSV, convert to readable format
            try:
                import csv
                import io
                reader = csv.reader(io.StringIO(text_content))
                rows = list(reader)
                if rows:
                    # Convert to markdown-like table
                    lines = []
                    for i, row in enumerate(rows):
                        lines.append(" | ".join(row))
                        if i == 0:
                            # Add header separator
                            lines.append(" | ".join(["---"] * len(row)))
                    text_content = "\n".join(lines)
            except Exception as e:
                logger.warning(f"Failed to parse CSV {filename}: {e}, using raw content")
        
        elif file_ext in ['.html', '.htm']:
            # For HTML, optionally strip tags (simple approach)
            try:
                import re
                # Remove script and style content
                text_content = re.sub(r'<script[^>]*>.*?</script>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
                text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
                # Remove HTML tags but keep content
                text_content = re.sub(r'<[^>]+>', ' ', text_content)
                # Clean up whitespace
                text_content = re.sub(r'\s+', ' ', text_content).strip()
            except Exception as e:
                logger.warning(f"Failed to clean HTML {filename}: {e}, using raw content")
        
        # For very long files, split into multiple pages
        MAX_CHARS_PER_PAGE = 10000  # ~2500 tokens per page
        pages = []
        
        if len(text_content) <= MAX_CHARS_PER_PAGE:
            # Single page
            pages.append(ExtractedPage(
                page_num=0,
                text=text_content,
                tables=[],
                images=[]
            ))
        else:
            # Split into multiple pages at natural boundaries
            chunks = self._split_text_into_pages(text_content, MAX_CHARS_PER_PAGE)
            for i, chunk in enumerate(chunks):
                pages.append(ExtractedPage(
                    page_num=i,
                    text=chunk,
                    tables=[],
                    images=[]
                ))
        
        logger.info(f"Created {len(pages)} pages from {filename}")
        return pages
    
    def _split_text_into_pages(self, text: str, max_chars: int) -> list[str]:
        """Split text into page-sized chunks at paragraph boundaries."""
        # Split by paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        
        pages = []
        current_page = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para) + 2  # +2 for \n\n
            
            if current_length + para_length > max_chars and current_page:
                # Flush current page
                pages.append('\n\n'.join(current_page))
                current_page = []
                current_length = 0
            
            current_page.append(para)
            current_length += para_length
        
        # Don't forget last page
        if current_page:
            pages.append('\n\n'.join(current_page))
        
        return pages
    
    async def upload_full_document(self, filename: str, doc_bytes: bytes, source_url: str):
        """Ensure full original document is in blob storage and track its URL.

        Args:
            filename: Document filename
            doc_bytes: Complete document file bytes
            source_url: Original source URL

        Behavior:
        - If input is already from blob: Use that blob URL directly
        - If input is local: Upload to blob and use the uploaded URL
        - Always ensures storage_url is a blob URL for use in search index
        """
        # Check if source is already a blob URL
        if source_url.startswith('http://') or source_url.startswith('https://'):
            # Input is already from blob storage - use that URL
            self.full_document_urls[filename] = source_url
            logger.info(f"Using existing blob URL for {filename}: {source_url}")
        else:
            # Input is local - either upload or construct blob URL
            if isinstance(self.artifact_storage, BlobArtifactStorage):
                # Blob storage configured - actually upload the file
                logger.info(f"Uploading full document {filename} to blob storage")
                try:
                    full_doc_url = await self.artifact_storage.write_full_document(filename, doc_bytes)
                    self.full_document_urls[filename] = full_doc_url
                    logger.info(f"✓ Uploaded full document: {full_doc_url}")
                except Exception as e:
                    logger.error(f"Failed to upload full document {filename}: {e}")
                    raise RuntimeError(f"Failed to upload document to blob storage: {e}") from e
            else:
                # No blob storage - try to construct URL from environment config
                logger.info(f"Constructing blob URL for {filename} from environment config (not uploading)")
                constructed_url = self._construct_blob_url_from_config(filename)
                if constructed_url:
                    self.full_document_urls[filename] = constructed_url
                    logger.info(f"✓ Constructed blob URL: {constructed_url}")
                else:
                    # No blob storage config - use local file URL for offline mode
                    # This allows ChromaDB and other vector stores to work without Azure blob storage
                    logger.warning(
                        f"⚠️  No blob storage configured for {filename}. "
                        f"Using local file URL (offline mode). "
                        f"Note: Azure AI Search requires blob URLs, but other vector stores like ChromaDB can work with file:// URLs."
                    )
                    # Use the source_url (which is already a file path) or construct a file:// URL
                    if source_url.startswith('file://'):
                        self.full_document_urls[filename] = source_url
                    else:
                        # Convert to file:// URL
                        import pathlib
                        abs_path = pathlib.Path(source_url).resolve()
                        file_url = abs_path.as_uri()
                        self.full_document_urls[filename] = file_url
                    logger.info(f"✓ Using local file URL: {self.full_document_urls[filename]}")

    async def _upload_page_pdf(
        self,
        filename: str,
        page_num: int,
        pdf_bytes: bytes
    ) -> tuple[int, str]:
        """Upload a single page PDF to blob storage.

        Args:
            filename: Document filename
            page_num: Page number (0-indexed)
            pdf_bytes: PDF bytes for the single page

        Returns:
            Tuple of (page_num, url) for caching
        """
        url = await self.artifact_storage.write_page_pdf(filename, page_num, pdf_bytes)
        logger.debug(f"Uploaded page PDF {page_num + 1}: {url}")
        return page_num, url

    async def split_and_store_page_pdfs(self, filename: str, pdf_bytes: bytes):
        """Split PDF into per-page PDFs and store in blob storage for citations.

        Args:
            filename: PDF filename
            pdf_bytes: Complete PDF file bytes

        Behavior:
        - If blob storage configured: Upload per-page PDFs and get real URLs
        - If no blob storage: Construct URLs from environment config (no upload)
        - Always ensures citation URLs are blob URLs for the search index
        """
        logger.info(f"Processing per-page PDFs for {filename}")

        try:
            # Split PDF
            page_pdfs = self.page_splitter.split_pdf(pdf_bytes, filename)

            if isinstance(self.artifact_storage, BlobArtifactStorage):
                # Blob storage configured - actually upload page PDFs in parallel
                logger.info(f"Uploading {len(page_pdfs)} per-page PDFs to blob storage for citations (parallel)")

                # Collect all upload tasks
                upload_tasks = [
                    self._upload_page_pdf(filename, page_num, pdf_bytes)
                    for page_num, pdf_bytes, _ in page_pdfs
                ]

                # Execute all uploads in parallel
                results = await asyncio.gather(*upload_tasks, return_exceptions=True)

                # Cache results and handle errors
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Failed to upload page PDF: {result}")
                    else:
                        page_num, url = result
                        # Cache URL for later use in chunking (these are blob URLs)
                        self.page_pdf_urls[(filename, page_num)] = url

                logger.info(f"✓ Successfully uploaded {len(page_pdfs)} page PDFs to blob storage")
            else:
                # No blob storage - construct URLs from environment config
                logger.info(f"Constructing {len(page_pdfs)} citation URLs from environment config (not uploading)")
                for page_num, page_pdf_bytes, page_filename in page_pdfs:
                    page_pdf_url = self._construct_page_pdf_url_from_config(filename, page_num)
                    if page_pdf_url:
                        # Cache URL for later use in chunking
                        self.page_pdf_urls[(filename, page_num)] = page_pdf_url
                        logger.debug(f"Constructed page PDF URL {page_num + 1}: {page_pdf_url}")
                    else:
                        logger.warning(f"Could not construct URL for page {page_num + 1} of {filename}")

                logger.info(f"✓ Successfully constructed {len(page_pdfs)} citation URLs from config")

        except Exception as e:
            logger.error(f"Failed to process per-page PDFs for {filename}: {e}")
            raise RuntimeError(f"Failed to process per-page PDFs: {e}") from e
    
    async def extract_pdf_offline(
        self,
        filename: str,
        pdf_bytes: bytes
    ) -> list[ExtractedPage]:
        """Extract pages from PDF using MarkItDown (offline, no Azure DI).

        Used when mode=markitdown or when hybrid mode falls back.
        This is a basic text extraction without table/figure detection.
        Uses MarkItDown library consistently with Office document extraction.
        """
        logger.info(f"Extracting PDF offline using MarkItDown: {filename}")

        from markitdown import MarkItDown

        # Write bytes to temporary file for MarkItDown
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name

        try:
            # Convert PDF to markdown using MarkItDown
            md = MarkItDown(enable_plugins=True)
            result = md.convert(tmp_path)

            # Split by form feed characters (\f) which mark page breaks
            page_texts = result.text_content.split('\f')

            # Remove empty pages
            page_texts = [p.strip() for p in page_texts if p.strip()]

            # Create ExtractedPage objects
            pages = []
            for page_num, text in enumerate(page_texts):
                extracted_page = ExtractedPage(
                    page_num=page_num,
                    text=text,
                    tables=[],  # No table extraction in offline mode
                    images=[],  # No image extraction in offline mode
                    offset=sum(len(p.text) for p in pages)
                )
                pages.append(extracted_page)

            logger.info(f"MarkItDown extracted {len(pages)} pages from {filename} (offline mode - no tables/figures)")
            return pages

        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(tmp_path)
            except:
                pass

    async def extract_document(
        self,
        filename: str,
        pdf_bytes: bytes,
        source_url: str
    ) -> list[ExtractedPage]:
        """Extract pages, tables, and figures from a PDF using Azure DI."""
        logger.info(f"Extracting content from {filename}")
        
        # Extract with DI
        pages = await self.di_extractor.extract_document(
            pdf_bytes,
            filename,
            process_figures=True
        )
        
        # Log DI response (if available)
        if hasattr(self.di_extractor, 'last_result') and self.di_extractor.last_result:
            log_di_response(self.log_dir, filename, self.di_extractor.last_result,
                          write_artifacts=self.write_artifacts)

        # Log DI extraction summary
        log_di_summary(self.log_dir, filename, pages, write_artifacts=self.write_artifacts)
        
        # Process images (describe + upload) in parallel
        image_tasks = []
        for page in pages:
            for idx, image in enumerate(page.images):
                image_tasks.append(self._process_image(page.page_num, idx, image, filename))

        if image_tasks:
            logger.info(f"Processing {len(image_tasks)} images in parallel (max concurrency: {self.config.performance.max_image_concurrency})")

            # Create semaphore to limit concurrent image operations
            max_image_concurrency = self.config.performance.max_image_concurrency
            image_semaphore = asyncio.Semaphore(max_image_concurrency)

            async def process_with_semaphore(task):
                async with image_semaphore:
                    return await task

            # Process all images in parallel with controlled concurrency
            processed_images = await asyncio.gather(*[
                process_with_semaphore(task) for task in image_tasks
            ], return_exceptions=True)

            # Handle exceptions and log errors
            for i, result in enumerate(processed_images):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process image {i}: {result}")
        
        # Process and log tables
        for page in pages:
            for idx, table in enumerate(page.tables):
                # Render table text
                rendered_text = self.table_renderer.render(table)

                # Log table processing
                log_table_processing(
                    self.log_dir, filename, page.page_num, idx, table, rendered_text,
                    write_artifacts=self.write_artifacts
                )

        # Write page artifacts in parallel
        json_write_tasks = [
            self.artifact_storage.write_page_json(
                filename,
                page.page_num,
                {
                    "page_num": page.page_num,
                    "text": page.text,
                    "tables": [
                        {
                            "table_id": t.table_id,
                            "page_nums": t.page_nums,
                            "row_count": t.row_count,
                            "column_count": t.column_count,
                            "cells": t.cells
                        }
                        for t in page.tables
                    ],
                    "images": [
                        {
                            "figure_id": img.figure_id,
                            "page_num": img.page_num,
                            "filename": img.filename,
                            "url": img.url,
                            "description": img.description
                        }
                        for img in page.images
                    ]
                }
            )
            for page in pages
        ]

        # Execute all writes in parallel
        await asyncio.gather(*json_write_tasks, return_exceptions=True)
        
        # Write manifest
        manifest = {
            "filename": filename,
            "source_url": source_url,
            "page_count": len(pages),
            "extracted_at": datetime.utcnow().isoformat() + "Z"
        }
        await self.artifact_storage.write_manifest(filename, manifest)
        
        logger.info(f"Extracted {len(pages)} pages from {filename}")
        return pages

    async def extract_office_document(
        self,
        filename: str,
        file_bytes: bytes,
        source_url: str
    ) -> list[ExtractedPage]:
        """Extract pages/slides, tables, and figures from Office document (DOCX/PPTX).

        Similar to extract_document but adapted for Office documents:
        - No per-page PDFs (handled separately at routing level)
        - PPTX: pages represent slides
        - DOCX: pages may be sections or natural document divisions
        """
        logger.info(f"Extracting content from Office document {filename}")

        # Extract with Office extractor
        pages = await self.office_extractor.extract_office_document(
            file_bytes,
            filename
        )

        # Log extraction summary
        file_ext = Path(filename).suffix.lower()
        page_type = "slides" if file_ext == '.pptx' else "pages"
        logger.info(f"Extracted {len(pages)} {page_type} from {filename}")

        # Process images (describe + upload)
        for page in pages:
            for idx, image in enumerate(page.images):
                # Describe image
                if self.media_describer:
                    logger.info(
                        f"Generating description for figure {image.figure_id} "
                        f"on {page_type[:-1]} {page.page_num + 1}"
                    )
                    image.description = await self.media_describer.describe_image(image.image_bytes)

                    # Log figure processing
                    log_figure_processing(
                        self.log_dir, filename, page.page_num, idx, image, image.description,
                        write_artifacts=self.write_artifacts
                    )

                # Upload image or construct URL from config
                if isinstance(self.artifact_storage, BlobArtifactStorage):
                    # Actually upload to blob storage
                    image.url = await self.artifact_storage.write_image(
                        filename,
                        image.page_num,
                        image.filename,
                        image.image_bytes,
                        figure_idx=idx
                    )
                else:
                    # Construct URL from config without uploading
                    image.url = self._construct_image_url_from_config(filename, image.page_num, idx)
                    if not image.url:
                        logger.warning(f"Could not construct image URL for {filename} page {image.page_num} figure {idx}")

        # Process and log tables
        for page in pages:
            for idx, table in enumerate(page.tables):
                # Render table text
                rendered_text = self.table_renderer.render(table)

                # Log table processing
                log_table_processing(
                    self.log_dir, filename, page.page_num, idx, table, rendered_text,
                    write_artifacts=self.write_artifacts
                )

        # Write page artifacts in parallel
        json_write_tasks = [
            self.artifact_storage.write_page_json(
                filename,
                page.page_num,
                {
                    "page_num": page.page_num,
                    "text": page.text,
                    "tables": [
                        {
                            "table_id": t.table_id,
                            "page_nums": t.page_nums,
                            "row_count": t.row_count,
                            "column_count": t.column_count,
                            "cells": t.cells
                        }
                        for t in page.tables
                    ],
                    "images": [
                        {
                            "figure_id": img.figure_id,
                            "page_num": img.page_num,
                            "filename": img.filename,
                            "url": img.url,
                            "description": img.description
                        }
                        for img in page.images
                    ]
                }
            )
            for page in pages
        ]

        # Execute all writes in parallel
        await asyncio.gather(*json_write_tasks, return_exceptions=True)

        # Write manifest
        manifest = {
            "filename": filename,
            "source_url": source_url,
            "page_count": len(pages),
            "document_type": file_ext[1:],  # "docx" or "pptx"
            "extracted_at": datetime.utcnow().isoformat() + "Z"
        }
        await self.artifact_storage.write_manifest(filename, manifest)

        logger.info(f"Extracted {len(pages)} {page_type} from {filename}")
        return pages

    async def chunk_document(
        self,
        filename: str,
        pages: list[ExtractedPage],
        source_url: str
    ) -> list[ChunkDocument]:
        """Chunk pages into searchable chunks."""
        logger.info(f"Chunking {filename}")
        
        # Chunk pages
        text_chunks: list[TextChunk] = self.chunker.chunk_pages(pages)
        
        # Log chunking process
        log_chunking_process(self.log_dir, filename, text_chunks, write_artifacts=self.write_artifacts)
        
        # Create chunk documents with metadata
        chunk_docs = []
        
        for text_chunk in text_chunks:
            # Generate chunk ID
            chunk_id = f"{Path(filename).stem}_page{text_chunk.page_num + 1}_chunk{text_chunk.chunk_index_on_page + 1}"
            chunk_id = chunk_id.replace(" ", "_").replace(".", "_")
            
            # Create sourcefile identifier (document name WITH extension)
            # This is used as an identifier for grouping chunks from same document
            doc_name = Path(filename).name  # Include file extension
            # Truncate long filenames but keep them readable
            if len(doc_name) > 40:
                doc_name = doc_name[:37] + "..."
            sourcefile_identifier = doc_name  # Document name with extension: "sample_pages_test.pdf"
            
            # Determine storage_url: ALWAYS use blob URL (never file:// URI)
            # storage_url must always be a blob URL for the search index
            storage_url = self.full_document_urls.get(filename)
            if not storage_url:
                # This shouldn't happen if upload_full_document succeeded
                logger.error(f"❌ Full document blob URL not found for {filename}")
                logger.error("This indicates upload_full_document was not called or failed")
                raise ValueError(
                    f"storage_url requires blob URL but none found for {filename}. "
                    "Ensure blob storage is configured and upload_full_document succeeded."
                )
            
            # Create document metadata
            doc_meta = DocumentMetadata(
                sourcefile=sourcefile_identifier,  # Document identifier: "sample_pages_test"
                storage_url=storage_url,           # Original full PDF URL (blob URL if artifacts=BLOB, file URI if LOCAL)
                md5_hash=hashlib.md5(filename.encode()).hexdigest()
            )
            
            # Get citation URL if page PDF was generated
            citation_url = self.page_pdf_urls.get((filename, text_chunk.page_num))

            # Check if this is a presentation (PPTX)
            file_ext = Path(filename).suffix.lower()
            is_presentation = file_ext == '.pptx'

            # Create page metadata with citation URL
            # sourcepage format:
            # - PPTX: "presentation.pptx#slide=3" (whole presentation as unit)
            # - PDF with blob: "docname/page-0001.pdf#page=1"
            # - Other: "filename.ext#page=1"
            page_meta = PageMetadata.create(
                page_num_0indexed=text_chunk.page_num,
                sourcefile=filename,
                page_blob_url=citation_url,  # Pass URL for sourcepage path construction
                is_presentation=is_presentation
            )
            
            # Create chunk metadata
            # page_header is extracted from <!-- PageHeader="..." --> and cleaned
            # (page number prefix removed) for use as keyword search title
            chunk_meta = ChunkMetadata(
                chunk_id=chunk_id,
                chunk_index_on_page=text_chunk.chunk_index_on_page,
                text=text_chunk.text,
                token_count=text_chunk.token_count,
                title=text_chunk.page_header  # Cleaned header for keyword search
            )
            
            # Create chunk artifact (URL will be set when written)
            chunk_artifact = ChunkArtifact()
            
            # Convert tables/figures to references
            table_refs = [
                TableReference(
                    table_id=t.table_id,
                    pages=t.page_nums,
                    rendered_text=t.rendered_text,
                    summary=t.summary,
                    bbox=t.bbox
                )
                for t in text_chunk.tables
            ]
            
            figure_refs = [
                FigureReference(
                    figure_id=img.figure_id,
                    page_num=img.page_num,
                    bbox=img.bbox,
                    url=img.url or "",
                    description=img.description,
                    filename=img.filename,
                    title=img.title
                )
                for img in text_chunk.images
            ]
            
            # Create chunk document
            chunk_doc = ChunkDocument(
                document=doc_meta,
                page=page_meta,
                chunk=chunk_meta,
                chunk_artifact=chunk_artifact,
                tables=table_refs,
                figures=figure_refs
            )
            
            # Write chunk artifact ONLY for local storage (for testing/debugging)
            # Skip chunk JSON writing for blob storage - chunks go to Azure AI Search index
            if self.config.artifacts.mode == ArtifactsMode.LOCAL:
                chunk_url = await self.artifact_storage.write_chunk_json(
                    filename,
                    text_chunk.page_num,
                    text_chunk.chunk_index_on_page,
                    chunk_doc.to_dict()
                )
                chunk_doc.chunk_artifact.url = chunk_url
            else:
                # Blob storage mode - skip chunk JSON writing (reduces cost and time)
                chunk_doc.chunk_artifact.url = None

            chunk_docs.append(chunk_doc)

        if self.config.artifacts.mode == ArtifactsMode.LOCAL:
            logger.info(f"Created {len(chunk_docs)} chunks from {filename} (chunk JSON artifacts written to local storage)")
        else:
            logger.info(f"Created {len(chunk_docs)} chunks from {filename} (chunk JSON artifacts skipped for blob storage)")
        return chunk_docs
    
    async def embed_chunks(self, chunk_docs: list[ChunkDocument]):
        """Generate embeddings for chunks using client-side embedding generation.

        This method is only called when NOT using integrated vectorization.
        Embeddings are generated using the configured embeddings provider (Azure OpenAI, Hugging Face, etc.).
        """
        logger.info(f"Generating client-side embeddings for {len(chunk_docs)} chunks")

        # Use new pluggable architecture
        if self.embeddings_provider:
            logger.info(f"  Provider: {self.embeddings_provider.get_model_name()}")
            logger.info(f"  Dimensions: {self.embeddings_provider.get_dimensions()}")

            # Extract texts
            texts = [doc.chunk.text for doc in chunk_docs]

            # Generate embeddings in batches
            embeddings = await self.embeddings_provider.generate_embeddings_batch(texts)

            # Assign embeddings to chunks
            for chunk_doc, embedding in zip(chunk_docs, embeddings):
                chunk_doc.chunk.embedding = embedding

            # Verify embeddings were generated
            if embeddings and len(embeddings) > 0:
                embedding_dim = len(embeddings[0])
                logger.info(f"Successfully generated {len(embeddings)} embeddings (dimension: {embedding_dim})")
            else:
                logger.warning("No embeddings were generated!")

        # Fallback to legacy embeddings_gen (should not happen with new initialization)
        elif self.embeddings_gen:
            logger.info(f"  Model: {self.embeddings_gen.model_name}")
            logger.info(f"  Deployment: {self.embeddings_gen.deployment}")
            if self.embeddings_gen.dimensions:
                logger.info(f"  Dimensions: {self.embeddings_gen.dimensions}")

            # Extract texts
            texts = [doc.chunk.text for doc in chunk_docs]

            # Generate embeddings in batches
            embeddings = await self.embeddings_gen.generate_embeddings_batch(texts)

            # Assign embeddings to chunks
            for chunk_doc, embedding in zip(chunk_docs, embeddings):
                chunk_doc.chunk.embedding = embedding

            # Verify embeddings were generated
            if embeddings and len(embeddings) > 0:
                embedding_dim = len(embeddings[0])
                logger.info(f"Successfully generated {len(embeddings)} embeddings (dimension: {embedding_dim})")
            else:
                logger.warning("No embeddings were generated!")
        else:
            raise RuntimeError("No embeddings provider configured!")
    
    async def index_chunks(self, chunk_docs: list[ChunkDocument]) -> int:
        """Upload chunks to vector store.

        Returns:
            Number of chunks successfully indexed.
        """
        logger.info(f"Indexing {len(chunk_docs)} chunks to vector store")

        # Pass include_embeddings based on configuration
        include_embeddings = not self.config.use_integrated_vectorization

        # Use new pluggable architecture
        if self.vector_store:
            count = await self.vector_store.upload_documents(chunk_docs, include_embeddings=include_embeddings)
        # Fallback to legacy search_uploader (should not happen with new initialization)
        elif self.search_uploader:
            count = await self.search_uploader.upload_documents(chunk_docs, include_embeddings=include_embeddings)
        else:
            raise RuntimeError("No vector store configured!")

        logger.info(f"Indexed {count} chunks")
        return count
    
    async def close(self):
        """Close all async resources."""
        # Close new pluggable components
        if self.embeddings_provider:
            await self.embeddings_provider.close()
        if self.vector_store:
            await self.vector_store.close()

        # Close legacy components (for backward compatibility)
        if self.embeddings_gen:
            await self.embeddings_gen.close()
        if self.search_uploader:
            await self.search_uploader.close()
        if self.media_describer and hasattr(self.media_describer, 'close'):
            await self.media_describer.close()
        if self.artifact_storage and hasattr(self.artifact_storage, 'close'):
            await self.artifact_storage.close()
        if self.di_extractor and hasattr(self.di_extractor, 'close'):
            await self.di_extractor.close()

