# Ingestor v4.0 Quick Reference

Fast lookup guide for common operations.

---

## Installation

```bash
pip install -e .
```

---

## Basic Usage

### 1. One-Liner (Simplest)
```python
from ingestor import run_pipeline

# Load from .env and process
status = await run_pipeline(input_glob="docs/*.pdf")
```

### 2. Synchronous (No async)
```python
from ingestor import sync_run_pipeline

status = sync_run_pipeline(input_glob="docs/*.pdf")
```

### 3. With Pipeline Class
```python
from ingestor import Pipeline, PipelineConfig

config = PipelineConfig.from_env()
pipeline = Pipeline(config)
try:
    status = await pipeline.run()
finally:
    await pipeline.close()
```

---

## Configuration Methods

### Load from .env File
```python
from ingestor import PipelineConfig

config = PipelineConfig.from_env()
# Or specific file:
config = PipelineConfig.from_env(env_path=".env.production")
```

### Build Programmatically
```python
from ingestor import ConfigBuilder

config = (
    ConfigBuilder()
    .with_search("my-service", "my-index", "key")
    .with_document_intelligence("https://di.endpoint", "key")
    .with_azure_openai("https://openai.endpoint", "key", "embedding-model")
    .with_local_files("docs/*.pdf")
    .build()
)
```

### Hybrid (Load + Override)
```python
from ingestor import create_config

config = create_config(
    input_glob="docs/*.pdf",
    chunking_max_tokens=1000,
    performance_max_workers=8
)
```

### Build from Scratch
```python
from ingestor import create_config

config = create_config(
    use_env=False,
    search_service_name="my-service",
    search_index_name="my-index",
    search_api_key="key",
    document_intelligence_endpoint="https://di.endpoint",
    # ... all other params
)
```

---

## Environment Management

### Multiple .env Files
```bash
# Create different environment files
.env.development
.env.staging
.env.production
```

```python
import os
from ingestor import load_config

env = os.getenv("ENVIRONMENT", "development")
config = load_config(f".env.{env}")
```

### Use Specific Environment
```python
from ingestor import PipelineConfig

# Development
config = PipelineConfig.from_env(".env.development")

# Production
config = PipelineConfig.from_env(".env.production")
```

---

## Secret Management

### Option 1: .env File
```bash
# .env
AZURE_SEARCH_KEY=your-key
AZURE_DOC_INT_KEY=your-key
AZURE_OPENAI_KEY=your-key
```

```python
from ingestor import run_pipeline
status = await run_pipeline(input_glob="docs/*.pdf")
```

### Option 2: Environment Variables
```bash
export AZURE_SEARCH_KEY="your-key"
export AZURE_DOC_INT_KEY="your-key"
export AZURE_OPENAI_KEY="your-key"
```

```python
from ingestor import PipelineConfig
config = PipelineConfig.from_env()  # Loads from env vars
```

### Option 3: Programmatic (Azure Key Vault)
```python
from ingestor import ConfigBuilder
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

client = SecretClient(vault_url="https://vault.azure.net", credential=DefaultAzureCredential())
search_key = client.get_secret("AZURE-SEARCH-KEY").value

config = (
    ConfigBuilder()
    .with_search("service", "index", search_key)
    # ... etc
    .build()
)
```

### Option 4: Custom Secret Store
```python
from ingestor import ConfigBuilder

def get_secrets():
    # Your custom logic (AWS, HashiCorp Vault, etc.)
    return {"search_key": "...", "di_key": "..."}

secrets = get_secrets()
config = (
    ConfigBuilder()
    .with_search("service", "index", secrets["search_key"])
    .build()
)
```

---

## Common Configuration Options

### Chunking
```python
config = create_config(
    chunking_max_tokens=1000,
    chunking_overlap_percent=15,
    chunking_cross_page_overlap=True
)
```

### Performance
```python
config = create_config(
    performance_max_workers=8,
    performance_embed_batch_size=256,
    performance_upload_batch_size=1000
)
```

### Document Extraction Mode
```python
from ingestor import ConfigBuilder, OfficeExtractorMode

config = (
    ConfigBuilder()
    # ... other config
    .with_office_extractor_mode(
        mode=OfficeExtractorMode.HYBRID,  # or AZURE_DI, MARKITDOWN
        offline_fallback=True
    )
    .build()
)
```

### Table Rendering
```python
from ingestor import create_config, TableRenderMode

config = create_config(
    table_render_mode=TableRenderMode.MARKDOWN,  # or PLAIN, HTML
    generate_table_summaries=True
)
```

### Media Descriptions
```python
from ingestor import create_config, MediaDescriberMode

config = create_config(
    media_describer_mode=MediaDescriberMode.GPT4O  # or CONTENT_UNDERSTANDING, DISABLED
)
```

---

## Input Sources

### Local Files
```python
config = create_config(input_glob="documents/*.pdf")

# Or with ConfigBuilder
from ingestor import ConfigBuilder
config = (
    ConfigBuilder()
    .with_local_files("documents/*.pdf", "./artifacts")
    .build()
)
```

### Azure Blob Storage
```python
from ingestor import ConfigBuilder

config = (
    ConfigBuilder()
    .with_blob_input(
        account_url="https://storage.blob.core.windows.net",
        container_in="documents",
        prefix="inbox/",
        account_key="key"
    )
    .build()
)
```

---

## Document Actions

### Add/Update Documents (Default)
```python
from ingestor import create_config, DocumentAction

config = create_config(
    document_action=DocumentAction.ADD  # Default
)
```

### Remove Specific Documents
```python
config = create_config(
    document_action=DocumentAction.REMOVE,
    input_glob="old_docs/*.pdf"  # These will be removed
)
```

### Remove All Documents
```python
config = create_config(
    document_action=DocumentAction.REMOVE_ALL
)
```

---

## Status and Results

```python
status = await run_pipeline(input_glob="docs/*.pdf")

# Access results
print(f"Documents processed: {status.successful_documents}")
print(f"Documents failed: {status.failed_documents}")
print(f"Total chunks: {status.total_chunks_indexed}")

# Individual results
for result in status.results:
    print(f"{result.filename}: {result.chunks_indexed} chunks")
    if not result.success:
        print(f"  Error: {result.error_message}")
```

---

## UI (Gradio)

### Launch Web Interface
```bash
python -m ingestor.gradio_app
# Opens at http://localhost:7860
```

### Programmatic Launch
```python
from ingestor import gradio_app

gradio_app.launch(share=False, server_port=7860)
```

---

## Common Patterns

### CI/CD Deployment
```python
import os
from ingestor import run_pipeline

async def deploy():
    # Uses environment variables set by CI/CD
    status = await run_pipeline(
        input_glob="production_data/*.pdf",
        azure_search_index=os.getenv("SEARCH_INDEX")
    )

    # Exit with error if any failures
    if status.failed_documents > 0:
        exit(1)
```

### Multi-Environment Script
```python
import sys
from ingestor import load_config, Pipeline

async def main(environment: str):
    config = load_config(f".env.{environment}")
    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        print(f"{environment}: {status.successful_documents} docs")
    finally:
        await pipeline.close()

# Usage: python script.py production
if __name__ == "__main__":
    import asyncio
    env = sys.argv[1] if len(sys.argv) > 1 else "development"
    asyncio.run(main(env))
```

### Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .

# Secrets passed at runtime via -e flags
CMD ["python", "-m", "ingestor.run"]
```

```bash
docker run \
  -e AZURE_SEARCH_SERVICE=my-service \
  -e AZURE_SEARCH_INDEX=my-index \
  -e AZURE_SEARCH_KEY=key \
  -v $(pwd)/docs:/app/docs \
  my-ingestor
```

---

## Validation and Debugging

### Validate Configuration
```python
from ingestor import PipelineConfig

try:
    config = PipelineConfig.from_env()
    print("✅ Configuration valid")
    print(f"   Search: {config.search.endpoint}")
    print(f"   Index: {config.search.index_name}")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

### Check Required Variables
```python
import os

required = [
    "AZURE_SEARCH_SERVICE",
    "AZURE_SEARCH_INDEX",
    "AZURE_DOC_INT_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT",
]

missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f"Missing: {missing}")
```

---

## Error Handling

```python
from ingestor import Pipeline, PipelineConfig

async def process_with_error_handling():
    try:
        config = PipelineConfig.from_env()
        pipeline = Pipeline(config)

        try:
            status = await pipeline.run()

            if status.failed_documents > 0:
                print(f"⚠️  {status.failed_documents} documents failed")
                for result in status.results:
                    if not result.success:
                        print(f"   - {result.filename}: {result.error_message}")

            return status

        finally:
            await pipeline.close()

    except ValueError as e:
        print(f"Configuration error: {e}")
        raise
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise
```

---

## File Locations

```
.env                              # Default environment file
.env.development                  # Development environment
.env.staging                      # Staging environment
.env.production                   # Production environment
env.example                       # Example template

docs/guides/LIBRARY_USAGE.md     # Complete usage guide
docs/guides/ENVIRONMENT_AND_SECRETS.md  # Env & secrets guide
docs/TEST_RESULTS.md              # Test results

examples/scripts/
  00_library_usage_guide.py       # Usage examples
  test_config_builder.py          # Config tests
  test_real_ingestion.py          # Real processing tests
  manage_environments.py          # Environment examples
```

---

## Help and Documentation

- **Usage Guide:** [docs/guides/LIBRARY_USAGE.md](guides/LIBRARY_USAGE.md)
- **Environment & Secrets:** [docs/guides/ENVIRONMENT_AND_SECRETS.md](guides/ENVIRONMENT_AND_SECRETS.md)
- **Test Results:** [docs/TEST_RESULTS.md](TEST_RESULTS.md)
- **Examples:** [examples/scripts/](../examples/scripts/)

---

## Common Issues

### "No files found to process"
```python
# Check glob pattern
config.input.local_glob = "documents/*.pdf"  # Correct path?

# Verify files exist
import glob
files = glob.glob("documents/*.pdf")
print(f"Found {len(files)} files")
```

### "Missing required environment variable"
```bash
# Check .env file exists
ls -la .env

# Verify variable is set
echo $AZURE_SEARCH_SERVICE
```

### "Authentication failed"
```python
# Verify keys are correct and not expired
# Check Key Vault if using managed secrets
# Ensure service principal has correct permissions
```

---

## Quick Commands

```bash
# Run configuration tests
python examples/scripts/test_config_builder.py

# Run real ingestion test
python examples/scripts/test_real_ingestion.py

# Test UI integration
python examples/scripts/test_ui_integration.py

# Manage environments
python examples/scripts/manage_environments.py

# Launch UI
python -m ingestor.gradio_app

# Run with specific environment
ENVIRONMENT=production python your_script.py
```

---

## Performance Optimization

### For Large PDFs (100+ pages)

```bash
# Add to .env for immediate performance boost

# Enable server-side embeddings (50-70% faster)
USE_INTEGRATED_VECTORIZATION=true

# Increase concurrency (requires adequate Azure quota)
AZURE_DI_MAX_CONCURRENCY=5           # Document Intelligence (default: 3)
AZURE_OPENAI_MAX_CONCURRENCY=10      # OpenAI embeddings (default: 5)

# Parallel document processing
MAX_WORKERS=4                  # Process multiple docs in parallel
```

### Performance Tuning

```python
from ingestor import create_config

# High-performance configuration
config = create_config(
    input_glob="large_documents/*.pdf",
    # Concurrency
    document_intelligence_max_concurrency=5,
    azure_openai_max_concurrency=10,
    performance_max_workers=4,
    # Batching
    performance_embed_batch_size=16,
    performance_upload_batch_size=1000,
    # Server-side embeddings
    use_integrated_vectorization=True
)
```

### Expected Performance

**Single 100-page PDF**:
- Before optimization: ~60-90 seconds
- After config tuning: ~30-45 seconds (with integrated vectorization)

**4 x 100-page PDFs**:
- Sequential processing: ~4-6 minutes
- Parallel processing (max_workers=4): ~2-3 minutes

### Monitor Rate Limits

```python
# Watch logs for retry messages:
# "Rate limited on embeddings API (attempt 1/3)..."
# "Document Intelligence request failed (attempt 1/3)..."

# If you see rate limits, reduce concurrency:
config = create_config(
    document_intelligence_max_concurrency=3,  # Reduce from 5
    azure_openai_max_concurrency=5            # Reduce from 10
)
```

### Detailed Guides

- [OPTIMIZATION_RECOMMENDATIONS.md](OPTIMIZATION_RECOMMENDATIONS.md) - Strategy & analysis
- [PARALLEL_PROCESSING_GUIDE.md](PARALLEL_PROCESSING_GUIDE.md) - Implementation guide

---

## That's It!

Ingestor v4.0 is a **library**, not an API. Just:
1. `pip install -e .`
2. Create `.env` with your credentials
3. `from ingestor import run_pipeline`
4. `await run_pipeline(input_glob="docs/*.pdf")`

**No server needed!** 🚀
