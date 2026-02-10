"""Input source implementations for local and blob storage with multiple file format support."""

import glob
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator, Optional, Set
from urllib.parse import unquote

from azure.storage.blob.aio import BlobServiceClient

from .config import InputConfig, InputMode
from .logging_utils import get_logger

logger = get_logger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS: Set[str] = {
    '.pdf',       # PDF documents (processed with Document Intelligence)
    '.docx',      # Word documents (processed with Office extractor)
    '.pptx',      # PowerPoint presentations (processed with Office extractor)
    '.doc',       # Legacy Word documents (processed with Office extractor - Phase 2)
    '.txt',       # Plain text
    '.md',        # Markdown
    '.html',      # HTML
    '.htm',       # HTML alternate
    '.json',      # JSON
    '.csv',       # CSV
}


class InputSource(ABC):
    """Abstract base class for input sources."""
    
    @abstractmethod
    async def list_files(self) -> AsyncGenerator[tuple[str, bytes, str], None]:
        """List and yield files as (filename, content_bytes, source_url).
        
        Supports multiple file formats: PDF, TXT, MD, HTML, JSON, CSV.
        """
        yield  # type: ignore
    
    async def list_pdfs(self) -> AsyncGenerator[tuple[str, bytes, str], None]:
        """Legacy method - list only PDFs. Use list_files for all formats."""
        async for filename, content, source_url in self.list_files():
            if filename.lower().endswith('.pdf'):
                yield filename, content, source_url


class LocalInputSource(InputSource):
    """Input source for local files."""
    
    def __init__(self, glob_pattern: str):
        self.glob_pattern = glob_pattern
    
    async def list_files(self) -> AsyncGenerator[tuple[str, bytes, str], None]:
        """List and yield files from local filesystem."""
        logger.info(f"Scanning for files matching pattern: {self.glob_pattern}")
        
        file_paths = glob.glob(self.glob_pattern, recursive=True)
        
        # Filter to supported file types
        supported_files = []
        for f in file_paths:
            if os.path.isfile(f):
                ext = Path(f).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    supported_files.append(f)
                else:
                    logger.debug(f"Skipping unsupported file type: {f}")
        
        logger.info(f"Found {len(supported_files)} supported files")
        
        for file_path in supported_files:
            filename = os.path.basename(file_path)
            ext = Path(filename).suffix.lower()
            logger.info(f"Reading local file ({ext}): {filename}")
            
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # For local files, use absolute path as URL
                source_url = Path(file_path).absolute().as_uri()
                
                yield filename, content, source_url
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue


class BlobInputSource(InputSource):
    """Input source for files in Azure Blob Storage."""
    
    def __init__(
        self,
        account_url: str,
        container: str,
        prefix: str = "",
        credential: Optional[str] = None
    ):
        self.account_url = account_url
        self.container = container
        self.prefix = prefix
        self.credential = credential
    
    async def list_files(self) -> AsyncGenerator[tuple[str, bytes, str], None]:
        """List and yield files from Azure Blob Storage."""
        logger.info(f"Listing files from blob container: {self.container}, prefix: {self.prefix or '(none)'}")
        
        async with BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(self.container)
            
            # List blobs with prefix
            blob_list = container_client.list_blobs(name_starts_with=self.prefix)
            
            count = 0
            async for blob in blob_list:
                ext = Path(blob.name).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    logger.debug(f"Skipping unsupported file type: {blob.name}")
                    continue
                
                filename = os.path.basename(blob.name)
                logger.info(f"Downloading blob ({ext}): {blob.name}")
                
                try:
                    blob_client = container_client.get_blob_client(blob.name)
                    downloader = await blob_client.download_blob()
                    content = await downloader.readall()
                    
                    # Get the blob URL (decoded)
                    source_url = unquote(blob_client.url)
                    
                    count += 1
                    yield filename, content, source_url
                except Exception as e:
                    logger.error(f"Error downloading {blob.name}: {e}")
                    continue
            
            logger.info(f"Downloaded {count} files from blob storage")


def create_input_source(config: InputConfig) -> InputSource:
    """Factory function to create input source from configuration."""
    if config.mode == InputMode.LOCAL:
        if not config.local_glob:
            raise ValueError("local_glob is required for local input mode")
        return LocalInputSource(config.local_glob)
    elif config.mode == InputMode.BLOB:
        if not config.blob_account_url or not config.blob_container_in:
            raise ValueError("blob_account_url and blob_container_in are required for blob input mode")
        return BlobInputSource(
            account_url=config.blob_account_url,
            container=config.blob_container_in,
            prefix=config.blob_prefix or "",
            credential=config.blob_key
        )
    else:
        raise ValueError(f"Unsupported input mode: {config.mode}")
