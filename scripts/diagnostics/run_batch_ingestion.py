"""Run batch ingestion for 7 files and time it."""
import asyncio
import time
from pathlib import Path
from ingestor.config import PipelineConfig
from ingestor.pipeline import Pipeline

async def run_ingestion():
    """Run ingestion for 7 test files."""

    # Files to process (7 diverse documents)
    files = [
        "data/sample_basic.pdf",
        "data/sample_complex.pdf",
        "data/Figures.pdf",
        "data/Tables.pdf",
        "data/research_paper.pdf",
        "data/medical_who_report.pdf",
        "data/legal_irs_form.pdf"
    ]

    # Verify files exist
    print("=" * 80)
    print("BATCH INGESTION - 7 FILES")
    print("=" * 80)
    print("\nFiles to process:")
    total_size = 0
    for i, f in enumerate(files, 1):
        path = Path(f)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"  {i}. {path.name} ({size_mb:.2f} MB)")
        else:
            print(f"  {i}. {path.name} [NOT FOUND]")

    print(f"\nTotal size: {total_size:.2f} MB")
    print()

    # Load config
    config = PipelineConfig.from_env()
    print(f"Configuration:")
    print(f"  Index: {config.search.index_name}")
    print(f"  Embedding mode: {'Client-Side' if not config.use_integrated_vectorization else 'Integrated'}")
    print()

    # Create pipeline
    pipeline = Pipeline(config)

    try:
        # Start timing
        print("=" * 80)
        print("STARTING INGESTION")
        print("=" * 80)
        start_time = time.time()

        # Run ingestion
        status = await pipeline.ingest_documents(files, action="add")

        # End timing
        end_time = time.time()
        elapsed = end_time - start_time

        # Results
        print()
        print("=" * 80)
        print("INGESTION COMPLETE")
        print("=" * 80)
        print(f"\nTotal time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        print(f"\nResults:")
        print(f"  Total documents: {status.total_documents}")
        print(f"  Successful: {status.successful_documents}")
        print(f"  Failed: {status.failed_documents}")
        print(f"  Total chunks indexed: {status.total_chunks_indexed}")
        print(f"  Success rate: {status.get_summary()['success_rate']}")

        # Per-document breakdown
        print(f"\nPer-Document Results:")
        print("-" * 80)
        for result in status.results:
            status_icon = "[OK]" if result.success else "[FAIL]"
            time_str = f"{result.processing_time_seconds:.2f}s" if result.processing_time_seconds else "N/A"
            chunks_str = f"{result.chunks_indexed} chunks" if result.success else result.error_message
            print(f"  {status_icon} {result.filename}: {chunks_str} ({time_str})")

        # Performance metrics
        print(f"\nPerformance:")
        print(f"  Average time per document: {elapsed / status.total_documents:.2f}s")
        print(f"  Average time per chunk: {elapsed / status.total_chunks_indexed:.2f}s")
        print(f"  Throughput: {status.total_chunks_indexed / elapsed:.2f} chunks/second")
        print(f"  Document throughput: {total_size / elapsed:.2f} MB/second")

    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(run_ingestion())
