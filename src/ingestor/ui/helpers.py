"""Shared utilities for the Gradio UI."""

import asyncio
import os
import queue
import threading
from typing import Dict, List, Optional

import tiktoken
from ingestor.logging_utils import get_logger

# Try to import Azure Storage SDK
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False

# Try to import Azure Search SDK
try:
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_SEARCH_AVAILABLE = True
except ImportError:
    AZURE_SEARCH_AVAILABLE = False

# Logger
logger = get_logger(__name__)

# Global log queue for real-time streaming
log_queue = queue.Queue()

# Token counter (same as used in chunker.py)
ENCODING_MODEL = "text-embedding-ada-002"
try:
    token_encoder = tiktoken.encoding_for_model(ENCODING_MODEL)
except Exception as e:
    logger.warning(f"Could not load tiktoken encoding: {e}. Token counts may be unavailable.")
    token_encoder = None


# =============================================================================
# Azure Blob Storage Helpers
# =============================================================================

def get_blob_service_client() -> Optional[BlobServiceClient]:
    """Get Azure Blob Service Client from environment.

    Returns:
        BlobServiceClient if credentials are configured, None otherwise
    """
    if not AZURE_STORAGE_AVAILABLE:
        return None

    try:
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        storage_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        connection_string = os.getenv("AZURE_CONNECTION_STRING")

        if connection_string:
            return BlobServiceClient.from_connection_string(connection_string)
        elif storage_account and storage_key:
            return BlobServiceClient(
                account_url=f"https://{storage_account}.blob.core.windows.net",
                credential=storage_key
            )
        return None
    except Exception as e:
        logger.error(f"Failed to create blob service client: {e}")
        return None


def list_blob_containers() -> List[str]:
    """List all blob containers in the storage account.

    Returns:
        List of container names, or error messages if unavailable
    """
    if not AZURE_STORAGE_AVAILABLE:
        return ["⚠️ Azure Storage SDK not installed"]

    try:
        client = get_blob_service_client()
        if not client:
            return ["⚠️ Storage credentials not configured"]

        containers = []
        for container in client.list_containers():
            containers.append(container.name)

        return containers if containers else ["⚠️ No containers found"]
    except Exception as e:
        logger.error(f"Failed to list containers: {e}")
        return [f"⚠️ Error: {str(e)[:50]}..."]


def list_blobs_in_container(container_name: str, prefix: str = "") -> List[Dict]:
    """List blobs in a container with optional prefix filter.

    Args:
        container_name: Name of the blob container
        prefix: Optional prefix to filter blobs

    Returns:
        List of blob metadata dictionaries
    """
    if not AZURE_STORAGE_AVAILABLE:
        return []

    try:
        client = get_blob_service_client()
        if not client:
            return []

        container_client = client.get_container_client(container_name)
        blobs = []

        for blob in container_client.list_blobs(name_starts_with=prefix):
            blobs.append({
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified
            })

        return blobs
    except Exception as e:
        logger.error(f"Failed to list blobs: {e}")
        return []


# =============================================================================
# Azure AI Search Helpers
# =============================================================================

def get_search_client() -> Optional[SearchClient]:
    """Get Azure Search client from environment variables.

    Returns:
        SearchClient if credentials are configured, None otherwise
    """
    if not AZURE_SEARCH_AVAILABLE:
        return None

    try:
        # Get search service details
        search_service = os.getenv("AZURE_SEARCH_SERVICE")
        index_name = os.getenv("AZURE_SEARCH_INDEX")
        search_key = os.getenv("AZURE_SEARCH_KEY")

        if not all([search_service, index_name, search_key]):
            logger.warning("Azure Search credentials not fully configured")
            return None

        endpoint = f"https://{search_service}.search.windows.net"
        credential = AzureKeyCredential(search_key)

        client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )

        return client
    except Exception as e:
        logger.error(f"Failed to create search client: {e}")
        return None


def search_documents_by_filename(filename_pattern: str, max_results: int = 1000) -> List[Dict]:
    """Search for documents by filename pattern.

    Args:
        filename_pattern: Pattern to match (e.g., "Tables*", "*.pdf", or "*" for all)
        max_results: Maximum number of results to return

    Returns:
        List of document dictionaries with metadata
    """
    client = get_search_client()
    if not client:
        return []

    try:
        # For "*" pattern, get all documents
        if filename_pattern == "*" or not filename_pattern.strip():
            results = client.search(
                search_text="",
                top=max_results
            )
        else:
            # Convert glob pattern: remove asterisks for search
            search_term = filename_pattern.replace("*", "").strip()

            if search_term:
                results = client.search(
                    search_text=search_term,
                    top=max_results
                )
            else:
                results = client.search(
                    search_text="",
                    top=max_results
                )

        # Group documents by filename
        documents = {}
        for result in results:
            # Try various field names for filename
            filename = None
            for file_field in ["sourcefile", "source_file", "filename", "file_name", "title"]:
                if file_field in result:
                    filename = result.get(file_field)
                    if filename:
                        break

            if not filename:
                doc_id = result.get("id", "")
                if doc_id and ("." in doc_id or "pdf" in doc_id.lower()):
                    filename = doc_id
                else:
                    filename = "Unknown"

            # Filter by pattern
            if filename_pattern != "*" and filename_pattern.strip():
                pattern_lower = filename_pattern.lower().replace("*", "")
                filename_lower = filename.lower()
                if pattern_lower and pattern_lower not in filename_lower:
                    continue

            # Group by filename
            if filename not in documents:
                documents[filename] = {
                    "id": filename,
                    "filename": filename,
                    "category": result.get("category", "") or result.get("type", ""),
                    "chunk_count": 0,
                    "chunks": []
                }

            documents[filename]["chunk_count"] += 1

        return list(documents.values())

    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        return []


def get_document_chunks(doc_id: str, max_chunks: int = 1000) -> List[Dict]:
    """Get all chunks for a specific document.

    Args:
        doc_id: The document ID (filename or identifier)
        max_chunks: Maximum number of chunks to retrieve

    Returns:
        List of chunks sorted by page number
    """
    client = get_search_client()
    if not client:
        return []

    try:
        results = client.search(
            search_text=doc_id,
            top=max_chunks
        )

        chunks = []
        for result in list(results):
            # Check if this result belongs to our document
            is_match = False
            for field in ["id", "sourcefile", "source_file", "filename", "file_name", "title"]:
                if field in result:
                    field_value = result.get(field, "")
                    if field_value and doc_id.lower() in field_value.lower():
                        is_match = True
                        break

            if not is_match:
                continue

            # Get page number
            page_num = 0
            for page_field in ["page_num", "page_number", "pageNumber", "page"]:
                if page_field in result:
                    page_num = result.get(page_field, 0)
                    break

            # Get chunk ID
            chunk_id = result.get("id") or f"chunk_{len(chunks)}"

            # Get content
            content = result.get("content", "")

            chunks.append({
                "id": chunk_id,
                "page": page_num,
                "content": content,
                "metadata": {k: v for k, v in result.items() if k not in ["content", "id"]}
            })

        # Sort by page number
        chunks.sort(key=lambda x: x["page"])
        return chunks

    except Exception as e:
        logger.error(f"Failed to get document chunks: {e}")
        return []


# =============================================================================
# Async Execution Helpers
# =============================================================================

def run_async(coroutine):
    """Run an async coroutine in a new event loop.

    Args:
        coroutine: The async coroutine to run

    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new one in a thread
            result = None
            exception = None

            def run_in_thread():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(coroutine)
                except Exception as e:
                    exception = e
                finally:
                    new_loop.close()

            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()

            if exception:
                raise exception
            return result
        else:
            return loop.run_until_complete(coroutine)
    except Exception as e:
        logger.error(f"Error running async coroutine: {e}")
        raise


# =============================================================================
# Token Counting
# =============================================================================

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for

    Returns:
        Number of tokens, or 0 if encoder is unavailable
    """
    if not token_encoder:
        return 0
    try:
        return len(token_encoder.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        return 0


# =============================================================================
# Environment Variable Utilities
# =============================================================================

def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """Mask sensitive values, showing only first few characters.

    Args:
        value: The value to mask
        show_chars: Number of characters to show at the start

    Returns:
        Masked value like "abc...***"
    """
    if not value:
        return ""
    if len(value) <= show_chars:
        return "*" * len(value)
    return f"{value[:show_chars]}...{'*' * 8}"


def get_env_var_safe(var_name: str, mask: bool = True) -> str:
    """Get environment variable with optional masking.

    Args:
        var_name: Name of the environment variable
        mask: Whether to mask sensitive values

    Returns:
        Value of the environment variable, possibly masked
    """
    value = os.getenv(var_name, "")
    if not value:
        return ""

    # Mask if it looks sensitive (contains "KEY", "SECRET", "PASSWORD")
    if mask and any(sensitive in var_name.upper() for sensitive in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
        return mask_sensitive_value(value)

    return value


__all__ = [
    "log_queue",
    "token_encoder",
    "AZURE_STORAGE_AVAILABLE",
    "AZURE_SEARCH_AVAILABLE",
    # Blob storage
    "get_blob_service_client",
    "list_blob_containers",
    "list_blobs_in_container",
    # Search
    "get_search_client",
    "search_documents_by_filename",
    "get_document_chunks",
    # Async
    "run_async",
    # Token counting
    "count_tokens",
    # Environment
    "mask_sensitive_value",
    "get_env_var_safe",
]
