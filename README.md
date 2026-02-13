# Ingestor

> Document ingestion pipeline for Azure AI Search with intelligent chunking and embeddings

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Ingestor** is a Python library for ingesting multi-format documents into Azure AI Search with layout-aware chunking, client-side embeddings, and no dependency on Azure AI Search indexers or skillsets.

## ✨ Features

- 📄 **Multi-format support**: PDF, DOCX, PPTX, TXT, MD, HTML, JSON, CSV
- 🧠 **Azure Document Intelligence**: Extract tables, figures, and layout information
- ✂️ **Layout-aware chunking**: Intelligent text segmentation respecting document structure
- 🎯 **Dynamic chunking**: Automatic adjustment based on embedding model token limits
- 🔢 **Pluggable embeddings**: Azure OpenAI, Hugging Face, Cohere, or OpenAI
- 🗄️ **Pluggable vector stores**: Azure AI Search or ChromaDB
- 🚀 **Direct index upload**: No skillsets or indexers required
- 🎨 **Table rendering**: Preserve table structure in Markdown or HTML
- 🖼️ **Figure captioning**: Optional AI-powered image descriptions
- ☁️ **Flexible storage**: Local files or Azure Blob Storage for input and artifacts
- 🔌 **Mix & Match**: Combine any vector store with any embedding provider

---

## 🔌 Pluggable Architecture

Ingestor now supports multiple vector databases and embedding providers through a pluggable architecture. Mix and match components to fit your needs!

### Vector Stores

| Store | Type | Offline | Features |
|-------|------|---------|----------|
| **Azure AI Search** | Cloud | ❌ | Enterprise SLA, hybrid search, integrated vectorization |
| **ChromaDB** | Local/Self-hosted | ✅ | Persistent, in-memory, or client/server modes |

### Embeddings Providers

| Provider | Type | Languages | Cost |
|----------|------|-----------|------|
| **Azure OpenAI** | Cloud | English++ | $$$ |
| **Hugging Face** | Local | 100+ | Free |
| **Cohere** | Cloud | 100+ | $$ |
| **OpenAI** | Cloud | English++ | $$-$$$ |

### Example Configurations

**Fully Offline (ChromaDB + Hugging Face):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=jinaai/jina-embeddings-v2-base-en  # Default: 768 dims, 8192 tokens
INPUT_MODE=local  # v2.0: renamed from AZURE_INPUT_MODE
EXTRACTION_MODE=markitdown  # v2.0: renamed from AZURE_OFFICE_EXTRACTOR_MODE
```

**Hybrid Cloud/Local (Azure Search + Hugging Face):**
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=huggingface
INPUT_MODE=local  # v2.0: renamed from AZURE_INPUT_MODE
```

**Cloud Optimized (Azure Search + Cohere):**
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-key
```

📖 **[See all configurations →](docs/configuration_examples.md)**

### Dynamic Chunking

The pipeline now features **automatic chunk size adjustment** based on your embedding model's token limit:

- 🎯 Prevents truncation and information loss
- 📊 15% safety buffer + overlap allowance
- ⚠️ Clear warning messages when adjustments occur
- 🔧 Works with any embedding model automatically

**Example:**
```
Model: all-mpnet-base-v2 (384 token limit)
Config: CHUNKING_MAX_TOKENS=500
Result: Automatically reduced to 288 tokens (with 15% buffer + 10% overlap)
```

**v2.0 Variable Naming**: Generic parameter names (Azure-prefixed names deprecated):
```bash
# v2.0 Generic Names (recommended)
CHUNKING_MAX_TOKENS=500
CHUNKING_MAX_CHARS=2000
CHUNKING_OVERLAP_PERCENT=10
INPUT_MODE=local
EXTRACTION_MODE=hybrid
MAX_WORKERS=4
EMBEDDING_BATCH_SIZE=128

# v1.x Azure-prefixed (deprecated, will be removed in v3.0)
AZURE_CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_MAX_CHARS=2000
AZURE_CHUNKING_OVERLAP_PERCENT=10
AZURE_INPUT_MODE=local
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_MAX_WORKERS=4
AZURE_EMBED_BATCH_SIZE=128
```

**Migration:** See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for upgrading from v1.x

See [Embeddings Providers Guide](docs/embeddings_providers.md#dynamic-chunking-feature) for details.

### Optional Dependencies

```bash
# For ChromaDB support
pip install -r requirements-chromadb.txt

# For Hugging Face, Cohere, OpenAI embeddings
pip install -r requirements-embeddings.txt
```

---

## 🚀 Quick Start

### Installation

**Using uv (recommended):**
```bash
uv pip install ingestor
```

**Using pip:**
```bash
pip install ingestor
```

**For development:**
```bash
git clone https://github.com/yourusername/ingestor
cd ingestor
uv pip install -e .
# Or: pip install -e .
```

### Basic Usage (Python Library)

```python
import asyncio
from ingestor import run_pipeline

async def main():
    # Process documents (requires .env with Azure credentials)
    status = await run_pipeline(input_glob="documents/*.pdf")
    print(f"✅ Processed {status.successful_documents} documents")
    print(f"📦 Indexed {status.total_chunks_indexed} chunks")

asyncio.run(main())
```

### Configuration

**Option 1: Environment variables (.env file)**

```bash
# Copy template
cp .env.example .env

# Edit with your Azure credentials
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=documents-index
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-di.cognitiveservices.azure.com
DOCUMENTINTELLIGENCE_KEY=your-di-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

See [.env.example](.env.example) for all available options.

**Option 2: Programmatic configuration**

```python
from ingestor import Pipeline, create_config

# Quick config with overrides
config = create_config(
    input_glob="docs/*.pdf",
    azure_search_index="my-index",
    split_pdf_by_page=True,
)

# Run pipeline
pipeline = Pipeline(config)
try:
    status = await pipeline.run()
finally:
    await pipeline.close()
```

---

## 📚 Library Usage

### Import and Basic Use

```python
from ingestor import Pipeline, PipelineConfig

# Load config from environment
config = PipelineConfig.from_env()

# Create and run pipeline
pipeline = Pipeline(config)
try:
    status = await pipeline.run()
    print(f"Indexed {status.total_chunks_indexed} chunks")
finally:
    await pipeline.close()
```

### Convenience Functions

```python
from ingestor import run_pipeline, create_config

# One-liner execution
status = await run_pipeline(input_glob="documents/*.pdf")

# With custom config
config = create_config(
    input_glob="documents/**/*.pdf",
    azure_search_index="custom-index",
    chunker_target_token_count=4000,
)
status = await run_pipeline(config=config)
```

### Synchronous Wrapper

```python
from ingestor import sync_run_pipeline

# For non-async contexts
status = sync_run_pipeline(input_glob="documents/*.pdf")
```

---

## 🖥️ Command-Line Interface

The `ingestor` CLI provides quick access to common operations.

### Basic Commands

```bash
# Process documents
ingestor --glob "documents/*.pdf"

# Setup index and process
ingestor --setup-index --glob "documents/*.pdf"

# Process single file
ingestor --pdf "document.pdf"

# Use specific environment file (test different configurations)
ingestor --env envs/.env.chromadb.example --glob "documents/*.pdf"
ingestor --env envs/.env.cohere.example --glob "documents/*.pdf"

# Delete index
ingestor --delete-index

# Check index status
ingestor --check-index
```

Run `ingestor --help` for all options.

### Testing Different Configurations

Use the `--env` flag to easily test different vector stores and embedding providers:

```bash
# Fully offline (ChromaDB + Hugging Face)
ingestor --env envs/.env.chromadb.example --glob "docs/*.pdf"

# Cloud optimized (Azure Search + Cohere)
ingestor --env envs/.env.cohere.example --glob "docs/*.pdf"

# Hybrid (Azure Search + local embeddings)
ingestor --env envs/.env.hybrid.example --glob "docs/*.pdf"
```

This makes it easy to compare performance, cost, and quality across different configurations without modifying your main `.env` file.

---

## 🎨 Gradio Web Interface

Launch the interactive web UI for document processing with a comprehensive feature set:

```bash
# Using the installed command
ingestor-ui

# Or using scripts
scripts/launch_ui.bat    # Windows
./scripts/launch_ui.sh   # Linux/Mac
```

The UI opens at http://localhost:7860 with:

### Key Features

- 🔧 **Environment File Selection** - Test different scenarios (offline, cloud, hybrid) without editing files
- ✅ **Configuration Validation** - Catch errors early with comprehensive pre-checks
- 📂 **Flexible Input** - Local files, folders, glob patterns, or Azure Blob Storage
- ⚙️ **Real-time Monitoring** - Live log streaming and progress tracking
- 🗑️ **Artifact Management** - Clean up blob storage artifacts (selective or full cleanup)
- 📊 **Index Review** - Search documents, view chunks, and remove documents from index
- 📈 **Usage Analytics** - Privacy-preserving local analytics (optional, opt-out available)
- 📚 **Built-in Help** - Environment variable reference and quick start guide

### Quick Start with UI

1. **Launch**: Run `ingestor-ui`
2. **Select Environment**: Choose from `envs/` directory (e.g., `.env.chromadb.example` for offline)
3. **Validate**: Click "Validate Configuration" to check your setup
4. **Process**: Upload a test file and click "Run Pipeline"
5. **Review**: Check "Review Index" tab to see indexed documents

**📖 [Complete Gradio UI Guide →](docs/guides/GRADIO_UI_GUIDE.md)** - Detailed documentation with all tabs, workflows, and troubleshooting

### Test Different Scenarios

Easily switch between configurations without editing files:

```bash
# Launch UI
ingestor-ui

# Then in the UI:
# 1. Select ".env.chromadb.example" → Test fully offline (ChromaDB + Hugging Face)
# 2. Select ".env.cohere.example" → Test cloud with Cohere embeddings
# 3. Select ".env.hybrid.example" → Test Azure Search + local embeddings
```

All environment files in `envs/` directory are automatically detected and available in the dropdown.

---

## 📖 Documentation

**[📚 Documentation Index](docs/INDEX.md)** - Central hub for all documentation (8 guides + 21 references)

### Getting Started
- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Gradio UI Guide](docs/guides/GRADIO_UI_GUIDE.md)** - Complete web interface documentation
- **[Quick Reference](docs/guides/QUICK_REFERENCE.md)** - Fast lookup for common operations
- **[Library Usage Guide](docs/guides/LIBRARY_USAGE.md)** - Using ingestor as a Python library

### Configuration
- **[Configuration Guide](docs/guides/CONFIGURATION.md)** - Detailed configuration options
- **[Vector Stores Guide](docs/vector_stores.md)** - Azure Search, ChromaDB, and more
- **[Embeddings Providers Guide](docs/embeddings_providers.md)** - Azure OpenAI, Hugging Face, Cohere, OpenAI
- **[Configuration Examples](docs/configuration_examples.md)** - All combinations and use cases
- **[Environment & Secrets](docs/guides/ENVIRONMENT_AND_SECRETS.md)** - Managing multiple environments
- **[Index Deployment Guide](docs/guides/INDEX_DEPLOYMENT_GUIDE.md)** - Azure Search index setup
- **[Logging Guide](docs/LOGGING_GUIDE.md)** - Centralized logging system and best practices

### Performance & Optimization
- **[Batch Processing Guide](docs/guides/BATCH_PROCESSING.md)** - Parallel document processing
- **[Performance Tuning Guide](docs/guides/PERFORMANCE_TUNING.md)** - Optimization strategies

### Additional Resources
- **[Examples](examples/)** - Python scripts and Jupyter notebooks
  - [Offline ChromaDB + Hugging Face](examples/offline_chromadb_huggingface.py) - Fully offline setup
  - [Azure Search + Cohere](examples/azure_search_cohere.py) - Cloud setup with Cohere
- **[Technical References](docs/reference/)** - 21 in-depth technical documents

---

## 🏗️ Architecture

### Pipeline Flow

```
Input Documents
    ↓
Extract Pages (Azure DI / MarkItDown)
    ↓
Chunk Text (Layout-aware)
    ↓
Generate Embeddings (Pluggable: Azure OpenAI / Hugging Face / Cohere / OpenAI)
    ↓
Upload to Vector Store (Pluggable: Azure Search / ChromaDB)
```

### Key Components

- **[Pipeline](src/ingestor/pipeline.py)** - Main orchestrator
- **[DI Extractor](src/ingestor/di_extractor.py)** - Azure Document Intelligence integration
- **[Office Extractor](src/ingestor/office_extractor.py)** - Office document processing
- **[Chunker](src/ingestor/chunker.py)** - Layout-aware tokenization
- **[Vector Store](src/ingestor/vector_store.py)** - Pluggable vector database abstraction (Azure Search, ChromaDB)
- **[Embeddings Provider](src/ingestor/embeddings_provider.py)** - Pluggable embeddings abstraction (Azure OpenAI, Hugging Face, Cohere, OpenAI)
- **[Index](src/ingestor/index.py)** - Azure Search index management
- **[Config](src/ingestor/config.py)** - Configuration handling

### Architecture Diagrams

For detailed visual representations of the system:
- **[High-Level Architecture](docs/architecture/01_HIGH_LEVEL_ARCHITECTURE.md)** - System overview
- **[Component Interactions](docs/architecture/02_COMPONENT_INTERACTIONS.md)** - Component relationships
- **[Data Flow](docs/architecture/03_DATA_FLOW.md)** - Processing pipeline
- **[Sequence Diagrams](docs/architecture/04_SEQUENCE_DOCUMENT_INGESTION.md)** - Workflow details
- **[All Architecture Docs](docs/architecture/)** - Complete architecture documentation

---

## 🔧 Configuration

The library supports extensive configuration via environment variables. See [.env.example](.env.example) for all options.

**Core settings:**
- `AZURE_SEARCH_SERVICE` - Azure Search service name
- `AZURE_SEARCH_KEY` - API key
- `AZURE_SEARCH_INDEX` - Index name
- `DOCUMENTINTELLIGENCE_ENDPOINT` - Azure DI endpoint
- `DOCUMENTINTELLIGENCE_KEY` - Azure DI key

See [Configuration Guide](docs/guides/CONFIGURATION.md) for details.

---

## 📊 Examples

See the [examples/](examples/) directory for Python scripts and Jupyter notebooks.

Quick example:

```python
# Basic usage
from ingestor import run_pipeline
status = await run_pipeline(input_glob="docs/*.pdf")
print(f"Indexed {status.total_chunks_indexed} chunks")
```

---

## 📄 License

This project is licensed under the MIT License.

---

**Made with ❤️ for the Azure AI community**
