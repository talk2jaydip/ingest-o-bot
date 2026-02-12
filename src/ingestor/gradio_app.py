"""Gradio UI for Document Indexing Pipeline.

A comprehensive web interface for running the document indexing pipeline with:
- Support for all configuration scenarios (azure_di, markitdown, hybrid)
- Real-time logging streaming
- Input/output path display
- Help system for environment variables
- Masked sensitive values
- Easy testing and configuration
"""

import asyncio
import os
import queue
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add parent directory to path to allow running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

import gradio as gr
import tiktoken
from dotenv import load_dotenv

# Load environment variables from default .env file
load_dotenv()

# Store the currently active env file path (global state)
_active_env_file: Optional[str] = None

from ingestor.config import (
    DocumentAction,
    InputMode,
    OfficeExtractorMode,
    PipelineConfig,
)
from ingestor.logging_utils import get_logger, setup_logging
from ingestor.pipeline import Pipeline
from ingestor.scenario_validator import (
    ScenarioValidator,
    ValidationResult,
    Scenario,
    validate_current_environment,
)

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

# Global log queue for real-time streaming
log_queue = queue.Queue()

# Logger
logger = get_logger(__name__)

# Token counter (same as used in chunker.py)
ENCODING_MODEL = "text-embedding-ada-002"
try:
    token_encoder = tiktoken.encoding_for_model(ENCODING_MODEL)
except Exception as e:
    logger.warning(f"Could not load tiktoken encoding: {e}. Token counts may be unavailable.")
    token_encoder = None


# =============================================================================
# Environment File Management
# =============================================================================

def list_env_files() -> list:
    """List all .env files in the envs/ directory.

    Returns:
        List of .env filenames with full paths
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        envs_dir = project_root / "envs"

        if not envs_dir.exists():
            logger.warning(f"envs directory not found at {envs_dir}")
            return []

        # Find all .env files (including .env.*.example files)
        env_files = []
        for file_path in envs_dir.glob("*.env*"):
            if file_path.is_file():
                env_files.append(str(file_path))

        # Sort by filename for easier browsing
        env_files.sort(key=lambda x: Path(x).name)

        return env_files

    except Exception as e:
        logger.error(f"Failed to list env files: {e}")
        return []


def get_env_file_display_name(file_path: str) -> str:
    """Get a friendly display name for an env file.

    Args:
        file_path: Full path to the env file

    Returns:
        User-friendly display name
    """
    if not file_path:
        return "None (using system environment)"
    return Path(file_path).name


def load_env_file(file_path: Optional[str] = None, override: bool = True) -> Tuple[bool, str]:
    """Load environment variables from a specific .env file.

    Args:
        file_path: Path to the .env file to load. If None, reloads the default .env
        override: Whether to override existing environment variables

    Returns:
        Tuple of (success: bool, message: str)
    """
    global _active_env_file

    try:
        if file_path:
            env_path = Path(file_path)
            if not env_path.exists():
                return False, f"❌ File not found: {file_path}"

            # Load the env file
            load_dotenv(env_path, override=override)
            _active_env_file = str(env_path)

            # Count loaded variables
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                var_count = len([line for line in lines if '=' in line])

            return True, f"✅ Loaded {var_count} variables from {env_path.name}"
        else:
            # Reload default .env
            project_root = Path(__file__).parent.parent.parent
            default_env = project_root / ".env"

            if default_env.exists():
                load_dotenv(default_env, override=override)
                _active_env_file = None
                return True, "✅ Reloaded default .env file"
            else:
                return False, "❌ No default .env file found"

    except Exception as e:
        logger.error(f"Failed to load env file: {e}")
        return False, f"❌ Error loading file: {str(e)}"


def get_active_env_file() -> str:
    """Get the currently active environment file.

    Returns:
        Display name of the active env file
    """
    global _active_env_file
    return get_env_file_display_name(_active_env_file)


def save_uploaded_env_file(file_obj) -> Tuple[bool, str, Optional[str]]:
    """Save an uploaded .env file to a temporary location and load it.

    Args:
        file_obj: Gradio file upload object

    Returns:
        Tuple of (success: bool, message: str, file_path: Optional[str])
    """
    try:
        if file_obj is None:
            return False, "❌ No file uploaded", None

        # Get the file path from Gradio's file object
        if hasattr(file_obj, 'name'):
            uploaded_path = file_obj.name
        else:
            uploaded_path = str(file_obj)

        # Verify it's a valid file
        upload_path = Path(uploaded_path)
        if not upload_path.exists():
            return False, f"❌ Uploaded file not found: {uploaded_path}", None

        # Load the uploaded file
        success, message = load_env_file(uploaded_path, override=True)

        if success:
            return True, f"✅ Loaded custom env file: {upload_path.name}", uploaded_path
        else:
            return False, message, None

    except Exception as e:
        logger.error(f"Failed to process uploaded env file: {e}")
        return False, f"❌ Error processing upload: {str(e)}", None


# =============================================================================
# Configuration Validation Functions
# =============================================================================

def validate_configuration(auto_validation: bool = False) -> Tuple[str, str, bool]:
    """Validate the current environment configuration.

    Args:
        auto_validation: Whether this is an automatic validation (affects messaging)

    Returns:
        Tuple of (validation_html: str, status_badge: str, is_valid: bool)
    """
    try:
        # Run validation
        result = validate_current_environment()

        # Build detailed HTML output
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; padding: 20px; background: white; border-radius: 5px;">
            <h3 style="color: {('#27ae60' if result.is_valid else '#e74c3c')}; margin-top: 0;">
                {'✅ Configuration Valid' if result.is_valid else '❌ Configuration Invalid'}
            </h3>
        """

        # Detected scenario
        if result.detected_scenario:
            scenario_name = result.detected_scenario.name.replace('_', ' ').title()
            html += f"""
            <div style="background: #e8f8f5; padding: 15px; border-left: 4px solid #27ae60; margin: 15px 0;">
                <strong>🎯 Detected Scenario:</strong> {scenario_name}
                <br/>
                <span style="color: #555;">{result.detected_scenario.description}</span>
            </div>
            """

        # Required variables
        if result.required_vars:
            html += "<h4 style='color: #2c3e50;'>📋 Required Variables:</h4><ul>"
            for var_name in result.required_vars:
                is_set = var_name in result.set_vars
                icon = "✅" if is_set else "❌"
                color = "#27ae60" if is_set else "#e74c3c"
                html += f"<li style='color: {color};'>{icon} <code>{var_name}</code></li>"
            html += "</ul>"

        # Optional variables
        if result.optional_vars:
            html += "<h4 style='color: #2c3e50;'>⚙️ Optional Variables:</h4><ul>"
            for var_name in result.optional_vars:
                is_set = var_name in result.set_vars
                icon = "✅" if is_set else "⚪"
                color = "#27ae60" if is_set else "#95a5a6"
                html += f"<li style='color: {color};'>{icon} <code>{var_name}</code></li>"
            html += "</ul>"

        # Missing required variables
        missing_required = set(result.required_vars) - set(result.set_vars)
        if missing_required:
            html += f"""
            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0;">
                <strong>⚠️ Missing Required Variables:</strong>
                <ul style="margin: 10px 0 0 0;">
            """
            for var_name in missing_required:
                html += f"<li><code>{var_name}</code></li>"
            html += "</ul></div>"

        # Warnings
        if result.warnings:
            html += "<h4 style='color: #f39c12;'>⚠️ Warnings:</h4><ul>"
            for warning in result.warnings:
                html += f"<li style='color: #f39c12;'>{warning}</li>"
            html += "</ul>"

        # Recommendations
        if result.recommendations:
            html += "<h4 style='color: #3498db;'>💡 Recommendations:</h4><ul>"
            for rec in result.recommendations:
                html += f"<li style='color: #555;'>{rec}</li>"
            html += "</ul>"

        html += "</div>"

        # Build status badge
        if result.is_valid:
            if result.warnings:
                status_badge = format_validation_badge(True, has_warnings=True)
            else:
                status_badge = format_validation_badge(True, has_warnings=False)
        else:
            status_badge = format_validation_badge(False)

        return html, status_badge, result.is_valid

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        error_html = f"""
        <div style="background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107;">
            <strong>⚠️ Validation Error:</strong><br/>
            {str(e)}
        </div>
        """
        return error_html, "⚠️ Validation Error", False


def format_validation_badge(is_valid: bool, has_warnings: bool = False) -> str:
    """Format validation status badge.

    Args:
        is_valid: Whether configuration is valid
        has_warnings: Whether there are warnings

    Returns:
        Formatted badge HTML
    """
    if is_valid:
        if has_warnings:
            return "<span style='background: #f39c12; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;'>⚠️ Valid (with warnings)</span>"
        else:
            return "<span style='background: #27ae60; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;'>✅ Configuration Valid</span>"
    else:
        return "<span style='background: #e74c3c; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;'>❌ Configuration Invalid</span>"


# =============================================================================
# Azure Blob Storage Helper Functions
# =============================================================================

def get_blob_service_client():
    """Get Azure Blob Service Client from environment."""
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


def list_blob_containers():
    """List all blob containers in the storage account."""
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


# =============================================================================
# Azure AI Search Helper Functions
# =============================================================================

def get_search_client():
    """Get Azure Search client from environment variables."""
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


def search_documents_by_filename(filename_pattern: str, max_results: int = 1000):
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
        # Otherwise, search in content for the pattern
        if filename_pattern == "*" or not filename_pattern.strip():
            # Get all documents - no select to avoid field name issues
            results = client.search(
                search_text="",
                top=max_results
            )
        else:
            # Convert glob pattern: remove asterisks for search
            # e.g., "ARCHITECTURE*" -> "ARCHITECTURE"
            search_term = filename_pattern.replace("*", "").strip()

            if search_term:
                # Search in content for the term - no select parameter
                results = client.search(
                    search_text=search_term,
                    top=max_results
                )
            else:
                # Empty search term, get all - no select parameter
                results = client.search(
                    search_text="",
                    top=max_results
                )

        # Group documents by ID (use id field as document identifier)
        documents = {}
        for result in results:
            # Try various field names for filename - THIS is our grouping key
            filename = None
            for file_field in ["sourcefile", "source_file", "filename", "file_name", "title"]:
                if file_field in result:
                    filename = result.get(file_field)
                    if filename:
                        break

            if not filename:
                # Try to get from ID if it looks like a filename
                doc_id = result.get("id", "")
                if doc_id and ("." in doc_id or "pdf" in doc_id.lower()):
                    filename = doc_id
                else:
                    filename = "Unknown"

            # If searching with pattern, check if filename matches
            if filename_pattern != "*" and filename_pattern.strip():
                pattern_lower = filename_pattern.lower().replace("*", "")
                filename_lower = filename.lower()
                if pattern_lower and pattern_lower not in filename_lower:
                    continue  # Skip non-matching files

            # Group by FILENAME (not ID) - all chunks with same filename go together
            if filename not in documents:
                documents[filename] = {
                    "id": filename,  # Use filename as document ID
                    "filename": filename,
                    "category": result.get("category", "") or result.get("type", ""),
                    "chunk_count": 0,
                    "chunks": []
                }

            # Count chunks (each result is a chunk from this document)
            documents[filename]["chunk_count"] += 1

        return list(documents.values())

    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def get_document_chunks(doc_id: str):
    """Get all chunks for a specific document.

    Args:
        doc_id: The document ID (filename or identifier)

    Returns:
        List of chunks sorted by page number
    """
    client = get_search_client()
    if not client:
        return []

    try:
        # Search for the document by ID/filename in content
        # Don't use select or filter to avoid field name issues
        results = client.search(
            search_text=doc_id,
            top=1000
        )

        # Get all results
        all_results = list(results)

        # Filter results to only those matching this document
        # Check various filename fields
        chunks = []
        for result in all_results:
            # Check if this result belongs to our document
            is_match = False

            # Try various field names
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
            chunk_id = None
            for chunk_field in ["chunk_id", "chunkId", "id"]:
                if chunk_field in result:
                    chunk_id = result.get(chunk_field)
                    if chunk_id:
                        break

            if not chunk_id:
                chunk_id = f"chunk_{len(chunks)}"

            # Get sourcepage
            sourcepage = None
            for page_field in ["sourcepage", "source_page", "sourcePage"]:
                if page_field in result:
                    sourcepage = result.get(page_field)
                    if sourcepage:
                        break

            if not sourcepage:
                sourcepage = f"page_{page_num + 1}"

            # Build comprehensive chunk metadata
            chunk_data = {
                "id": result.get("id", chunk_id),
                "chunk_id": chunk_id,
                "page_num": page_num,
                "content": result.get("content", ""),
                "sourcefile": doc_id,
                "sourcepage": sourcepage,
                "category": result.get("category", "")
            }

            # Add metadata about content type (table, image, text, etc.)
            # Check various field names that might indicate content type
            for type_field in ["content_type", "type", "chunk_type", "element_type"]:
                if type_field in result:
                    chunk_data["content_type"] = result.get(type_field)
                    break

            # Check for table indicators
            for table_field in ["is_table", "has_table", "table", "tables"]:
                if table_field in result:
                    chunk_data["has_table"] = result.get(table_field)
                    break

            # Check for image indicators
            for image_field in ["is_image", "has_image", "image", "images", "figures"]:
                if image_field in result:
                    chunk_data["has_image"] = result.get(image_field)
                    break

            # Add any additional metadata fields that exist
            metadata_fields = ["url", "metadata", "tags", "title"]
            for meta_field in metadata_fields:
                if meta_field in result:
                    chunk_data[meta_field] = result.get(meta_field)

            chunks.append(chunk_data)

        # Sort by page_num
        chunks.sort(key=lambda x: x["page_num"])

        return chunks

    except Exception as e:
        logger.error(f"Failed to get document chunks: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def get_index_schema():
    """Get the actual schema of the index by querying a sample document.

    Returns:
        List of field names available in the index
    """
    try:
        client = get_search_client()
        if not client:
            return []

        # Get one document without specifying select fields
        results = client.search(search_text="", top=1)
        results_list = list(results)

        if results_list:
            # Return all field names from the first document
            return list(results_list[0].keys())

        return []
    except Exception as e:
        logger.error(f"Failed to get index schema: {e}")
        return []


def test_search_connection():
    """Test connection to Azure AI Search.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        client = get_search_client()
        if not client:
            return False, "❌ Search client not configured. Check AZURE_SEARCH_SERVICE, AZURE_SEARCH_INDEX, and AZURE_SEARCH_KEY."

        # Get index schema first
        fields = get_index_schema()

        if not fields:
            return False, "❌ Could not retrieve index schema. Index might be empty."

        # Try to get document count
        results = client.search(search_text="", top=10)
        results_list = list(results)
        count = len(results_list)

        index_name = os.getenv("AZURE_SEARCH_INDEX", "unknown")
        search_service = os.getenv("AZURE_SEARCH_SERVICE", "unknown")

        # Show available fields
        sample_info = f"\n📋 Available fields ({len(fields)}): {', '.join(fields)}"

        # Show sample values for key fields
        if count > 0:
            sample = results_list[0]

            # Check for various filename/document identifier fields
            for field in ["sourcefile", "source_file", "filename", "file_name", "title", "id"]:
                if field in sample:
                    value = sample.get(field, "N/A")
                    if value and value != "N/A":
                        sample_info += f"\n📄 Sample {field}: {value}"
                        break

        return True, f"✅ Connected to index '{index_name}' on service '{search_service}'\n📊 Found {count}+ documents{sample_info}"

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Connection test failed: {error_details}")
        return False, f"❌ Connection failed: {str(e)}"


def get_current_config_display():
    """Get current configuration display from environment."""
    config_info = {
        "index_name": os.getenv("AZURE_SEARCH_INDEX", "Not configured"),
        "search_service": os.getenv("AZURE_SEARCH_SERVICE", "Not configured"),
        "storage_account": os.getenv("AZURE_STORAGE_ACCOUNT", "Not configured"),
        "input_mode": os.getenv("AZURE_INPUT_MODE", "local"),
        "extractor_mode": os.getenv("AZURE_OFFICE_EXTRACTOR_MODE", "hybrid"),
        "local_glob": os.getenv("AZURE_LOCAL_GLOB", ""),
        "blob_container_in": os.getenv("AZURE_BLOB_CONTAINER_IN", ""),
        "artifacts_dir": os.getenv("AZURE_ARTIFACTS_DIR", ""),
    }
    return config_info


# =============================================================================
# Configuration Help System
# =============================================================================

@dataclass
class EnvVarHelp:
    """Help information for environment variables."""
    name: str
    description: str
    required: bool
    sensitive: bool
    default: Optional[str] = None
    example: Optional[str] = None
    category: str = "General"


ENV_HELP_DATA = [
    # Azure Credentials
    EnvVarHelp(
        "AZURE_TENANT_ID",
        "Azure AD Tenant ID for service principal authentication",
        required=False,
        sensitive=True,
        example="b5b8b483-5597-4ae7-8e27-fcc464a3b584",
        category="Azure Credentials"
    ),
    EnvVarHelp(
        "AZURE_CLIENT_ID",
        "Azure AD Client ID (Application ID) for service principal",
        required=False,
        sensitive=True,
        example="d0e06358-47d7-480a-b576-cdb4c30593a8",
        category="Azure Credentials"
    ),
    EnvVarHelp(
        "AZURE_CLIENT_SECRET",
        "Azure AD Client Secret for service principal authentication",
        required=False,
        sensitive=True,
        example="Q2Y8Q~...SecretValue...",
        category="Azure Credentials"
    ),

    # Key Vault
    EnvVarHelp(
        "KEY_VAULT_URI",
        "Azure Key Vault URI for storing secrets (optional)",
        required=False,
        sensitive=False,
        example="https://mykeyvault.vault.azure.net/",
        category="Key Vault"
    ),

    # Document Intelligence
    EnvVarHelp(
        "AZURE_DOC_INT_ENDPOINT",
        "Azure Document Intelligence endpoint for PDF/Office document processing",
        required=True,
        sensitive=False,
        example="https://mydocint.cognitiveservices.azure.com/",
        category="Document Intelligence"
    ),
    EnvVarHelp(
        "AZURE_DOC_INT_KEY",
        "Azure Document Intelligence API key",
        required=True,
        sensitive=True,
        example="ffa403f9...key...",
        category="Document Intelligence"
    ),
    EnvVarHelp(
        "AZURE_DI_MAX_CONCURRENCY",
        "Maximum concurrent requests to Document Intelligence",
        required=False,
        sensitive=False,
        default="3",
        example="3",
        category="Document Intelligence"
    ),

    # Azure AI Search
    EnvVarHelp(
        "AZURE_SEARCH_SERVICE",
        "Azure AI Search service name (without .search.windows.net)",
        required=True,
        sensitive=False,
        example="mysearchservice",
        category="Azure AI Search"
    ),
    EnvVarHelp(
        "AZURE_SEARCH_KEY",
        "Azure AI Search admin API key",
        required=True,
        sensitive=True,
        example="tfCipsmo4jZo...key...",
        category="Azure AI Search"
    ),
    EnvVarHelp(
        "AZURE_SEARCH_INDEX",
        "Azure AI Search index name (must match deployed index)",
        required=True,
        sensitive=False,
        example="myproject-index",
        category="Azure AI Search"
    ),

    # Azure OpenAI
    EnvVarHelp(
        "AZURE_OPENAI_ENDPOINT",
        "Azure OpenAI endpoint for embeddings and chat",
        required=True,
        sensitive=False,
        example="https://myopenai.openai.azure.com/",
        category="Azure OpenAI"
    ),
    EnvVarHelp(
        "AZURE_OPENAI_KEY",
        "Azure OpenAI API key",
        required=True,
        sensitive=True,
        example="bccd5ce9...key...",
        category="Azure OpenAI"
    ),
    EnvVarHelp(
        "AZURE_OPENAI_API_VERSION",
        "Azure OpenAI API version",
        required=False,
        sensitive=False,
        default="2024-12-01-preview",
        example="2024-12-01-preview",
        category="Azure OpenAI"
    ),
    EnvVarHelp(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "Deployment name for embedding model",
        required=True,
        sensitive=False,
        example="text-embedding-ada-002",
        category="Azure OpenAI"
    ),
    EnvVarHelp(
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        "Deployment name for chat model (figure descriptions)",
        required=False,
        sensitive=False,
        example="gpt-4o-mini",
        category="Azure OpenAI"
    ),

    # Storage
    EnvVarHelp(
        "AZURE_STORAGE_ACCOUNT",
        "Azure Storage account name for blob storage",
        required=False,
        sensitive=False,
        example="mystorageaccount",
        category="Azure Storage"
    ),
    EnvVarHelp(
        "AZURE_STORAGE_ACCOUNT_KEY",
        "Azure Storage account access key",
        required=False,
        sensitive=True,
        example="u73g8veJY5...key...",
        category="Azure Storage"
    ),

    # Input Configuration
    EnvVarHelp(
        "AZURE_INPUT_MODE",
        "Input source mode: 'local' (filesystem) or 'blob' (Azure Storage)",
        required=True,
        sensitive=False,
        default="local",
        example="local",
        category="Input/Output"
    ),
    EnvVarHelp(
        "AZURE_LOCAL_GLOB",
        "Glob pattern for local file input (when input_mode=local)",
        required=False,
        sensitive=False,
        example="./documents/*.pdf",
        category="Input/Output"
    ),
    EnvVarHelp(
        "AZURE_BLOB_CONTAINER_IN",
        "Input blob container name (when input_mode=blob)",
        required=False,
        sensitive=False,
        example="myproject-index-input",
        category="Input/Output"
    ),
    EnvVarHelp(
        "AZURE_ARTIFACTS_DIR",
        "Local directory for artifacts (overrides input_mode for output)",
        required=False,
        sensitive=False,
        example="./test_artifacts",
        category="Input/Output"
    ),
    EnvVarHelp(
        "AZURE_STORE_ARTIFACTS_TO_BLOB",
        "Force blob storage for artifacts (true/false)",
        required=False,
        sensitive=False,
        default="false",
        example="true",
        category="Input/Output"
    ),

    # Document Action
    EnvVarHelp(
        "AZURE_DOCUMENT_ACTION",
        "Action: 'add' (index documents), 'remove' (remove specific), 'removeall' (remove all)",
        required=False,
        sensitive=False,
        default="add",
        example="add",
        category="Processing"
    ),

    # Office Processing
    EnvVarHelp(
        "AZURE_OFFICE_EXTRACTOR_MODE",
        "Office extraction mode: 'azure_di', 'markitdown', or 'hybrid' (recommended)",
        required=False,
        sensitive=False,
        default="hybrid",
        example="hybrid",
        category="Office Processing"
    ),
    EnvVarHelp(
        "AZURE_OFFICE_OFFLINE_FALLBACK",
        "Enable MarkItDown fallback in hybrid/azure_di mode (true/false)",
        required=False,
        sensitive=False,
        default="true",
        example="true",
        category="Office Processing"
    ),
    EnvVarHelp(
        "AZURE_OFFICE_MAX_FILE_SIZE_MB",
        "Maximum file size in MB for Office documents",
        required=False,
        sensitive=False,
        default="100",
        example="100",
        category="Office Processing"
    ),
    EnvVarHelp(
        "AZURE_OFFICE_EQUATION_EXTRACTION",
        "Enable LaTeX equation extraction (requires premium tier)",
        required=False,
        sensitive=False,
        default="false",
        example="true",
        category="Office Processing"
    ),
    EnvVarHelp(
        "AZURE_OFFICE_VERBOSE",
        "Enable verbose logging for Office processing",
        required=False,
        sensitive=False,
        default="false",
        example="true",
        category="Office Processing"
    ),

    # Performance
    EnvVarHelp(
        "AZURE_MAX_WORKERS",
        "Maximum parallel workers for document processing",
        required=False,
        sensitive=False,
        default="4",
        example="4",
        category="Performance"
    ),
    EnvVarHelp(
        "AZURE_EMBED_BATCH_SIZE",
        "Batch size for embedding generation",
        required=False,
        sensitive=False,
        default="128",
        example="128",
        category="Performance"
    ),
    EnvVarHelp(
        "AZURE_UPLOAD_BATCH_SIZE",
        "Batch size for uploading to search index",
        required=False,
        sensitive=False,
        default="500",
        example="500",
        category="Performance"
    ),
]


def mask_sensitive_value(value: str, visible_chars: int = 8) -> str:
    """Mask sensitive values showing only first few characters."""
    if not value or len(value) <= visible_chars:
        return "*" * 8
    return f"{value[:visible_chars]}...{'*' * 8}"


def get_env_status() -> Dict[str, Dict]:
    """Get current environment variable status with masking."""
    status = {}

    for env_help in ENV_HELP_DATA:
        value = os.getenv(env_help.name)

        if value:
            display_value = mask_sensitive_value(value) if env_help.sensitive else value
            status[env_help.name] = {
                "set": True,
                "value": display_value,
                "masked": env_help.sensitive,
                "required": env_help.required,
                "category": env_help.category,
            }
        else:
            status[env_help.name] = {
                "set": False,
                "value": env_help.default or "Not set",
                "masked": False,
                "required": env_help.required,
                "category": env_help.category,
            }

    return status


def generate_env_help_html() -> str:
    """Generate HTML help documentation for environment variables."""
    # Group by category
    categories = {}
    for env_help in ENV_HELP_DATA:
        if env_help.category not in categories:
            categories[env_help.category] = []
        categories[env_help.category].append(env_help)

    html = """
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
            📚 Environment Variables Guide
        </h2>
    """

    for category, envs in categories.items():
        html += f"""
        <div style="margin-top: 30px;">
            <h3 style="color: #34495e; background: linear-gradient(90deg, #ecf0f1 0%, transparent 100%);
                       padding: 10px; border-left: 4px solid #3498db;">
                {category}
            </h3>
        """

        for env in envs:
            required_badge = (
                '<span style="background: #e74c3c; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px; margin-left: 10px;">REQUIRED</span>'
                if env.required else
                '<span style="background: #95a5a6; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px; margin-left: 10px;">OPTIONAL</span>'
            )

            sensitive_badge = (
                '<span style="background: #f39c12; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px; margin-left: 5px;">🔒 SENSITIVE</span>'
                if env.sensitive else ''
            )

            default_text = (
                f'<br><strong>Default:</strong> <code>{env.default}</code>'
                if env.default else ''
            )

            example_text = (
                f'<br><strong>Example:</strong> <code>{env.example}</code>'
                if env.example else ''
            )

            html += f"""
            <div style="background: white; border: 1px solid #ddd; border-radius: 5px;
                        padding: 15px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 16px; font-weight: bold; color: #2c3e50;">
                    <code>{env.name}</code>
                    {required_badge}
                    {sensitive_badge}
                </div>
                <div style="margin-top: 8px; color: #555; line-height: 1.6;">
                    {env.description}
                    {default_text}
                    {example_text}
                </div>
            </div>
            """

        html += "</div>"

    html += "</div>"
    return html


def generate_env_status_html() -> str:
    """Generate HTML display of current environment status."""
    status = get_env_status()

    # Group by category
    categories = {}
    for var_name, var_info in status.items():
        cat = var_info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((var_name, var_info))

    # Get active env file
    active_env = get_active_env_file()

    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
            ⚙️ Current Configuration Status
        </h2>

        <div style="background: #e8f8f5; border-left: 4px solid #27ae60; padding: 15px; margin: 15px 0; border-radius: 3px;">
            <div style="display: flex; align-items: center;">
                <span style="font-weight: bold; color: #2c3e50; margin-right: 10px;">📂 Active Environment File:</span>
                <span style="font-family: 'Courier New', monospace; color: #27ae60; font-weight: bold;">{active_env}</span>
            </div>
        </div>
    """

    for category, vars_list in categories.items():
        html += f"""
        <div style="margin-top: 25px;">
            <h3 style="color: #34495e; background: linear-gradient(90deg, #e8f8f5 0%, transparent 100%);
                       padding: 10px; border-left: 4px solid #27ae60;">
                {category}
            </h3>
        """

        for var_name, var_info in vars_list:
            if var_info["set"]:
                status_icon = "✅"
                status_color = "#27ae60"
                status_text = "SET"
            elif var_info["required"]:
                status_icon = "❌"
                status_color = "#e74c3c"
                status_text = "MISSING (REQUIRED)"
            else:
                status_icon = "⚪"
                status_color = "#95a5a6"
                status_text = "NOT SET (OPTIONAL)"

            masked_note = " 🔒" if var_info["masked"] else ""

            html += f"""
            <div style="background: white; border-left: 4px solid {status_color};
                        padding: 12px 15px; margin: 8px 0; border-radius: 3px;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.08);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="font-family: 'Courier New', monospace; font-weight: bold;
                                     color: #2c3e50;">{var_name}</span>
                        {masked_note}
                    </div>
                    <span style="background: {status_color}; color: white; padding: 3px 10px;
                                 border-radius: 3px; font-size: 11px; font-weight: bold;">
                        {status_icon} {status_text}
                    </span>
                </div>
                <div style="margin-top: 5px; color: #555; font-family: 'Courier New', monospace;
                           font-size: 13px;">
                    {var_info["value"]}
                </div>
            </div>
            """

        html += "</div>"

    html += "</div>"
    return html


# =============================================================================
# Scenario Templates
# =============================================================================

SCENARIO_TEMPLATES = {
    "Scenario 1: Azure DI Only": {
        "description": "Best quality with Azure Document Intelligence. DOC support via fallback.",
        "AZURE_OFFICE_EXTRACTOR_MODE": "azure_di",
        "AZURE_OFFICE_OFFLINE_FALLBACK": "true",
        "AZURE_INPUT_MODE": "local",
        "notes": "Requires: Azure DI credentials, MarkItDown for DOC support"
    },
    "Scenario 2: MarkItDown Only (Offline)": {
        "description": "Fully offline processing. No Azure services required for extraction.",
        "AZURE_OFFICE_EXTRACTOR_MODE": "markitdown",
        "AZURE_INPUT_MODE": "local",
        "notes": "Requires: MarkItDown installed (pip install markitdown)"
    },
    "Scenario 3: Hybrid Mode (Recommended)": {
        "description": "Azure DI first, automatic fallback. Maximum reliability.",
        "AZURE_OFFICE_EXTRACTOR_MODE": "hybrid",
        "AZURE_OFFICE_OFFLINE_FALLBACK": "true",
        "AZURE_INPUT_MODE": "local",
        "notes": "Recommended for production. Graceful degradation if Azure DI fails."
    },
    "Scenario 4: Blob Input → Blob Output": {
        "description": "Production mode. Read from blob, write to blob.",
        "AZURE_INPUT_MODE": "blob",
        "AZURE_OFFICE_EXTRACTOR_MODE": "hybrid",
        "AZURE_STORE_ARTIFACTS_TO_BLOB": "true",
        "notes": "Requires: Storage account, input container with files uploaded"
    },
    "Scenario 5: Local Input → Blob Output": {
        "description": "Test locally but store artifacts in blob storage.",
        "AZURE_INPUT_MODE": "local",
        "AZURE_OFFICE_EXTRACTOR_MODE": "hybrid",
        "AZURE_STORE_ARTIFACTS_TO_BLOB": "true",
        "notes": "Useful for testing with local files before production deployment"
    },
}


# =============================================================================
# Logging Capture
# =============================================================================

import logging
import io


class QueueHandler(logging.Handler):
    """Custom logging handler that writes to a queue."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """Emit a log record to the queue."""
        try:
            msg = self.format(record)
            self.log_queue.put(msg + "\n")
        except Exception:
            self.handleError(record)


class StreamToQueue(io.StringIO):
    """Redirect stdout/stderr to queue."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def write(self, message):
        """Write message to queue."""
        if message and message.strip():
            self.log_queue.put(message)

    def flush(self):
        """Flush (no-op for queue)."""
        pass


# =============================================================================
# Pipeline Execution
# =============================================================================

async def run_pipeline_async(
    input_mode: str,
    local_glob: str,
    blob_container: str,
    extractor_mode: str,
    offline_fallback: bool,
    document_action: str,
    max_workers: int,
    setup_index: bool,
    verbose: bool,
) -> Tuple[str, str]:
    """Run the indexing pipeline asynchronously."""

    # Save original stdout/stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        # Clear log queue
        while not log_queue.empty():
            log_queue.get_nowait()

        # Set up logging to capture to queue (don't call setup_logging as it overwrites stdout!)
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()

        # Configure ingestor logger specifically
        app_logger = logging.getLogger("ingestor")
        app_logger.setLevel(logging.DEBUG)
        app_logger.handlers.clear()

        # Add queue handler to both loggers
        queue_handler = QueueHandler(log_queue)
        queue_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')
        queue_handler.setFormatter(formatter)
        root_logger.addHandler(queue_handler)
        app_logger.addHandler(queue_handler)

        # Now redirect stdout/stderr to queue (AFTER setting up logging)
        sys.stdout = StreamToQueue(log_queue)
        sys.stderr = StreamToQueue(log_queue)

        # Override environment variables with UI selections
        os.environ["AZURE_INPUT_MODE"] = input_mode
        if input_mode == "local" and local_glob:
            os.environ["AZURE_LOCAL_GLOB"] = local_glob
        elif input_mode == "blob" and blob_container:
            os.environ["AZURE_BLOB_CONTAINER_IN"] = blob_container

        os.environ["AZURE_OFFICE_EXTRACTOR_MODE"] = extractor_mode
        os.environ["AZURE_OFFICE_OFFLINE_FALLBACK"] = str(offline_fallback).lower()
        os.environ["AZURE_DOCUMENT_ACTION"] = document_action
        os.environ["AZURE_MAX_WORKERS"] = str(max_workers)
        os.environ["AZURE_OFFICE_VERBOSE"] = str(verbose).lower()

        print(f"\n{'='*80}")
        print(f"🚀 Starting Document Indexing Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        print(f"📋 Configuration:")
        print(f"   Input Mode: {input_mode}")
        if input_mode == "local":
            print(f"   Local Glob: {local_glob}")
        else:
            print(f"   Blob Container: {blob_container}")
        print(f"   Extractor Mode: {extractor_mode}")
        print(f"   Offline Fallback: {offline_fallback}")
        print(f"   Document Action: {document_action}")
        print(f"   Max Workers: {max_workers}")
        print(f"   Setup Index: {setup_index}\n")

        # Load configuration
        config = PipelineConfig.from_env()

        # Display paths
        print(f"📂 Paths:")
        if config.input.mode == InputMode.LOCAL:
            print(f"   Input: {config.input.local_glob}")
        else:
            print(f"   Input: blob://{config.input.blob_container_in}")

        if config.artifacts.local_dir:
            print(f"   Output: {config.artifacts.local_dir}")
        else:
            print(f"   Output: blob://{config.artifacts.blob_container_prefix}-*")
        print()

        # Create pipeline
        pipeline = Pipeline(config)

        # Setup index if requested
        if setup_index:
            print("🔧 Setting up search index...")
            await pipeline.setup_index()
            print("✅ Index setup complete\n")

        # Run ingestion
        print("📄 Starting document ingestion...\n")
        await pipeline.run()

        print(f"\n{'='*80}")
        print(f"✅ Pipeline completed successfully! - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")

        return "✅ Success", "Pipeline completed successfully!"

    except Exception as e:
        error_msg = f"❌ Pipeline failed: {str(e)}"
        print(f"\n{error_msg}")
        logger.exception("Pipeline execution failed")
        import traceback
        traceback.print_exc()
        return "❌ Error", error_msg

    finally:
        # Restore original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        # Remove queue handlers from both loggers
        for logger_name in [None, "ingestor"]:
            logger = logging.getLogger(logger_name)
            handlers_to_remove = [h for h in logger.handlers if isinstance(h, QueueHandler)]
            for handler in handlers_to_remove:
                logger.removeHandler(handler)


def run_pipeline_sync(*args, **kwargs):
    """Synchronous wrapper for pipeline execution with real-time log streaming."""
    import threading

    # Storage for pipeline result
    result = {"status": None, "message": None, "error": None}

    def run_pipeline_thread():
        """Run pipeline in separate thread."""
        try:
            status, message = asyncio.run(run_pipeline_async(*args, **kwargs))
            result["status"] = status
            result["message"] = message
        except Exception as e:
            result["status"] = "❌ Error"
            result["message"] = str(e)
            result["error"] = e

    # Start pipeline in background thread
    pipeline_thread = threading.Thread(target=run_pipeline_thread, daemon=True)
    pipeline_thread.start()

    # Stream logs in real-time
    accumulated_logs = []
    last_status = "🔄 Running..."

    while pipeline_thread.is_alive() or not log_queue.empty():
        try:
            # Try to get log from queue with timeout
            log = log_queue.get(timeout=0.1)
            accumulated_logs.append(log)

            # Yield current status and accumulated logs
            log_text = "".join(accumulated_logs)
            yield last_status, log_text

        except queue.Empty:
            # No new logs, just yield current state
            if accumulated_logs:
                log_text = "".join(accumulated_logs)
                yield last_status, log_text
            continue

    # Wait for thread to complete
    pipeline_thread.join(timeout=1.0)

    # Collect any remaining logs
    while not log_queue.empty():
        try:
            log = log_queue.get_nowait()
            accumulated_logs.append(log)
        except queue.Empty:
            break

    # Final yield with completion status
    final_status = result["status"] or "✅ Completed"
    log_text = "".join(accumulated_logs)

    if not log_text.strip():
        log_text = result["message"] or "Pipeline completed but no logs captured."

    yield final_status, log_text


# =============================================================================
# Gradio UI
# =============================================================================

def create_ui():
    """Create the Gradio interface."""

    with gr.Blocks(title="Document Indexing Pipeline") as demo:

        gr.Markdown("""
        # 🚀 Document Indexing Pipeline
        ### Comprehensive UI for Azure AI Search Document Ingestion

        Upload and process documents with real-time logging, multiple scenarios, and full configuration support.
        """)

        with gr.Tabs() as tabs:

            # =================================================================
            # Tab 1: Run Pipeline
            # =================================================================
            with gr.Tab("🎯 Run Pipeline"):
                # Current Configuration Display
                config_display = get_current_config_display()
                gr.Markdown(f"""
                ### 📋 Current Configuration
                **Search Index**: `{config_display['index_name']}`  |  **Search Service**: `{config_display['search_service']}`  |  **Storage Account**: `{config_display['storage_account']}`
                """)

                gr.Markdown("---")

                # =================================================================
                # Environment Configuration Section (NEW)
                # =================================================================
                gr.Markdown("### 🔧 Environment Configuration")
                gr.Markdown("Load environment variables from different .env files to test various scenarios without copying files.")

                with gr.Row():
                    with gr.Column(scale=3):
                        # Get list of env files
                        env_file_list = list_env_files()
                        env_file_choices = ["None (use system environment)"] + [get_env_file_display_name(f) for f in env_file_list]

                        env_file_dropdown = gr.Dropdown(
                            choices=env_file_choices,
                            label="📂 Select Environment File",
                            value="None (use system environment)",
                            info="Choose a .env file from envs/ directory",
                            interactive=True
                        )

                    with gr.Column(scale=2):
                        env_file_upload = gr.File(
                            label="📤 Upload Custom .env File",
                            file_types=[".env"],
                            type="filepath",
                            interactive=True
                        )

                with gr.Row():
                    env_load_button = gr.Button("🔄 Load Selected Environment", variant="primary", size="sm")
                    env_reload_button = gr.Button("♻️ Reload Current", variant="secondary", size="sm")
                    env_refresh_button = gr.Button("🔍 Refresh File List", variant="secondary", size="sm")

                with gr.Row():
                    env_status_display = gr.Markdown(
                        f"**Active Environment**: {get_active_env_file()}",
                        elem_classes=["env-status"]
                    )

                env_message_display = gr.Markdown("")

                gr.Markdown("---")

                # =================================================================
                # Configuration Validation Section (NEW)
                # =================================================================
                gr.Markdown("### ✅ Configuration Validation")
                gr.Markdown("Validate your environment configuration before running the pipeline to catch errors early.")

                with gr.Row():
                    with gr.Column(scale=2):
                        validate_btn = gr.Button("🔍 Validate Configuration", variant="primary", size="lg")
                    with gr.Column(scale=1):
                        auto_validate_checkbox = gr.Checkbox(
                            label="Auto-validate on env file change",
                            value=True,
                            info="Automatically run validation when loading a new environment file"
                        )

                with gr.Row():
                    validation_status_badge = gr.Markdown(
                        "<span style='color: #666;'>Click 'Validate Configuration' to check your setup</span>",
                        elem_classes=["validation-badge"]
                    )

                # Collapsible validation results
                with gr.Accordion("Validation Results", open=False) as validation_accordion:
                    validation_results = gr.HTML(
                        value="<p style='color: #666; padding: 20px; text-align: center;'>No validation run yet. Click 'Validate Configuration' to start.</p>",
                        elem_classes=["validation-results"]
                    )

                gr.Markdown("---")

                # Scenario Selection
                with gr.Row():
                    scenario_dropdown = gr.Dropdown(
                        choices=list(SCENARIO_TEMPLATES.keys()),
                        label="📋 Quick Scenario Templates",
                        value="Scenario 3: Hybrid Mode (Recommended)",
                        info="Select a pre-configured scenario (auto-loads on selection)"
                    )
                scenario_info = gr.Markdown()

                gr.Markdown("---")
                gr.Markdown("### ⚙️ Pipeline Configuration")

                with gr.Row():
                    # Left Column: Input Configuration
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📥 Input Source")

                        input_mode = gr.Radio(
                            choices=["local", "blob"],
                            label="Input Mode",
                            value=config_display['input_mode'],
                            info="Where to read documents from"
                        )

                        # Local input options
                        with gr.Group(visible=(config_display['input_mode'] == 'local')) as local_group:
                            gr.Markdown("**📁 How do you want to select files?**")

                            local_path_type = gr.Radio(
                                choices=["📤 Browse Files", "📂 Folder Path", "🔍 Advanced Pattern"],
                                label="Selection Method",
                                value="📤 Browse Files",
                                info="Choose the easiest method for you"
                            )

                            # File upload with prominent browse button
                            with gr.Group(visible=True) as local_file_group:
                                gr.Markdown("**Click the box below to browse and select your files** 👇")
                                local_files = gr.File(
                                    label="📂 BROWSE FILES",
                                    file_count="multiple",
                                    file_types=[".pdf", ".docx", ".pptx", ".doc", ".txt", ".md"],
                                    type="filepath",
                                    interactive=True,
                                    height=150
                                )
                                gr.Markdown("""
                                💡 **Tips:**
                                - Click the box above to open file browser
                                - Select multiple files (Ctrl+Click or Cmd+Click)
                                - Drag & drop files onto the box
                                - Supported: PDF, DOCX, PPTX, DOC, TXT, MD
                                """)

                            # Directory path with clear instructions
                            with gr.Group(visible=False) as local_dir_group:
                                gr.Markdown("**Enter the path to your folder:**")
                                local_dir = gr.Textbox(
                                    label="📂 Folder Path",
                                    placeholder="Example: C:\\Users\\Documents or ./test_file",
                                    info="Copy and paste the full path to your folder",
                                    lines=1,
                                    scale=4
                                )

                                gr.Markdown("**Which file types do you want to process?**")
                                local_dir_patterns = gr.CheckboxGroup(
                                    choices=[".pdf", ".docx", ".pptx", ".doc", ".txt", ".md"],
                                    label="✅ Select File Types",
                                    value=[".pdf"],
                                    info="Check all types you want to include"
                                )

                                gr.Markdown("""
                                📍 **How to find your folder path:**
                                - **Windows**: Right-click folder → Properties → copy Location
                                - **Mac**: Right-click folder → Get Info → copy path
                                - **Examples**:
                                  - Windows: `C:\\Users\\YourName\\Documents\\Reports`
                                  - Mac: `/Users/yourname/Documents/Reports`
                                  - Linux: `/home/yourname/documents/reports`
                                  - Relative: `./test_file` or `../parent_folder`
                                """)

                            # Glob pattern for advanced users
                            with gr.Group(visible=False) as local_pattern_group:
                                gr.Markdown("**Advanced Pattern Matching** (for power users)")
                                local_glob = gr.Textbox(
                                    label="🔍 Glob Pattern",
                                    value=config_display['local_glob'] or "test_file/*.pdf",
                                    placeholder="Example: ./documents/**/*.{pdf,docx}",
                                    info="Use glob syntax for complex file matching",
                                    lines=1
                                )
                                gr.Markdown("""
                                **Common Patterns:**
                                ```
                                ./docs/*.pdf              → All PDFs in docs folder
                                ./docs/**/*.pdf           → All PDFs recursively (including subfolders)
                                ./docs/*.{pdf,docx,pptx}  → Multiple file types
                                ./reports/2024-*.pdf      → Files matching pattern "2024-*.pdf"
                                test_file/sample.pdf      → Single specific file
                                ```

                                **Wildcards:**
                                - `*` = any characters (except /)
                                - `**` = any directories (recursive)
                                - `{pdf,docx}` = either extension
                                - `?` = single character
                                - `[0-9]` = any digit
                                """)

                        # Blob input options
                        with gr.Group(visible=(config_display['input_mode'] == 'blob')) as blob_group:
                            refresh_containers_btn = gr.Button(
                                "🔄 Refresh Containers",
                                size="sm",
                                variant="secondary"
                            )

                            blob_container_in = gr.Dropdown(
                                choices=list_blob_containers(),
                                label="Input Blob Container",
                                value=config_display['blob_container_in'],
                                info="Select container with source documents",
                                allow_custom_value=True
                            )

                            blob_prefix = gr.Textbox(
                                label="Blob Prefix (Optional)",
                                placeholder="documents/2024/",
                                info="Filter blobs by prefix path"
                            )

                            blob_file_patterns = gr.CheckboxGroup(
                                choices=[".pdf", ".docx", ".pptx", ".doc", ".txt", ".md"],
                                label="File Type Filter",
                                value=[".pdf"],
                                info="Filter blobs by file extensions"
                            )

                    # Right Column: Processing Configuration
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📤 Output & Processing")

                        document_action = gr.Radio(
                            choices=["add", "remove", "removeall"],
                            label="Document Action",
                            value="add",
                            info="What to do with the documents"
                        )

                        extractor_mode = gr.Dropdown(
                            choices=["azure_di", "markitdown", "hybrid"],
                            label="Office Extractor Mode",
                            value=config_display['extractor_mode'],
                            info="How to process Office documents"
                        )

                        offline_fallback = gr.Checkbox(
                            label="Enable Offline Fallback",
                            value=True,
                            info="Use MarkItDown fallback for DOC files or failures"
                        )

                        gr.Markdown("**Performance Settings**")
                        max_workers = gr.Slider(
                            minimum=1,
                            maximum=16,
                            value=4,
                            step=1,
                            label="Max Workers",
                            info="Parallel processing threads"
                        )

                        with gr.Row():
                            setup_index = gr.Checkbox(
                                label="Setup Index First",
                                value=False,
                                info="Create/update search index before ingestion"
                            )
                            verbose = gr.Checkbox(
                                label="Verbose Logging",
                                value=True,
                                info="Enable detailed debug logs"
                            )

                gr.Markdown("---")

                # Run Controls
                with gr.Row():
                    run_btn = gr.Button("▶️ Run Pipeline", variant="primary", size="lg", scale=3)
                    stop_btn = gr.Button("⏹️ Stop", variant="stop", size="lg", scale=1)

                gr.Markdown("---")
                gr.Markdown("### 📊 Pipeline Execution")

                with gr.Row():
                    status_output = gr.Textbox(
                        label="Status",
                        placeholder="Ready to run...",
                        interactive=False
                    )

                logs_output = gr.Textbox(
                    label="Real-time Logs",
                    lines=25,
                    max_lines=50,
                    placeholder="Logs will appear here during execution...",
                    elem_classes=["log-output"],
                    interactive=False,
                    autoscroll=True
                )

                # Helper Functions
                def toggle_input_groups(mode):
                    """Show/hide input groups based on mode selection."""
                    return {
                        local_group: gr.update(visible=(mode == "local")),
                        blob_group: gr.update(visible=(mode == "blob"))
                    }

                def toggle_local_input_type(selection_type):
                    """Toggle between file upload, directory, and pattern."""
                    return {
                        local_file_group: gr.update(visible=(selection_type == "📤 Browse Files")),
                        local_dir_group: gr.update(visible=(selection_type == "📂 Folder Path")),
                        local_pattern_group: gr.update(visible=(selection_type == "🔍 Advanced Pattern"))
                    }

                def build_glob_from_directory(directory, patterns):
                    """Build glob pattern from directory path and file patterns."""
                    if not directory:
                        return ""

                    # Normalize path separators
                    directory = directory.replace('\\', '/')
                    if not directory.endswith('/'):
                        directory += '/'

                    if not patterns:
                        return f"{directory}*"

                    if len(patterns) == 1:
                        return f"{directory}*{patterns[0]}"
                    else:
                        # Remove dots and join
                        exts = [p.lstrip('.') for p in patterns]
                        pattern_str = ','.join(exts)
                        return f"{directory}*.{{{pattern_str}}}"

                def get_effective_glob_pattern(path_type, files, directory, dir_patterns, glob_pattern):
                    """Get the effective glob pattern based on selection type."""
                    if path_type == "📤 Browse Files" and files:
                        # If files are uploaded, use the file paths directly
                        if isinstance(files, list):
                            # Return paths of uploaded files
                            return ','.join([str(f) for f in files])
                        return str(files) if files else glob_pattern
                    elif path_type == "📂 Folder Path":
                        return build_glob_from_directory(directory, dir_patterns)
                    else:  # 🔍 Advanced Pattern
                        return glob_pattern

                def update_scenario_and_load(scenario_name):
                    """Update scenario info and auto-load configuration."""
                    if scenario_name not in SCENARIO_TEMPLATES:
                        return "", None, None, None

                    template = SCENARIO_TEMPLATES[scenario_name]
                    info = f"**{template['description']}**\n\n_{template['notes']}_"

                    # Auto-load configuration
                    new_input_mode = template.get("AZURE_INPUT_MODE", "local")
                    new_extractor = template.get("AZURE_OFFICE_EXTRACTOR_MODE", "hybrid")
                    new_fallback = template.get("AZURE_OFFICE_OFFLINE_FALLBACK", "true") == "true"

                    return info, new_input_mode, new_extractor, new_fallback

                def refresh_blob_containers():
                    """Refresh the list of blob containers."""
                    containers = list_blob_containers()
                    return gr.update(choices=containers)

                def apply_file_pattern_filter(base_glob, patterns):
                    """Apply file pattern filters to glob pattern."""
                    if not patterns:
                        return base_glob

                    # Extract base path
                    if '/' in base_glob or '\\' in base_glob:
                        parts = base_glob.replace('\\', '/').rsplit('/', 1)
                        base_path = parts[0]
                        if len(parts) > 1:
                            base_path += '/'
                        else:
                            base_path = ''
                    else:
                        base_path = ''

                    # Build pattern with multiple extensions
                    if len(patterns) == 1:
                        return f"{base_path}*{patterns[0]}"
                    else:
                        pattern_str = ','.join(patterns)
                        return f"{base_path}*.{{{pattern_str}}}"

                # Event Handlers

                # Input mode change - toggle visibility
                input_mode.change(
                    fn=toggle_input_groups,
                    inputs=[input_mode],
                    outputs=[local_group, blob_group]
                )

                # Local path type change - toggle between file/directory/pattern
                local_path_type.change(
                    fn=toggle_local_input_type,
                    inputs=[local_path_type],
                    outputs=[local_file_group, local_dir_group, local_pattern_group]
                )

                # Directory pattern update - rebuild glob when patterns change
                local_dir_patterns.change(
                    fn=build_glob_from_directory,
                    inputs=[local_dir, local_dir_patterns],
                    outputs=[]  # Just for side effect
                )

                # Environment File Event Handlers
                def handle_env_file_selection(selected_display_name):
                    """Handle environment file selection from dropdown."""
                    try:
                        if selected_display_name == "None (use system environment)":
                            success, message = load_env_file(None, override=True)
                            active = get_active_env_file()
                            return f"**Active Environment**: {active}", message

                        env_file_list = list_env_files()
                        for file_path in env_file_list:
                            if get_env_file_display_name(file_path) == selected_display_name:
                                success, message = load_env_file(file_path, override=True)
                                active = get_active_env_file()
                                return f"**Active Environment**: {active}", message

                        return f"**Active Environment**: {get_active_env_file()}", "❌ File not found"
                    except Exception as e:
                        logger.error(f"Error handling env file selection: {e}")
                        return f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}"

                def handle_env_file_upload(file_obj):
                    """Handle custom .env file upload."""
                    try:
                        success, message, file_path = save_uploaded_env_file(file_obj)
                        active = get_active_env_file()
                        return f"**Active Environment**: {active}", message
                    except Exception as e:
                        logger.error(f"Error handling env file upload: {e}")
                        return f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}"

                def handle_env_reload():
                    """Reload the currently active environment file."""
                    global _active_env_file
                    try:
                        success, message = load_env_file(_active_env_file, override=True)
                        active = get_active_env_file()
                        return f"**Active Environment**: {active}", message
                    except Exception as e:
                        logger.error(f"Error reloading env file: {e}")
                        return f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}"

                def handle_env_refresh():
                    """Refresh the list of available environment files."""
                    try:
                        env_file_list = list_env_files()
                        env_file_choices = ["None (use system environment)"] + [get_env_file_display_name(f) for f in env_file_list]
                        active = get_active_env_file()
                        return gr.Dropdown(choices=env_file_choices), f"**Active Environment**: {active}", f"✅ Refreshed file list. Found {len(env_file_list)} files."
                    except Exception as e:
                        logger.error(f"Error refreshing env file list: {e}")
                        return gr.Dropdown(choices=["None (use system environment)"]), f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}"

                # Validation Event Handlers
                def handle_validate_configuration():
                    """Handle validation button click."""
                    validation_html, status_badge, is_valid = validate_configuration(auto_validation=False)
                    # Return results and open the accordion
                    return validation_html, status_badge, gr.Accordion(open=True)

                def handle_env_load_with_validation(selected_display_name, auto_validate_enabled):
                    """Handle environment file selection with optional auto-validation."""
                    # First load the env file
                    try:
                        if selected_display_name == "None (use system environment)":
                            success, message = load_env_file(None, override=True)
                            active = get_active_env_file()
                            env_status = f"**Active Environment**: {active}"
                            env_message = message
                        else:
                            env_file_list = list_env_files()
                            for file_path in env_file_list:
                                if get_env_file_display_name(file_path) == selected_display_name:
                                    success, message = load_env_file(file_path, override=True)
                                    active = get_active_env_file()
                                    env_status = f"**Active Environment**: {active}"
                                    env_message = message
                                    break
                            else:
                                env_status = f"**Active Environment**: {get_active_env_file()}"
                                env_message = "❌ File not found"
                                success = False

                        # Run auto-validation if enabled
                        if auto_validate_enabled and success:
                            validation_html, status_badge, is_valid = validate_configuration(auto_validation=True)
                            return env_status, env_message, validation_html, status_badge, gr.Accordion(open=True)
                        else:
                            # Return unchanged validation UI
                            return env_status, env_message, gr.HTML(), gr.Markdown(), gr.Accordion()

                    except Exception as e:
                        logger.error(f"Error handling env file selection with validation: {e}")
                        return f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}", gr.HTML(), gr.Markdown(), gr.Accordion()

                def handle_env_upload_with_validation(file_obj, auto_validate_enabled):
                    """Handle custom .env file upload with optional auto-validation."""
                    try:
                        success, message, file_path = save_uploaded_env_file(file_obj)
                        active = get_active_env_file()
                        env_status = f"**Active Environment**: {active}"

                        # Run auto-validation if enabled
                        if auto_validate_enabled and success:
                            validation_html, status_badge, is_valid = validate_configuration(auto_validation=True)
                            return env_status, message, validation_html, status_badge, gr.Accordion(open=True)
                        else:
                            return env_status, message, gr.HTML(), gr.Markdown(), gr.Accordion()

                    except Exception as e:
                        logger.error(f"Error handling env file upload with validation: {e}")
                        return f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}", gr.HTML(), gr.Markdown(), gr.Accordion()

                def handle_env_reload_with_validation(auto_validate_enabled):
                    """Reload the currently active environment file with optional auto-validation."""
                    global _active_env_file
                    try:
                        success, message = load_env_file(_active_env_file, override=True)
                        active = get_active_env_file()
                        env_status = f"**Active Environment**: {active}"

                        # Run auto-validation if enabled
                        if auto_validate_enabled and success:
                            validation_html, status_badge, is_valid = validate_configuration(auto_validation=True)
                            return env_status, message, validation_html, status_badge, gr.Accordion(open=True)
                        else:
                            return env_status, message, gr.HTML(), gr.Markdown(), gr.Accordion()

                    except Exception as e:
                        logger.error(f"Error reloading env file with validation: {e}")
                        return f"**Active Environment**: {get_active_env_file()}", f"❌ Error: {str(e)}", gr.HTML(), gr.Markdown(), gr.Accordion()

                # Wire up validation button
                validate_btn.click(
                    fn=handle_validate_configuration,
                    inputs=[],
                    outputs=[validation_results, validation_status_badge, validation_accordion]
                )

                # Update env file handlers to include validation
                env_load_button.click(
                    fn=handle_env_load_with_validation,
                    inputs=[env_file_dropdown, auto_validate_checkbox],
                    outputs=[env_status_display, env_message_display, validation_results, validation_status_badge, validation_accordion]
                )

                env_file_upload.change(
                    fn=handle_env_upload_with_validation,
                    inputs=[env_file_upload, auto_validate_checkbox],
                    outputs=[env_status_display, env_message_display, validation_results, validation_status_badge, validation_accordion]
                )

                env_reload_button.click(
                    fn=handle_env_reload_with_validation,
                    inputs=[auto_validate_checkbox],
                    outputs=[env_status_display, env_message_display, validation_results, validation_status_badge, validation_accordion]
                )

                env_refresh_button.click(
                    fn=handle_env_refresh,
                    inputs=[],
                    outputs=[env_file_dropdown, env_status_display, env_message_display]
                )

                # Scenario dropdown - auto-load on change
                scenario_dropdown.change(
                    fn=update_scenario_and_load,
                    inputs=[scenario_dropdown],
                    outputs=[scenario_info, input_mode, extractor_mode, offline_fallback]
                )

                # Refresh containers button
                refresh_containers_btn.click(
                    fn=refresh_blob_containers,
                    outputs=[blob_container_in]
                )

                # Initialize scenario info on load
                demo.load(
                    fn=update_scenario_and_load,
                    inputs=[scenario_dropdown],
                    outputs=[scenario_info, input_mode, extractor_mode, offline_fallback]
                )

                # Wrapper to handle different input types
                def run_pipeline_with_inputs(
                    inp_mode,
                    path_type,
                    files,
                    directory,
                    dir_patterns,
                    glob_pattern,
                    blob_container,
                    blob_pre,
                    blob_patterns,
                    extr_mode,
                    off_fallback,
                    doc_action,
                    workers,
                    setup_idx,
                    verb
                ):
                    """Wrapper to determine effective glob and run pipeline."""
                    # Determine the effective glob pattern for local mode
                    if inp_mode == "local":
                        effective_glob = get_effective_glob_pattern(
                            path_type, files, directory, dir_patterns, glob_pattern
                        )
                    else:
                        # For blob mode, use container
                        effective_glob = ""

                    # Update environment variables at runtime
                    os.environ["AZURE_INPUT_MODE"] = inp_mode
                    os.environ["AZURE_OFFICE_EXTRACTOR_MODE"] = extr_mode
                    os.environ["AZURE_OFFICE_OFFLINE_FALLBACK"] = str(off_fallback).lower()
                    os.environ["AZURE_DOCUMENT_ACTION"] = doc_action
                    os.environ["AZURE_MAX_WORKERS"] = str(int(workers))
                    os.environ["AZURE_OFFICE_VERBOSE"] = str(verb).lower()

                    if inp_mode == "local":
                        os.environ["AZURE_LOCAL_GLOB"] = effective_glob
                    else:
                        os.environ["AZURE_BLOB_CONTAINER_IN"] = blob_container
                        if blob_pre:
                            os.environ["AZURE_BLOB_PREFIX"] = blob_pre

                    # Call the actual pipeline runner and yield from it
                    # (run_pipeline_sync is a generator, so we need to yield from it)
                    yield from run_pipeline_sync(
                        inp_mode,
                        effective_glob,
                        blob_container,
                        extr_mode,
                        off_fallback,
                        doc_action,
                        workers,
                        setup_idx,
                        verb
                    )

                # Run pipeline button with all inputs
                run_event = run_btn.click(
                    fn=run_pipeline_with_inputs,
                    inputs=[
                        input_mode,
                        local_path_type,
                        local_files,
                        local_dir,
                        local_dir_patterns,
                        local_glob,
                        blob_container_in,
                        blob_prefix,
                        blob_file_patterns,
                        extractor_mode,
                        offline_fallback,
                        document_action,
                        max_workers,
                        setup_index,
                        verbose,
                    ],
                    outputs=[status_output, logs_output]
                )

            # =================================================================
            # Tab 2: Configuration Status
            # =================================================================
            with gr.Tab("⚙️ Configuration Status"):
                gr.Markdown("### Current Environment Configuration")
                gr.Markdown("View your current environment variables with sensitive values masked.")

                refresh_status_btn = gr.Button("🔄 Refresh Status", variant="secondary")

                config_status_html = gr.HTML(
                    value=generate_env_status_html(),
                    elem_classes=["config-status"]
                )

                refresh_status_btn.click(
                    fn=lambda: generate_env_status_html(),
                    outputs=[config_status_html]
                )

            # =================================================================
            # Tab 3: Help & Documentation
            # =================================================================
            with gr.Tab("📚 Help & Documentation"):
                gr.Markdown("### Environment Variables Reference")
                gr.Markdown("Complete guide to all environment variables used in the pipeline.")

                help_html = gr.HTML(
                    value=generate_env_help_html()
                )

                gr.Markdown("---")
                gr.Markdown("### 📖 Additional Resources")
                gr.Markdown("""
                - **Configuration Scenarios**: See `docs/configuration-scenarios.md` for detailed scenario guides
                - **Unified Mode Configuration**: See `docs/unified-mode-configuration.md` for mode details
                - **Office Processing**: See `docs/office-processing.md` for Office document handling

                ### 🔧 Quick Start

                1. **Set up Azure resources**:
                   - Azure Document Intelligence service
                   - Azure AI Search service
                   - Azure OpenAI service
                   - Azure Storage account (for blob mode)

                2. **Configure environment**:
                   - Copy `.env.example` to `.env`
                   - Fill in your Azure credentials
                   - Choose a scenario (hybrid mode recommended)

                3. **Run pipeline**:
                   - Select scenario in "Run Pipeline" tab
                   - Configure input source
                   - Click "Run Pipeline"
                   - Monitor real-time logs

                ### ⚠️ Important Notes

                - **Sensitive values** are automatically masked in the UI
                - **DOC files** require MarkItDown fallback enabled
                - **Blob mode** requires storage account and pre-created input container
                - **Index setup** only needed on first run or schema changes
                """)

            # =================================================================
            # Tab 4: Review Index - Redesigned UI
            # =================================================================
            with gr.Tab("📊 Review Index"):
                # Hero section with title and description
                gr.Markdown("""
                # 🔍 Index Explorer
                ### Discover, analyze, and verify your indexed documents with powerful search and navigation
                """)

                # Statistics Dashboard
                with gr.Row():
                    with gr.Column(scale=1):
                        total_docs_display = gr.Markdown("### 📚 Total Documents\n**—**")
                    with gr.Column(scale=1):
                        total_chunks_display = gr.Markdown("### 📄 Total Chunks\n**—**")
                    with gr.Column(scale=1):
                        connection_indicator = gr.Markdown("### 🔌 Connection\n**Not Connected**")
                    with gr.Column(scale=1):
                        index_info_display = gr.Markdown("### 🏷️ Index Info\n**—**")

                gr.Markdown("---")

                # Connection & Quick Actions Bar
                with gr.Row():
                    test_connection_btn = gr.Button("🔌 Test Connection", variant="primary", scale=1, size="sm")
                    clear_search_btn = gr.Button("🗑️ Clear Search", variant="secondary", scale=1, size="sm")
                    refresh_stats_btn = gr.Button("🔄 Refresh Stats", variant="secondary", scale=1, size="sm")

                connection_status = gr.Textbox(
                    label="Status Messages",
                    value="Ready to explore your index",
                    interactive=False,
                    lines=2
                )

                gr.Markdown("---")

                # Search Section with Tabs
                with gr.Tabs():
                    # Simple Search Tab
                    with gr.Tab("🔍 Quick Search"):
                        gr.Markdown("**Find documents by filename pattern**")
                        with gr.Row():
                            filename_pattern = gr.Textbox(
                                label="",
                                placeholder="🔎 Enter filename pattern (e.g., ARCHITECTURE*, *.pdf, or * for all)",
                                value="*",
                                scale=4,
                                show_label=False
                            )
                            search_btn = gr.Button("🔍 Search Documents", variant="primary", scale=1)

                        # Quick search suggestions
                        with gr.Row():
                            gr.Markdown("**Quick Filters:**")
                            all_docs_btn = gr.Button("📚 All Documents", size="sm", scale=1)
                            pdf_only_btn = gr.Button("📄 PDFs Only", size="sm", scale=1)
                            docx_only_btn = gr.Button("📝 DOCX Only", size="sm", scale=1)
                            recent_btn = gr.Button("🕐 Recent", size="sm", scale=1)

                    # Advanced Search Tab
                    with gr.Tab("⚙️ Advanced Search"):
                        gr.Markdown("**Advanced search options (coming soon)**")
                        with gr.Row():
                            category_filter = gr.Dropdown(
                                label="Category Filter",
                                choices=["All", "document", "table", "figure"],
                                value="All",
                                scale=1
                            )
                            min_chunks = gr.Number(
                                label="Min Chunks",
                                value=0,
                                scale=1
                            )
                            max_chunks = gr.Number(
                                label="Max Chunks",
                                value=10000,
                                scale=1
                            )

                gr.Markdown("---")

                # Results Section - Two Column Layout
                with gr.Row():
                    # Left Column: Document List
                    with gr.Column(scale=2):
                        gr.Markdown("### 📂 Documents")
                        search_results_info = gr.Markdown("*No search performed yet. Click 'Search Documents' to begin.*")

                        document_list = gr.Dataframe(
                            headers=["📄 Filename", "🧩 Chunks", "🏷️ Category"],
                            datatype=["str", "number", "str"],
                            label="",
                            interactive=False,
                            wrap=True,
                            show_label=False,
                            row_count=10
                        )
                        selected_doc_id = gr.State(value="")

                    # Right Column: Quick Document Info
                    with gr.Column(scale=1):
                        gr.Markdown("### ℹ️ Document Info")
                        doc_info_card = gr.Markdown("""
                        **Select a document** from the list to view details:

                        - 📄 View all chunks
                        - 🧩 Navigate page by page
                        - 📊 See metadata
                        - 🔍 Analyze content
                        """)

                gr.Markdown("---")

                # Chunk Viewer Section (hidden by default) - Redesigned with Sidebar
                with gr.Group(visible=False) as chunk_review_section:
                    gr.Markdown("## 📖 Chunk Viewer")

                    # Document header
                    with gr.Row():
                        with gr.Column(scale=3):
                            selected_doc_name = gr.Textbox(
                                label="📄 Document",
                                interactive=False,
                                show_label=True
                            )
                        with gr.Column(scale=1):
                            chunk_navigation_info = gr.Textbox(
                                label="📍 Total Chunks",
                                value="0 chunks",
                                interactive=False,
                                show_label=True
                            )

                    # Quick actions
                    with gr.Row():
                        refresh_chunks_btn = gr.Button("🔄 Reload All Chunks", scale=1, variant="secondary")
                        export_chunk_btn = gr.Button("💾 Export Current", scale=1, size="sm")
                        close_viewer_btn = gr.Button("❌ Close Viewer", scale=1, size="sm")

                    gr.Markdown("---")

                    # Main Layout: Sidebar + Content (Side-by-Side)
                    with gr.Row():
                        # LEFT SIDEBAR: Chunk List Navigator
                        with gr.Column(scale=2):
                            gr.Markdown("### 📑 All Chunks")
                            gr.Markdown("*Click on any chunk to view its content*")

                            # Chunk list as clickable table
                            chunk_list_navigator = gr.Dataframe(
                                headers=["#", "📄 Page", "📝 Preview"],
                                datatype=["number", "str", "str"],
                                label="",
                                interactive=False,
                                wrap=True,
                                show_label=False,
                                row_count=15,
                                col_count=(3, "fixed")
                            )

                            # Search within chunks
                            with gr.Row():
                                chunk_search_input = gr.Textbox(
                                    label="🔍 Search in chunks",
                                    placeholder="Search text within chunks...",
                                    scale=3,
                                    show_label=False
                                )
                                chunk_search_btn = gr.Button("🔍", scale=1, size="sm")

                        # RIGHT MAIN AREA: Chunk Content Details
                        with gr.Column(scale=3):
                            gr.Markdown("### 📄 Chunk Content")

                            # Current chunk indicator
                            current_chunk_header = gr.Markdown("**Select a chunk from the sidebar →**")

                            # Content Display with Tabs
                            with gr.Tabs():
                                # Content Tab
                                with gr.Tab("📝 Content"):
                                    chunk_page_info = gr.Markdown("**Page Info:** —")

                                    chunk_content = gr.Textbox(
                                        label="",
                                        lines=25,
                                        max_lines=35,
                                        interactive=False,
                                        show_label=False,
                                        placeholder="Click on a chunk in the sidebar to view its content..."
                                    )

                                    with gr.Row():
                                        chunk_token_count = gr.Markdown("**🔢 Tokens:** —")
                                        chunk_char_count = gr.Markdown("**📝 Characters:** —")
                                        chunk_lines_count = gr.Markdown("**📄 Lines:** —")

                                # Metadata Tab
                                with gr.Tab("📊 Metadata"):
                                    chunk_metadata_formatted = gr.Markdown("*Select a chunk to view metadata*")
                                    chunk_metadata = gr.JSON(
                                        label="Raw Metadata (JSON)",
                                        show_label=True
                                    )

                                # Analysis Tab
                                with gr.Tab("🔬 Analysis"):
                                    chunk_analysis = gr.Markdown("""
                                    ### Content Analysis
                                    *Analysis will appear here after selecting a chunk*

                                    - Content type detection
                                    - Table/Image indicators
                                    - Text statistics
                                    - Quality metrics
                                    """)

                                # Context Tab - Show surrounding chunks
                                with gr.Tab("🔄 Context"):
                                    chunk_context = gr.Markdown("""
                                    ### Chunk Context
                                    *Shows previous and next chunks for context*

                                    Select a chunk to see surrounding content.
                                    """)

                # State for chunk navigation
                current_chunks = gr.State(value=[])
                current_chunk_index = gr.State(value=0)
                filtered_chunk_indices = gr.State(value=[])  # For search filtering

                # Functions for index review
                def test_connection():
                    """Test connection to Azure AI Search and update dashboard."""
                    success, message = test_search_connection()

                    # Update connection indicator
                    if "✅" in message or "Connected" in message:
                        connection_md = "### 🔌 Connection\n**✅ Connected**"
                        # Extract index name if available
                        if "index" in message.lower():
                            parts = message.split("'")
                            if len(parts) >= 2:
                                index_name = parts[1]
                                index_info = f"### 🏷️ Index Info\n**{index_name}**"
                            else:
                                index_info = "### 🏷️ Index Info\n**Connected**"
                        else:
                            index_info = "### 🏷️ Index Info\n**Connected**"
                    else:
                        connection_md = "### 🔌 Connection\n**❌ Failed**"
                        index_info = "### 🏷️ Index Info\n**—**"

                    return {
                        connection_status: message,
                        connection_indicator: connection_md,
                        index_info_display: index_info
                    }

                def search_documents(pattern):
                    """Search for documents by filename pattern with enhanced UI updates."""
                    if not pattern or pattern.strip() == "":
                        pattern = "*"

                    docs = search_documents_by_filename(pattern)

                    if not docs:
                        results_info = "**No documents found** 😞\n\nTry a different search pattern or check your index."
                        status_msg = "❌ No documents found"
                        return {
                            document_list: [],
                            connection_status: status_msg,
                            search_results_info: results_info,
                            total_docs_display: "### 📚 Total Documents\n**0**",
                            total_chunks_display: "### 📄 Total Chunks\n**0**"
                        }

                    # Format for dataframe
                    rows = []
                    total_chunks = 0
                    for doc in docs:
                        rows.append([
                            doc["filename"],
                            doc["chunk_count"],
                            doc["category"] or "—"
                        ])
                        total_chunks += doc["chunk_count"]

                    # Create results info markdown
                    results_info = f"""
**✅ Found {len(docs)} document(s)** with **{total_chunks} total chunks**

📊 Click on any row to explore chunks and metadata.
"""

                    status_msg = f"✅ Found {len(docs)} document(s) with {total_chunks} chunks"

                    return {
                        document_list: rows,
                        connection_status: status_msg,
                        search_results_info: results_info,
                        total_docs_display: f"### 📚 Total Documents\n**{len(docs)}**",
                        total_chunks_display: f"### 📄 Total Chunks\n**{total_chunks}**"
                    }

                def quick_filter_all():
                    """Quick filter: All documents."""
                    return "*"

                def quick_filter_pdf():
                    """Quick filter: PDF only."""
                    return "*.pdf"

                def quick_filter_docx():
                    """Quick filter: DOCX only."""
                    return "*.docx"

                def quick_filter_recent():
                    """Quick filter: Recent (all for now)."""
                    return "*"

                def clear_search():
                    """Clear search results."""
                    return {
                        document_list: [],
                        filename_pattern: "*",
                        search_results_info: "*No search performed yet. Click 'Search Documents' to begin.*",
                        connection_status: "Search cleared. Ready to search.",
                        chunk_review_section: gr.update(visible=False)
                    }

                def format_metadata_display(chunk):
                    """Format chunk metadata as readable markdown."""
                    md = "### 📊 Chunk Metadata\n\n"

                    # Core info
                    md += f"**🆔 Chunk ID:** `{chunk.get('chunk_id', 'N/A')}`\n\n"
                    md += f"**📄 Page Number:** {chunk.get('page_num', 0) + 1}\n\n"
                    md += f"**📍 Source Page:** `{chunk.get('sourcepage', 'N/A')}`\n\n"
                    md += f"**🏷️ Category:** {chunk.get('category', 'N/A') or '—'}\n\n"

                    # Content type indicators
                    if chunk.get('content_type'):
                        md += f"**📝 Content Type:** {chunk.get('content_type')}\n\n"

                    if chunk.get('has_table'):
                        md += f"**📊 Has Table:** ✅ Yes\n\n"

                    if chunk.get('has_image'):
                        md += f"**🖼️ Has Image:** ✅ Yes\n\n"

                    # Additional metadata
                    if chunk.get('url'):
                        md += f"**🔗 URL:** {chunk.get('url')}\n\n"

                    if chunk.get('title'):
                        md += f"**📌 Title:** {chunk.get('title')}\n\n"

                    return md

                def analyze_chunk_content(chunk):
                    """Analyze chunk content and return insights."""
                    content = chunk.get('content', '')

                    # Calculate metrics (same as chunker.py)
                    # Token count using tiktoken (same encoding as embeddings)
                    if token_encoder:
                        try:
                            tokens = len(token_encoder.encode(content))
                        except Exception:
                            tokens = 0
                    else:
                        tokens = 0

                    # Check if token_count is already in chunk metadata
                    if chunk.get('token_count') is not None:
                        tokens = chunk.get('token_count')

                    chars = len(content)
                    lines = len(content.split('\n'))

                    # Content analysis
                    analysis = f"""
### 🔬 Content Analysis

#### 📏 Size Metrics
- **Tokens:** {tokens:,} (using {ENCODING_MODEL})
- **Characters:** {chars:,}
- **Lines:** {lines:,}

#### 📊 Content Type
- **Category:** {chunk.get('category', 'Unknown')}
"""

                    if chunk.get('content_type'):
                        analysis += f"- **Type:** {chunk.get('content_type')}\n"

                    analysis += "\n#### 🔍 Features Detected\n"

                    features = []
                    if chunk.get('has_table'):
                        features.append("📊 Contains table data")
                    if chunk.get('has_image'):
                        features.append("🖼️ Contains images/figures")

                    # Simple content analysis
                    if any(word in content.lower() for word in ['table', 'row', 'column', 'cell']):
                        features.append("📋 Table-related content")
                    if any(word in content.lower() for word in ['figure', 'image', 'diagram', 'chart']):
                        features.append("📈 Visual content references")
                    if any(word in content.lower() for word in ['http://', 'https://', 'www.']):
                        features.append("🔗 Contains URLs")

                    if features:
                        for feature in features:
                            analysis += f"- {feature}\n"
                    else:
                        analysis += "- 📝 Standard text content\n"

                    # Quality indicators
                    analysis += "\n#### ✅ Quality Indicators\n"
                    if tokens > 0:
                        analysis += f"- ✅ Non-empty content\n"
                    if tokens > 50:
                        analysis += f"- ✅ Substantial content ({tokens} tokens)\n"
                    if tokens > 400:
                        analysis += f"- ⚠️ Large chunk (near token limit)\n"
                    if chunk.get('page_num') is not None:
                        analysis += f"- ✅ Page information available\n"

                    return analysis, f"**{tokens:,}**", f"**{chars:,}**", f"**{lines}**"

                def build_chunk_navigator(chunks):
                    """Build the chunk navigator sidebar table."""
                    if not chunks:
                        return []

                    rows = []
                    for idx, chunk in enumerate(chunks):
                        chunk_num = idx + 1
                        page_info = f"Page {chunk.get('page_num', 0) + 1}"

                        # Get preview (first 50 chars of content)
                        content = chunk.get('content', '')
                        preview = content[:50].replace('\n', ' ').strip()
                        if len(content) > 50:
                            preview += "..."

                        # Add special indicators
                        if chunk.get('has_table'):
                            preview = "📊 " + preview
                        elif chunk.get('has_image'):
                            preview = "🖼️ " + preview

                        rows.append([chunk_num, page_info, preview])

                    return rows

                def get_chunk_context(chunks, current_index):
                    """Get context showing previous and next chunks."""
                    if not chunks or current_index < 0 or current_index >= len(chunks):
                        return "*No context available*"

                    context_md = "### 🔄 Surrounding Chunks\n\n"

                    # Previous chunk
                    if current_index > 0:
                        prev_chunk = chunks[current_index - 1]
                        prev_content = prev_chunk.get('content', '')[:200].replace('\n', ' ')
                        context_md += f"#### ⬆️ Previous Chunk (#{current_index})\n"
                        context_md += f"**Page {prev_chunk.get('page_num', 0) + 1}**\n\n"
                        context_md += f"> {prev_content}...\n\n"
                        context_md += "---\n\n"

                    # Current chunk indicator
                    context_md += f"#### 📍 Current Chunk (#{current_index + 1})\n"
                    context_md += f"**You are viewing this chunk**\n\n"
                    context_md += "---\n\n"

                    # Next chunk
                    if current_index < len(chunks) - 1:
                        next_chunk = chunks[current_index + 1]
                        next_content = next_chunk.get('content', '')[:200].replace('\n', ' ')
                        context_md += f"#### ⬇️ Next Chunk (#{current_index + 2})\n"
                        context_md += f"**Page {next_chunk.get('page_num', 0) + 1}**\n\n"
                        context_md += f"> {next_content}...\n\n"

                    return context_md

                def search_in_chunks(search_term, chunks):
                    """Search for text within chunks and return matching indices."""
                    if not search_term or not chunks:
                        return list(range(len(chunks)))  # Return all if no search

                    search_lower = search_term.lower()
                    matching_indices = []

                    for idx, chunk in enumerate(chunks):
                        content = chunk.get('content', '').lower()
                        if search_lower in content:
                            matching_indices.append(idx)

                    return matching_indices if matching_indices else list(range(len(chunks)))

                def select_document(evt: gr.SelectData, dataframe_data):
                    """Handle document selection from dataframe with enhanced UI updates."""
                    # Check if dataframe is empty - handle both pandas DataFrame and list
                    if dataframe_data is None:
                        return {
                            chunk_review_section: gr.update(visible=False),
                            selected_doc_name: "",
                            selected_doc_id: "",
                            current_chunks: [],
                            current_chunk_index: 0
                        }

                    # Convert pandas DataFrame to list if needed
                    import pandas as pd
                    if isinstance(dataframe_data, pd.DataFrame):
                        if dataframe_data.empty:
                            return {
                                chunk_review_section: gr.update(visible=False),
                                selected_doc_name: "",
                                selected_doc_id: "",
                                current_chunks: [],
                                current_chunk_index: 0
                            }
                        # Convert to list of lists for easier access
                        dataframe_data = dataframe_data.values.tolist()
                    elif len(dataframe_data) == 0:
                        return {
                            chunk_review_section: gr.update(visible=False),
                            selected_doc_name: "",
                            selected_doc_id: "",
                            current_chunks: [],
                            current_chunk_index: 0
                        }

                    # Get selected row
                    row_index = evt.index[0]
                    if row_index >= len(dataframe_data):
                        return {
                            chunk_review_section: gr.update(visible=False)
                        }

                    filename = dataframe_data[row_index][0]

                    # Update doc info card
                    doc_info = f"""
### 📄 {filename}

**Loading chunks...**
"""

                    # Search for this document to get parent_id
                    docs = search_documents_by_filename(filename)
                    if not docs:
                        return {
                            chunk_review_section: gr.update(visible=False),
                            selected_doc_name: filename,
                            connection_status: f"❌ Could not find document: {filename}",
                            doc_info_card: f"### ❌ Error\n\nCould not find document: {filename}"
                        }

                    doc = docs[0]
                    parent_id = doc["id"]

                    # Get chunks for this document
                    chunks = get_document_chunks(parent_id)

                    if not chunks:
                        return {
                            chunk_review_section: gr.update(visible=True),
                            selected_doc_name: filename,
                            selected_doc_id: parent_id,
                            current_chunks: [],
                            current_chunk_index: 0,
                            chunk_navigation_info: "0 / 0",
                            chunk_page_info: "**Page Info:** —",
                            chunk_content: "",
                            chunk_metadata: {},
                            chunk_metadata_formatted: "*No chunks found*",
                            chunk_analysis: "*No content to analyze*",
                            chunk_token_count: "**🔢 Tokens:** 0",
                            chunk_char_count: "**Characters:** 0",
                            connection_status: f"⚠️ No chunks found for: {filename}",
                            doc_info_card: f"### ⚠️ {filename}\n\n**0 chunks found**"
                        }

                    # Build chunk navigator table
                    navigator_rows = build_chunk_navigator(chunks)

                    # Show first chunk by default
                    first_chunk = chunks[0]
                    metadata = {
                        "chunk_id": first_chunk.get("chunk_id", ""),
                        "page_num": first_chunk.get("page_num", 0),
                        "sourcepage": first_chunk.get("sourcepage", ""),
                        "category": first_chunk.get("category", "")
                    }

                    # Add content type metadata if available
                    if first_chunk.get('content_type'):
                        metadata['content_type'] = first_chunk.get('content_type')
                    if first_chunk.get('has_table'):
                        metadata['has_table'] = first_chunk.get('has_table')
                    if first_chunk.get('has_image'):
                        metadata['has_image'] = first_chunk.get('has_image')

                    # Format metadata and analysis
                    metadata_md = format_metadata_display(first_chunk)
                    analysis_md, token_count, char_count, line_count = analyze_chunk_content(first_chunk)
                    context_md = get_chunk_context(chunks, 0)

                    # Update doc info card
                    doc_info = f"""
### 📄 {filename}

**✅ {len(chunks)} chunks loaded**

- 🧩 Total chunks: **{len(chunks)}**
- 📄 First page: **Page {first_chunk.get('page_num', 0) + 1}**
- 🏷️ Category: **{doc.get('category', 'N/A') or '—'}**

**👈 Click any chunk in the sidebar to view it**
"""

                    return {
                        chunk_review_section: gr.update(visible=True),
                        selected_doc_name: filename,
                        selected_doc_id: parent_id,
                        current_chunks: chunks,
                        current_chunk_index: 0,
                        chunk_navigation_info: f"{len(chunks)} chunks",
                        chunk_list_navigator: navigator_rows,
                        current_chunk_header: f"**📄 Chunk 1 of {len(chunks)}** • Page {first_chunk.get('page_num', 0) + 1}",
                        chunk_page_info: f"**Page {first_chunk.get('page_num', 0) + 1}** • Chunk `{first_chunk.get('chunk_id', 'N/A')}` • {first_chunk.get('sourcepage', 'N/A')}",
                        chunk_content: first_chunk.get("content", ""),
                        chunk_metadata: metadata,
                        chunk_metadata_formatted: metadata_md,
                        chunk_analysis: analysis_md,
                        chunk_token_count: token_count,
                        chunk_char_count: char_count,
                        chunk_lines_count: line_count,
                        chunk_context: context_md,
                        connection_status: f"✅ Loaded {len(chunks)} chunks for: {filename}",
                        doc_info_card: doc_info,
                        filtered_chunk_indices: list(range(len(chunks)))
                    }

                def select_chunk_from_sidebar(evt: gr.SelectData, chunks):
                    """Handle chunk selection from sidebar navigator."""
                    if not chunks or len(chunks) == 0:
                        return {
                            current_chunk_index: 0,
                            current_chunk_header: "**No chunks available**",
                            chunk_page_info: "**Page Info:** —",
                            chunk_content: "",
                            chunk_metadata: {},
                            chunk_metadata_formatted: "*No metadata available*",
                            chunk_analysis: "*No content to analyze*",
                            chunk_token_count: "**🔢 Tokens:** —",
                            chunk_char_count: "**Characters:** —",
                            chunk_lines_count: "**Lines:** —",
                            chunk_context: "*No context available*"
                        }

                    # Get selected row index (which corresponds to chunk index)
                    chunk_index = evt.index[0]

                    if chunk_index < 0 or chunk_index >= len(chunks):
                        return {}

                    # Get selected chunk
                    chunk = chunks[chunk_index]

                    # Build metadata
                    metadata = {
                        "chunk_id": chunk.get("chunk_id", ""),
                        "page_num": chunk.get("page_num", 0),
                        "sourcepage": chunk.get("sourcepage", ""),
                        "category": chunk.get("category", "")
                    }

                    if chunk.get('content_type'):
                        metadata['content_type'] = chunk.get('content_type')
                    if chunk.get('has_table'):
                        metadata['has_table'] = chunk.get('has_table')
                    if chunk.get('has_image'):
                        metadata['has_image'] = chunk.get('has_image')

                    # Format metadata and analysis
                    metadata_md = format_metadata_display(chunk)
                    analysis_md, token_count, char_count, line_count = analyze_chunk_content(chunk)
                    context_md = get_chunk_context(chunks, chunk_index)

                    return {
                        current_chunk_index: chunk_index,
                        current_chunk_header: f"**📄 Chunk {chunk_index + 1} of {len(chunks)}** • Page {chunk.get('page_num', 0) + 1}",
                        chunk_page_info: f"**Page {chunk.get('page_num', 0) + 1}** • Chunk `{chunk.get('chunk_id', 'N/A')}` • {chunk.get('sourcepage', 'N/A')}",
                        chunk_content: chunk.get("content", ""),
                        chunk_metadata: metadata,
                        chunk_metadata_formatted: metadata_md,
                        chunk_analysis: analysis_md,
                        chunk_token_count: token_count,
                        chunk_char_count: char_count,
                        chunk_lines_count: line_count,
                        chunk_context: context_md
                    }

                def search_chunks(search_term, chunks):
                    """Search within chunks and filter the navigator."""
                    if not chunks:
                        return {
                            chunk_list_navigator: [],
                            connection_status: "No chunks to search"
                        }

                    if not search_term or search_term.strip() == "":
                        # Show all chunks
                        navigator_rows = build_chunk_navigator(chunks)
                        return {
                            chunk_list_navigator: navigator_rows,
                            filtered_chunk_indices: list(range(len(chunks))),
                            connection_status: f"Showing all {len(chunks)} chunks"
                        }

                    # Search and filter
                    matching_indices = search_in_chunks(search_term, chunks)
                    matching_chunks = [chunks[i] for i in matching_indices]

                    # Build navigator with only matching chunks
                    navigator_rows = build_chunk_navigator(matching_chunks)

                    return {
                        chunk_list_navigator: navigator_rows,
                        filtered_chunk_indices: matching_indices,
                        connection_status: f"✅ Found {len(matching_indices)} chunks matching '{search_term}'"
                    }

                def close_chunk_viewer():
                    """Close the chunk viewer."""
                    return {
                        chunk_review_section: gr.update(visible=False),
                        connection_status: "Chunk viewer closed"
                    }

                def export_current_chunk(chunk_index, chunks, filename):
                    """Export current chunk (placeholder for future implementation)."""
                    if not chunks or chunk_index < 0 or chunk_index >= len(chunks):
                        return "❌ No chunk to export"

                    # For now, just show a message
                    return f"💾 Export functionality coming soon! Would export chunk {chunk_index + 1} from {filename}"

                def refresh_chunks(parent_id):
                    """Refresh chunks for current document with sidebar navigator."""
                    if not parent_id:
                        return {
                            current_chunks: [],
                            current_chunk_index: 0,
                            connection_status: "No document selected"
                        }

                    chunks = get_document_chunks(parent_id)

                    if not chunks:
                        return {
                            current_chunks: [],
                            current_chunk_index: 0,
                            chunk_navigation_info: "0 chunks",
                            chunk_list_navigator: [],
                            current_chunk_header: "**No chunks available**",
                            chunk_page_info: "**Page Info:** —",
                            chunk_content: "",
                            chunk_metadata: {},
                            chunk_metadata_formatted: "*No chunks found*",
                            chunk_analysis: "*No content to analyze*",
                            chunk_token_count: "**🔢 Tokens:** —",
                            chunk_char_count: "**Characters:** —",
                            chunk_lines_count: "**Lines:** —",
                            chunk_context: "*No context available*",
                            connection_status: f"⚠️ No chunks found"
                        }

                    # Build navigator
                    navigator_rows = build_chunk_navigator(chunks)

                    # Show first chunk
                    first_chunk = chunks[0]
                    metadata = {
                        "chunk_id": first_chunk.get("chunk_id", ""),
                        "page_num": first_chunk.get("page_num", 0),
                        "sourcepage": first_chunk.get("sourcepage", ""),
                        "category": first_chunk.get("category", "")
                    }

                    if first_chunk.get('content_type'):
                        metadata['content_type'] = first_chunk.get('content_type')
                    if first_chunk.get('has_table'):
                        metadata['has_table'] = first_chunk.get('has_table')
                    if first_chunk.get('has_image'):
                        metadata['has_image'] = first_chunk.get('has_image')

                    metadata_md = format_metadata_display(first_chunk)
                    analysis_md, token_count, char_count, line_count = analyze_chunk_content(first_chunk)
                    context_md = get_chunk_context(chunks, 0)

                    return {
                        current_chunks: chunks,
                        current_chunk_index: 0,
                        chunk_navigation_info: f"{len(chunks)} chunks",
                        chunk_list_navigator: navigator_rows,
                        current_chunk_header: f"**📄 Chunk 1 of {len(chunks)}** • Page {first_chunk.get('page_num', 0) + 1}",
                        chunk_page_info: f"**Page {first_chunk.get('page_num', 0) + 1}** • Chunk `{first_chunk.get('chunk_id', 'N/A')}` • {first_chunk.get('sourcepage', 'N/A')}",
                        chunk_content: first_chunk.get("content", ""),
                        chunk_metadata: metadata,
                        chunk_metadata_formatted: metadata_md,
                        chunk_analysis: analysis_md,
                        chunk_token_count: token_count,
                        chunk_char_count: char_count,
                        chunk_lines_count: line_count,
                        chunk_context: context_md,
                        filtered_chunk_indices: list(range(len(chunks))),
                        connection_status: f"✅ Refreshed {len(chunks)} chunks"
                    }

                # Event handlers - Enhanced UI connections
                test_connection_btn.click(
                    fn=test_connection,
                    outputs=[connection_status, connection_indicator, index_info_display]
                )

                search_btn.click(
                    fn=search_documents,
                    inputs=[filename_pattern],
                    outputs=[document_list, connection_status, search_results_info, total_docs_display, total_chunks_display]
                )

                # Quick filter buttons
                all_docs_btn.click(
                    fn=quick_filter_all,
                    outputs=[filename_pattern]
                )

                pdf_only_btn.click(
                    fn=quick_filter_pdf,
                    outputs=[filename_pattern]
                )

                docx_only_btn.click(
                    fn=quick_filter_docx,
                    outputs=[filename_pattern]
                )

                recent_btn.click(
                    fn=quick_filter_recent,
                    outputs=[filename_pattern]
                )

                clear_search_btn.click(
                    fn=clear_search,
                    outputs=[document_list, filename_pattern, search_results_info, connection_status, chunk_review_section]
                )

                document_list.select(
                    fn=select_document,
                    inputs=[document_list],
                    outputs=[
                        chunk_review_section,
                        selected_doc_name,
                        selected_doc_id,
                        current_chunks,
                        current_chunk_index,
                        chunk_navigation_info,
                        chunk_list_navigator,
                        current_chunk_header,
                        chunk_page_info,
                        chunk_content,
                        chunk_metadata,
                        chunk_metadata_formatted,
                        chunk_analysis,
                        chunk_token_count,
                        chunk_char_count,
                        chunk_lines_count,
                        chunk_context,
                        connection_status,
                        doc_info_card,
                        filtered_chunk_indices
                    ]
                )

                # Sidebar chunk navigator - click on any chunk
                chunk_list_navigator.select(
                    fn=select_chunk_from_sidebar,
                    inputs=[current_chunks],
                    outputs=[
                        current_chunk_index,
                        current_chunk_header,
                        chunk_page_info,
                        chunk_content,
                        chunk_metadata,
                        chunk_metadata_formatted,
                        chunk_analysis,
                        chunk_token_count,
                        chunk_char_count,
                        chunk_lines_count,
                        chunk_context
                    ]
                )

                # Search within chunks
                chunk_search_btn.click(
                    fn=search_chunks,
                    inputs=[chunk_search_input, current_chunks],
                    outputs=[
                        chunk_list_navigator,
                        filtered_chunk_indices,
                        connection_status
                    ]
                )

                # Refresh all chunks
                refresh_chunks_btn.click(
                    fn=refresh_chunks,
                    inputs=[selected_doc_id],
                    outputs=[
                        current_chunks,
                        current_chunk_index,
                        chunk_navigation_info,
                        chunk_list_navigator,
                        current_chunk_header,
                        chunk_page_info,
                        chunk_content,
                        chunk_metadata,
                        chunk_metadata_formatted,
                        chunk_analysis,
                        chunk_token_count,
                        chunk_char_count,
                        chunk_lines_count,
                        chunk_context,
                        filtered_chunk_indices,
                        connection_status
                    ]
                )

                # Close viewer
                close_viewer_btn.click(
                    fn=close_chunk_viewer,
                    outputs=[
                        chunk_review_section,
                        connection_status
                    ]
                )

                # Export current chunk
                export_chunk_btn.click(
                    fn=export_current_chunk,
                    inputs=[current_chunk_index, current_chunks, selected_doc_name],
                    outputs=[connection_status]
                )

        gr.Markdown("---")
        gr.Markdown("Built with ❤️ using Gradio | Powered by Azure AI")

    return demo


# =============================================================================
# Main
# =============================================================================

def launch():
    """Entry point for prepdocs-ui command."""
    print("🚀 Starting Gradio UI for Document Indexing Pipeline...")
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"🔧 Loading .env file...")

    # Create and launch UI
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    launch()
