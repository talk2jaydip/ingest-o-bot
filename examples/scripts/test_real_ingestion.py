"""Real end-to-end test using sample documents and actual configuration.

This test demonstrates:
1. Loading config from .env
2. Using ConfigBuilder programmatically
3. Processing actual sample documents
4. Verifying the pipeline works end-to-end

Run this to verify the library works correctly!
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


async def test_1_env_config():
    """Test 1: Load configuration from .env and process samples."""
    print("\n" + "=" * 80)
    print("TEST 1: Real Ingestion with .env Configuration")
    print("=" * 80)

    try:
        from ingestor import Pipeline, PipelineConfig

        # Load config from .env
        config = PipelineConfig.from_env()

        # Override to use sample files
        config.input.local_glob = "samples/*.pdf"

        print(f"✅ Config loaded successfully")
        print(f"   - Search endpoint: {config.search.endpoint}")
        print(f"   - Search index: {config.search.index_name}")
        print(f"   - Input glob: {config.input.local_glob}")
        print(f"   - Office extractor mode: {config.office_extractor.mode}")
        print(f"   - Chunking max tokens: {config.chunking.max_tokens}")

        # Create pipeline
        pipeline = Pipeline(config)

        print("\n🚀 Starting ingestion...")
        try:
            status = await pipeline.run()

            print("\n✅ INGESTION COMPLETED SUCCESSFULLY!")
            print(f"   - Documents processed: {status.successful_documents}")
            print(f"   - Total chunks indexed: {status.total_chunks_indexed}")
            total_time = sum(r.processing_time_seconds or 0 for r in status.results)
            print(f"   - Total processing time: {total_time:.2f}s")
            print(f"   - Chunks per document: {status.total_chunks_indexed / max(status.successful_documents, 1):.1f}")

            if status.failed_documents > 0:
                print(f"   ⚠️  Failed documents: {status.failed_documents}")

            return True
        finally:
            await pipeline.close()

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_2_programmatic_config():
    """Test 2: Build configuration programmatically and process."""
    print("\n" + "=" * 80)
    print("TEST 2: Real Ingestion with Programmatic Configuration")
    print("=" * 80)

    try:
        from ingestor import Pipeline, create_config

        # Build config programmatically, loading from env but overriding specific values
        config = create_config(
            input_glob="samples/*.pdf",
            chunking_max_tokens=800,
            performance_max_workers=2
        )

        print(f"✅ Config created programmatically")
        print(f"   - Input: {config.input.local_glob}")
        print(f"   - Chunking: {config.chunking.max_tokens} tokens")
        print(f"   - Workers: {config.performance.max_workers}")

        # Create and run pipeline
        pipeline = Pipeline(config)

        print("\n🚀 Starting ingestion...")
        try:
            status = await pipeline.run()

            print("\n✅ INGESTION COMPLETED!")
            print(f"   - Documents: {status.successful_documents}")
            print(f"   - Chunks: {status.total_chunks_indexed}")
            total_time = sum(r.processing_time_seconds or 0 for r in status.results)
            print(f"   - Total processing time: {total_time:.2f}s")

            return True
        finally:
            await pipeline.close()

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_run_pipeline_helper():
    """Test 3: Use the run_pipeline() convenience function."""
    print("\n" + "=" * 80)
    print("TEST 3: Real Ingestion with run_pipeline() Helper")
    print("=" * 80)

    try:
        from ingestor import run_pipeline

        print("🚀 Running pipeline with one-liner...")

        # One-liner: load from env and override input
        status = await run_pipeline(input_glob="samples/*.pdf")

        print("\n✅ INGESTION COMPLETED!")
        print(f"   - Documents: {status.successful_documents}")
        print(f"   - Chunks: {status.total_chunks_indexed}")
        total_time = sum(r.processing_time_seconds or 0 for r in status.results)
        print(f"   - Total processing time: {total_time:.2f}s")

        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_config_builder_dry_run():
    """Test 4: ConfigBuilder without actual ingestion (dry run)."""
    print("\n" + "=" * 80)
    print("TEST 4: ConfigBuilder Dry Run (No Ingestion)")
    print("=" * 80)

    try:
        from ingestor import ConfigBuilder, OfficeExtractorMode, TableRenderMode
        import os

        # Get credentials from environment
        search_service = os.getenv("AZURE_SEARCH_SERVICE")
        search_index = os.getenv("AZURE_SEARCH_INDEX")
        search_key = os.getenv("AZURE_SEARCH_KEY")
        di_endpoint = os.getenv("AZURE_DOC_INT_ENDPOINT")
        di_key = os.getenv("AZURE_DOC_INT_KEY")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        openai_key = os.getenv("AZURE_OPENAI_KEY")
        openai_emb = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Build complete config
        config = (
            ConfigBuilder()
            .with_search(search_service, search_index, search_key)
            .with_document_intelligence(di_endpoint, di_key, max_concurrency=3)
            .with_azure_openai(openai_endpoint, openai_key, openai_emb)
            .with_local_files("samples/*.pdf", "./test_artifacts")
            .with_office_extractor_mode(OfficeExtractorMode.HYBRID, offline_fallback=True)
            .with_table_rendering(TableRenderMode.MARKDOWN, generate_summaries=False)
            .with_chunking(max_tokens=1000, overlap_percent=15)
            .with_performance(max_workers=4, embed_batch_size=128)
            .build()
        )

        print("✅ ConfigBuilder test PASSED")
        print(f"   - Search: {config.search.endpoint}")
        print(f"   - Index: {config.search.index_name}")
        print(f"   - DI: {config.document_intelligence.endpoint}")
        print(f"   - OpenAI: {config.azure_openai.endpoint}")
        print(f"   - Input: {config.input.local_glob}")
        print(f"   - Artifacts: {config.artifacts.local_dir}")
        print(f"   - Extractor mode: {config.office_extractor.mode}")
        print(f"   - Table render: {config.table_render_mode}")
        print(f"   - Chunking: {config.chunking.max_tokens} tokens, {config.chunking.overlap_percent}% overlap")
        print(f"   - Performance: {config.performance.max_workers} workers, {config.performance.embed_batch_size} batch")

        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 80)
    print("REAL END-TO-END INGESTION TESTS")
    print("=" * 80)
    print()
    print("These tests process actual sample documents using your .env configuration.")
    print("Make sure your .env file has valid Azure credentials!")
    print()

    # Check if sample files exist
    sample_path = Path("samples/sample_pages_test.pdf")
    if not sample_path.exists():
        print("⚠️  Warning: Sample file not found at samples/sample_pages_test.pdf")
        print("   Some tests may fail.")

    tests = [
        ("Config Builder Dry Run", test_4_config_builder_dry_run, False),  # Sync, no ingestion
        ("Load from .env", test_1_env_config, True),  # Async, with ingestion
        ("Programmatic Config", test_2_programmatic_config, True),  # Async, with ingestion
        ("run_pipeline() Helper", test_3_run_pipeline_helper, True),  # Async, with ingestion
    ]

    results = []
    for i, (name, test_func, is_async) in enumerate(tests, 1):
        print(f"\n{'=' * 80}")
        print(f"Running test {i}/{len(tests)}: {name}")
        print(f"{'=' * 80}")

        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed or were skipped")
        print("\nNOTE: Ingestion tests require valid Azure credentials in .env")
        print("If you see authentication errors, check your .env file.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
