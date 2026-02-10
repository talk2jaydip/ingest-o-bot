# Environment Management and Secrets Configuration

This guide shows how to use your own environments and manage secrets securely with Ingestor v4.0.

---

## Table of Contents

1. [Multiple Environments Setup](#multiple-environments-setup)
2. [Secret Management Options](#secret-management-options)
3. [Best Practices](#best-practices)
4. [Examples](#examples)

---

## Multiple Environments Setup

### Option 1: Multiple .env Files (Recommended for Most Users)

Create separate .env files for each environment:

```bash
.env.development     # Local development
.env.staging         # Staging environment
.env.production      # Production environment
```

#### Example: .env.development
```bash
# Development Environment
AZURE_SEARCH_SERVICE=dev-search-service
AZURE_SEARCH_INDEX=dev-documents-index
AZURE_SEARCH_KEY=dev-search-key-here

AZURE_DOC_INT_ENDPOINT=https://dev-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=dev-di-key-here

AZURE_OPENAI_ENDPOINT=https://dev-openai.openai.azure.com/
AZURE_OPENAI_KEY=dev-openai-key-here
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

AZURE_LOCAL_GLOB=test_data/*.pdf
AZURE_ARTIFACTS_DIR=./dev_artifacts
```

#### Example: .env.production
```bash
# Production Environment
AZURE_SEARCH_SERVICE=prod-search-service
AZURE_SEARCH_INDEX=prod-documents-index
AZURE_SEARCH_KEY=prod-search-key-here

AZURE_DOC_INT_ENDPOINT=https://prod-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=prod-di-key-here

AZURE_OPENAI_ENDPOINT=https://prod-openai.openai.azure.com/
AZURE_OPENAI_KEY=prod-openai-key-here
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

AZURE_LOCAL_GLOB=production_data/*.pdf
AZURE_ARTIFACTS_DIR=./prod_artifacts
```

#### Using Different Environments

**Method 1: Specify env_path in code**
```python
from ingestor import PipelineConfig, Pipeline
import os

# Get environment from environment variable or default to dev
environment = os.getenv("ENVIRONMENT", "development")
env_file = f".env.{environment}"

# Load config from specific environment file
config = PipelineConfig.from_env(env_path=env_file)

# Run pipeline
pipeline = Pipeline(config)
status = await pipeline.run()
```

**Method 2: Use create_config() with env_path**
```python
from ingestor import create_config
import os

environment = os.getenv("ENVIRONMENT", "development")

config = create_config(
    env_path=f".env.{environment}",
    input_glob="documents/*.pdf"
)
```

**Method 3: Use environment variable to select file**
```bash
# Set environment
export ENVIRONMENT=production

# Then in Python
import os
from ingestor import load_config

env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
config = load_config(env_path=env_file)
```

---

## Secret Management Options

### Option 1: Environment Files (.env) - Simple

**Pros:**
- ✅ Simple to use
- ✅ Works offline
- ✅ Good for development

**Cons:**
- ❌ Must be careful not to commit to git
- ❌ Manual rotation required

**Setup:**
```bash
# Create .env file
cat > .env << EOF
AZURE_SEARCH_KEY=your-search-key
AZURE_DOC_INT_KEY=your-di-key
AZURE_OPENAI_KEY=your-openai-key
EOF

# Add to .gitignore
echo ".env*" >> .gitignore
```

**Usage:**
```python
from ingestor import run_pipeline

# Automatically loads from .env
status = await run_pipeline(input_glob="docs/*.pdf")
```

---

### Option 2: System Environment Variables - CI/CD

**Pros:**
- ✅ Secure for CI/CD
- ✅ No files to manage
- ✅ Works with container orchestration

**Cons:**
- ❌ Must set variables in each environment

**Setup:**

**Linux/Mac:**
```bash
export AZURE_SEARCH_KEY="your-search-key"
export AZURE_DOC_INT_KEY="your-di-key"
export AZURE_OPENAI_KEY="your-openai-key"
```

**Windows:**
```powershell
$env:AZURE_SEARCH_KEY="your-search-key"
$env:AZURE_DOC_INT_KEY="your-di-key"
$env:AZURE_OPENAI_KEY="your-openai-key"
```

**Usage:**
```python
from ingestor import PipelineConfig, Pipeline

# Loads from system environment variables
config = PipelineConfig.from_env()

pipeline = Pipeline(config)
status = await pipeline.run()
```

---

### Option 3: Azure Key Vault (Recommended for Production)

**Pros:**
- ✅ Most secure
- ✅ Centralized secret management
- ✅ Automatic rotation support
- ✅ Audit logging

**Cons:**
- ❌ Requires Azure setup
- ❌ Needs managed identity or service principal

**Setup:**

1. **Store secrets in Key Vault:**
```bash
# Azure CLI
az keyvault secret set --vault-name my-keyvault --name AZURE-SEARCH-KEY --value "search-key"
az keyvault secret set --vault-name my-keyvault --name AZURE-DI-KEY --value "di-key"
az keyvault secret set --vault-name my-keyvault --name AZURE-OPENAI-KEY --value "openai-key"
```

2. **Configure service principal:**
```bash
# .env file
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
KEY_VAULT_URI=https://my-keyvault.vault.azure.net/
```

3. **Use in code:**
```python
from ingestor import ConfigBuilder
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import os

# Get secrets from Key Vault
credential = DefaultAzureCredential()
vault_uri = os.getenv("KEY_VAULT_URI")
client = SecretClient(vault_url=vault_uri, credential=credential)

search_key = client.get_secret("AZURE-SEARCH-KEY").value
di_key = client.get_secret("AZURE-DI-KEY").value
openai_key = client.get_secret("AZURE-OPENAI-KEY").value

# Build config with Key Vault secrets
config = (
    ConfigBuilder()
    .with_search("my-search-service", "my-index", search_key)
    .with_document_intelligence("https://my-di.endpoint", di_key)
    .with_azure_openai("https://my-openai.endpoint", openai_key, "embedding-model")
    .with_local_files("docs/*.pdf")
    .build()
)
```

---

### Option 4: Programmatic Configuration - Full Control

**Pros:**
- ✅ Maximum flexibility
- ✅ Can load from any secret store
- ✅ Runtime configuration

**Cons:**
- ❌ More code to write

**Example with custom secret management:**
```python
from ingestor import ConfigBuilder, Pipeline

def get_secrets_from_your_vault():
    """Load secrets from your custom secret management system."""
    # Your custom logic here (AWS Secrets Manager, HashiCorp Vault, etc.)
    return {
        "search_key": "...",
        "di_key": "...",
        "openai_key": "...",
    }

# Load secrets
secrets = get_secrets_from_your_vault()

# Build configuration
config = (
    ConfigBuilder()
    .with_search(
        service_name="my-search",
        index_name="my-index",
        api_key=secrets["search_key"]
    )
    .with_document_intelligence(
        endpoint="https://my-di.endpoint",
        key=secrets["di_key"]
    )
    .with_azure_openai(
        endpoint="https://my-openai.endpoint",
        api_key=secrets["openai_key"],
        embedding_deployment="text-embedding-ada-002"
    )
    .with_local_files("docs/*.pdf")
    .build()
)

# Run pipeline
pipeline = Pipeline(config)
status = await pipeline.run()
```

---

## Best Practices

### 1. Never Commit Secrets to Git

**Always add to .gitignore:**
```bash
# .gitignore
.env
.env.*
!.env.example
secrets.json
credentials.json
*.key
*.pem
```

**Create example file instead:**
```bash
# .env.example (safe to commit)
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=your-index
AZURE_SEARCH_KEY=your-key-here

AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-key-here
```

### 2. Use Managed Identity in Azure

When running in Azure (VMs, App Service, Functions, etc.), use Managed Identity:

```python
from ingestor import ConfigBuilder
from azure.identity import DefaultAzureCredential

# No keys needed! Uses managed identity
config = (
    ConfigBuilder()
    .with_search("my-search", "my-index", api_key=None)  # Will use managed identity
    .with_document_intelligence("https://my-di.endpoint", key=None)
    .with_azure_openai("https://my-openai.endpoint", api_key=None, ...)
    .with_local_files("docs/*.pdf")
    .build()
)
```

### 3. Rotate Secrets Regularly

**Example rotation script:**
```python
from ingestor import create_config
import os

def rotate_to_new_keys():
    """Switch to rotated keys."""
    # Load config with new keys
    config = create_config(
        use_env=False,
        search_service_name=os.getenv("AZURE_SEARCH_SERVICE"),
        search_index_name=os.getenv("AZURE_SEARCH_INDEX"),
        search_api_key=os.getenv("AZURE_SEARCH_KEY_NEW"),  # New rotated key
        # ... other configs
    )
    return config
```

### 4. Use Different Keys for Different Environments

Never use production keys in development!

```bash
# Development: Read-only keys if possible
AZURE_SEARCH_KEY=dev-readonly-key

# Production: Full access keys
AZURE_SEARCH_KEY=prod-full-access-key
```

### 5. Validate Configuration Before Running

```python
from ingestor import PipelineConfig
import os

def validate_config():
    """Validate configuration before running pipeline."""
    required_vars = [
        "AZURE_SEARCH_SERVICE",
        "AZURE_SEARCH_INDEX",
        "AZURE_DOC_INT_ENDPOINT",
        "AZURE_OPENAI_ENDPOINT",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    # Try loading config
    try:
        config = PipelineConfig.from_env()
        print("✅ Configuration valid")
        return config
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        raise

# Use it
config = validate_config()
```

---

## Examples

### Example 1: Development → Staging → Production Pipeline

```python
"""Deploy script that works across all environments."""

import os
from ingestor import create_config, Pipeline

async def deploy_documents(environment: str):
    """Deploy documents to specified environment."""

    # Select environment file
    env_file = f".env.{environment}"

    print(f"🚀 Deploying to {environment}")
    print(f"📄 Loading config from {env_file}")

    # Load environment-specific config
    config = create_config(
        env_path=env_file,
        input_glob=f"{environment}_data/*.pdf"
    )

    print(f"✅ Configuration loaded")
    print(f"   - Search: {config.search.endpoint}")
    print(f"   - Index: {config.search.index_name}")

    # Run pipeline
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"✅ Deployment complete!")
        print(f"   - Documents: {status.successful_documents}")
        print(f"   - Chunks: {status.total_chunks_indexed}")
        return status
    finally:
        await pipeline.close()

# Usage:
# await deploy_documents("development")
# await deploy_documents("staging")
# await deploy_documents("production")
```

### Example 2: CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Documents

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Deploy to Production
        env:
          AZURE_SEARCH_SERVICE: ${{ secrets.AZURE_SEARCH_SERVICE }}
          AZURE_SEARCH_INDEX: ${{ secrets.AZURE_SEARCH_INDEX }}
          AZURE_SEARCH_KEY: ${{ secrets.AZURE_SEARCH_KEY }}
          AZURE_DOC_INT_ENDPOINT: ${{ secrets.AZURE_DOC_INT_ENDPOINT }}
          AZURE_DOC_INT_KEY: ${{ secrets.AZURE_DOC_INT_KEY }}
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_KEY: ${{ secrets.AZURE_OPENAI_KEY }}
          AZURE_OPENAI_EMBEDDING_DEPLOYMENT: text-embedding-ada-002
        run: |
          python deploy.py
```

**deploy.py:**
```python
"""CI/CD deployment script."""

import asyncio
from ingestor import PipelineConfig, Pipeline

async def main():
    # Loads from environment variables set by GitHub Actions
    config = PipelineConfig.from_env()
    config.input.local_glob = "production_data/*.pdf"

    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"Deployed {status.successful_documents} documents")

        # Exit with error code if any failures
        if status.failed_documents > 0:
            exit(1)
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Docker Container with Environment Variables

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# No secrets in Dockerfile!
# Pass them at runtime via -e flags

CMD ["python", "run_ingestion.py"]
```

**Run with secrets:**
```bash
docker run \
  -e AZURE_SEARCH_SERVICE=my-search \
  -e AZURE_SEARCH_INDEX=my-index \
  -e AZURE_SEARCH_KEY=my-key \
  -e AZURE_DOC_INT_ENDPOINT=https://my-di.endpoint \
  -e AZURE_DOC_INT_KEY=my-di-key \
  -e AZURE_OPENAI_ENDPOINT=https://my-openai.endpoint \
  -e AZURE_OPENAI_KEY=my-openai-key \
  -e AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002 \
  -v $(pwd)/documents:/app/documents \
  my-ingestor-image
```

### Example 4: Update Secrets Without Code Changes

```python
"""Update secrets at runtime without changing code."""

from ingestor import ConfigBuilder, Pipeline
import os

def get_current_credentials():
    """Load latest credentials from your secret store."""
    # This could call AWS Secrets Manager, Azure Key Vault, etc.
    # For demo, using environment variables
    return {
        "search_key": os.getenv("AZURE_SEARCH_KEY"),
        "di_key": os.getenv("AZURE_DOC_INT_KEY"),
        "openai_key": os.getenv("AZURE_OPENAI_KEY"),
    }

async def run_with_latest_credentials():
    """Always uses latest credentials from secret store."""

    # Get fresh credentials
    creds = get_current_credentials()

    # Build config with current credentials
    config = (
        ConfigBuilder()
        .with_search("my-search", "my-index", creds["search_key"])
        .with_document_intelligence("https://my-di.endpoint", creds["di_key"])
        .with_azure_openai("https://my-openai.endpoint", creds["openai_key"], "embedding")
        .with_local_files("docs/*.pdf")
        .build()
    )

    # Run with latest credentials
    pipeline = Pipeline(config)
    try:
        return await pipeline.run()
    finally:
        await pipeline.close()

# Credentials are fetched fresh each time
# If you rotate keys externally, next run will pick them up automatically
```

---

## Quick Reference

### Load from Different Environments

```python
# Method 1: env_path parameter
from ingestor import PipelineConfig
config = PipelineConfig.from_env(env_path=".env.production")

# Method 2: create_config with env_path
from ingestor import create_config
config = create_config(env_path=".env.staging")

# Method 3: load_config helper
from ingestor import load_config
config = load_config(env_path=".env.development")
```

### Build Config with Secrets from Code

```python
from ingestor import ConfigBuilder

config = (
    ConfigBuilder()
    .with_search("service", "index", api_key="secret-key")
    .with_document_intelligence("https://endpoint", key="secret-key")
    .with_azure_openai("https://endpoint", api_key="secret-key", embedding_deployment="model")
    .with_local_files("docs/*.pdf")
    .build()
)
```

### Environment Variable Selection

```python
import os
from ingestor import load_config

# Use ENVIRONMENT variable to select config
env = os.getenv("ENVIRONMENT", "development")
config = load_config(f".env.{env}")
```

---

## Summary

**Choose the right approach for your use case:**

| Use Case | Recommended Approach |
|----------|---------------------|
| Local development | Multiple .env files |
| CI/CD pipelines | Environment variables |
| Production on Azure | Managed Identity + Key Vault |
| Production elsewhere | Programmatic config with secret management |
| Kubernetes | Environment variables from secrets |
| Docker | Environment variables at runtime |
| Multi-tenant | Programmatic config per tenant |

**All approaches are fully supported by Ingestor v4.0!**
