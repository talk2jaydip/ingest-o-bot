"""Process documents from Azure Blob Storage."""

import asyncio
from ingestor import Pipeline, create_config
from ingestor.config import InputMode, ArtifactsMode


async def main():
    """Process documents from Azure Blob Storage."""
    print("🚀 Azure Blob Storage Integration Example")
    print("=" * 60)

    # Create configuration for blob storage input
    config = create_config(
        # Input from blob storage
        input_mode=InputMode.BLOB_STORAGE,
        blob_container_name="documents",  # Your blob container
        blob_glob="**/*.pdf",            # Process all PDFs in container

        # Output artifacts to blob storage (optional)
        artifacts_mode=ArtifactsMode.BLOB_STORAGE,
        artifacts_container_name="artifacts",

        # Azure Search index
        azure_search_index="documents-index"
    )

    # Create and run pipeline
    pipeline = Pipeline(config)
    try:
        print("\n📂 Reading documents from blob storage...")
        print(f"   Container: {config.input.blob.container_name}")
        print(f"   Pattern: {config.input.blob.glob}")
        print()

        status = await pipeline.run()

        # Display results
        print()
        print("=" * 60)
        print("📊 Results:")
        print("=" * 60)
        print(f"✅ Successful documents: {status.successful_documents}")
        print(f"❌ Failed documents: {status.failed_documents}")
        print(f"📦 Total chunks indexed: {status.total_chunks_indexed}")
        print()

        if status.results:
            print("📋 Document Details:")
            for result in status.results:
                if result.success:
                    print(f"  ✅ {result.filename}: {result.chunks_indexed} chunks")
                else:
                    print(f"  ❌ {result.filename}: {result.error_message}")

        print("=" * 60)

    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
