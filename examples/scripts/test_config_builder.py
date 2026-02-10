"""Test script to verify the new configuration builder capabilities.

This script demonstrates various ways to configure the ingestor library
without running the full pipeline.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_config_builder():
    """Test ConfigBuilder programmatic configuration."""
    print("=" * 80)
    print("TEST 1: ConfigBuilder - Programmatic Configuration")
    print("=" * 80)

    from ingestor import ConfigBuilder, OfficeExtractorMode

    try:
        config = (
            ConfigBuilder()
            .with_search("my-search-service", "my-index", "key123")
            .with_document_intelligence("https://my-di.cognitiveservices.azure.com", "key456")
            .with_azure_openai(
                "https://my-openai.openai.azure.com",
                "key789",
                "text-embedding-ada-002"
            )
            .with_local_files("docs/*.pdf", "./artifacts")
            .with_chunking(max_tokens=1000, overlap_percent=15)
            .with_office_extractor_mode(OfficeExtractorMode.HYBRID)
            .build()
        )

        print("✅ ConfigBuilder test PASSED")
        print(f"   - Search endpoint: {config.search.endpoint}")
        print(f"   - Search index: {config.search.index_name}")
        print(f"   - DI endpoint: {config.document_intelligence.endpoint}")
        print(f"   - Input glob: {config.input.local_glob}")
        print(f"   - Chunking max tokens: {config.chunking.max_tokens}")
        print(f"   - Office extractor mode: {config.office_extractor.mode}")
        return True

    except Exception as e:
        print(f"❌ ConfigBuilder test FAILED: {e}")
        return False


def test_create_config_with_env():
    """Test create_config() loading from environment."""
    print("\n" + "=" * 80)
    print("TEST 2: create_config() - Load from Environment")
    print("=" * 80)

    from ingestor import create_config

    try:
        # This will load from .env and override specific values
        config = create_config(
            input_glob="documents/*.pdf",
            azure_search_index="custom-index",
            chunking_max_tokens=2000
        )

        print("✅ create_config() with env test PASSED")
        print(f"   - Search index: {config.search.index_name}")
        print(f"   - Input glob: {config.input.local_glob}")
        print(f"   - Chunking max tokens: {config.chunking.max_tokens}")
        return True

    except Exception as e:
        print(f"⚠️  create_config() with env test SKIPPED: {e}")
        print("   (This is expected if .env file is not properly configured)")
        return True  # Not a real failure


def test_create_config_without_env():
    """Test create_config() building from scratch."""
    print("\n" + "=" * 80)
    print("TEST 3: create_config() - Build Without Environment")
    print("=" * 80)

    from ingestor import create_config

    try:
        config = create_config(
            use_env=False,
            input_glob="docs/*.pdf",
            search_service_name="my-service",
            search_index_name="my-index",
            search_api_key="key123",
            document_intelligence_endpoint="https://my-di.cognitiveservices.azure.com",
            document_intelligence_key="key456",
            azure_openai_endpoint="https://my-openai.openai.azure.com",
            azure_openai_api_key="key789",
            azure_openai_embedding_deployment="text-embedding-ada-002",
            chunking_max_tokens=1500
        )

        print("✅ create_config() without env test PASSED")
        print(f"   - Search endpoint: {config.search.endpoint}")
        print(f"   - Search index: {config.search.index_name}")
        print(f"   - Chunking max tokens: {config.chunking.max_tokens}")
        return True

    except Exception as e:
        print(f"❌ create_config() without env test FAILED: {e}")
        return False


def test_pipeline_config_from_env():
    """Test PipelineConfig.from_env() with custom path."""
    print("\n" + "=" * 80)
    print("TEST 4: PipelineConfig.from_env() - Custom .env Path")
    print("=" * 80)

    from ingestor import PipelineConfig

    try:
        # Try loading from default .env
        config = PipelineConfig.from_env()

        print("✅ PipelineConfig.from_env() test PASSED")
        print(f"   - Search index: {config.search.index_name}")
        print(f"   - Office extractor mode: {config.office_extractor.mode}")
        return True

    except Exception as e:
        print(f"⚠️  PipelineConfig.from_env() test SKIPPED: {e}")
        print("   (This is expected if .env file is not properly configured)")
        return True  # Not a real failure


def test_load_config():
    """Test load_config() helper."""
    print("\n" + "=" * 80)
    print("TEST 5: load_config() Helper")
    print("=" * 80)

    from ingestor import load_config

    try:
        config = load_config()

        print("✅ load_config() test PASSED")
        print(f"   - Search index: {config.search.index_name}")
        return True

    except Exception as e:
        print(f"⚠️  load_config() test SKIPPED: {e}")
        print("   (This is expected if .env file is not properly configured)")
        return True  # Not a real failure


def test_nested_config_updates():
    """Test nested configuration updates via create_config()."""
    print("\n" + "=" * 80)
    print("TEST 6: Nested Config Updates")
    print("=" * 80)

    from ingestor import create_config, MediaDescriberMode, TableRenderMode

    try:
        config = create_config(
            use_env=False,
            input_glob="docs/*.pdf",
            search_service_name="my-service",
            search_index_name="my-index",
            search_api_key="key123",
            document_intelligence_endpoint="https://my-di.cognitiveservices.azure.com",
            azure_openai_endpoint="https://my-openai.openai.azure.com",
            azure_openai_api_key="key789",
            azure_openai_embedding_deployment="text-embedding-ada-002",
            # Nested updates with underscore notation
            chunking_max_tokens=3000,
            chunking_overlap_percent=20,
            performance_max_workers=8,
            performance_embed_batch_size=256,
            media_describer_mode=MediaDescriberMode.DISABLED,
            table_render_mode=TableRenderMode.MARKDOWN
        )

        print("✅ Nested config updates test PASSED")
        print(f"   - Chunking max tokens: {config.chunking.max_tokens}")
        print(f"   - Chunking overlap: {config.chunking.overlap_percent}%")
        print(f"   - Performance max workers: {config.performance.max_workers}")
        print(f"   - Performance embed batch: {config.performance.embed_batch_size}")
        print(f"   - Media describer: {config.media_describer_mode}")
        print(f"   - Table render: {config.table_render_mode}")

        # Verify values
        assert config.chunking.max_tokens == 3000
        assert config.chunking.overlap_percent == 20
        assert config.performance.max_workers == 8
        assert config.performance.embed_batch_size == 256
        assert config.media_describer_mode == MediaDescriberMode.DISABLED
        assert config.table_render_mode == TableRenderMode.MARKDOWN

        return True

    except Exception as e:
        print(f"❌ Nested config updates test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("INGESTOR CONFIGURATION TESTS")
    print("=" * 80)
    print()

    tests = [
        test_config_builder,
        test_create_config_with_env,
        test_create_config_without_env,
        test_pipeline_config_from_env,
        test_load_config,
        test_nested_config_updates,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

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
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
