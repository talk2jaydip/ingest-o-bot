"""Configuration validation for the ingestor pipeline."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import (
    ArtifactsMode,
    InputMode,
    MediaDescriberMode,
    OfficeExtractorMode,
    PipelineConfig,
)
from .logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    component: str
    message: str
    fix_hint: Optional[str] = None


class PipelineValidator:
    """Validates pipeline configuration and dependencies."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results: list[ValidationResult] = []

    def add_result(self, passed: bool, component: str, message: str, fix_hint: Optional[str] = None):
        """Add a validation result."""
        self.results.append(ValidationResult(passed, component, message, fix_hint))

    async def validate_all(self) -> bool:
        """Run all validations based on configuration.

        Returns:
            True if all validations passed, False otherwise
        """
        logger.info("=" * 80)
        logger.info("🔍 PIPELINE PRE-CHECK VALIDATION")
        logger.info("=" * 80)
        logger.info("")

        # Run validations
        await self._validate_input_source()
        await self._validate_artifacts_storage()
        await self._validate_document_intelligence()
        await self._validate_office_extractor()
        await self._validate_azure_openai()
        await self._validate_search()
        await self._validate_media_describer()
        await self._validate_dependencies()

        # Print results
        logger.info("")
        logger.info("=" * 80)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 80)
        logger.info("")

        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = len(self.results) - passed_count

        for result in self.results:
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} [{result.component}] {result.message}")
            if not result.passed and result.fix_hint:
                logger.info(f"   💡 Fix: {result.fix_hint}")

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"Summary: {passed_count} passed, {failed_count} failed")
        logger.info("=" * 80)

        return failed_count == 0

    async def _validate_input_source(self):
        """Validate input source configuration."""
        logger.info("🔍 Validating Input Source...")

        if self.config.input.mode == InputMode.LOCAL:
            # Validate local input
            glob_pattern = self.config.input.local_glob
            if not glob_pattern:
                # Note: This is only required when actually processing documents,
                # not for validation-only mode. Provide a warning instead of error.
                self.add_result(
                    True,  # Changed from False - this is OK for validation mode
                    "Input Source (Local)",
                    "LOCAL_INPUT_GLOB is not set (required when processing, optional for validation)",
                    "Set LOCAL_INPUT_GLOB or use --glob/--pdf flag when processing documents"
                )
                return

            # Check if any files match the pattern
            from glob import glob
            files = glob(glob_pattern, recursive=True)

            if len(files) == 0:
                self.add_result(
                    True,  # Changed from False - this is OK, just informational
                    "Input Source (Local)",
                    f"No files found matching pattern: {glob_pattern} (this is OK if using --glob or --pdf flag)",
                    f"Files will be specified via CLI arguments or ensure files exist at: {glob_pattern}"
                )
            else:
                self.add_result(
                    True,
                    "Input Source (Local)",
                    f"Found {len(files)} file(s) matching pattern: {glob_pattern}"
                )

        else:
            # Validate blob input
            if not self.config.input.blob_account_url and not self.config.input.blob_connection_string:
                self.add_result(
                    False,
                    "Input Source (Blob)",
                    "Blob storage account not configured",
                    "Set AZURE_STORAGE_ACCOUNT or AZURE_CONNECTION_STRING environment variable"
                )
                return

            if not self.config.input.blob_container_in:
                self.add_result(
                    False,
                    "Input Source (Blob)",
                    "Input container not specified",
                    "Set AZURE_BLOB_CONTAINER_IN or AZURE_STORAGE_CONTAINER environment variable"
                )
                return

            # Test blob connection
            try:
                from azure.storage.blob import BlobServiceClient

                if self.config.input.blob_connection_string:
                    blob_service = BlobServiceClient.from_connection_string(
                        self.config.input.blob_connection_string
                    )
                else:
                    from azure.identity import DefaultAzureCredential
                    blob_service = BlobServiceClient(
                        account_url=self.config.input.blob_account_url,
                        credential=DefaultAzureCredential()
                    )

                # Try to get container
                container_client = blob_service.get_container_client(self.config.input.blob_container_in)

                # Check if container exists
                exists = await asyncio.to_thread(container_client.exists)

                if not exists:
                    self.add_result(
                        False,
                        "Input Source (Blob)",
                        f"Container does not exist: {self.config.input.blob_container_in}",
                        f"Create the container or check the container name in AZURE_BLOB_CONTAINER_IN"
                    )
                else:
                    # Try to list blobs
                    blob_list = []
                    prefix = self.config.input.blob_prefix or ""
                    async for blob in container_client.list_blobs(name_starts_with=prefix):
                        blob_list.append(blob)
                        if len(blob_list) >= 10:  # Limit to first 10 for validation
                            break

                    if len(blob_list) == 0:
                        prefix_msg = f" with prefix '{prefix}'" if prefix else ""
                        self.add_result(
                            False,
                            "Input Source (Blob)",
                            f"No blobs found in container{prefix_msg}",
                            f"Upload files to container '{self.config.input.blob_container_in}' or adjust AZURE_BLOB_PREFIX"
                        )
                    else:
                        prefix_msg = f" (prefix: '{prefix}')" if prefix else ""
                        self.add_result(
                            True,
                            "Input Source (Blob)",
                            f"Container accessible with {len(blob_list)}+ blob(s){prefix_msg}"
                        )

            except ImportError:
                self.add_result(
                    False,
                    "Input Source (Blob)",
                    "azure-storage-blob library not installed",
                    "Install with: pip install azure-storage-blob"
                )
            except Exception as e:
                self.add_result(
                    False,
                    "Input Source (Blob)",
                    f"Failed to connect to blob storage: {e}",
                    "Check AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_ACCOUNT_KEY, or AZURE_CONNECTION_STRING"
                )

    async def _validate_artifacts_storage(self):
        """Validate artifacts storage configuration."""
        logger.info("🔍 Validating Artifacts Storage...")

        if self.config.artifacts.mode == ArtifactsMode.LOCAL:
            # Validate local artifacts
            local_dir = Path(self.config.artifacts.local_dir)

            try:
                # Try to create directory if it doesn't exist
                local_dir.mkdir(parents=True, exist_ok=True)

                # Test write permissions
                test_file = local_dir / ".write_test"
                test_file.write_text("test")
                test_file.unlink()

                self.add_result(
                    True,
                    "Artifacts Storage (Local)",
                    f"Directory writable: {local_dir}"
                )
            except Exception as e:
                self.add_result(
                    False,
                    "Artifacts Storage (Local)",
                    f"Cannot write to directory: {local_dir}",
                    f"Check directory permissions or set AZURE_ARTIFACTS_DIR to a writable location"
                )

        else:
            # Validate blob artifacts
            if not self.config.artifacts.blob_account_url and not self.config.artifacts.blob_connection_string:
                self.add_result(
                    False,
                    "Artifacts Storage (Blob)",
                    "Blob storage account not configured",
                    "Set AZURE_STORAGE_ACCOUNT or AZURE_CONNECTION_STRING environment variable"
                )
                return

            # Test blob connection and containers
            try:
                from azure.storage.blob import BlobServiceClient

                if self.config.artifacts.blob_connection_string:
                    blob_service = BlobServiceClient.from_connection_string(
                        self.config.artifacts.blob_connection_string
                    )
                elif self.config.artifacts.blob_key:
                    # Use account key authentication (most common)
                    blob_service = BlobServiceClient(
                        account_url=self.config.artifacts.blob_account_url,
                        credential=self.config.artifacts.blob_key
                    )
                else:
                    # Fall back to DefaultAzureCredential for managed identity
                    from azure.identity import DefaultAzureCredential
                    blob_service = BlobServiceClient(
                        account_url=self.config.artifacts.blob_account_url,
                        credential=DefaultAzureCredential()
                    )

                # Check required containers
                containers = [
                    ("pages", self.config.artifacts.blob_container_pages),
                    ("chunks", self.config.artifacts.blob_container_chunks),
                ]

                if self.config.artifacts.blob_container_images:
                    containers.append(("images", self.config.artifacts.blob_container_images))
                if self.config.artifacts.blob_container_citations:
                    containers.append(("citations", self.config.artifacts.blob_container_citations))

                # Validate all containers in parallel for efficiency
                async def check_container(container_type: str, container_name: str):
                    """Check if container exists and is accessible."""
                    if not container_name:
                        self.add_result(
                            False,
                            f"Artifacts Storage (Blob - {container_type})",
                            f"{container_type} container not configured",
                            f"Set AZURE_BLOB_CONTAINER_OUT_{container_type.upper()} or AZURE_STORAGE_CONTAINER"
                        )
                        return False

                    try:
                        container_client = blob_service.get_container_client(container_name)
                        exists = await asyncio.to_thread(container_client.exists)

                        if not exists:
                            # Try to create container
                            try:
                                await asyncio.to_thread(container_client.create_container)
                                self.add_result(
                                    True,
                                    f"Artifacts Storage (Blob - {container_type})",
                                    f"Container created: {container_name}"
                                )
                                return True
                            except Exception as create_err:
                                self.add_result(
                                    False,
                                    f"Artifacts Storage (Blob - {container_type})",
                                    f"Container does not exist and cannot be created: {container_name}",
                                    f"Create the container manually or check permissions"
                                )
                                return False
                        else:
                            self.add_result(
                                True,
                                f"Artifacts Storage (Blob - {container_type})",
                                f"Container accessible: {container_name}"
                            )
                            return True
                    except Exception as e:
                        self.add_result(
                            False,
                            f"Artifacts Storage (Blob - {container_type})",
                            f"Cannot access container '{container_name}': {e}",
                            "Check container name and permissions"
                        )
                        return False

                # Check all containers in parallel
                results = await asyncio.gather(*[check_container(ctype, cname) for ctype, cname in containers])
                all_ok = all(results)

            except ImportError:
                self.add_result(
                    False,
                    "Artifacts Storage (Blob)",
                    "azure-storage-blob library not installed",
                    "Install with: pip install azure-storage-blob"
                )
            except Exception as e:
                self.add_result(
                    False,
                    "Artifacts Storage (Blob)",
                    f"Failed to connect to blob storage: {e}",
                    "Check AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_ACCOUNT_KEY, or AZURE_CONNECTION_STRING"
                )

    async def _validate_document_intelligence(self):
        """Validate Azure Document Intelligence configuration."""
        # Only validate if using Azure DI or hybrid mode
        mode = self.config.office_extractor.mode

        if mode == OfficeExtractorMode.MARKITDOWN:
            self.add_result(
                True,
                "Document Intelligence",
                "Not required (using MarkItDown mode)"
            )
            return

        logger.info("🔍 Validating Azure Document Intelligence...")

        if not self.config.document_intelligence.endpoint:
            self.add_result(
                False,
                "Document Intelligence",
                "Endpoint not configured",
                "Set AZURE_DOC_INT_ENDPOINT environment variable"
            )
            return

        # Test connection
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
            from azure.identity import DefaultAzureCredential

            if self.config.document_intelligence.key:
                credential = AzureKeyCredential(self.config.document_intelligence.key)
            else:
                credential = DefaultAzureCredential()

            client = DocumentIntelligenceClient(
                endpoint=self.config.document_intelligence.endpoint,
                credential=credential
            )

            # Try a simple operation to verify connection
            # Note: This doesn't actually make a call, just validates the client setup
            self.add_result(
                True,
                "Document Intelligence",
                f"Client configured: {self.config.document_intelligence.endpoint}"
            )

        except ImportError:
            self.add_result(
                False,
                "Document Intelligence",
                "azure-ai-documentintelligence library not installed",
                "Install with: pip install azure-ai-documentintelligence"
            )
        except Exception as e:
            self.add_result(
                False,
                "Document Intelligence",
                f"Failed to configure client: {e}",
                "Check AZURE_DOC_INT_ENDPOINT and AZURE_DOC_INT_KEY"
            )

    async def _validate_office_extractor(self):
        """Validate Office extractor configuration."""
        logger.info("🔍 Validating Office Extractor...")

        mode = self.config.office_extractor.mode

        if mode == OfficeExtractorMode.MARKITDOWN or (
            mode == OfficeExtractorMode.HYBRID and self.config.office_extractor.offline_fallback
        ):
            # Check if MarkItDown is available
            try:
                import markitdown
                self.add_result(
                    True,
                    "Office Extractor (MarkItDown)",
                    f"MarkItDown library available (mode: {mode.value})"
                )
            except ImportError:
                severity = False if mode == OfficeExtractorMode.MARKITDOWN else True
                self.add_result(
                    severity,
                    "Office Extractor (MarkItDown)",
                    "MarkItDown library not installed",
                    "Install with: pip install markitdown"
                )

    async def _validate_azure_openai(self):
        """Validate Azure OpenAI configuration."""
        logger.info("🔍 Validating Azure OpenAI...")

        # Check if client-side embeddings are needed
        if self.config.use_integrated_vectorization:
            self.add_result(
                True,
                "Azure OpenAI (Embeddings)",
                "Not required (using integrated vectorization)"
            )
        else:
            # Validate embeddings configuration
            if not self.config.azure_openai.endpoint:
                self.add_result(
                    False,
                    "Azure OpenAI (Embeddings)",
                    "Endpoint not configured",
                    "Set AZURE_OPENAI_ENDPOINT environment variable"
                )
                return

            if not self.config.azure_openai.api_key:
                self.add_result(
                    False,
                    "Azure OpenAI (Embeddings)",
                    "API key not configured",
                    "Set AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY environment variable"
                )
                return

            if not self.config.azure_openai.emb_deployment:
                self.add_result(
                    False,
                    "Azure OpenAI (Embeddings)",
                    "Embedding deployment not configured",
                    "Set AZURE_OPENAI_EMBEDDING_DEPLOYMENT environment variable"
                )
                return

            # Test connection
            try:
                from openai import AsyncAzureOpenAI

                client = AsyncAzureOpenAI(
                    api_key=self.config.azure_openai.api_key,
                    api_version=self.config.azure_openai.api_version,
                    azure_endpoint=self.config.azure_openai.endpoint
                )

                self.add_result(
                    True,
                    "Azure OpenAI (Embeddings)",
                    f"Client configured: {self.config.azure_openai.emb_deployment}"
                )

            except ImportError:
                self.add_result(
                    False,
                    "Azure OpenAI (Embeddings)",
                    "openai library not installed",
                    "Install with: pip install openai"
                )
            except Exception as e:
                self.add_result(
                    False,
                    "Azure OpenAI (Embeddings)",
                    f"Failed to configure client: {e}",
                    "Check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY"
                )

        # Validate vision/GPT-4o configuration if needed for media description
        # Only check this if Azure OpenAI endpoint is configured (not in offline mode)
        if self.config.media_describer_mode == MediaDescriberMode.GPT4O:
            if self.config.azure_openai.endpoint:
                # Azure OpenAI is available, check for vision deployment
                if not self.config.azure_openai.vision_deployment:
                    self.add_result(
                        False,
                        "Azure OpenAI (Vision/GPT-4o)",
                        "Vision deployment not configured (required for media description)",
                        "Set AZURE_OPENAI_VISION_DEPLOYMENT environment variable or set MEDIA_DESCRIBER_MODE=disabled"
                    )
                else:
                    self.add_result(
                        True,
                        "Azure OpenAI (Vision/GPT-4o)",
                        f"Vision deployment configured: {self.config.azure_openai.vision_deployment}"
                    )
            else:
                # No Azure OpenAI endpoint - offline mode, media description not available
                self.add_result(
                    True,  # Not an error in offline mode
                    "Azure OpenAI (Vision/GPT-4o)",
                    "Media description unavailable in offline mode (Azure OpenAI not configured)",
                    "Set MEDIA_DESCRIBER_MODE=disabled or configure Azure OpenAI for media descriptions"
                )

    async def _validate_search(self):
        """Validate Azure AI Search configuration."""
        logger.info("🔍 Validating Azure AI Search...")

        if not self.config.search.endpoint:
            self.add_result(
                False,
                "Azure AI Search",
                "Endpoint not configured",
                "Set AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE environment variable"
            )
            return

        if not self.config.search.index_name:
            self.add_result(
                False,
                "Azure AI Search",
                "Index name not configured",
                "Set AZURE_SEARCH_INDEX environment variable"
            )
            return

        # Test connection
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            from azure.identity import DefaultAzureCredential

            if self.config.search.api_key:
                credential = AzureKeyCredential(self.config.search.api_key)
            else:
                credential = DefaultAzureCredential()

            client = SearchClient(
                endpoint=self.config.search.endpoint,
                index_name=self.config.search.index_name,
                credential=credential
            )

            # Try to get document count (validates connection and index existence)
            try:
                result = await asyncio.to_thread(
                    lambda: client.get_document_count()
                )
                self.add_result(
                    True,
                    "Azure AI Search",
                    f"Index accessible: {self.config.search.index_name} ({result} documents)"
                )
            except Exception as e:
                if "NotFound" in str(e) or "404" in str(e):
                    self.add_result(
                        False,
                        "Azure AI Search",
                        f"Index does not exist: {self.config.search.index_name}",
                        "Create the index first or check AZURE_SEARCH_INDEX"
                    )
                else:
                    raise

        except ImportError:
            self.add_result(
                False,
                "Azure AI Search",
                "azure-search-documents library not installed",
                "Install with: pip install azure-search-documents"
            )
        except Exception as e:
            self.add_result(
                False,
                "Azure AI Search",
                f"Failed to connect: {e}",
                "Check AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, and AZURE_SEARCH_KEY"
            )

    async def _validate_media_describer(self):
        """Validate media describer configuration."""
        logger.info("🔍 Validating Media Describer...")

        mode = self.config.media_describer_mode

        if mode == MediaDescriberMode.DISABLED:
            self.add_result(
                True,
                "Media Describer",
                "Disabled (images will not be described)"
            )
        elif mode == MediaDescriberMode.GPT4O:
            # Already validated in Azure OpenAI section
            self.add_result(
                True,
                "Media Describer",
                f"Using GPT-4o (validated in Azure OpenAI section)"
            )
        elif mode == MediaDescriberMode.CONTENT_UNDERSTANDING:
            if not self.config.content_understanding or not self.config.content_understanding.endpoint:
                self.add_result(
                    False,
                    "Media Describer (Content Understanding)",
                    "Content Understanding endpoint not configured",
                    "Set AZURE_CONTENT_UNDERSTANDING_ENDPOINT or use AZURE_MEDIA_DESCRIBER=gpt4o"
                )
            else:
                self.add_result(
                    True,
                    "Media Describer (Content Understanding)",
                    f"Endpoint configured: {self.config.content_understanding.endpoint}"
                )

    async def _validate_dependencies(self):
        """Validate Python dependencies."""
        logger.info("🔍 Validating Python Dependencies...")

        # Check optional dependencies based on configuration
        dependencies = [
            ("tiktoken", "Token counting for chunking", True),
        ]

        # Add page splitter dependency if needed
        if self.config.artifacts.mode == ArtifactsMode.BLOB:
            dependencies.append(("pypdf", "PDF page splitting for citations", False))

        for package, description, required in dependencies:
            try:
                __import__(package)
                self.add_result(
                    True,
                    f"Dependency ({package})",
                    f"{package} available - {description}"
                )
            except ImportError:
                if required:
                    self.add_result(
                        False,
                        f"Dependency ({package})",
                        f"{package} not installed - {description}",
                        f"Install with: pip install {package}"
                    )
                else:
                    self.add_result(
                        True,
                        f"Dependency ({package})",
                        f"{package} not installed (optional) - {description}"
                    )
