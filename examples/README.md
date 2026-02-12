# Ingestor Examples

Example scripts and notebooks demonstrating ingestor library usage with the pluggable architecture.

## 📚 NEW: Comprehensive Playbooks

**[Playbooks Directory](playbooks/)** - Production-ready, end-to-end workflow examples:
- **[01_basic_pdf_ingestion.py](playbooks/01_basic_pdf_ingestion.py)** - Complete beginner workflow with detailed steps
- **[02_multi_stage_pipeline.py](playbooks/02_multi_stage_pipeline.py)** - Process different document types with optimized settings
- **[03_error_handling_recovery.py](playbooks/03_error_handling_recovery.py)** - Robust error handling with retry and checkpoint/resume
- **[04_local_development.py](playbooks/04_local_development.py)** - Complete offline development setup (FREE)
- **[05_production_deployment.py](playbooks/05_production_deployment.py)** - Enterprise production deployment with Azure

Each playbook includes:
- ✅ Complete end-to-end workflow
- ✅ Companion .env.example file with detailed configuration
- ✅ Error handling and validation
- ✅ Step-by-step execution with logging
- ✅ Production best practices
- ✅ Troubleshooting guides

**[→ Explore Playbooks](playbooks/README.md)**

---

## 🔌 Pluggable Architecture Examples

The ingestor library supports multiple vector stores and embeddings providers. These examples demonstrate different configurations:

### Quick Examples
- **[offline_chromadb_huggingface.py](offline_chromadb_huggingface.py)** - Fully offline setup with ChromaDB + Hugging Face (zero API costs)
- **[azure_search_cohere.py](azure_search_cohere.py)** - Cloud setup with Azure Search + Cohere embeddings

### Configuration Examples (envs/ directory)
- **[.env.example](../envs/.env.example)** - Default Azure Search + Azure OpenAI
- **[.env.chromadb.example](../envs/.env.chromadb.example)** - Fully offline ChromaDB + Hugging Face
- **[.env.cohere.example](../envs/.env.cohere.example)** - Azure Search + Cohere
- **[.env.hybrid.example](../envs/.env.hybrid.example)** - Azure Search + local Hugging Face

## 📁 Directory Structure

```
examples/
├── README.md                           # This file
├── playbooks/                          # 🆕 Production-ready workflow examples
│   ├── README.md                        # Playbooks guide
│   ├── 01_basic_pdf_ingestion.py        # Basic end-to-end workflow
│   ├── .env.basic-pdf.example           # Basic configuration
│   ├── 02_multi_stage_pipeline.py       # Multi-stage processing
│   ├── 03_error_handling_recovery.py    # Error handling & retry
│   ├── 04_local_development.py          # Offline development setup
│   ├── 05_production_deployment.py      # Production deployment
│   └── .env.production.example          # Production configuration
├── offline_chromadb_huggingface.py    # Fully offline example
├── azure_search_cohere.py              # Cloud example with Cohere
├── scripts/                            # Python script examples
│   ├── 01_basic_usage.py               # Simplest example
│   ├── 02_custom_config.py             # Programmatic configuration
│   ├── 03_streaming_logs.py            # Real-time logging
│   ├── 04_batch_processing.py          # Multiple document sets
│   ├── 05_azure_blob.py                # Blob storage example
│   └── 06_index_management.py          # Index operations
├── notebooks/                          # Jupyter notebook examples
│   ├── 00_quick_playbook.ipynb         # Quick reference
│   ├── 01_quickstart.ipynb             # Getting started
│   ├── 02_configuration.ipynb          # Configuration deep dive
│   ├── 09_pluggable_architecture.ipynb # Vector stores & embeddings
│   └── ...                             # Additional notebooks
└── data/                               # Sample documents for testing
    └── (place your test PDFs here)
```

## 🚀 Getting Started

### Prerequisites

1. **Install ingestor:**
   ```bash
   # Using uv (recommended)
   uv pip install ingestor

   # Or using pip
   pip install ingestor
   ```

2. **Choose your configuration:**

   **Option A: Fully Offline (ChromaDB + Hugging Face)**
   ```bash
   # Install dependencies
   pip install -r requirements-chromadb.txt
   pip install -r requirements-embeddings.txt

   # Copy configuration
   cp envs/.env.chromadb.example .env

   # No Azure credentials needed!
   # Run: python examples/offline_chromadb_huggingface.py
   ```

   **Option B: Cloud (Azure Search + Azure OpenAI)**
   ```bash
   # Copy configuration
   cp envs/.env.example .env

   # Edit .env with your Azure credentials:
   # - AZURE_SEARCH_SERVICE
   # - AZURE_SEARCH_KEY
   # - AZURE_SEARCH_INDEX
   # - DOCUMENTINTELLIGENCE_ENDPOINT (optional)
   # - DOCUMENTINTELLIGENCE_KEY (optional)
   # - AZURE_OPENAI_ENDPOINT
   # - AZURE_OPENAI_KEY
   # - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
   ```

   **Option C: Hybrid (Azure Search + Hugging Face)**
   ```bash
   pip install -r requirements-embeddings.txt
   cp envs/.env.hybrid.example .env
   # Edit with Azure Search credentials only (no embedding API costs!)
   ```

3. **Place documents:**
   ```bash
   # Create documents directory
   mkdir documents

   # Copy your PDF files to documents/
   ```

## 🎯 Quick Start Examples

### Offline Example (No Cloud Required)
**[offline_chromadb_huggingface.py](offline_chromadb_huggingface.py)**

Fully offline document processing with ChromaDB + Hugging Face embeddings.

```bash
# Install dependencies
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt

# Run
python examples/offline_chromadb_huggingface.py
```

**Benefits:**
- Zero API costs
- Complete data privacy
- No internet required (after initial model download)
- Works with any document format

---

### Cloud Example
**[azure_search_cohere.py](azure_search_cohere.py)**

Enterprise setup with Azure AI Search + Cohere multilingual embeddings.

```bash
# Install Cohere
pip install cohere

# Configure .env with Azure and Cohere credentials

# Run
python examples/azure_search_cohere.py
```

**Benefits:**
- Enterprise-grade vector search
- 100+ language support
- Competitive pricing
- Scalable cloud infrastructure

---

## 📝 Python Script Examples

### 01_basic_usage.py
**Minimal hello-world example**

The simplest way to use ingestor. Loads configuration from `.env` and processes documents. Works with any vector store and embeddings configuration.

```bash
python examples/scripts/01_basic_usage.py
```

**What it demonstrates:**
- Using `run_pipeline()` convenience function
- Reading configuration from `.env` file
- Works with any pluggable configuration
- Basic result handling

---

### 02_custom_config.py
**Explicit configuration without .env**

Shows how to create configuration programmatically without relying on environment variables.

```bash
python examples/scripts/02_custom_config.py
```

**What it demonstrates:**
- Using `create_config()` helper
- Manual `PipelineConfig` creation
- Custom processing options
- Proper resource cleanup with try/finally

---

### 03_streaming_logs.py
**Monitor pipeline progress with detailed logging**

Enables detailed logging to see real-time progress as documents are processed.

```bash
python examples/scripts/03_streaming_logs.py
```

**What it demonstrates:**
- Setting up Python logging
- Monitoring pipeline progress
- Viewing detailed per-document results

---

### 04_batch_processing.py
**Process multiple document sets**

Process different document collections to different indexes in batches.

```bash
python examples/scripts/04_batch_processing.py
```

**What it demonstrates:**
- Processing multiple glob patterns
- Targeting different Azure Search indexes
- Aggregating results across batches
- Error handling per batch

---

## 📓 Jupyter Notebooks

Interactive notebooks for learning and experimentation.

### 01_quickstart.ipynb
Introduction to ingestor with step-by-step examples.

### 02_configuration.ipynb
Deep dive into all configuration options and how to use them.

### 03_advanced_features.ipynb
Advanced features like custom chunking, media description, and optimization.

**To use notebooks:**
```bash
# Install Jupyter
pip install jupyter

# Launch Jupyter
jupyter notebook examples/notebooks/
```

---

## 📊 Sample Data

The `data/` subdirectory contains sample documents for testing. Add your own test documents here.

**Supported formats:**
- PDF (`.pdf`)
- Word Documents (`.docx`)
- PowerPoint (`.pptx`)
- Text files (`.txt`, `.md`)
- HTML (`.html`)
- JSON (`.json`)
- CSV (`.csv`)

---

## 🆘 Troubleshooting

### Common Issues

**1. ImportError: No module named 'ingestor'**
```bash
# Make sure ingestor is installed
pip install ingestor
```

**2. Authentication errors**
```bash
# Check your .env file has correct Azure credentials
# Make sure environment variables are loaded
```

**3. "No documents found" error**
```bash
# Check your glob pattern matches actual files
# Use absolute paths if relative paths don't work
```

### Getting Help

- 📖 [Full Documentation](../docs/INDEX.md)
- 🐛 [Report Issues](https://github.com/yourusername/ingestor/issues)
- 💬 [Discussions](https://github.com/yourusername/ingestor/discussions)

---

## 🔗 Additional Resources

- [Main README](../README.md)
- [Configuration Guide](../docs/guides/CONFIGURATION.md)
- [API Reference](../docs/reference/)
- [Migration Guide](../MIGRATION.md)

---

## 📝 License

These examples are part of the ingestor project and are licensed under the MIT License.
