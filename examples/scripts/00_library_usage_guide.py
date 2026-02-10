"""Comprehensive guide to using ingestor as a Python library.

This example demonstrates all the ways to configure and use the ingestor library
for document ingestion. No API or web service needed - just import and use!

Usage patterns:
1. Load from .env file (simplest)
2. Build configuration programmatically (most flexible)
3. Hybrid approach (load from .env, override specific values)
4. Multiple environment configurations (dev, staging, prod)
"""

import asyncio
from pathlib import Path


# ============================================================================
# PATTERN 1: Load from .env file (Simplest)
# ============================================================================
async def example_1_load_from_env():
    """Simplest approach: Load all config from .env file and run."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Load Configuration from .env File")
    print("=" * 80)

    from ingestor import run_pipeline

    # One-liner: load from .env and process documents
    status = await run_pipeline(input_glob="samples/*.pdf")

    print(f"✅ Processed {status.successful_documents} documents")
    print(f"📦 Indexed {status.total_chunks_indexed} chunks")


# ============================================================================
# PATTERN 2: ConfigBuilder (Most Flexible - No Environment Needed)
# ============================================================================
async def example_2_config_builder():
    """Build configuration entirely in code without environment variables."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: ConfigBuilder - Programmatic Configuration")
    print("=" * 80)

    from ingestor import Pipeline, ConfigBuilder, OfficeExtractorMode

    # Build config programmatically
    config = (
        ConfigBuilder()
        # Azure AI Search
        .with_search(
            service_name="your-search-service",
            index_name="documents-index",
            api_key="your-search-key"
        )
        # Azure Document Intelligence
        .with_document_intelligence(
            endpoint="https://your-di.cognitiveservices.azure.com",
            key="your-di-key",
            max_concurrency=3
        )
        # Azure OpenAI (for embeddings)
        .with_azure_openai(
            endpoint="https://your-openai.openai.azure.com",
            api_key="your-openai-key",
            embedding_deployment="text-embedding-3-large",
            embedding_model="text-embedding-3-large",
            embedding_dimensions=1536
        )
        # Input files
        .with_local_files(
            glob_pattern="documents/*.pdf",
            artifacts_dir="./my_artifacts"
        )
        # Chunking settings
        .with_chunking(
            max_tokens=1000,
            overlap_percent=15,
            cross_page_overlap=True
        )
        # Processing mode
        .with_office_extractor_mode(
            mode=OfficeExtractorMode.HYBRID,
            offline_fallback=True
        )
        # Performance tuning
        .with_performance(
            max_workers=8,
            embed_batch_size=256
        )
        .build()
    )

    # Run pipeline with custom config
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"✅ Processed {status.successful_documents} documents")
        print(f"📦 Indexed {status.total_chunks_indexed} chunks")
    finally:
        await pipeline.close()


# ============================================================================
# PATTERN 3: Hybrid Approach (Load .env + Override)
# ============================================================================
async def example_3_hybrid_approach():
    """Load base config from .env, then override specific values."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Hybrid - Load from .env + Override Values")
    print("=" * 80)

    from ingestor import create_config, Pipeline

    # Load from .env but override specific settings
    config = create_config(
        input_glob="custom_docs/*.pdf",  # Override input
        azure_search_index="custom-index",  # Override index
        chunking_max_tokens=2000,  # Override chunking
        chunking_overlap_percent=20,
        performance_max_workers=16  # Override performance
    )

    # Run with hybrid config
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"✅ Processed {status.successful_documents} documents")
    finally:
        await pipeline.close()


# ============================================================================
# PATTERN 4: Multiple Environments (Dev, Staging, Prod)
# ============================================================================
async def example_4_multiple_environments():
    """Use different .env files for different environments."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Multiple Environments (Dev/Staging/Prod)")
    print("=" * 80)

    from ingestor import PipelineConfig, Pipeline

    # Load from environment-specific .env file
    environment = "staging"  # Could be from os.getenv("ENVIRONMENT")
    env_file = f".env.{environment}"

    config = PipelineConfig.from_env(env_path=env_file)

    # Run with environment-specific config
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"✅ Processed {status.successful_documents} documents in {environment}")
    finally:
        await pipeline.close()


# ============================================================================
# PATTERN 5: Full Programmatic Control (Advanced)
# ============================================================================
async def example_5_full_control():
    """Complete programmatic control over all settings."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Full Programmatic Control")
    print("=" * 80)

    from ingestor import (
        ConfigBuilder,
        Pipeline,
        OfficeExtractorMode,
        TableRenderMode,
        MediaDescriberMode,
        DocumentAction
    )

    # Build complete configuration
    config = (
        ConfigBuilder()
        # Core Azure services
        .with_search("my-search", "my-index", "key123")
        .with_document_intelligence("https://my-di.cognitiveservices.azure.com", "key456")
        .with_azure_openai(
            "https://my-openai.openai.azure.com",
            "key789",
            "text-embedding-ada-002"
        )
        # Input and output
        .with_local_files("data/*.pdf", "./output")
        # Processing options
        .with_office_extractor_mode(OfficeExtractorMode.HYBRID, offline_fallback=True)
        .with_media_descriptions(MediaDescriberMode.GPT4O)
        .with_table_rendering(TableRenderMode.MARKDOWN, generate_summaries=True)
        .with_document_action(DocumentAction.ADD)
        # Performance
        .with_chunking(max_tokens=800, overlap_percent=10)
        .with_performance(max_workers=4, embed_batch_size=128)
        .build()
    )

    # Run pipeline
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"✅ Success! Processed {status.successful_documents} documents")
        print(f"   Total chunks indexed: {status.total_chunks_indexed}")
        print(f"   Duration: {status.duration_seconds:.2f}s")
        print(f"   Chunks per document: {status.total_chunks_indexed / status.successful_documents:.1f}")
    finally:
        await pipeline.close()


# ============================================================================
# PATTERN 6: Minimal Setup (Just the essentials)
# ============================================================================
async def example_6_minimal():
    """Minimal configuration for quick prototyping."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Minimal Configuration")
    print("=" * 80)

    from ingestor import create_config, Pipeline, OfficeExtractorMode

    # Minimal config - only required fields
    config = create_config(
        use_env=False,
        input_glob="test/*.pdf",
        search_service_name="search-service",
        search_index_name="test-index",
        search_api_key="key",
        document_intelligence_endpoint="https://di.cognitiveservices.azure.com",
        document_intelligence_key="key",
        azure_openai_endpoint="https://openai.openai.azure.com",
        azure_openai_api_key="key",
        azure_openai_embedding_deployment="text-embedding-ada-002"
    )

    print("✅ Minimal config created successfully")
    print(f"   Search endpoint: {config.search.endpoint}")
    print(f"   Input glob: {config.input.local_glob}")


# ============================================================================
# PATTERN 7: Azure Blob Storage Input/Output
# ============================================================================
async def example_7_blob_storage():
    """Configure for Azure Blob Storage input and output."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Azure Blob Storage Configuration")
    print("=" * 80)

    from ingestor import ConfigBuilder, Pipeline

    config = (
        ConfigBuilder()
        # Core services
        .with_search("my-search", "my-index", "key")
        .with_document_intelligence("https://my-di.cognitiveservices.azure.com", "key")
        .with_azure_openai("https://my-openai.openai.azure.com", "key", "embedding-model")
        # Blob storage input
        .with_blob_input(
            account_url="https://mystorage.blob.core.windows.net",
            container_in="documents",
            prefix="inbox/",
            account_key="storage-key"
        )
        # Blob storage output for artifacts
        .with_blob_artifacts(
            account_url="https://mystorage.blob.core.windows.net",
            container_pages="pages",
            container_chunks="chunks",
            container_images="images",
            account_key="storage-key"
        )
        .build()
    )

    print("✅ Blob storage config created")
    print(f"   Input container: {config.input.blob_container_in}")
    print(f"   Output pages: {config.artifacts.blob_container_pages}")


# ============================================================================
# PATTERN 8: Synchronous Usage (Non-async contexts)
# ============================================================================
def example_8_synchronous():
    """Use the library in synchronous (non-async) contexts."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Synchronous Usage")
    print("=" * 80)

    from ingestor import sync_run_pipeline

    # Synchronous wrapper - no async/await needed
    status = sync_run_pipeline(
        input_glob="documents/*.pdf",
        azure_search_index="my-index"
    )

    print(f"✅ Processed {status.successful_documents} documents (synchronously)")


# ============================================================================
# Main: Show all examples
# ============================================================================
def main():
    """Run all examples (as demonstrations, not actual processing)."""
    print("=" * 80)
    print("INGESTOR LIBRARY USAGE GUIDE")
    print("=" * 80)
    print()
    print("This guide shows different ways to use the ingestor library.")
    print("No API or web service needed - just import and use!")
    print()

    # Show the examples (most don't actually run to avoid requiring credentials)
    examples = [
        ("Load from .env", example_1_load_from_env),
        ("ConfigBuilder", example_2_config_builder),
        ("Hybrid Approach", example_3_hybrid_approach),
        ("Multiple Environments", example_4_multiple_environments),
        ("Full Control", example_5_full_control),
        ("Minimal Setup", example_6_minimal),
        ("Blob Storage", example_7_blob_storage),
        ("Synchronous", example_8_synchronous),
    ]

    print("Available Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nNote: Most examples are for demonstration only.")
    print("To actually run ingestion, ensure you have valid Azure credentials.")
    print()

    # Run non-async examples that just show configuration
    try:
        asyncio.run(example_6_minimal())
    except Exception as e:
        print(f"Example 6 skipped: {e}")

    try:
        asyncio.run(example_7_blob_storage())
    except Exception as e:
        print(f"Example 7 skipped: {e}")

    print("\n" + "=" * 80)
    print("Key Takeaways:")
    print("=" * 80)
    print("1. 📦 Import the library - no API server needed")
    print("2. ⚙️  Configure via .env, code, or hybrid approach")
    print("3. 🚀 Run end-to-end ingestion in your process")
    print("4. 🎯 Full control over all settings and credentials")
    print("5. 🔄 Use sync or async patterns as needed")
    print()
    print("Perfect for:")
    print("  - Data pipelines and ETL workflows")
    print("  - Batch processing scripts")
    print("  - Jupyter notebooks and exploration")
    print("  - Integration into existing applications")
    print("  - CI/CD automation")


if __name__ == "__main__":
    main()
