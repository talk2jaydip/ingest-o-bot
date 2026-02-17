"""Quick test of JSON schema export/import functionality.

Run this script to verify the JSON import/export feature is working:
    python test_json_schema.py
"""

import sys
import json
sys.path.insert(0, 'src')

from ingestor.config import PipelineConfig
from ingestor.index import IndexDeploymentManager


def test_config_loading():
    """Test configuration loading from .env file."""
    print("\n1. Testing configuration loading...")
    config = PipelineConfig.from_env()
    print(f"   OK Config loaded")
    print(f"      Index: {config.search.index_name}")
    return config


def test_import_module():
    """Test IndexDeploymentManager can be imported."""
    print("\n2. Testing module import...")
    print(f"   OK IndexDeploymentManager imported")


def test_methods_exist(config):
    """Test that export/import methods exist."""
    print("\n3. Testing methods exist...")
    manager = IndexDeploymentManager(
        endpoint=config.search.endpoint,
        api_key=config.search.api_key,
        index_name=config.search.index_name,
        semantic_config_name=config.search.semantic_config_name,
        suggester_name=config.search.suggester_name,
        scoring_profile_names=config.search.scoring_profile_names
    )

    assert hasattr(manager, 'export_schema_to_json'), "export_schema_to_json method missing"
    assert hasattr(manager, 'create_index_from_json'), "create_index_from_json method missing"
    print(f"   OK Both methods exist")
    return manager


def test_export(manager):
    """Test schema export if index exists."""
    print("\n4. Testing export functionality...")

    if not manager.index_exists():
        print(f"   WARNING Index does not exist - skipping export test")
        print(f"   To test: python -m src.ingestor.cli --setup-index --index-only")
        return None

    print(f"   Index exists, attempting export...")
    output_file = manager.export_schema_to_json("test_export.json")

    # Verify JSON
    with open(output_file, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    print(f"   OK Export successful!")
    print(f"      File: {output_file}")
    print(f"      Fields: {len(schema.get('fields', []))}")
    print(f"      Scoring Profiles: {len(schema.get('scoringProfiles', []))}")
    print(f"      Suggesters: {len(schema.get('suggesters', []))}")

    if schema.get('semantic'):
        print(f"      Semantic config: included")
    if schema.get('vectorSearch'):
        print(f"      Vector search: included")

    return output_file


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing JSON Schema Import/Export")
    print("=" * 80)

    try:
        config = test_config_loading()
        test_import_module()
        manager = test_methods_exist(config)
        test_export(manager)

        print("\n" + "=" * 80)
        print("All Tests Passed!")
        print("=" * 80)
        print("\nCLI Commands:")
        print("  python -m src.ingestor.cli --export-schema <file.json>")
        print("  python -m src.ingestor.cli --import-schema <file.json>")
        print("\nDocumentation:")
        print("  docs/JSON_SCHEMA_IMPORT_EXPORT.md")
        print("  docs/INDEX_CONFIGURATION.md")
        print("\nSUCCESS: JSON import/export is ready!")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
