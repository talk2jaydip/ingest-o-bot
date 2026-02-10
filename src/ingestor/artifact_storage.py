"""Artifact storage implementations for local and blob storage."""

import io
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from PIL import Image, ImageDraw, ImageFont

from .config import ArtifactsConfig, ArtifactsMode
from .logging_utils import get_logger

logger = get_logger(__name__)


def add_image_citation(
    image_bytes: bytes,
    document_filename: str,
    image_filename: str,
    page_num: int
) -> bytes:
    """Add citation text to an image (burns citation into the image).
    
    This matches the original prepdocslib behavior of adding source info to images.
    """
    try:
        # Load and modify the image to add text
        image = Image.open(io.BytesIO(image_bytes))
        line_height = 30
        text_height = line_height * 2  # Two lines of text
        new_img = Image.new("RGB", (image.width, image.height + text_height), "white")
        new_img.paste(image, (0, text_height))
        
        # Add text
        draw = ImageDraw.Draw(new_img)
        sourcepage = f"{document_filename}#page={page_num + 1}"
        text = sourcepage
        figure_text = image_filename
        
        # Try to load font (use default if not available)
        try:
            # Look for Jupiteroid font from original prepdocslib
            font_path = Path(__file__).parent.parent / "app" / "backend" / "prepdocslib" / "Jupiteroid-Regular.ttf"
            if not font_path.exists():
                # Fall back to any available font
                font = ImageFont.load_default()
            else:
                font = ImageFont.truetype(str(font_path), 20)
        except Exception:
            font = ImageFont.load_default()
        
        # Calculate text widths for right alignment
        try:
            fig_width = draw.textlength(figure_text, font=font)
        except Exception:
            fig_width = len(figure_text) * 10  # Rough estimate
        
        # Left align document name, right align figure name
        padding = 20
        draw.text((padding, 5), text, font=font, fill="black")
        draw.text((new_img.width - fig_width - padding, line_height + 5), figure_text, font=font, fill="black")
        
        # Convert back to bytes
        output = io.BytesIO()
        format = image.format or "PNG"
        new_img.save(output, format=format)
        
        return output.getvalue()
    except Exception as e:
        logger.warning(f"Failed to add citation to image: {e}. Using original image.")
        return image_bytes


class ArtifactStorage(ABC):
    """Abstract base class for artifact storage."""
    
    @abstractmethod
    async def write_page_json(self, doc_name: str, page_num: int, data: dict) -> str:
        """Write page JSON and return URL/path."""
        pass
    
    @abstractmethod
    async def write_page_pdf(self, doc_name: str, page_num: int, pdf_bytes: bytes) -> str:
        """Write per-page PDF and return URL/path."""
        pass

    @abstractmethod
    async def write_full_document(self, doc_name: str, pdf_bytes: bytes) -> str:
        """Write full original PDF document and return URL/path.

        Args:
            doc_name: Document name
            pdf_bytes: Complete PDF file bytes

        Returns:
            URL/path to the stored full PDF
        """
        pass

    @abstractmethod
    async def write_chunk_json(self, doc_name: str, page_num: int, chunk_idx: int, data: dict) -> str:
        """Write chunk JSON and return URL/path."""
        pass
    
    @abstractmethod
    async def write_image(self, doc_name: str, page_num: int, image_name: str, image_bytes: bytes, figure_idx: int = 0) -> str:
        """Write image and return URL/path.

        Args:
            doc_name: Document name
            page_num: Page number (0-indexed)
            image_name: Original image filename
            image_bytes: Image data
            figure_idx: Figure index on the page (0-indexed, used to prevent naming collisions)
        """
        pass
    
    @abstractmethod
    async def write_manifest(self, doc_name: str, data: dict) -> str:
        """Write manifest JSON and return URL/path."""
        pass

    @abstractmethod
    async def write_status_json(self, status_name: str, data: dict) -> str:
        """Write pipeline status JSON and return URL/path."""
        pass

    async def ensure_containers_exist(self):
        """Ensure storage containers/resources exist.

        Override in subclasses that need container initialization.
        Default implementation does nothing (for local storage).
        """
        pass

    async def delete_document_artifacts(self, doc_name: str) -> int:
        """Delete all artifacts for a specific document.

        Override in subclasses that support cleanup.
        Default implementation does nothing.

        Returns:
            Number of items deleted
        """
        return 0

    async def delete_all_artifacts(self) -> int:
        """Delete ALL artifacts (DANGEROUS!).

        Override in subclasses that support cleanup.
        Default implementation does nothing.

        Returns:
            Number of items deleted
        """
        return 0


class LocalArtifactStorage(ArtifactStorage):
    """Local filesystem artifact storage."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
    
    def _get_doc_dir(self, doc_name: str) -> Path:
        """Get document directory, creating if needed.

        Returns base filename directory without extension.
        """
        # Sanitize document name and remove extension
        from pathlib import Path as PathLib
        base_name = PathLib(doc_name).stem  # Get filename without extension
        safe_name = base_name.replace('/', '_').replace('\\', '_')
        doc_dir = self.base_dir / safe_name
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir
    
    async def write_page_json(self, doc_name: str, page_num: int, data: dict) -> str:
        """Write page JSON to local filesystem.

        Structure: {base_filename}/page-0001.json (no /pages/ subdirectory)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
        """
        doc_dir = self._get_doc_dir(doc_name)

        # Use 1-based page number for storage (page-0001.json instead of page-0000.json)
        page_num_1based = page_num + 1
        page_file = doc_dir / f"page-{page_num_1based:04d}.json"
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return page_file.absolute().as_uri()
    
    async def write_page_pdf(self, doc_name: str, page_num: int, pdf_bytes: bytes) -> str:
        """Write per-page PDF to local filesystem.

        Structure: {base_filename}_page_0001.pdf (flat, underscore separator)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
        """
        # Get base filename without extension
        from pathlib import Path as PathLib
        base_name = PathLib(doc_name).stem
        safe_name = base_name.replace('/', '_').replace('\\', '_')

        # Use 1-based page number for storage (page_0001.pdf instead of page_0000.pdf)
        page_num_1based = page_num + 1
        page_file = self.base_dir / f"{safe_name}_page_{page_num_1based:04d}.pdf"
        with open(page_file, 'wb') as f:
            f.write(pdf_bytes)

        return page_file.absolute().as_uri()

    async def write_full_document(self, doc_name: str, pdf_bytes: bytes) -> str:
        """Write full original PDF document to local filesystem.

        For local storage, we don't duplicate the file. Instead, we return
        the file URI of the original document location.

        Structure: Original file location (not duplicated)

        Args:
            doc_name: Document name (path to original file)
            pdf_bytes: Complete PDF file bytes (not used, file already exists)

        Returns:
            File URI to the original document
        """
        # For local storage, just return the file URI without duplicating
        # The original file is already accessible at its location
        from pathlib import Path as PathLib
        original_path = PathLib(doc_name).absolute()
        return original_path.as_uri()

    async def write_chunk_json(self, doc_name: str, page_num: int, chunk_idx: int, data: dict) -> str:
        """Write chunk JSON to local filesystem.

        Structure: {base_filename}/page-0001/chunk-000001.json (no /chunks/ subdirectory)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
        """
        doc_dir = self._get_doc_dir(doc_name)
        # Use 1-based page number for storage (page-0001 instead of page-0000)
        page_num_1based = page_num + 1
        page_chunks_dir = doc_dir / f"page-{page_num_1based:04d}"
        page_chunks_dir.mkdir(parents=True, exist_ok=True)

        chunk_file = page_chunks_dir / f"chunk-{chunk_idx:06d}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return chunk_file.absolute().as_uri()
    
    async def write_image(self, doc_name: str, page_num: int, image_name: str, image_bytes: bytes, figure_idx: int = 0) -> str:
        """Write image to local filesystem with citation burned in.

        Structure: {base_filename}/page_01_fig_01.png (flattened, no subdirectories)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
            image_name: Original image filename (e.g., "figure-1.png")
            figure_idx: Figure index on the page (0-indexed, will be converted to 1-based for storage)
        """
        doc_dir = self._get_doc_dir(doc_name)

        # Use 1-based numbering for storage
        page_num_1based = page_num + 1
        fig_num_1based = figure_idx + 1

        # Get file extension from original image
        from pathlib import Path as PathLib
        ext = PathLib(image_name).suffix or '.png'

        # Create new filename: page_01_fig_01.png (using 1-based figure index)
        new_image_name = f"page_{page_num_1based:02d}_fig_{fig_num_1based:02d}{ext}"

        # Add citation to image (matches original prepdocslib behavior)
        image_bytes = add_image_citation(image_bytes, doc_name, image_name, page_num)

        image_file = doc_dir / new_image_name
        with open(image_file, 'wb') as f:
            f.write(image_bytes)

        return image_file.absolute().as_uri()
    
    async def write_manifest(self, doc_name: str, data: dict) -> str:
        """Write manifest JSON to local filesystem."""
        doc_dir = self._get_doc_dir(doc_name)
        manifest_file = doc_dir / "manifest.json"

        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return manifest_file.absolute().as_uri()

    async def write_status_json(self, status_name: str, data: dict) -> str:
        """Write pipeline status JSON to local filesystem."""
        # Store in a 'status' subdirectory at the base level
        status_dir = self.base_dir / "status"
        status_dir.mkdir(parents=True, exist_ok=True)

        status_file = status_dir / f"{status_name}.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return status_file.absolute().as_uri()


class BlobArtifactStorage(ArtifactStorage):
    """Azure Blob Storage artifact storage."""
    
    def __init__(
        self,
        account_url: str,
        pages_container: str,
        chunks_container: str,
        images_container: Optional[str] = None,
        citations_container: Optional[str] = None,
        credential: Optional[str] = None
    ):
        self.account_url = account_url
        self.pages_container = pages_container
        self.chunks_container = chunks_container
        self.images_container = images_container or chunks_container
        self.citations_container = citations_container or pages_container  # Use separate container if provided, else use pages
        self.credential = credential
    
    def _sanitize_doc_name(self, doc_name: str) -> str:
        """Sanitize document name for blob storage.

        Returns base filename without extension.
        """
        from pathlib import Path as PathLib
        base_name = PathLib(doc_name).stem  # Get filename without extension
        return base_name.replace('\\', '/').strip('/')
    
    async def ensure_containers_exist(self):
        """Efficiently ensure all required containers exist.
        
        Checks if containers exist first, then creates only if needed.
        This should be called once during initialization.
        """
        containers_to_create = set()
        
        # Collect unique containers
        containers_to_create.add(self.pages_container)
        containers_to_create.add(self.chunks_container)
        containers_to_create.add(self.images_container)
        if self.citations_container:
            containers_to_create.add(self.citations_container)
        
        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            for container_name in containers_to_create:
                container_client = blob_service_client.get_container_client(container_name)
                
                # Check if container exists first
                try:
                    await container_client.get_container_properties()
                    logger.debug(f"Container '{container_name}' already exists")
                except Exception:
                    # Container doesn't exist, create it
                    try:
                        await container_client.create_container()
                        logger.info(f"Created container: {container_name}")
                    except ResourceExistsError:
                        # Container was created between check and create (race condition)
                        logger.debug(f"Container '{container_name}' was created by another process")
                    except Exception as e:
                        logger.error(f"Failed to create container '{container_name}': {e}")
                        raise
    
    async def write_page_json(self, doc_name: str, page_num: int, data: dict) -> str:
        """Write page JSON to blob storage.

        Structure: {base_filename}/page-0001.json (no /pages/ subdirectory)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
        """
        safe_name = self._sanitize_doc_name(doc_name)
        # Use 1-based page number for storage (page-0001.json instead of page-0000.json)
        page_num_1based = page_num + 1
        blob_name = f"{safe_name}/page-{page_num_1based:04d}.json"

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(self.pages_container)
            blob_client = container_client.get_blob_client(blob_name)
            json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            await blob_client.upload_blob(json_bytes, overwrite=True)

            return unquote(blob_client.url)
    
    async def write_page_pdf(self, doc_name: str, page_num: int, pdf_bytes: bytes) -> str:
        """Write per-page PDF to blob storage (pages container).

        Structure: {base_filename}_page_0001.pdf (flat, underscore separator)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
        """
        safe_name = self._sanitize_doc_name(doc_name)
        # Use 1-based page number for storage (page_0001.pdf instead of page_0000.pdf)
        page_num_1based = page_num + 1
        blob_name = f"{safe_name}_page_{page_num_1based:04d}.pdf"

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(self.pages_container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.upload_blob(pdf_bytes, overwrite=True)

            return unquote(blob_client.url)

    async def write_full_document(self, doc_name: str, pdf_bytes: bytes) -> str:
        """Write full original document to blob storage (PDF, DOCX, PPTX, etc.).

        Structure: {base_filename}.{ext} at root level in citations container

        Args:
            doc_name: Document name (with extension)
            pdf_bytes: Complete document file bytes

        Returns:
            Blob URL to the stored full document
        """
        from pathlib import Path

        safe_name = self._sanitize_doc_name(doc_name)
        # Preserve original file extension (PDF, DOCX, PPTX, etc.)
        original_ext = Path(doc_name).suffix.lower()
        # If sanitized name already has extension, use it; otherwise add from original
        if not Path(safe_name).suffix:
            blob_name = f"{safe_name}{original_ext}"
        else:
            blob_name = safe_name

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(self.citations_container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.upload_blob(pdf_bytes, overwrite=True)

            return unquote(blob_client.url)

    async def write_chunk_json(self, doc_name: str, page_num: int, chunk_idx: int, data: dict) -> str:
        """Write chunk JSON to blob storage.

        Structure: {base_filename}/page-0001/chunk-000001.json (no /chunks/ subdirectory)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
        """
        safe_name = self._sanitize_doc_name(doc_name)
        # Use 1-based page number for storage (page-0001 instead of page-0000)
        page_num_1based = page_num + 1
        blob_name = f"{safe_name}/page-{page_num_1based:04d}/chunk-{chunk_idx:06d}.json"

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(self.chunks_container)
            blob_client = container_client.get_blob_client(blob_name)
            json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            await blob_client.upload_blob(json_bytes, overwrite=True)

            return unquote(blob_client.url)
    
    async def write_image(self, doc_name: str, page_num: int, image_name: str, image_bytes: bytes, figure_idx: int = 0) -> str:
        """Write image to blob storage with citation burned in.

        Structure: {base_filename}/page_01_fig_01.png (flattened, no subdirectories)

        Args:
            page_num: 0-indexed page number (will be converted to 1-based for storage)
            image_name: Original image filename (e.g., "figure-1.png")
            figure_idx: Figure index on the page (0-indexed, will be converted to 1-based for storage)
        """
        safe_name = self._sanitize_doc_name(doc_name)

        # Use 1-based numbering for storage
        page_num_1based = page_num + 1
        fig_num_1based = figure_idx + 1

        # Get file extension from original image
        from pathlib import Path as PathLib
        ext = PathLib(image_name).suffix or '.png'

        # Create new filename: page_01_fig_01.png (using 1-based figure index)
        new_image_name = f"page_{page_num_1based:02d}_fig_{fig_num_1based:02d}{ext}"
        blob_name = f"{safe_name}/{new_image_name}"

        # Add citation to image (matches original prepdocslib behavior)
        image_bytes = add_image_citation(image_bytes, doc_name, image_name, page_num)

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(self.images_container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.upload_blob(image_bytes, overwrite=True)

            return unquote(blob_client.url)

    async def delete_document_artifacts(self, doc_name: str) -> int:
        """Delete all artifacts for a specific document from blob storage.

        Args:
            doc_name: Document name

        Returns:
            Total number of blobs deleted
        """
        safe_name = self._sanitize_doc_name(doc_name)
        deleted_count = 0

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            # Delete from all containers
            containers = [
                self.pages_container,
                self.chunks_container,
                self.images_container,
            ]
            if self.citations_container:
                containers.append(self.citations_container)

            for container_name in containers:
                try:
                    container_client = blob_service_client.get_container_client(container_name)

                    # Delete all blobs with the document prefix (pages/, figures/, chunks/, etc.)
                    async for blob in container_client.list_blobs(name_starts_with=f"{safe_name}/"):
                        try:
                            await container_client.delete_blob(blob.name)
                            deleted_count += 1
                            logger.debug(f"Deleted blob: {container_name}/{blob.name}")
                        except Exception as e:
                            logger.warning(f"Failed to delete blob {blob.name}: {e}")

                    # Also delete root-level full document PDF if in citations container
                    if container_name == self.citations_container:
                        try:
                            root_pdf_name = f"{safe_name}.pdf"
                            await container_client.delete_blob(root_pdf_name)
                            deleted_count += 1
                            logger.debug(f"Deleted full document: {container_name}/{root_pdf_name}")
                        except Exception as e:
                            # Blob might not exist (no full document was uploaded)
                            logger.debug(f"No full document PDF found: {root_pdf_name}")

                    logger.info(f"Cleaned artifacts from container: {container_name}")
                except Exception as e:
                    logger.warning(f"Failed to clean container '{container_name}': {e}")

        return deleted_count

    async def delete_all_artifacts(self) -> int:
        """Delete ALL artifacts from ALL containers (DANGEROUS!).

        Returns:
            Total number of blobs deleted
        """
        deleted_count = 0

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            # Delete from all containers
            containers = [
                self.pages_container,
                self.chunks_container,
                self.images_container,
            ]
            if self.citations_container:
                containers.append(self.citations_container)

            for container_name in containers:
                try:
                    container_client = blob_service_client.get_container_client(container_name)

                    # List and delete all blobs
                    async for blob in container_client.list_blobs():
                        try:
                            await container_client.delete_blob(blob.name)
                            deleted_count += 1
                            logger.debug(f"Deleted blob: {container_name}/{blob.name}")
                        except Exception as e:
                            logger.warning(f"Failed to delete blob {blob.name}: {e}")

                    logger.info(f"Cleaned all artifacts from container: {container_name}")
                except Exception as e:
                    logger.error(f"Failed to clean container '{container_name}': {e}")

        return deleted_count

    async def write_manifest(self, doc_name: str, data: dict) -> str:
        """Write manifest JSON to blob storage."""
        safe_name = self._sanitize_doc_name(doc_name)
        blob_name = f"{safe_name}/manifest.json"

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            # Store manifest in the pages container
            container_client = blob_service_client.get_container_client(self.pages_container)
            blob_client = container_client.get_blob_client(blob_name)
            json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            await blob_client.upload_blob(json_bytes, overwrite=True)

            return unquote(blob_client.url)

    async def write_status_json(self, status_name: str, data: dict) -> str:
        """Write pipeline status JSON to blob storage."""
        # Store in a 'status' directory at the root level
        blob_name = f"status/{status_name}.json"

        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            # Store status in the pages container
            container_client = blob_service_client.get_container_client(self.pages_container)
            blob_client = container_client.get_blob_client(blob_name)
            json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            await blob_client.upload_blob(json_bytes, overwrite=True)

            return unquote(blob_client.url)


def create_artifact_storage(config: ArtifactsConfig) -> ArtifactStorage:
    """Factory function to create artifact storage from configuration."""
    if config.mode == ArtifactsMode.LOCAL:
        if not config.local_dir:
            raise ValueError("local_dir is required for local artifacts mode")
        return LocalArtifactStorage(config.local_dir)
    elif config.mode == ArtifactsMode.BLOB:
        if not config.blob_account_url:
            raise ValueError("blob_account_url is required for blob artifacts mode")
        if not config.blob_container_pages or not config.blob_container_chunks:
            raise ValueError("blob containers are required for blob artifacts mode")
        return BlobArtifactStorage(
            account_url=config.blob_account_url,
            pages_container=config.blob_container_pages,
            chunks_container=config.blob_container_chunks,
            images_container=config.blob_container_images,
            citations_container=config.blob_container_citations,
            credential=config.blob_key
        )
    else:
        raise ValueError(f"Unsupported artifacts mode: {config.mode}")

