# Ingestor Examples

Example scripts and notebooks demonstrating ingestor library usage.

## 📁 Directory Structure

```
examples/
├── README.md                   # This file
├── scripts/                    # Python script examples
│   ├── 01_basic_usage.py
│   ├── 02_custom_config.py
│   ├── 03_streaming_logs.py
│   └── 04_batch_processing.py
├── notebooks/                  # Jupyter notebook examples (coming soon)
│   ├── 01_quickstart.ipynb
│   ├── 02_configuration.ipynb
│   └── 03_advanced_features.ipynb
└── data/                       # Sample documents for testing
    └── sample.pdf
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

2. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp ../.env.example .env

   # Edit .env with your Azure credentials
   # Required variables:
   # - AZURE_SEARCH_SERVICE
   # - AZURE_SEARCH_KEY
   # - AZURE_SEARCH_INDEX
   # - DOCUMENTINTELLIGENCE_ENDPOINT
   # - DOCUMENTINTELLIGENCE_KEY
   # - AZURE_OPENAI_ENDPOINT
   # - AZURE_OPENAI_KEY
   # - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
   ```

## 📝 Python Script Examples

### 01_basic_usage.py
**Minimal hello-world example**

The simplest way to use ingestor. Loads configuration from `.env` and processes documents.

```bash
python examples/scripts/01_basic_usage.py
```

**What it demonstrates:**
- Using `run_pipeline()` convenience function
- Reading configuration from `.env` file
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
