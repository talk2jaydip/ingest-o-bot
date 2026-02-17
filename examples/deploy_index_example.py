"""Example: Deploy Azure AI Search Index with Custom Configuration

This example demonstrates how to deploy an index using:
1. Environment variables from .env file
2. SearchConfig for automatic config loading
3. Custom semantic config, suggester, and scoring profile names
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from src.ingestor.config import SearchConfig, AzureOpenAIConfig
from src.ingestor.index import IndexDeploymentManager

# Load environment variables
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)


def deploy_index_with_config():
    """Deploy index using SearchConfig (reads from environment variables)."""

    print("=" * 80)
    print("DEPLOYING INDEX WITH SEARCHCONFIG")
    print("=" * 80)

    # Load configuration from environment variables
    search_config = SearchConfig.from_env()
    openai_config = AzureOpenAIConfig.from_env()

    # Create index manager
    # The config values are automatically picked up from .env:
    # - AZURE_SEARCH_SEMANTIC_CONFIG_NAME (optional)
    # - AZURE_SEARCH_SUGGESTER_NAME (optional)
    # - AZURE_SEARCH_SCORING_PROFILES (optional, comma-separated)
    manager = IndexDeploymentManager(
        endpoint=search_config.endpoint,
        api_key=search_config.api_key,
        index_name=search_config.index_name,
        openai_endpoint=openai_config.endpoint,
        openai_deployment=openai_config.emb_deployment,
        openai_key=openai_config.api_key,
        verbose=True,
        # These come from SearchConfig (from .env):
        semantic_config_name=search_config.semantic_config_name,
        suggester_name=search_config.suggester_name,
        scoring_profile_names=search_config.scoring_profile_names
    )

    print(f"\n📋 Index Configuration:")
    print(f"   Index Name: {search_config.index_name}")
    print(f"   Semantic Config: {search_config.semantic_config_name or 'default-semantic-config (default)'}")
    print(f"   Suggester: {search_config.suggester_name or 'default-suggester (default)'}")
    print(f"   Scoring Profiles: {search_config.scoring_profile_names or ('productBoostingProfile', 'contentRAGProfile')}")

    # Deploy the index
    success = manager.deploy_index(
        dry_run=False,
        force=False,
        skip_if_exists=True
    )

    if success:
        print("\n✅ Index deployed successfully!")
    else:
        print("\n❌ Index deployment failed!")

    return success


def deploy_index_with_custom_names():
    """Deploy index with custom names (override defaults)."""

    print("\n" + "=" * 80)
    print("DEPLOYING INDEX WITH CUSTOM NAMES")
    print("=" * 80)

    # Create index manager with custom names
    manager = IndexDeploymentManager(
        endpoint=os.getenv("AZURE_SEARCH_SERVICE") and f"https://{os.getenv('AZURE_SEARCH_SERVICE')}.search.windows.net",
        api_key=os.getenv("AZURE_SEARCH_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        openai_key=os.getenv("AZURE_OPENAI_KEY"),
        verbose=True,
        # Custom names (override defaults):
        semantic_config_name="my-custom-semantic-config",
        suggester_name="my-custom-suggester",
        scoring_profile_names=("customProfile1", "customProfile2")
    )

    print(f"\n📋 Custom Configuration:")
    print(f"   Semantic Config: my-custom-semantic-config")
    print(f"   Suggester: my-custom-suggester")
    print(f"   Scoring Profiles: ('customProfile1', 'customProfile2')")

    # Deploy with dry run to see what would be created
    success = manager.deploy_index(dry_run=True)

    return success


def deploy_index_with_env_override():
    """Deploy index using .env variables for custom names."""

    print("\n" + "=" * 80)
    print("DEPLOYING INDEX WITH .ENV OVERRIDE")
    print("=" * 80)
    print("\nTo use custom names, add these to your .env file:")
    print("   AZURE_SEARCH_SEMANTIC_CONFIG_NAME=alfred-semantic-config")
    print("   AZURE_SEARCH_SUGGESTER_NAME=product-suggester")
    print("   AZURE_SEARCH_SCORING_PROFILES=productBoostingProfile,contentRAGProfile")

    search_config = SearchConfig.from_env()

    if search_config.semantic_config_name:
        print(f"\n✅ Custom semantic config detected: {search_config.semantic_config_name}")
    else:
        print(f"\n⚠️  No custom semantic config - will use default")

    if search_config.suggester_name:
        print(f"✅ Custom suggester detected: {search_config.suggester_name}")
    else:
        print(f"⚠️  No custom suggester - will use default")

    if search_config.scoring_profile_names:
        print(f"✅ Custom scoring profiles detected: {search_config.scoring_profile_names}")
    else:
        print(f"⚠️  No custom scoring profiles - will use defaults")


if __name__ == "__main__":
    print("\n🚀 Azure AI Search Index Deployment Examples\n")

    # Example 1: Deploy with SearchConfig (automatic from .env)
    # This uses values from .env file if set, otherwise uses defaults
    deploy_index_with_config()

    # Example 2: Deploy with custom names (programmatic override)
    # deploy_index_with_custom_names()

    # Example 3: Show how .env override works
    deploy_index_with_env_override()
