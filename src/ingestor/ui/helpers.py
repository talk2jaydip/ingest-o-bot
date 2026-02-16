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

# =============================================================================
# Module Configuration
# =============================================================================

# Logger
logger = get_logger(__name__)

# Global log queue for real-time streaming
log_queue = queue.Queue()

# Token counter configuration (same as used in chunker.py)
ENCODING_MODEL = "text-embedding-ada-002"
try:
    token_encoder = tiktoken.encoding_for_model(ENCODING_MODEL)
except Exception as e:
    logger.warning(f"Could not load tiktoken encoding: {e}. Token counts may be unavailable.")
    token_encoder = None

# UI Display Constants
DEFAULT_MASKED_CHARS = 4
DEFAULT_CHUNK_LIMIT = 100
DEFAULT_MAX_SEARCH_RESULTS = 1000
DEFAULT_CONTENT_PREVIEW_LENGTH = 100


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

    Only creates a client if VECTOR_STORE_MODE is set to 'azure_search'.

    Returns:
        SearchClient if credentials are configured and Azure Search is the active vector store, None otherwise
    """
    # Check if Azure Search is the active vector store
    vector_store_mode = os.getenv("VECTOR_STORE_MODE", "azure_search").lower()
    if vector_store_mode != "azure_search":
        logger.debug(f"Skipping Azure Search client creation - VECTOR_STORE_MODE is '{vector_store_mode}'")
        return None

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


def search_documents_by_filename(filename_pattern: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[Dict]:
    """Search for documents by filename pattern.

    Args:
        filename_pattern: Pattern to match (e.g., "Tables*", "*.pdf", or "*" for all)
        max_results: Maximum number of results to return (default: 1000)

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


def get_document_chunks(doc_id: str, max_chunks: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[Dict]:
    """Get all chunks for a specific document.

    Args:
        doc_id: The document ID (filename or identifier)
        max_chunks: Maximum number of chunks to retrieve (default: 1000)

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

def mask_sensitive_value(value: str, show_chars: int = DEFAULT_MASKED_CHARS) -> str:
    """Mask sensitive values, showing only first few characters.

    Args:
        value: The value to mask
        show_chars: Number of characters to show at the start (default: 4)

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


# =============================================================================
# ChromaDB Helpers
# =============================================================================

# Try to import ChromaDB
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def get_chromadb_client():
    """Get ChromaDB client from environment variables.

    Supports three modes:
    - Persistent: CHROMADB_PERSIST_DIR set
    - In-memory: No CHROMADB_PERSIST_DIR or CHROMADB_HOST
    - Client/server: CHROMADB_HOST and CHROMADB_PORT set

    Returns:
        ChromaDB client instance or None if unavailable/misconfigured
    """
    if not CHROMADB_AVAILABLE:
        return None

    try:
        persist_dir = os.getenv("CHROMADB_PERSIST_DIR")
        host = os.getenv("CHROMADB_HOST")
        port = os.getenv("CHROMADB_PORT")
        auth_token = os.getenv("CHROMADB_AUTH_TOKEN")

        if host and port:
            # Client/server mode
            settings = chromadb.config.Settings(
                chroma_api_impl="rest",
                chroma_server_host=host,
                chroma_server_http_port=int(port)
            )
            if auth_token:
                settings.chroma_client_auth_provider = "token"
                settings.chroma_client_auth_credentials = auth_token

            client = chromadb.HttpClient(host=host, port=int(port), settings=settings)
        elif persist_dir:
            # Persistent mode
            client = chromadb.PersistentClient(path=persist_dir)
        else:
            # In-memory mode
            client = chromadb.EphemeralClient()

        return client
    except Exception as e:
        logger.error(f"Failed to create ChromaDB client: {e}")
        return None


def list_chromadb_collections() -> List[str]:
    """List all ChromaDB collections.

    Returns:
        List of collection names, or error messages if unavailable
    """
    if not CHROMADB_AVAILABLE:
        return ["⚠️ ChromaDB not installed"]

    try:
        client = get_chromadb_client()
        if not client:
            return ["⚠️ ChromaDB client not configured"]

        collections = client.list_collections()
        names = [col.name for col in collections]

        return names if names else ["⚠️ No collections found"]
    except Exception as e:
        logger.error(f"Failed to list ChromaDB collections: {e}")
        return [f"⚠️ Error: {str(e)[:50]}..."]


def get_collection_info(collection_name: str) -> dict:
    """Get collection metadata (count, dimensions, etc.).

    Args:
        collection_name: Name of the ChromaDB collection

    Returns:
        Dictionary with count, dimensions, and other metadata
    """
    if not CHROMADB_AVAILABLE:
        return {"error": "ChromaDB not installed"}

    try:
        client = get_chromadb_client()
        if not client:
            return {"error": "ChromaDB client not configured"}

        collection = client.get_collection(collection_name)
        count = collection.count()

        # Get dimensions from first embedding (if any)
        dimensions = 0
        if count > 0:
            sample = collection.peek(limit=1)
            if sample and sample.get('embeddings') and len(sample['embeddings']) > 0:
                dimensions = len(sample['embeddings'][0])

        return {
            "count": count,
            "dimensions": dimensions,
            "name": collection_name
        }
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        return {"error": str(e)}


def get_collection_chunks(
    collection_name: str,
    limit: int = DEFAULT_CHUNK_LIMIT,
    offset: int = 0,
    filters: Optional[dict] = None
) -> tuple[List[List], str]:
    """Get chunks from ChromaDB collection with optional filtering.

    Args:
        collection_name: Name of the ChromaDB collection
        limit: Maximum number of chunks to retrieve (default: 100)
        offset: Number of chunks to skip (for pagination)
        filters: Optional metadata filters (e.g., {"sourcefile": "doc.pdf"})

    Returns:
        Tuple of (rows_for_dataframe, status_message)
    """
    if not CHROMADB_AVAILABLE:
        return [], "ChromaDB not installed"

    try:
        client = get_chromadb_client()
        if not client:
            return [], "ChromaDB client not configured"

        collection = client.get_collection(collection_name)

        # Build where clause for filters
        where_clause = None
        if filters:
            # Convert filters to ChromaDB where clause format
            where_clause = {}
            for key, value in filters.items():
                if value is not None and value != "":
                    where_clause[key] = value
            if not where_clause:
                where_clause = None

        # Get chunks from collection
        results = collection.get(
            where=where_clause,
            limit=limit,
            offset=offset,
            include=['metadatas', 'documents']
        )

        # Format for dataframe
        rows = []
        if results and results.get('ids'):
            for i, chunk_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if i < len(results['metadatas']) else {}
                document = results['documents'][i] if i < len(results['documents']) else ""

                # Extract key fields
                sourcefile = metadata.get('sourcefile', 'Unknown')
                page_num = metadata.get('page_number', 0)
                token_count = metadata.get('token_count', 0)

                # Content preview
                content_preview = (
                    document[:DEFAULT_CONTENT_PREVIEW_LENGTH] + "..."
                    if len(document) > DEFAULT_CONTENT_PREVIEW_LENGTH
                    else document
                )

                rows.append([chunk_id, sourcefile, page_num, content_preview, token_count])

        status = f"Found {len(rows)} chunks"
        return rows, status

    except Exception as e:
        logger.error(f"Failed to get collection chunks: {e}")
        return [], f"Error: {str(e)}"


def get_chunk_details(collection_name: str, chunk_id: str) -> Optional[dict]:
    """Get detailed information for a specific chunk.

    Args:
        collection_name: Name of the ChromaDB collection
        chunk_id: ID of the chunk to retrieve

    Returns:
        Dictionary with content, metadata, embedding or None if not found
    """
    if not CHROMADB_AVAILABLE:
        return None

    try:
        client = get_chromadb_client()
        if not client:
            return None

        collection = client.get_collection(collection_name)

        # Get chunk with full details
        results = collection.get(
            ids=[chunk_id],
            include=['embeddings', 'metadatas', 'documents']
        )

        if not results or not results.get('ids'):
            return None

        return {
            "id": results['ids'][0],
            "content": results['documents'][0] if results.get('documents') else "",
            "metadata": results['metadatas'][0] if results.get('metadatas') else {},
            "embedding": results['embeddings'][0] if results.get('embeddings') else []
        }

    except Exception as e:
        logger.error(f"Failed to get chunk details: {e}")
        return None


# =============================================================================
# Embedding Visualization Helpers
# =============================================================================

# Try to import visualization libraries
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    import numpy as np
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False


def get_embeddings_from_chromadb(collection_name: str, max_points: int) -> tuple:
    """Extract embeddings and metadata from ChromaDB collection.

    Args:
        collection_name: Name of the ChromaDB collection
        max_points: Maximum number of embeddings to extract

    Returns:
        Tuple of (embeddings_array, metadata_list)
    """
    if not CHROMADB_AVAILABLE or not VISUALIZATION_AVAILABLE:
        return np.array([]), []

    try:
        client = get_chromadb_client()
        if not client:
            return np.array([]), []

        collection = client.get_collection(collection_name)

        # Get chunks with embeddings
        results = collection.get(
            limit=max_points,
            include=['embeddings', 'metadatas', 'documents']
        )

        if not results or not results.get('embeddings'):
            return np.array([]), []

        embeddings = np.array(results['embeddings'])
        metadata_list = []

        for i, chunk_id in enumerate(results['ids']):
            metadata = results['metadatas'][i] if i < len(results['metadatas']) else {}
            document = results['documents'][i] if i < len(results['documents']) else ""

            metadata_list.append({
                "id": chunk_id,
                "sourcefile": metadata.get('sourcefile', 'Unknown'),
                "page_number": metadata.get('page_number', 0),
                "title": metadata.get('title', ''),
                "token_count": metadata.get('token_count', 0),
                "content_preview": (
                    document[:DEFAULT_CONTENT_PREVIEW_LENGTH] + "..."
                    if len(document) > DEFAULT_CONTENT_PREVIEW_LENGTH
                    else document
                )
            })

        return embeddings, metadata_list

    except Exception as e:
        logger.error(f"Failed to get embeddings from ChromaDB: {e}")
        return np.array([]), []


def get_embeddings_from_azure_search(index_name: str, max_points: int) -> tuple:
    """Extract embeddings from Azure Search index.

    Args:
        index_name: Name of the Azure Search index
        max_points: Maximum number of embeddings to extract

    Returns:
        Tuple of (embeddings_array, metadata_list)
    """
    if not AZURE_SEARCH_AVAILABLE or not VISUALIZATION_AVAILABLE:
        return np.array([]), []

    try:
        client = get_search_client()
        if not client:
            return np.array([]), []

        # Search for documents with embeddings
        results = client.search(
            search_text="",
            top=max_points,
            select=["id", "embeddings", "sourcefile", "pageNumber", "title", "token_count", "content"]
        )

        embeddings_list = []
        metadata_list = []

        for result in results:
            if "embeddings" in result and result["embeddings"]:
                embeddings_list.append(result["embeddings"])

                metadata_list.append({
                    "id": result.get("id", ""),
                    "sourcefile": result.get("sourcefile", "Unknown"),
                    "page_number": result.get("pageNumber", 0),
                    "title": result.get("title", ""),
                    "token_count": result.get("token_count", 0),
                    "content_preview": (
                        result.get("content", "")[:DEFAULT_CONTENT_PREVIEW_LENGTH] + "..."
                        if result.get("content") and len(result.get("content", "")) > DEFAULT_CONTENT_PREVIEW_LENGTH
                        else result.get("content", "")
                    )
                })

        if embeddings_list:
            embeddings = np.array(embeddings_list)
            return embeddings, metadata_list
        else:
            return np.array([]), []

    except Exception as e:
        logger.error(f"Failed to get embeddings from Azure Search: {e}")
        return np.array([]), []


def reduce_embeddings_pca(embeddings: "np.ndarray", n_components: int = 2) -> "np.ndarray":
    """Reduce embeddings to 2D/3D using PCA.

    Args:
        embeddings: NumPy array of embeddings
        n_components: Number of dimensions (2 or 3)

    Returns:
        Reduced embeddings as NumPy array
    """
    if not VISUALIZATION_AVAILABLE:
        return np.array([])

    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=n_components, random_state=42)
        return pca.fit_transform(embeddings)
    except Exception as e:
        logger.error(f"PCA reduction failed: {e}")
        return np.array([])


def reduce_embeddings_tsne(embeddings: "np.ndarray", n_components: int = 2) -> "np.ndarray":
    """Reduce embeddings using t-SNE.

    Args:
        embeddings: NumPy array of embeddings
        n_components: Number of dimensions (2 or 3)

    Returns:
        Reduced embeddings as NumPy array
    """
    if not VISUALIZATION_AVAILABLE:
        return np.array([])

    try:
        from sklearn.manifold import TSNE
        tsne = TSNE(n_components=n_components, random_state=42, perplexity=min(30, len(embeddings) - 1))
        return tsne.fit_transform(embeddings)
    except Exception as e:
        logger.error(f"t-SNE reduction failed: {e}")
        return np.array([])


def reduce_embeddings_umap(embeddings: "np.ndarray", n_components: int = 2) -> "np.ndarray":
    """Reduce embeddings using UMAP.

    Args:
        embeddings: NumPy array of embeddings
        n_components: Number of dimensions (2 or 3)

    Returns:
        Reduced embeddings as NumPy array
    """
    if not UMAP_AVAILABLE or not VISUALIZATION_AVAILABLE:
        return np.array([])

    try:
        import umap as umap_lib
        reducer = umap_lib.UMAP(n_components=n_components, random_state=42)
        return reducer.fit_transform(embeddings)
    except Exception as e:
        logger.error(f"UMAP reduction failed: {e}")
        return np.array([])


def create_embedding_plot(
    coords: "np.ndarray",
    metadata: List[dict],
    color_by: str,
    is_3d: bool = False
) -> Optional["go.Figure"]:
    """Create interactive Plotly scatter plot.

    Args:
        coords: Reduced coordinates (2D or 3D)
        metadata: List of metadata dictionaries
        color_by: Field to color points by
        is_3d: Whether to create 3D plot

    Returns:
        Plotly Figure object or None if visualization unavailable
    """
    if not VISUALIZATION_AVAILABLE:
        return None

    try:
        import plotly.graph_objects as go
        import plotly.express as px

        # Extract color values
        color_values = []
        hover_texts = []

        for i, meta in enumerate(metadata):
            # Get color value
            color_val = meta.get(color_by, "Unknown")
            if isinstance(color_val, (int, float)):
                color_values.append(color_val)
            else:
                color_values.append(str(color_val))

            # Create hover text
            hover_text = f"<b>{meta.get('id', 'Unknown')}</b><br>"
            hover_text += f"Source: {meta.get('sourcefile', 'Unknown')}<br>"
            hover_text += f"Page: {meta.get('page_number', 0)}<br>"
            hover_text += f"Tokens: {meta.get('token_count', 0)}<br>"
            hover_text += f"Content: {meta.get('content_preview', '')}"
            hover_texts.append(hover_text)

        # Create plot
        if is_3d:
            fig = go.Figure(data=[go.Scatter3d(
                x=coords[:, 0],
                y=coords[:, 1],
                z=coords[:, 2],
                mode='markers',
                marker=dict(
                    size=5,
                    color=color_values if isinstance(color_values[0], (int, float)) else None,
                    colorscale='Viridis' if isinstance(color_values[0], (int, float)) else None,
                    showscale=True,
                    colorbar=dict(title=color_by) if isinstance(color_values[0], (int, float)) else None
                ),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>'
            )])

            fig.update_layout(
                title=f"3D Embedding Visualization (colored by {color_by})",
                scene=dict(
                    xaxis_title="Dimension 1",
                    yaxis_title="Dimension 2",
                    zaxis_title="Dimension 3"
                ),
                height=700
            )
        else:
            fig = go.Figure(data=[go.Scatter(
                x=coords[:, 0],
                y=coords[:, 1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=color_values if isinstance(color_values[0], (int, float)) else None,
                    colorscale='Viridis' if isinstance(color_values[0], (int, float)) else None,
                    showscale=True,
                    colorbar=dict(title=color_by) if isinstance(color_values[0], (int, float)) else None
                ),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>'
            )])

            fig.update_layout(
                title=f"2D Embedding Visualization (colored by {color_by})",
                xaxis_title="Dimension 1",
                yaxis_title="Dimension 2",
                height=600
            )

        return fig

    except Exception as e:
        logger.error(f"Failed to create plot: {e}")
        return None


# =============================================================================
# Chunk Locking Helpers
# =============================================================================

def get_chunk_lock_state(chunk_id: str, artifacts_path: str, is_blob: bool = False) -> Optional[dict]:
    """Get lock state from chunk JSON artifact.

    Args:
        chunk_id: ID of the chunk
        artifacts_path: Path to artifacts directory or container name
        is_blob: Whether using blob storage

    Returns:
        Dictionary with locked, locked_by, locked_at, lock_reason or None
    """
    try:
        # For now, implement simple local file reading
        # In production, this would need to parse chunk_id and find artifact
        # This is a placeholder that should be enhanced
        import json
        from pathlib import Path

        if is_blob:
            # TODO: Implement blob storage reading
            logger.warning("Blob storage lock state reading not yet implemented")
            return None

        # Search for chunk JSON in artifacts directory
        artifacts_dir = Path(artifacts_path)
        if not artifacts_dir.exists():
            return None

        # Simple search - in production would parse chunk_id for exact path
        for chunk_file in artifacts_dir.rglob(f"*{chunk_id}*.json"):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Check if lock metadata exists
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        metadata = data['metadata']
                        if metadata.get('locked'):
                            return {
                                "locked": metadata.get('locked', False),
                                "locked_by": metadata.get('locked_by', ''),
                                "locked_at": metadata.get('locked_at', ''),
                                "lock_reason": metadata.get('lock_reason', '')
                            }
            except Exception as e:
                logger.warning(f"Failed to read chunk file {chunk_file}: {e}")
                continue

        return None

    except Exception as e:
        logger.error(f"Failed to get lock state: {e}")
        return None


def set_chunk_lock_state(
    chunk_id: str,
    locked: bool,
    locked_by: str,
    lock_reason: str,
    artifacts_path: str,
    is_blob: bool = False
) -> bool:
    """Update lock state in chunk artifact.

    Args:
        chunk_id: ID of the chunk
        locked: Whether to lock (True) or unlock (False)
        locked_by: User/system performing the lock
        lock_reason: Reason for locking
        artifacts_path: Path to artifacts directory or container name
        is_blob: Whether using blob storage

    Returns:
        True if successful, False otherwise
    """
    try:
        import json
        from pathlib import Path
        from datetime import datetime

        if is_blob:
            # TODO: Implement blob storage writing
            logger.warning("Blob storage lock state writing not yet implemented")
            return False

        # Search for chunk JSON in artifacts directory
        artifacts_dir = Path(artifacts_path)
        if not artifacts_dir.exists():
            logger.error(f"Artifacts directory not found: {artifacts_path}")
            return False

        # Find chunk file
        chunk_file = None
        for file in artifacts_dir.rglob(f"*{chunk_id}*.json"):
            chunk_file = file
            break

        if not chunk_file:
            logger.error(f"Chunk file not found for ID: {chunk_id}")
            return False

        # Read, modify, and write back
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure metadata dict exists
        if 'metadata' not in data:
            data['metadata'] = {}

        # Update lock fields
        if locked:
            data['metadata']['locked'] = True
            data['metadata']['locked_by'] = locked_by
            data['metadata']['locked_at'] = datetime.utcnow().isoformat() + 'Z'
            data['metadata']['lock_reason'] = lock_reason
        else:
            data['metadata']['locked'] = False
            data['metadata']['locked_by'] = ''
            data['metadata']['locked_at'] = ''
            data['metadata']['lock_reason'] = ''

        # Write back
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Updated lock state for chunk {chunk_id}: locked={locked}")
        return True

    except Exception as e:
        logger.error(f"Failed to set lock state: {e}")
        return False


def get_all_chunks_with_locks(artifacts_path: str, is_blob: bool = False) -> List[dict]:
    """Scan all chunk artifacts and collect lock states.

    Args:
        artifacts_path: Path to artifacts directory or container name
        is_blob: Whether using blob storage

    Returns:
        List of dictionaries with chunk_id, sourcefile, page, locked, locked_by, locked_at
    """
    try:
        import json
        from pathlib import Path

        if is_blob:
            # TODO: Implement blob storage scanning
            logger.warning("Blob storage scanning not yet implemented")
            return []

        artifacts_dir = Path(artifacts_path)
        if not artifacts_dir.exists():
            return []

        chunks = []

        # Search for all chunk JSON files
        for chunk_file in artifacts_dir.rglob("*.json"):
            try:
                # Skip non-chunk files
                if "manifest" in chunk_file.name.lower() or "status" in chunk_file.name.lower():
                    continue

                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract chunk info
                chunk_id = data.get('chunk_id', chunk_file.stem)
                metadata = data.get('metadata', {})

                chunks.append({
                    "chunk_id": chunk_id,
                    "sourcefile": metadata.get('sourcefile', 'Unknown'),
                    "page": metadata.get('page_number', 0),
                    "locked": metadata.get('locked', False),
                    "locked_by": metadata.get('locked_by', ''),
                    "locked_at": metadata.get('locked_at', ''),
                    "lock_reason": metadata.get('lock_reason', '')
                })

            except Exception as e:
                logger.warning(f"Failed to read chunk file {chunk_file}: {e}")
                continue

        return chunks

    except Exception as e:
        logger.error(f"Failed to get all chunks: {e}")
        return []


def bulk_lock_chunks(
    chunk_ids: List[str],
    locked_by: str,
    lock_reason: str,
    artifacts_path: str,
    is_blob: bool = False
) -> dict:
    """Lock multiple chunks in bulk.

    Args:
        chunk_ids: List of chunk IDs to lock
        locked_by: User/system performing the lock
        lock_reason: Reason for locking
        artifacts_path: Path to artifacts directory or container name
        is_blob: Whether using blob storage

    Returns:
        Dictionary with succeeded: int, failed: int, errors: List[str]
    """
    succeeded = 0
    failed = 0
    errors = []

    for chunk_id in chunk_ids:
        try:
            success = set_chunk_lock_state(
                chunk_id, True, locked_by, lock_reason, artifacts_path, is_blob
            )
            if success:
                succeeded += 1
            else:
                failed += 1
                errors.append(f"Failed to lock {chunk_id}")
        except Exception as e:
            failed += 1
            errors.append(f"Error locking {chunk_id}: {str(e)}")

    return {
        "succeeded": succeeded,
        "failed": failed,
        "errors": errors
    }


def bulk_unlock_chunks(
    chunk_ids: List[str],
    artifacts_path: str,
    is_blob: bool = False
) -> dict:
    """Unlock multiple chunks in bulk.

    Args:
        chunk_ids: List of chunk IDs to unlock
        artifacts_path: Path to artifacts directory or container name
        is_blob: Whether using blob storage

    Returns:
        Dictionary with succeeded: int, failed: int, errors: List[str]
    """
    succeeded = 0
    failed = 0
    errors = []

    for chunk_id in chunk_ids:
        try:
            success = set_chunk_lock_state(
                chunk_id, False, "", "", artifacts_path, is_blob
            )
            if success:
                succeeded += 1
            else:
                failed += 1
                errors.append(f"Failed to unlock {chunk_id}")
        except Exception as e:
            failed += 1
            errors.append(f"Error unlocking {chunk_id}: {str(e)}")

    return {
        "succeeded": succeeded,
        "failed": failed,
        "errors": errors
    }


__all__ = [
    # Configuration
    "log_queue",
    "token_encoder",
    # Feature flags
    "AZURE_STORAGE_AVAILABLE",
    "AZURE_SEARCH_AVAILABLE",
    "CHROMADB_AVAILABLE",
    "VISUALIZATION_AVAILABLE",
    "UMAP_AVAILABLE",
    # Constants
    "DEFAULT_MASKED_CHARS",
    "DEFAULT_CHUNK_LIMIT",
    "DEFAULT_MAX_SEARCH_RESULTS",
    "DEFAULT_CONTENT_PREVIEW_LENGTH",
    # Blob storage
    "get_blob_service_client",
    "list_blob_containers",
    "list_blobs_in_container",
    # Search
    "get_search_client",
    "search_documents_by_filename",
    "get_document_chunks",
    # ChromaDB
    "get_chromadb_client",
    "list_chromadb_collections",
    "get_collection_info",
    "get_collection_chunks",
    "get_chunk_details",
    # Visualization
    "get_embeddings_from_chromadb",
    "get_embeddings_from_azure_search",
    "reduce_embeddings_pca",
    "reduce_embeddings_tsne",
    "reduce_embeddings_umap",
    "create_embedding_plot",
    # Chunk locking
    "get_chunk_lock_state",
    "set_chunk_lock_state",
    "get_all_chunks_with_locks",
    "bulk_lock_chunks",
    "bulk_unlock_chunks",
    # Async
    "run_async",
    # Token counting
    "count_tokens",
    # Environment
    "mask_sensitive_value",
    "get_env_var_safe",
]
