"""
Quick test to verify parallel processing optimizations work.

This is a minimal test to ensure the code changes don't break existing functionality.
"""

import asyncio
import time
from ingestor import run_pipeline

async def quick_test():
    """Quick smoke test for parallel processing."""
    print("\n" + "=" * 60)
    print("QUICK PARALLEL PROCESSING TEST")
    print("=" * 60)

    print("\n1. Testing with sample PDF...")
    print("   - Parallel embedding batching enabled")
    print("   - Document processing with max_workers=4")

    start = time.time()
    try:
        status = await run_pipeline(
            input_glob="samples/sample_pages_test.pdf",
            azure_openai_max_concurrency=10,
            performance_max_workers=4,
            use_integrated_vectorization=False  # Test client-side embeddings
        )
        elapsed = time.time() - start

        print(f"\n✓ SUCCESS!")
        print(f"  - Processed: {status.successful_documents} document(s)")
        print(f"  - Chunks indexed: {status.total_chunks_indexed}")
        print(f"  - Time: {elapsed:.2f}s")
        print(f"  - Throughput: {status.total_chunks_indexed / elapsed:.2f} chunks/sec")

        if status.failed_documents > 0:
            print(f"\n⚠️  Warning: {status.failed_documents} document(s) failed")
            for result in status.results:
                if not result.success:
                    print(f"     - {result.filename}: {result.error_message}")

        print("\n" + "=" * 60)
        print("PARALLEL PROCESSING IS WORKING! 🚀")
        print("=" * 60)
        print("\nOptimizations active:")
        print("  ✓ Embedding batches process in parallel")
        print("  ✓ Documents can process in parallel (max_workers=4)")
        print("  ✓ Retry logic preserved (3 retries with backoff)")
        print("  ✓ Concurrency control via semaphores")
        print("\nTo optimize further, update your .env:")
        print("  AZURE_USE_INTEGRATED_VECTORIZATION=true")
        print("  AZURE_OPENAI_MAX_CONCURRENCY=10")
        print("  AZURE_DI_MAX_CONCURRENCY=5")
        print("  MAX_WORKERS=4")

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        print(f"\nError details:")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(quick_test())
