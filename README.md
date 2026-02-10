# Ingestor

> Document ingestion pipeline for Azure AI Search with intelligent chunking and embeddings

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Ingestor** is a Python library for ingesting multi-format documents into Azure AI Search with layout-aware chunking, client-side embeddings, and no dependency on Azure AI Search indexers or skillsets.

## ✨ Features

- 📄 **Multi-format support**: PDF, DOCX, PPTX, TXT, MD, HTML, JSON, CSV
- 🧠 **Azure Document Intelligence**: Extract tables, figures, and layout information
- ✂️ **Layout-aware chunking**: Intelligent text segmentation respecting document structure
- 🔢 **Client-side embeddings**: Generate embeddings with Azure OpenAI before upload
- 🚀 **Direct index upload**: No skillsets or indexers required
- 🎨 **Table rendering**: Preserve table structure in Markdown or HTML
- 🖼️ **Figure captioning**: Optional AI-powered image descriptions
- ☁️ **Flexible storage**: Local files or Azure Blob Storage for input and artifacts

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

# Delete index
ingestor --delete-index

# Check index status
ingestor --check-index
```

Run `ingestor --help` for all options.

---

## 🎨 Web Interface

Launch the Gradio web UI for interactive document processing:

```bash
# Using the installed command
ingestor-ui

# Or using scripts
scripts/launch_ui.bat    # Windows
./scripts/launch_ui.sh   # Linux/Mac
```

The UI will open at http://localhost:7860 with features for:
- 📂 File browsing (local and blob storage)
- ⚙️ Configuration management
- 📊 Real-time log streaming
- 🔍 Artifacts inspection
- 📈 Token counting

---

## 📖 Documentation

**[📚 Documentation Index](docs/INDEX.md)** - Central hub for all documentation (8 guides + 21 references)

### Getting Started
- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Quick Reference](docs/guides/QUICK_REFERENCE.md)** - Fast lookup for common operations
- **[Library Usage Guide](docs/guides/LIBRARY_USAGE.md)** - Using ingestor as a Python library

### Configuration
- **[Configuration Guide](docs/guides/CONFIGURATION.md)** - Detailed configuration options
- **[Environment & Secrets](docs/guides/ENVIRONMENT_AND_SECRETS.md)** - Managing multiple environments
- **[Index Deployment Guide](docs/guides/INDEX_DEPLOYMENT_GUIDE.md)** - Azure Search index setup

### Performance & Optimization
- **[Batch Processing Guide](docs/guides/BATCH_PROCESSING.md)** - Parallel document processing
- **[Performance Tuning Guide](docs/guides/PERFORMANCE_TUNING.md)** - Optimization strategies

### Additional Resources
- **[Examples](examples/)** - Python scripts and Jupyter notebooks
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
Generate Embeddings (Azure OpenAI)
    ↓
Upload to Azure Search
```

### Key Components

- **[Pipeline](src/ingestor/pipeline.py)** - Main orchestrator
- **[DI Extractor](src/ingestor/di_extractor.py)** - Azure Document Intelligence integration
- **[Office Extractor](src/ingestor/office_extractor.py)** - Office document processing
- **[Chunker](src/ingestor/chunker.py)** - Layout-aware tokenization
- **[Embeddings](src/ingestor/embeddings.py)** - Embedding generation
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

## 🔀 Migrating from prepdocslib-minimal

See the [Migration Guide](MIGRATION.md) for upgrading from `prepdocslib-minimal` to `ingestor`.

**Quick migration:**
```bash
pip uninstall prepdocslib-minimal
pip install ingestor
# Update imports: from prepdocslib_minimal → from ingestor
```

---

## 📄 License

This project is licensed under the MIT License.

---

**Made with ❤️ for the Azure AI community**
