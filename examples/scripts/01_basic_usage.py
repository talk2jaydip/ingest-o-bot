"""Basic usage example for ingestor library.

This example demonstrates the simplest way to use ingestor:
- Load configuration from .env file
- Process documents with a glob pattern
- Display results

Requirements:
    - .env file with configuration (see envs/.env.example)
    - Documents in ./documents/ directory

Usage:
    python examples/scripts/01_basic_usage.py
"""

import asyncio
from ingestor import run_pipeline


async def main():
    """Process documents with default configuration from .env file."""
    print("🚀 Starting document ingestion pipeline...")
    print("📄 Processing documents from environment configuration")
    print()

    # Process documents (configuration loaded from .env)
    # Works with any vector store and embeddings provider configured in .env
    status = await run_pipeline(input_glob="documents/*.pdf")

    # Print results
    print()
    print("=" * 60)
    print("📊 Pipeline Results")
    print("=" * 60)
    print(f"✅ Successfully processed: {status.successful_documents} documents")
    print(f"❌ Failed: {status.failed_documents} documents")
    print(f"📦 Total chunks indexed: {status.total_chunks_indexed}")
    print()

    # Show individual results
    if status.results:
        print("Document Details:")
        print("-" * 60)
        for result in status.results:
            status_icon = "✅" if result.success else "❌"
            print(f"{status_icon} {result.filename}: {result.chunks_indexed} chunks")
            if not result.success and result.error_message:
                print(f"   Error: {result.error_message}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
