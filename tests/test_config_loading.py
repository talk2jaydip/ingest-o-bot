"""Test script to verify .env file loading and configuration.

Run this script to verify configuration is loading correctly:
    python test_config_loading.py
"""

import sys
sys.path.insert(0, 'src')

from ingestor.config import PipelineConfig


def main():
    """Test configuration loading from .env file."""
    print("=" * 80)
    print("Testing Configuration Loading")
    print("=" * 80)

    try:
        config = PipelineConfig.from_env()

        print("\nSUCCESS: Configuration loaded from .env file")
        print("-" * 80)

        # Azure Search
        print("\n1. Azure Search Configuration:")
        print(f"   Endpoint: {config.search.endpoint}")
        print(f"   Index: {config.search.index_name}")
        print(f"   API Key: {'*' * 10}... (hidden)")

        # Index Schema
        print("\n2. Index Schema Configuration:")
        semantic = config.search.semantic_config_name or "default-semantic-config (default)"
        suggester = config.search.suggester_name or "default-suggester (default)"
        profiles = config.search.scoring_profile_names or ("productBoostingProfile", "contentRAGProfile")
        print(f"   Semantic Config: {semantic}")
        print(f"   Suggester: {suggester}")
        print(f"   Scoring Profiles: {profiles}")

        # Vector Store
        print("\n3. Vector Store Configuration:")
        print(f"   Mode: {config.vector_store_mode}")

        # Embeddings
        print("\n4. Embeddings Configuration:")
        print(f"   Mode: {config.embeddings_mode}")
        print(f"   Deployment: {config.azure_openai.emb_deployment}")
        print(f"   Dimensions: {config.azure_openai.emb_dimensions}")

        print("\n" + "=" * 80)
        print("All Tests PASSED!")
        print("=" * 80)

        print("\nTo customize index schema, add to .env:")
        print("  AZURE_SEARCH_SEMANTIC_CONFIG_NAME=your-semantic-config")
        print("  AZURE_SEARCH_SUGGESTER_NAME=your-suggester")
        print("  AZURE_SEARCH_SCORING_PROFILES=profile1,profile2")

        print("\nDocumentation:")
        print("  docs/INDEX_CONFIGURATION.md")

    except Exception as e:
        print(f"\nERROR: Configuration loading failed!")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure .env file exists in project root")
        print("2. Verify required variables are set:")
        print("   - AZURE_SEARCH_SERVICE or AZURE_SEARCH_ENDPOINT")
        print("   - AZURE_SEARCH_INDEX")
        print("   - AZURE_SEARCH_API_KEY")
        sys.exit(1)


if __name__ == "__main__":
    main()
