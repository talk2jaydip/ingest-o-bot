# Ingestor Library Usage Guide

**Ingestor v4.0** is designed as a **Python library**, not an API service. Users import it directly into their Python code for full control over document ingestion.

## Why Library, Not API?

The library approach provides:

- ✅ **Direct Integration**: Import and use in your Python code
- ✅ **Full Control**: Configure everything programmatically or via .env
- ✅ **No Server Needed**: Runs in your process, not as a separate service
- ✅ **Flexible Deployment**: Use in scripts, notebooks, pipelines, or applications
- ✅ **Environment Isolation**: Each user controls their own credentials and settings

An API would only be needed if you need to serve multiple clients over HTTP, which is not the goal here.

---

## Installation

```bash
pip install ingestor
```

Or for development:

```bash
git clone https://github.com/yourusername/ingestor
cd ingestor
pip install -e .
```

---

## Usage Patterns

### 1. Load from .env (Simplest)

Create a `.env` file with your Azure credentials:

```bash
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents-index
AZURE_SEARCH_KEY=your-key
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-di.cognitiveservices.azure.com
DOCUMENTINTELLIGENCE_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

Then run:

```python
from ingestor import run_pipeline

# One-liner: load from .env and process
status = await run_pipeline(input_glob="documents/*.pdf")
print(f"Indexed {status.total_chunks_indexed} chunks")
```

### 2. ConfigBuilder (Most Flexible)

Build configuration entirely in code without environment variables:

```python
from ingestor import Pipeline, ConfigBuilder, OfficeExtractorMode

config = (
    ConfigBuilder()
    .with_search("my-search-service", "my-index", "key123")
    .with_document_intelligence("https://my-di.cognitiveservices.azure.com", "key456")
    .with_azure_openai("https://my-openai.openai.azure.com", "key789", "text-embedding-ada-002")
    .with_local_files("docs/*.pdf", "./artifacts")
    .with_chunking(max_tokens=1000, overlap_percent=15)
    .with_office_extractor_mode(OfficeExtractorMode.HYBRID)
    .build()
)

pipeline = Pipeline(config)
try:
    status = await pipeline.run()
    print(f"Processed {status.successful_documents} documents")
finally:
    await pipeline.close()
```

### 3. Hybrid Approach

Load base config from .env, then override specific values:

```python
from ingestor import create_config, Pipeline

config = create_config(
    input_glob="custom_docs/*.pdf",
    azure_search_index="custom-index",
    chunking_max_tokens=2000,
    performance_max_workers=16
)

pipeline = Pipeline(config)
try:
    status = await pipeline.run()
finally:
    await pipeline.close()
```

### 4. Multiple Environments

Use different .env files for dev, staging, and production:

```python
from ingestor import PipelineConfig, Pipeline

# Load from environment-specific file
config = PipelineConfig.from_env(env_path=".env.staging")

pipeline = Pipeline(config)
try:
    status = await pipeline.run()
finally:
    await pipeline.close()
```

### 5. Synchronous Usage

For non-async contexts (e.g., simple scripts):

```python
from ingestor import sync_run_pipeline

# No async/await needed
status = sync_run_pipeline(input_glob="documents/*.pdf")
print(f"Processed {status.successful_documents} documents")
```

---

## Configuration Options

### ConfigBuilder Methods

The `ConfigBuilder` class provides a fluent API for building configurations:

```python
ConfigBuilder()
    # Azure AI Search
    .with_search(service_name, index_name, api_key)
    .with_search_endpoint(endpoint, index_name, api_key)

    # Document Intelligence
    .with_document_intelligence(endpoint, key, max_concurrency)

    # Azure OpenAI
    .with_azure_openai(endpoint, api_key, embedding_deployment, ...)

    # Input sources
    .with_local_files(glob_pattern, artifacts_dir)
    .with_blob_input(account_url, container_in, prefix, ...)

    # Artifacts storage
    .with_blob_artifacts(account_url, container_pages, container_chunks, ...)

    # Processing options
    .with_office_extractor_mode(mode, offline_fallback, equation_extraction)
    .with_media_descriptions(mode)
    .with_table_rendering(mode, generate_summaries)
    .with_integrated_vectorization(enabled)

    # Performance
    .with_chunking(max_tokens, overlap_percent, ...)
    .with_performance(max_workers, embed_batch_size, ...)

    .build()
```

### create_config() Parameters

The `create_config()` helper supports:

**Direct parameters:**
- `input_glob` - Local file glob pattern
- `azure_search_index` - Search index name
- `env_path` - Path to .env file
- `use_env` - Whether to load from environment (default: True)

**Nested parameters** (using underscore notation):
- `chunking_max_tokens` → `config.chunking.max_tokens`
- `chunking_overlap_percent` → `config.chunking.overlap_percent`
- `performance_max_workers` → `config.performance.max_workers`
- `search_service_name` - For building from scratch
- `document_intelligence_endpoint` - For building from scratch
- `azure_openai_endpoint` - For building from scratch

**Example:**

```python
config = create_config(
    use_env=False,
    input_glob="docs/*.pdf",
    search_service_name="my-service",
    search_index_name="my-index",
    search_api_key="key",
    document_intelligence_endpoint="https://my-di.cognitiveservices.azure.com",
    azure_openai_endpoint="https://my-openai.openai.azure.com",
    azure_openai_api_key="key",
    azure_openai_embedding_deployment="text-embedding-ada-002",
    chunking_max_tokens=1500,
    performance_max_workers=8
)
```

---

## Common Use Cases

### Data Pipeline Integration

```python
from ingestor import Pipeline, PipelineConfig

def ingest_documents(file_paths: list[str]):
    """Integrate into your ETL pipeline."""
    config = PipelineConfig.from_env()
    # Override input dynamically
    config.input.local_glob = None  # Will process specific files

    pipeline = Pipeline(config)
    try:
        # Process specific files
        for file_path in file_paths:
            status = await pipeline.process_single_file(file_path)
            print(f"Processed {file_path}: {status.total_chunks_indexed} chunks")
    finally:
        await pipeline.close()
```

### Jupyter Notebook Exploration

```python
# In Jupyter cell
from ingestor import sync_run_pipeline

# Quick processing
status = sync_run_pipeline(
    input_glob="test_docs/*.pdf",
    azure_search_index="test-index",
    chunking_max_tokens=500
)

# Analyze results
print(f"Documents: {status.successful_documents}")
print(f"Chunks: {status.total_chunks_indexed}")
print(f"Avg chunks/doc: {status.total_chunks_indexed / status.successful_documents:.1f}")
```

### CI/CD Automation

```python
# In GitHub Actions or other CI
import os
from ingestor import create_config, Pipeline

async def ci_ingestion():
    """Run in CI environment."""
    config = create_config(
        env_path=".env.ci",  # CI-specific credentials
        input_glob="test_data/*.pdf",
        azure_search_index=f"test-{os.getenv('BUILD_ID')}"
    )

    pipeline = Pipeline(config)
    try:
        status = await pipeline.run()
        assert status.successful_documents > 0
        return status
    finally:
        await pipeline.close()
```

---

## Complete Examples

See [examples/scripts/00_library_usage_guide.py](../../examples/scripts/00_library_usage_guide.py) for comprehensive examples of all usage patterns.

Run the examples:

```bash
python examples/scripts/00_library_usage_guide.py
```

Test the configuration builders:

```bash
python examples/scripts/test_config_builder.py
```

---

## Why This Design?

### Library Benefits

1. **Simplicity**: Just `pip install` and import
2. **Flexibility**: Configure via code, .env, or both
3. **Integration**: Easy to embed in existing applications
4. **Debugging**: Runs in your process, easy to debug
5. **Credentials**: Users control their own Azure credentials
6. **No Server**: No need to deploy/maintain a web service

### When You Might Need an API

You'd only need a REST API if:
- Multiple clients need to share a single service
- You want centralized processing for many users
- You need language-agnostic access (non-Python clients)
- You want to abstract credentials from end users

For the stated goal ("let someone import this for ingestion purpose selecting their own env and flag"), the library approach is perfect.

---

## Migration from API-based Approach

If you previously used an API-based approach:

**Before (API):**
```bash
# Start server
uvicorn api:app

# Call from client
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"files": ["doc.pdf"]}'
```

**After (Library):**
```python
from ingestor import run_pipeline

# Direct import and use
status = await run_pipeline(input_glob="documents/*.pdf")
```

Benefits:
- ✅ No server to maintain
- ✅ No HTTP overhead
- ✅ Direct error handling
- ✅ Simpler deployment
- ✅ Better performance

---

## Summary

**Ingestor v4.0** is a library, not an API. Users import it, configure it their way, and run end-to-end ingestion in their own Python process. This provides maximum flexibility and control without the complexity of a web service.

For questions or issues, see:
- [Configuration Guide](CONFIGURATION.md)
- [Quick Start](QUICKSTART.md)
- [Examples](../../examples/)
