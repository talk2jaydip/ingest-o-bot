# Release v0.1.0 - Initial Release

> **Ingestor** - Document ingestion pipeline for Azure AI Search with intelligent chunking and embeddings

Released: 2026-02-06

---

## 🎉 What's New

This is the initial release of **Ingestor**, a Python library for ingesting multi-format documents into Azure AI Search with layout-aware chunking, client-side embeddings, and no dependency on Azure AI Search indexers or skillsets.

## ✨ Key Features

### Core Capabilities
- **📄 Multi-format document processing**: PDF, DOCX, PPTX, TXT, MD, HTML, JSON, CSV
- **🧠 Azure Document Intelligence integration**: Intelligent extraction of text, tables, and figures
- **✂️ Layout-aware chunking**: Token-first approach with smart segmentation (default: 8100 tokens per chunk)
- **🔢 Client-side embeddings**: Generate embeddings with Azure OpenAI before upload
- **🚀 Direct Azure AI Search upload**: No skillsets or indexers required
- **🖼️ GPT-4o figure captioning**: AI-powered image descriptions and visual media analysis
- **📑 Page-by-page PDF splitting**: Enable direct citations to specific pages

### Index Management
- Separate index operations (deploy, update, delete) independent of ingestion
- BM25 similarity optimized for technical/medical documents
- Vector search with HNSW and scalar quantization
- Semantic search with enhanced content ranking
- Configurable retry logic (default: 3 attempts)
- Graceful error handling for missing resources

### Multiple Interfaces
- **Command-line interface (CLI)**: Comprehensive options for batch processing
- **Gradio web UI**: Visual configuration, monitoring, and artifact browsing
- **Python library**: Full async API for programmatic integration
- Real-time processing logs and progress tracking

### Storage & Configuration
- Flexible input: local filesystem or Azure Blob Storage
- Azure Key Vault integration for secrets management
- Comprehensive environment variable configuration
- Support for multiple configuration scenarios

---

## 🚀 Quick Start

### Installation

**Using pip:**
```bash
pip install ingestor
```

**Using uv (recommended):**
```bash
uv pip install ingestor
```

**For development:**
```bash
git clone https://github.com/yourusername/ingestor
cd ingestor
uv pip install -e .
```

### Basic Usage

**Python Library:**
```python
import asyncio
from ingestor import run_pipeline

async def main():
    status = await run_pipeline(input_glob="documents/*.pdf")
    print(f"✅ Processed {status.successful_documents} documents")
    print(f"📦 Indexed {status.total_chunks_indexed} chunks")

asyncio.run(main())
```

**Command Line:**
```bash
ingestor --glob "documents/*.pdf"
```

**Web UI:**
```bash
ingestor-ui
```

---

## 📋 Requirements

- **Python**: 3.10+
- **Azure Services**:
  - Azure Document Intelligence
  - Azure AI Search
  - Azure OpenAI (with embedding deployment)

---

## 📚 Documentation

- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Configuration Guide](docs/guides/CONFIGURATION.md)** - Detailed configuration options
- **[Library Usage Guide](docs/guides/LIBRARY_USAGE.md)** - Using ingestor as a Python library
- **[Documentation Index](docs/INDEX.md)** - Central hub for all guides and references

---

## 🔧 Configuration

Create a `.env` file with your Azure credentials:

```bash
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=documents-index
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-di.cognitiveservices.azure.com
DOCUMENTINTELLIGENCE_KEY=your-di-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

See [Configuration Guide](docs/guides/CONFIGURATION.md) for all available options.

---

## 🏗️ Architecture

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

---

## ⚠️ Known Limitations

- Large files (>50MB) may require increased memory
- Concurrent processing limited by Azure service quotas
- Web UI currently single-user only

---

## 🔄 Migration

If you're migrating from **prepdocslib-minimal**, see the [Migration Guide](MIGRATION.md).

**Quick migration:**
```bash
pip uninstall prepdocslib-minimal
pip install ingestor
# Update imports: from prepdocslib_minimal → from ingestor
```

---

## 🐛 Bug Reports & Feature Requests

Please report issues on our [GitHub Issues](https://github.com/yourusername/ingestor/issues) page.

---

## 📄 License

This project is licensed under the MIT License.

---

**Made with ❤️ for the Azure AI community**
