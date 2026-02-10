# 📚 ingestor Documentation

Welcome to the documentation for ingestor - a minimal document ingestion pipeline for Azure AI Search.

---

## 🚀 Getting Started

| # | Document | Description |
|---|----------|-------------|
| 1 | **[Quick Start Guide](guides/QUICKSTART.md)** | ⭐ **Get started in 5 minutes** |
| 2 | **[Configuration Guide](guides/CONFIGURATION.md)** | Complete configuration reference |
| 3 | **[Index Deployment Guide](guides/INDEX_DEPLOYMENT_GUIDE.md)** | Deploy and configure Azure AI Search index |

---

## ⚡ Performance & Optimization

| # | Document | Description |
|---|----------|-------------|
| 1 | **[Batch Processing Guide](guides/BATCH_PROCESSING.md)** | ⭐ **Parallel document processing and batch optimization** |
| 2 | **[Performance Tuning Guide](guides/PERFORMANCE_TUNING.md)** | Optimization strategies, tuning, and monitoring |

---

## 📖 User Guides

Located in `docs/guides/`:

| # | Guide | Description |
|---|-------|-------------|
| 1 | [Quick Start](guides/QUICKSTART.md) | ⭐ **Installation, setup, and first run** |
| 2 | [Quick Reference](guides/QUICK_REFERENCE.md) | Fast lookup guide for common operations |
| 3 | [Validation Guide](guides/VALIDATION.md) | ⭐ **Pre-check validation of configuration and environment** |
| 4 | [Library Usage](guides/LIBRARY_USAGE.md) | Using ingestor as a Python library |
| 5 | [Configuration](guides/CONFIGURATION.md) | All configuration options explained |
| 6 | [Environment & Secrets](guides/ENVIRONMENT_AND_SECRETS.md) | Managing multiple environments and secrets |
| 7 | [Artifact Storage Simplified](guides/ARTIFACT_STORAGE_SIMPLIFIED.md) | Simplified artifact storage configuration guide |
| 8 | [Logging Guide](LOGGING_GUIDE.md) | Centralized logging system and best practices |
| 9 | [Batch Processing](guides/BATCH_PROCESSING.md) | Parallel document processing and batch optimization |
| 10 | [Performance Tuning](guides/PERFORMANCE_TUNING.md) | Performance optimization strategies and tuning |
| 11 | [Index Deployment](guides/INDEX_DEPLOYMENT_GUIDE.md) | Deploy index + ingest in one command |

---

## 📚 Technical Reference

Located in `docs/reference/` - Organized by implementation order:

### Configuration & Setup
| # | Document | Description |
|---|----------|-------------|
| 01 | [Configuration Matrix](reference/01_CONFIGURATION_MATRIX.md) | All input/output scenarios with exact env vars |
| 02 | [Input Sources](reference/02_INPUT_SOURCES.md) | Understanding INPUT vs OUTPUT containers |
| 03 | [Blob Storage](reference/03_BLOB_STORAGE.md) | Container prefix pattern & efficient creation |
| 12 | [Environment Variables](reference/12_ENVIRONMENT_VARIABLES.md) | ⭐ **Complete env vars guide** |
| 22 | [Validation Reference](reference/validation-reference.md) | Technical validation system reference |

### Document Processing
| # | Document | Description |
|---|----------|-------------|
| 04 | [Document Intelligence](reference/04_DOCUMENT_INTELLIGENCE.md) | How documents are extracted |
| 05 | [Figure Processing](reference/05_FIGURE_PROCESSING.md) | ⭐ **Extract BOTH OCR text AND AI descriptions** |
| 20 | [Table Processing](reference/20_TABLE_PROCESSING.md) | Table rendering modes and chunking strategies |

### Chunking
| # | Document | Description |
|---|----------|-------------|
| 06 | [Chunking](reference/06_CHUNKING.md) | ⭐ **Token-first approach with advanced mechanisms** |
| 07 | [Chunking Overlap](reference/07_CHUNKING_OVERLAP.md) | Chunking overlap & offset tracking |
| 08 | [Chunking Config](reference/08_CHUNKING_CONFIG.md) | Chunking configuration reference |

### Embeddings & Search
| # | Document | Description |
|---|----------|-------------|
| 09 | [Embeddings](reference/09_EMBEDDINGS.md) | Client-side vs integrated vectorization |
| 15 | [Index Configuration](reference/15_INDEX_CONFIGURATION.md) | BM25, analyzers, vector tuning |
| 16 | [Scoring Profiles](reference/16_SCORING_PROFILES.md) | Scoring profiles & hybrid search |

### Storage & Artifacts
| # | Document | Description |
|---|----------|-------------|
| 10 | [Document Actions](reference/10_DOCUMENT_ACTIONS.md) | Document identification, deletion, and updates |
| 11 | [Page Splitting](reference/11_PAGE_SPLITTING.md) | Per-page PDF splitting for citations |
| 13 | [Storage URLs](reference/13_STORAGE_URLS.md) | Storage URL structure and flow |
| 14 | [URL Structure](reference/14_URL_STRUCTURE.md) | Complete URL structure reference |
| 19 | [Citations](reference/19_CITATIONS.md) | Image citation format and usage |

### Architecture & Overview
| # | Document | Description |
|---|----------|-------------|
| 17 | [Features](reference/17_FEATURES.md) | All features documented |
| 18 | [Architecture](reference/18_ARCHITECTURE.md) | Technical architecture & design |
| 21 | [Index Schema](reference/21_INDEX_SCHEMA.md) | Complete Azure AI Search index schema reference |

---

## 🏗️ Architecture Diagrams

Located in `docs/architecture/` - Visual representations of system design:

| # | Diagram | Description |
|---|---------|-------------|
| 1 | **[High-Level Architecture](architecture/01_HIGH_LEVEL_ARCHITECTURE.md)** | ⭐ **System overview with all major components** |
| 2 | [Component Interactions](architecture/02_COMPONENT_INTERACTIONS.md) | Detailed component relationships and dependencies |
| 3 | [Data Flow Diagram](architecture/03_DATA_FLOW.md) | End-to-end data processing flow |
| 4 | [Document Ingestion Sequence](architecture/04_SEQUENCE_DOCUMENT_INGESTION.md) | ⭐ **Step-by-step ADD workflow** |
| 5 | [Document Removal Sequence](architecture/05_SEQUENCE_DOCUMENT_REMOVAL.md) | REMOVE workflow details |
| 6 | [Index Management Sequence](architecture/06_SEQUENCE_INDEX_MANAGEMENT.md) | Setup, deletion, and REMOVE_ALL operations |
| 7 | [DrawIO Architecture](architecture/07_DRAWIO_ARCHITECTURE.drawio) | Editable architecture diagram (import into diagrams.net) |

**Getting Started with Diagrams:**
- New to the system? Start with [High-Level Architecture](architecture/01_HIGH_LEVEL_ARCHITECTURE.md)
- Understanding workflows? Check [Document Ingestion Sequence](architecture/04_SEQUENCE_DOCUMENT_INGESTION.md)
- Need editable diagram? Use [DrawIO file](architecture/07_DRAWIO_ARCHITECTURE.drawio) with diagrams.net

---

## 🗂️ Documentation Structure

```
docs/
├── INDEX.md                       # This file - main documentation index
├── LOGGING_GUIDE.md              # Centralized logging system guide
│
├── guides/                        # User-facing guides (10 guides)
│   ├── QUICKSTART.md             # Get started in 5 minutes
│   ├── QUICK_REFERENCE.md        # Fast lookup guide
│   ├── VALIDATION.md             # Configuration validation guide
│   ├── LIBRARY_USAGE.md          # Using as a Python library
│   ├── CONFIGURATION.md          # Complete configuration reference
│   ├── ENVIRONMENT_AND_SECRETS.md # Managing environments
│   ├── ARTIFACT_STORAGE_SIMPLIFIED.md # Artifact storage configuration
│   ├── BATCH_PROCESSING.md       # Batch processing and parallel execution
│   ├── PERFORMANCE_TUNING.md     # Performance optimization guide
│   └── INDEX_DEPLOYMENT_GUIDE.md # Index deployment guide
│
├── architecture/                  # Architecture diagrams (7 diagrams)
│   ├── README.md                 # Architecture documentation index
│   ├── 01_HIGH_LEVEL_ARCHITECTURE.md    # System overview
│   ├── 02_COMPONENT_INTERACTIONS.md     # Component relationships
│   ├── 03_DATA_FLOW.md                  # Data processing flow
│   ├── 04_SEQUENCE_DOCUMENT_INGESTION.md # ADD workflow
│   ├── 05_SEQUENCE_DOCUMENT_REMOVAL.md  # REMOVE workflow
│   ├── 06_SEQUENCE_INDEX_MANAGEMENT.md  # Index operations
│   └── 07_DRAWIO_ARCHITECTURE.drawio    # Editable diagram
│
└── reference/                     # Technical reference (22 docs)
    ├── 01_CONFIGURATION_MATRIX.md
    ├── 02_INPUT_SOURCES.md
    ├── 03_BLOB_STORAGE.md
    ├── 04_DOCUMENT_INTELLIGENCE.md
    ├── 05_FIGURE_PROCESSING.md
    ├── 06_CHUNKING.md
    ├── 07_CHUNKING_OVERLAP.md
    ├── 08_CHUNKING_CONFIG.md
    ├── 09_EMBEDDINGS.md
    ├── 10_DOCUMENT_ACTIONS.md
    ├── 11_PAGE_SPLITTING.md
    ├── 12_ENVIRONMENT_VARIABLES.md
    ├── 13_STORAGE_URLS.md
    ├── 14_URL_STRUCTURE.md
    ├── 15_INDEX_CONFIGURATION.md
    ├── 16_SCORING_PROFILES.md
    ├── 17_FEATURES.md
    ├── 18_ARCHITECTURE.md
    ├── 19_CITATIONS.md
    ├── 20_TABLE_PROCESSING.md
    ├── 21_INDEX_SCHEMA.md
    └── validation-reference.md    # Validation system reference

scripts/
├── utils/                         # Utility scripts
│   ├── validate_config.py        # Validation script
│   └── README.md
│
└── diagnostics/                   # Diagnostic and test scripts
    ├── test_*.py                  # Test scripts
    ├── verify_*.py                # Verification scripts
    ├── diagnose_*.py              # Diagnostic scripts
    ├── check_*.py                 # Check scripts
    ├── analyze_*.py               # Analysis scripts
    └── README.md
```

---

## 🚀 Quick Links

### Getting Started
```bash
# Install
pip install -r requirements.txt

# Configure
cp envs/env.example .env

# Run
python -m ingestor.cli --glob "data/*.pdf"
```

### Common Commands
```bash
# Process PDFs
python -m ingestor.cli --glob "*.pdf"

# Process all formats
python -m ingestor.cli --glob "**/*"

# Remove documents
python -m ingestor.cli --action remove --glob "old.pdf"
```

---

## 🔧 Core Modules

| Module | Purpose |
|--------|---------|
| `cli.py` | Command-line interface |
| `config.py` | Configuration management |
| `pipeline.py` | Main orchestrator |
| `di_extractor.py` | Document Intelligence |
| `chunker.py` | Text chunking |
| `embeddings.py` | Embedding generation |
| `search_uploader.py` | Azure AI Search upload |
| `artifact_storage.py` | Artifact storage |
| `input_source.py` | Input handling |
| `media_describer.py` | Image description |
| `table_renderer.py` | Table rendering |
| `page_splitter.py` | PDF page splitting |
| `models.py` | Data models |
| `logging_utils.py` | Logging utilities |

---

## ✨ Key Features

- **Multi-Format Support**: PDF, TXT, MD, HTML, JSON, CSV
- **Azure Integration**: Document Intelligence, OpenAI, AI Search
- **Smart Chunking**: Layout-aware with semantic overlap (10% default) and offset tracking
- **Citation System**: Per-page PDF linking
- **Document Actions**: Add, Remove, RemoveAll
- **Retry Logic**: Configurable retries (default: 3)

---

## 📝 Documentation Updates

This documentation structure was reorganized to match the implementation order:
- **Numbered reference files** - Organized by implementation flow
- **guides/** - User-facing guides for getting started and common tasks
- **reference/** - Technical reference documentation matching code structure

---

## 🔍 Finding What You Need

- **New to the project?** → Start with [Quick Start Guide](guides/QUICKSTART.md)
- **Validating setup?** → See [Validation Guide](guides/VALIDATION.md) ⭐
- **Need quick commands?** → Check [Quick Reference](guides/QUICK_REFERENCE.md)
- **Using as a library?** → See [Library Usage Guide](guides/LIBRARY_USAGE.md)
- **Processing multiple documents?** → See [Batch Processing Guide](guides/BATCH_PROCESSING.md)
- **Optimizing performance?** → Check [Performance Tuning Guide](guides/PERFORMANCE_TUNING.md)
- **Configuring the pipeline?** → Review [Configuration Guide](guides/CONFIGURATION.md)
- **Managing environments?** → See [Environment & Secrets Guide](guides/ENVIRONMENT_AND_SECRETS.md)
- **Configuring logging?** → See [Logging Guide](LOGGING_GUIDE.md)
- **Understanding a feature?** → Check [Features](reference/17_FEATURES.md)
- **Troubleshooting?** → Review [Environment Variables](reference/12_ENVIRONMENT_VARIABLES.md)
- **Advanced topics?** → Browse [Architecture](reference/18_ARCHITECTURE.md)

---

## 📞 Getting Help

```bash
# Validate configuration and environment
python -m ingestor.cli --validate

# Check configuration options
python -m ingestor.cli --help

# Verify index exists
python -m ingestor.cli --check-index

# Test with sample file first
AZURE_INPUT_MODE=local \
AZURE_LOCAL_GLOB=samples/sample_pages_test.pdf \
python -m ingestor.cli
```

---

**Last Updated**: Documentation reorganized to match implementation order
