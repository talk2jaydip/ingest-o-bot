"""Example script demonstrating environment and secret management.

This shows how to:
1. Use different .env files for different environments
2. Update secrets programmatically
3. Validate configuration
4. Switch between environments
"""

import asyncio
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def setup_example_env_files():
    """Create example .env files for different environments."""
    print("\n" + "=" * 80)
    print("SETUP: Creating Example Environment Files")
    print("=" * 80)

    envs = {
        ".env.example.dev": {
            "ENVIRONMENT": "development",
            "AZURE_SEARCH_SERVICE": "dev-search-service",
            "AZURE_SEARCH_INDEX": "dev-documents-index",
            "AZURE_SEARCH_KEY": "dev-search-key-placeholder",
            "AZURE_DOC_INT_ENDPOINT": "https://dev-di.cognitiveservices.azure.com/",
            "AZURE_DOC_INT_KEY": "dev-di-key-placeholder",
            "AZURE_OPENAI_ENDPOINT": "https://dev-openai.openai.azure.com/",
            "AZURE_OPENAI_KEY": "dev-openai-key-placeholder",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_LOCAL_GLOB": "test_data/*.pdf",
            "AZURE_ARTIFACTS_DIR": "./dev_artifacts",
        },
        ".env.example.staging": {
            "ENVIRONMENT": "staging",
            "AZURE_SEARCH_SERVICE": "staging-search-service",
            "AZURE_SEARCH_INDEX": "staging-documents-index",
            "AZURE_SEARCH_KEY": "staging-search-key-placeholder",
            "AZURE_DOC_INT_ENDPOINT": "https://staging-di.cognitiveservices.azure.com/",
            "AZURE_DOC_INT_KEY": "staging-di-key-placeholder",
            "AZURE_OPENAI_ENDPOINT": "https://staging-openai.openai.azure.com/",
            "AZURE_OPENAI_KEY": "staging-openai-key-placeholder",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
            "AZURE_LOCAL_GLOB": "staging_data/*.pdf",
            "AZURE_ARTIFACTS_DIR": "./staging_artifacts",
        },
        ".env.example.prod": {
            "ENVIRONMENT": "production",
            "AZURE_SEARCH_SERVICE": "prod-search-service",
            "AZURE_SEARCH_INDEX": "prod-documents-index",
            "AZURE_SEARCH_KEY": "prod-search-key-placeholder",
            "AZURE_DOC_INT_ENDPOINT": "https://prod-di.cognitiveservices.azure.com/",
            "AZURE_DOC_INT_KEY": "prod-di-key-placeholder",
            "AZURE_OPENAI_ENDPOINT": "https://prod-openai.openai.azure.com/",
            "AZURE_OPENAI_KEY": "prod-openai-key-placeholder",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-large",
            "AZURE_LOCAL_GLOB": "production_data/*.pdf",
            "AZURE_ARTIFACTS_DIR": "./prod_artifacts",
        },
    }

    for filename, config in envs.items():
        with open(filename, "w") as f:
            f.write(f"# Example {config['ENVIRONMENT'].title()} Environment\n")
            f.write("# Copy to .env.{} and update with real credentials\n\n".format(
                config['ENVIRONMENT']
            ))
            for key, value in config.items():
                f.write(f"{key}={value}\n")

        print(f"✅ Created {filename}")

    print("\n📝 To use these:")
    print("   1. Copy to .env.<environment> (e.g., cp .env.example.dev .env.development)")
    print("   2. Update with your real Azure credentials")
    print("   3. Use in code with env_path parameter")


def example_1_load_different_envs():
    """Example 1: Load configuration from different environment files."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Load from Different Environments")
    print("=" * 80)

    from ingestor import PipelineConfig

    environments = ["development", "staging", "production"]

    for env in environments:
        env_file = f".env.{env}"

        try:
            print(f"\n📂 Loading {env_file}...")

            config = PipelineConfig.from_env(env_path=env_file)

            print(f"✅ {env.title()} config loaded:")
            print(f"   - Search: {config.search.endpoint}")
            print(f"   - Index: {config.search.index_name}")
            print(f"   - Input: {config.input.local_glob}")
            print(f"   - Artifacts: {config.artifacts.local_dir}")

        except Exception as e:
            print(f"⚠️  {env.title()} config not found: {e}")
            print(f"   Create it from: cp .env.example.{env[:3]} {env_file}")


def example_2_programmatic_secrets():
    """Example 2: Load secrets programmatically and build config."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Programmatic Secret Loading")
    print("=" * 80)

    from ingestor import ConfigBuilder

    def get_secrets_from_vault(environment: str):
        """Simulate loading secrets from a secret vault."""
        # In real code, this would call Azure Key Vault, AWS Secrets Manager, etc.
        secrets = {
            "development": {
                "search_key": "dev-search-key-abc123",
                "di_key": "dev-di-key-xyz789",
                "openai_key": "dev-openai-key-def456",
            },
            "production": {
                "search_key": "prod-search-key-abc123",
                "di_key": "prod-di-key-xyz789",
                "openai_key": "prod-openai-key-def456",
            },
        }
        return secrets.get(environment, {})

    # Load secrets for production
    environment = "production"
    secrets = get_secrets_from_vault(environment)

    if secrets:
        print(f"✅ Loaded secrets for {environment}")
        print(f"   - Search key: {secrets['search_key'][:10]}... (masked)")
        print(f"   - DI key: {secrets['di_key'][:10]}... (masked)")
        print(f"   - OpenAI key: {secrets['openai_key'][:10]}... (masked)")

        # Build config with secrets
        config = (
            ConfigBuilder()
            .with_search(
                "prod-search-service",
                "prod-index",
                secrets["search_key"]
            )
            .with_document_intelligence(
                "https://prod-di.cognitiveservices.azure.com/",
                secrets["di_key"]
            )
            .with_azure_openai(
                "https://prod-openai.openai.azure.com/",
                secrets["openai_key"],
                "text-embedding-3-large"
            )
            .with_local_files("production_data/*.pdf")
            .build()
        )

        print("\n✅ Config built with secrets from vault")
        print(f"   - Search endpoint: {config.search.endpoint}")
        print(f"   - Has API key: {config.search.api_key is not None}")


def example_3_env_variable_selection():
    """Example 3: Use environment variable to select config file."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Environment Variable Selection")
    print("=" * 80)

    from ingestor import load_config

    # Simulate different ENVIRONMENT values
    test_envs = ["development", "staging", "production"]

    for env in test_envs:
        print(f"\n🔧 Simulating ENVIRONMENT={env}")

        # In real usage, this would be: os.getenv("ENVIRONMENT", "development")
        env_file = f".env.{env}"

        try:
            config = load_config(env_path=env_file)
            print(f"✅ Loaded {env} configuration")
            print(f"   - Index: {config.search.index_name}")
        except Exception as e:
            print(f"⚠️  Config not found: {e}")

    print("\n💡 Usage in production:")
    print("   export ENVIRONMENT=production")
    print("   python your_script.py")
    print()
    print("   In your script:")
    print("   env = os.getenv('ENVIRONMENT', 'development')")
    print("   config = load_config(f'.env.{env}')")


def example_4_validate_config():
    """Example 4: Validate configuration before using."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Configuration Validation")
    print("=" * 80)

    from ingestor import PipelineConfig
    import os

    def validate_configuration(env_file: str):
        """Validate that configuration has all required fields."""
        print(f"\n🔍 Validating {env_file}...")

        required_env_vars = [
            "AZURE_SEARCH_SERVICE",
            "AZURE_SEARCH_INDEX",
            "AZURE_DOC_INT_ENDPOINT",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        ]

        try:
            # Try loading config
            config = PipelineConfig.from_env(env_path=env_file)

            # Check all required fields
            checks = []
            checks.append(("Search endpoint", config.search.endpoint))
            checks.append(("Search index", config.search.index_name))
            checks.append(("DI endpoint", config.document_intelligence.endpoint))
            checks.append(("OpenAI endpoint", config.azure_openai.endpoint))
            checks.append(("Embedding deployment", config.azure_openai.emb_deployment))

            print("   Checking required fields:")
            all_valid = True
            for name, value in checks:
                if value:
                    print(f"   ✅ {name}: {value[:50]}...")
                else:
                    print(f"   ❌ {name}: MISSING")
                    all_valid = False

            if all_valid:
                print(f"\n✅ Configuration is valid and ready to use!")
                return True
            else:
                print(f"\n❌ Configuration is incomplete!")
                return False

        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return False

    # Test with current .env
    if Path(".env").exists():
        validate_configuration(".env")
    else:
        print("⚠️  No .env file found")
        print("   Create one from: cp env.example .env")


def example_5_update_secrets():
    """Example 5: Update secrets without changing code."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Updating Secrets at Runtime")
    print("=" * 80)

    from ingestor import ConfigBuilder

    print("Scenario: Your Azure keys have been rotated")
    print()

    # Simulate old and new keys
    old_config = {
        "search_key": "old-search-key-123",
        "di_key": "old-di-key-456",
        "openai_key": "old-openai-key-789",
    }

    new_config = {
        "search_key": "NEW-search-key-abc",
        "di_key": "NEW-di-key-def",
        "openai_key": "NEW-openai-key-ghi",
    }

    print("Old keys (expired):")
    for key, value in old_config.items():
        print(f"   {key}: {value}")

    print("\nNew keys (rotated):")
    for key, value in new_config.items():
        print(f"   {key}: {value}")

    # Build config with new keys
    config = (
        ConfigBuilder()
        .with_search("my-search", "my-index", new_config["search_key"])
        .with_document_intelligence("https://my-di.endpoint", new_config["di_key"])
        .with_azure_openai("https://my-openai.endpoint", new_config["openai_key"], "embedding")
        .with_local_files("docs/*.pdf")
        .build()
    )

    print("\n✅ Configuration updated with new keys")
    print("   - Next pipeline run will use new credentials")
    print("   - No code changes required!")
    print()
    print("💡 Best practice:")
    print("   1. Store keys in secret vault (Azure Key Vault, AWS Secrets Manager)")
    print("   2. Fetch latest keys at runtime")
    print("   3. Build config with fresh credentials")
    print("   4. Run pipeline")


async def example_6_multi_environment_deployment():
    """Example 6: Deploy to multiple environments."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Multi-Environment Deployment")
    print("=" * 80)

    from ingestor import create_config

    async def deploy_to_environment(environment: str, dry_run: bool = True):
        """Deploy documents to specified environment."""
        env_file = f".env.{environment}"

        print(f"\n🚀 Deploying to {environment.upper()}")

        try:
            # Load environment-specific config
            config = create_config(
                env_path=env_file,
                input_glob=f"{environment}_data/*.pdf"
            )

            print(f"✅ Configuration loaded:")
            print(f"   - Search: {config.search.endpoint}")
            print(f"   - Index: {config.search.index_name}")
            print(f"   - Input: {config.input.local_glob}")

            if dry_run:
                print(f"   [DRY RUN - would process files here]")
            else:
                from ingestor import Pipeline
                pipeline = Pipeline(config)
                try:
                    status = await pipeline.run()
                    print(f"✅ Deployment complete: {status.successful_documents} documents")
                finally:
                    await pipeline.close()

        except Exception as e:
            print(f"❌ Deployment failed: {e}")

    # Simulate deployment pipeline
    print("Simulating deployment pipeline...")
    print("(Set dry_run=False to actually deploy)")

    await deploy_to_environment("development", dry_run=True)
    # await deploy_to_environment("staging", dry_run=True)
    # await deploy_to_environment("production", dry_run=True)

    print("\n💡 In real CI/CD:")
    print("   1. Dev: Auto-deploy on every commit")
    print("   2. Staging: Auto-deploy on merge to main")
    print("   3. Production: Manual approval + deploy")


def main():
    """Run all examples."""
    print("=" * 80)
    print("ENVIRONMENT AND SECRET MANAGEMENT EXAMPLES")
    print("=" * 80)
    print()
    print("This script demonstrates how to:")
    print("  1. Use different .env files for different environments")
    print("  2. Load secrets programmatically")
    print("  3. Select environment via environment variables")
    print("  4. Validate configuration")
    print("  5. Update secrets at runtime")
    print("  6. Deploy to multiple environments")
    print()

    examples = [
        ("Setup Example Files", setup_example_env_files, False),
        ("Load Different Envs", example_1_load_different_envs, False),
        ("Programmatic Secrets", example_2_programmatic_secrets, False),
        ("Env Variable Selection", example_3_env_variable_selection, False),
        ("Validate Config", example_4_validate_config, False),
        ("Update Secrets", example_5_update_secrets, False),
        ("Multi-Env Deployment", example_6_multi_environment_deployment, True),
    ]

    for name, func, is_async in examples:
        try:
            if is_async:
                asyncio.run(func())
            else:
                func()
        except Exception as e:
            print(f"❌ {name} error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ All examples completed!")
    print()
    print("Next steps:")
    print("  1. Copy .env.example.<env> to .env.<environment>")
    print("  2. Update with your real Azure credentials")
    print("  3. Use env_path parameter to load specific environment")
    print()
    print("See docs/guides/ENVIRONMENT_AND_SECRETS.md for full guide")


if __name__ == "__main__":
    main()
