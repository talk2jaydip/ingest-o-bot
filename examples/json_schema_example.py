"""Example: Azure AI Search Index JSON Schema Import/Export

This example demonstrates how to:
1. Export an existing index schema to JSON
2. Create a new index from a JSON schema file
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestor.config import PipelineConfig
from ingestor.index import IndexDeploymentManager


def example_export_schema():
    """Export current index schema to JSON file."""
    print("=" * 80)
    print("Example 1: Export Index Schema to JSON")
    print("=" * 80)

    # Load configuration from .env
    config = PipelineConfig.from_env()

    # Create index manager
    manager = IndexDeploymentManager(
        endpoint=config.search.endpoint,
        api_key=config.search.api_key,
        index_name=config.search.index_name,
        semantic_config_name=config.search.semantic_config_name,
        suggester_name=config.search.suggester_name,
        scoring_profile_names=config.search.scoring_profile_names
    )

    # Export schema to JSON file
    try:
        output_file = manager.export_schema_to_json("examples/exported_schema.json")
        print(f"\n✓ Schema exported successfully!")
        print(f"  File: {output_file}")
        print(f"\nYou can now:")
        print(f"  - Version control: git add {output_file}")
        print(f"  - Share with team: Send JSON file")
        print(f"  - Backup: Save for disaster recovery")
        print(f"  - Migrate: Use in different environment")
    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        print(f"  Make sure the index exists first:")
        print(f"  python -m src.ingestor.cli --setup-index --index-only")


def example_import_schema():
    """Create new index from JSON schema file."""
    print("\n" + "=" * 80)
    print("Example 2: Create Index from JSON Schema")
    print("=" * 80)

    # Load configuration from .env
    config = PipelineConfig.from_env()

    # For this example, we'll use a different index name to avoid conflicts
    # In production, you'd typically use the same name or a new environment
    new_index_name = f"{config.search.index_name}-from-json"

    print(f"\nCreating new index: {new_index_name}")
    print(f"From JSON file: examples/exported_schema.json")
    print(f"Note: Using a different index name to avoid overwriting existing index")

    # Create index manager with new index name
    manager = IndexDeploymentManager(
        endpoint=config.search.endpoint,
        api_key=config.search.api_key,
        index_name=new_index_name,
        semantic_config_name=config.search.semantic_config_name,
        suggester_name=config.search.suggester_name,
        scoring_profile_names=config.search.scoring_profile_names
    )

    # Import schema from JSON file
    try:
        json_file = "examples/exported_schema.json"

        if not os.path.exists(json_file):
            print(f"\n⚠️  JSON file not found: {json_file}")
            print(f"   Run example_export_schema() first to create it")
            return

        success = manager.create_index_from_json(json_file, skip_if_exists=True)

        if success:
            print(f"\n✓ Index created successfully from JSON!")
            print(f"  Index name: {new_index_name}")
            print(f"\nYou can now:")
            print(f"  - Ingest data: python -m src.ingestor.cli --glob 'data/*.pdf'")
            print(f"  - Check index: python -m src.ingestor.cli --check-index")
            print(f"  - Export again: python -m src.ingestor.cli --export-schema backup.json")
            print(f"\nTo use this index, update AZURE_SEARCH_INDEX in .env:")
            print(f"  AZURE_SEARCH_INDEX={new_index_name}")
    except Exception as e:
        print(f"\n✗ Import failed: {e}")


def example_backup_and_restore():
    """Example: Backup schema before making changes, then restore if needed."""
    print("\n" + "=" * 80)
    print("Example 3: Backup Before Changes (Recommended Pattern)")
    print("=" * 80)

    config = PipelineConfig.from_env()

    manager = IndexDeploymentManager(
        endpoint=config.search.endpoint,
        api_key=config.search.api_key,
        index_name=config.search.index_name,
        semantic_config_name=config.search.semantic_config_name,
        suggester_name=config.search.suggester_name,
        scoring_profile_names=config.search.scoring_profile_names
    )

    print(f"\nBest Practice Workflow:")
    print(f"1. Export current schema as backup")
    print(f"   python -m src.ingestor.cli --export-schema backups/schema_backup.json")

    print(f"\n2. Make your changes (e.g., add new fields, update scoring profiles)")
    print(f"   # Edit index.py or use programmatic updates")

    print(f"\n3. If something goes wrong, restore from backup:")
    print(f"   python -m src.ingestor.cli --delete-index")
    print(f"   python -m src.ingestor.cli --import-schema backups/schema_backup.json")

    print(f"\n4. Version control your schemas:")
    print(f"   git add backups/schema_backup.json")
    print(f"   git commit -m 'Backup schema before v2 changes'")


def example_migrate_environments():
    """Example: Migrate schema from dev to prod."""
    print("\n" + "=" * 80)
    print("Example 4: Migrate Schema Between Environments")
    print("=" * 80)

    print(f"\nEnvironment Migration Workflow:")

    print(f"\n1. Export schema from development:")
    print(f"   python -m src.ingestor.cli --env .env.dev --export-schema schemas/dev_schema.json")

    print(f"\n2. Review and test the schema:")
    print(f"   # Manually inspect schemas/dev_schema.json")
    print(f"   # Validate JSON: python -c 'import json; json.load(open(\"schemas/dev_schema.json\"))'")

    print(f"\n3. Import to production (after updating .env.prod with prod credentials):")
    print(f"   python -m src.ingestor.cli --env .env.prod --import-schema schemas/dev_schema.json")

    print(f"\n4. Verify production index:")
    print(f"   python -m src.ingestor.cli --env .env.prod --check-index")


def example_use_azure_portal_json():
    """Example: Use JSON exported from Azure Portal."""
    print("\n" + "=" * 80)
    print("Example 5: Import Schema from Azure Portal JSON")
    print("=" * 80)

    print(f"\nUsing Azure Portal JSON:")

    print(f"\n1. Export JSON from Azure Portal:")
    print(f"   - Go to Azure Portal > Your Search Service > Indexes")
    print(f"   - Select your index")
    print(f"   - Click 'JSON View' or 'Export'")
    print(f"   - Save as 'portal_index.json'")

    print(f"\n2. Import the portal JSON:")
    print(f"   python -m src.ingestor.cli --import-schema portal_index.json")

    print(f"\n3. The importer will:")
    print(f"   - Parse all fields with types and analyzers")
    print(f"   - Create scoring profiles")
    print(f"   - Configure semantic search")
    print(f"   - Set up vector search")

    print(f"\nNote: Portal JSON may need minor adjustments for full compatibility.")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Azure AI Search Index - JSON Schema Import/Export Examples")
    print("=" * 80)

    print("\nThese examples demonstrate index schema management:")

    # Example 1: Export current index schema
    try:
        example_export_schema()
    except Exception as e:
        print(f"Example 1 error: {e}")

    # Example 2: Import schema to create new index
    try:
        example_import_schema()
    except Exception as e:
        print(f"Example 2 error: {e}")

    # Example 3: Backup and restore pattern
    example_backup_and_restore()

    # Example 4: Environment migration
    example_migrate_environments()

    # Example 5: Azure Portal JSON
    example_use_azure_portal_json()

    print("\n" + "=" * 80)
    print("Examples Complete!")
    print("=" * 80)
    print(f"\nFor more information, see:")
    print(f"  - docs/JSON_SCHEMA_IMPORT_EXPORT.md")
    print(f"  - docs/INDEX_CONFIGURATION.md")
    print(f"\nCLI Commands:")
    print(f"  python -m src.ingestor.cli --export-schema <output.json>")
    print(f"  python -m src.ingestor.cli --import-schema <input.json>")
