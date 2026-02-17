"""Cloud Setup: Azure AI Search + Cohere Embeddings

This example demonstrates a cloud-based document processing pipeline
using Azure AI Search for vector storage and Cohere's v3 multilingual
embeddings API.

Features:
- ✅ Enterprise-grade Azure Search
- ✅ Cohere v3 multilingual embeddings (100+ languages)
- ✅ Scalable cloud infrastructure
- ✅ Good cost optimization (Cohere is competitive)

Requirements:
    pip install cohere

Environment Variables Required:
    AZURE_SEARCH_SERVICE (or AZURE_SEARCH_ENDPOINT)
    AZURE_SEARCH_INDEX
    AZURE_SEARCH_KEY
    COHERE_API_KEY
    AZURE_STORAGE_ACCOUNT
    AZURE_STORAGE_KEY (or AZURE_STORAGE_CONNECTION_STRING)
    AZURE_STORAGE_CONTAINER

Usage:
    # Set environment variables in .env file
    python examples/azure_search_cohere.py
"""

import asyncio
import os
from pathlib import Path

# Load from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed. Using system environment variables.")

# Set additional configuration (override .env if needed)
os.environ.update({
    # Vector Store: Azure AI Search
    "VECTOR_STORE_MODE": "azure_search",
    # AZURE_SEARCH_SERVICE, AZURE_SEARCH_INDEX, AZURE_SEARCH_KEY from .env

    # Embeddings: Cohere v3 Multilingual
    "EMBEDDINGS_MODE": "cohere",
    "COHERE_MODEL_NAME": "embed-multilingual-v3.0",  # 1024 dims, 100+ languages
    "COHERE_INPUT_TYPE": "search_document",
    # COHERE_API_KEY from .env

    # Important: Disable integrated vectorization (using Cohere, not Azure OpenAI)
    "AZURE_USE_INTEGRATED_VECTORIZATION": "false",

    # Input: Blob storage
    "INPUT_MODE": "blob",
    # AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY, AZURE_STORAGE_CONTAINER from .env

    # Artifacts: Blob storage
    "ARTIFACTS_MODE": "blob",
    "AZURE_ARTIFACTS_CONTAINER": "artifacts",

    # Document Processing
    "OFFICE_EXTRACTOR_MODE": "hybrid",  # Try Azure DI, fallback to MarkItDown

    # Chunking settings
    "CHUNKING_MAX_CHARS": "2000",
    "CHUNKING_MAX_TOKENS": "500",
    "CHUNKING_OVERLAP_PERCENT": "10",

    # Logging
    "LOG_LEVEL": "INFO",
})

from ingestor import Pipeline
from ingestor.config import PipelineConfig


def check_required_env_vars():
    """Check that all required environment variables are set."""
    required = [
        "AZURE_SEARCH_SERVICE",  # or AZURE_SEARCH_ENDPOINT
        "AZURE_SEARCH_INDEX",
        "AZURE_SEARCH_KEY",
        "COHERE_API_KEY",
        "AZURE_STORAGE_ACCOUNT",
        "AZURE_STORAGE_CONTAINER",
    ]

    missing = []
    for var in required:
        if var == "AZURE_SEARCH_SERVICE" and os.getenv("AZURE_SEARCH_ENDPOINT"):
            continue  # AZURE_SEARCH_ENDPOINT is alternative
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print()
        print("Please set these in your .env file or environment.")
        print()
        print("Example .env file:")
        print("-" * 80)
        print("""
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
AZURE_SEARCH_KEY=your-admin-key

COHERE_API_KEY=your-cohere-api-key

AZURE_STORAGE_ACCOUNT=yourstorage
AZURE_STORAGE_KEY=your-storage-key
AZURE_STORAGE_CONTAINER=documents

# Optional: Document Intelligence for better extraction
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key
        """)
        print("-" * 80)
        return False

    return True


async def main():
    """Run the Azure Search + Cohere pipeline."""

    print("=" * 80)
    print("Cloud Processing: Azure AI Search + Cohere Embeddings")
    print("=" * 80)
    print()

    # Check environment variables
    if not check_required_env_vars():
        return

    # Load configuration from environment
    print("Loading configuration...")
    try:
        config = PipelineConfig.from_env()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    print(f"✅ Vector Store: {config.vector_store_mode.value if config.vector_store_mode else 'N/A'}")
    print(f"✅ Embeddings: {config.embeddings_mode.value if config.embeddings_mode else 'N/A'}")
    print(f"✅ Search Service: {config.search.endpoint if config.search else 'N/A'}")
    print(f"✅ Search Index: {config.search.index_name if config.search else 'N/A'}")
    print()

    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = Pipeline(config)

    # Validate configuration
    print("Validating configuration...")
    try:
        await pipeline.validate()
        print("✅ Configuration valid")
    except RuntimeError as e:
        print(f"❌ Validation failed: {e}")
        print()
        print("Common issues:")
        print("- cohere not installed: pip install cohere")
        print("- Invalid API keys")
        print("- Azure Search index doesn't exist")
        print("- No documents in blob storage")
        return

    print()

    # Run pipeline
    print("Processing documents from blob storage...")
    print()

    try:
        results = await pipeline.run()

        print()
        print("=" * 80)
        print("Processing Complete!")
        print("=" * 80)
        print(f"Documents processed: {len(results.results)}")
        print(f"Total chunks: {sum(r.num_chunks for r in results.results if r.status == 'success')}")
        print(f"Success: {sum(1 for r in results.results if r.status == 'success')}")
        print(f"Failed: {sum(1 for r in results.results if r.status == 'failed')}")
        print()
        print(f"Azure Search Index: {config.search.index_name}")
        print(f"Search Endpoint: {config.search.endpoint}")
        print()
        print("Your documents are now indexed and searchable in Azure AI Search!")
        print()
        print("Next steps:")
        print("- Use Azure Portal to browse your index")
        print("- Query your index via REST API or SDK")
        print("- Integrate with your application")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        raise

    finally:
        # Cleanup
        await pipeline.close()


if __name__ == "__main__":
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print()
        print("⚠️  No .env file found. Create one with your Azure and Cohere credentials.")
        print()

    # Run the pipeline
    asyncio.run(main())
