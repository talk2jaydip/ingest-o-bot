"""Process multiple document sets in batches."""

import asyncio
from pathlib import Path
from ingestor import run_pipeline


async def process_batch(glob_pattern: str, index_name: str):
    """Process a batch of documents to a specific index."""
    print(f"\n📂 Processing: {glob_pattern} → {index_name}")
    print("-" * 60)

    status = await run_pipeline(
        input_glob=glob_pattern,
        azure_search_index=index_name
    )

    print(f"  ✅ {status.successful_documents} documents indexed")
    print(f"  📦 {status.total_chunks_indexed} chunks created")

    return status


async def main():
    """Process multiple document collections."""
    print("🚀 Batch Processing Multiple Document Sets")
    print("=" * 60)

    # Define your document batches
    batches = [
        ("legal/*.pdf", "legal-docs-index"),
        ("medical/*.pdf", "medical-docs-index"),
        ("technical/*.pdf", "technical-docs-index"),
    ]

    total_docs = 0
    total_chunks = 0

    # Process each batch sequentially
    for glob_pattern, index_name in batches:
        try:
            status = await process_batch(glob_pattern, index_name)
            total_docs += status.successful_documents
            total_chunks += status.total_chunks_indexed
        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Final summary
    print()
    print("=" * 60)
    print("📊 Overall Summary")
    print("=" * 60)
    print(f"✅ Total documents processed: {total_docs}")
    print(f"📦 Total chunks indexed: {total_chunks}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
