# CLI Reference Guide

Complete command-line interface reference for the Ingestor document ingestion pipeline.

## Table of Contents

- [Quick Start](#quick-start)
- [Validation Commands](#validation-commands)
- [Index Management Commands](#index-management-commands)
- [Document Processing Commands](#document-processing-commands)
- [Azure AI Search Commands](#azure-ai-search-commands)
- [ChromaDB Commands](#chromadb-commands)
- [Advanced Options](#advanced-options)
- [Environment File Management](#environment-file-management)
- [Complete Workflows](#complete-workflows)

---

## Quick Start

```bash
# Validate configuration
python -m ingestor.cli --validate

# Process documents
python -m ingestor.cli --glob "documents/*.pdf"

# Setup index and process
python -m ingestor.cli --setup-index --glob "documents/*.pdf"
```

---

## Validation Commands

### Pre-Check Validation

Validate your entire configuration before processing documents:

```bash
# Run full validation check
python -m ingestor.cli --validate
```

**What it validates:**
- ✅ Input source configuration and file access
- ✅ Artifacts storage (local directory or blob container)
- ✅ Azure Document Intelligence connection
- ✅ Office extractor availability (MarkItDown)
- ✅ Azure OpenAI embeddings configuration
- ✅ Azure OpenAI vision deployment (if enabled)
- ✅ Azure AI Search index accessibility
- ✅ Media describer configuration
- ✅ Python dependencies (tiktoken, etc.)

**Example output:**
```
✅ [Input Source (Local)] Found 12 file(s) matching pattern: data/**/*.pdf
✅ [Artifacts Storage (Local)] Directory writable: artifacts
✅ [Document Intelligence] Client configured: https://your-di.cognitiveservices.azure.com/
✅ [Azure OpenAI (Embeddings)] Client configured: text-embedding-ada-002
✅ [Azure AI Search] Index accessible: documents-index (0 documents)
Summary: 5 passed, 0 failed
```

### Check Index Status

Check if an index exists without processing documents:

```bash
# Check index existence
python -m ingestor.cli --check-index

# With verbose output
python -m ingestor.cli --verbose --check-index
```

**Example output:**
```
✓ Index 'documents-index' exists
```

---

## Index Management Commands

### Create/Update Index Only

Deploy or update the Azure AI Search index without ingesting documents:

```bash
# Create/update index
python -m ingestor.cli --index-only

# With verbose logging
python -m ingestor.cli --verbose --index-only

# With specific environment file
python -m ingestor.cli --env .env.prod --index-only
```

**Use cases:**
- Initial index setup
- Schema updates
- Testing index configuration
- Preparing index before batch ingestion

### Setup Index Before Processing

Create/update index, then process documents:

```bash
# Setup index and process documents
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# Setup index then skip ingestion (separate steps)
python -m ingestor.cli --setup-index --skip-ingestion
python -m ingestor.cli --glob "documents/*.pdf"
```

### Delete Index

Remove the index entirely:

```bash
# Delete index (WARNING: destroys all data)
python -m ingestor.cli --delete-index

# Delete with specific environment
python -m ingestor.cli --env .env.test --delete-index
```

**⚠️ Warning:** This permanently deletes all indexed documents.

### Force Recreate Index

Delete and recreate the index (fresh start):

```bash
# Force recreate index (no ingestion)
python -m ingestor.cli --force-index

# Force recreate and process documents
python -m ingestor.cli --force-index --glob "documents/*.pdf"
```

**⚠️ Warning:** This destroys all existing data in the index.

**Use cases:**
- Schema changes requiring recreation
- Corrupted index recovery
- Testing with clean slate

---

## Document Processing Commands

### Process Documents with Glob Pattern

```bash
# Process all PDFs in directory
python -m ingestor.cli --glob "documents/*.pdf"

# Process all supported files recursively
python -m ingestor.cli --glob "documents/**/*"

# Process specific file types
python -m ingestor.cli --glob "documents/**/*.{pdf,docx,pptx}"
```

**Supported file types:**
- PDF (`.pdf`)
- Word Documents (`.docx`)
- PowerPoint (`.pptx`)
- Old Word/PowerPoint (`.doc`, `.ppt`) - requires LibreOffice
- Text files (`.txt`, `.md`)
- HTML (`.html`)
- JSON (`.json`)
- CSV (`.csv`)

### Process Single File

```bash
# Process single PDF
python -m ingestor.cli --pdf "document.pdf"

# Process single file (alias)
python -m ingestor.cli --file "document.pdf"
```

### Document Actions

```bash
# Add documents (default action)
python -m ingestor.cli --glob "documents/*.pdf"
python -m ingestor.cli --action add --glob "documents/*.pdf"

# Remove specific documents by filename
python -m ingestor.cli --action remove --glob "old_document.pdf"

# Remove ALL documents (WARNING: clears index)
python -m ingestor.cli --action removeall
```

---

## Azure AI Search Commands

### Complete Azure Search Workflow

```bash
# 1. Validate configuration
python -m ingestor.cli --validate

# 2. Create/update index
python -m ingestor.cli --index-only

# 3. Process documents
python -m ingestor.cli --glob "documents/**/*.pdf"

# 4. Verify index
python -m ingestor.cli --check-index
```

### Quick Setup (Single Command)

```bash
# Setup index and process in one command
python -m ingestor.cli --setup-index --glob "documents/**/*.pdf"
```

### Reset and Rebuild

```bash
# Delete everything and start fresh
python -m ingestor.cli --delete-index
python -m ingestor.cli --setup-index --glob "documents/**/*.pdf"
```

### Production Deployment

```bash
# Use production environment file
python -m ingestor.cli --env .env.prod --validate
python -m ingestor.cli --env .env.prod --setup-index --glob "production/**/*.pdf"
```

---

## ChromaDB Commands

### ChromaDB Workflow

ChromaDB automatically creates collections on first use - no index setup needed:

```bash
# Process documents (creates collection automatically)
python -m ingestor.cli --env .env.chromadb --glob "documents/*.pdf"

# Validate ChromaDB configuration
python -m ingestor.cli --env .env.chromadb --validate
```

### ChromaDB Modes

**Persistent (data saved to disk):**

`.env.chromadb`:
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=documents
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_BATCH_SIZE=1000
```

```bash
python -m ingestor.cli --glob "documents/*.pdf"
```

**In-Memory (temporary, lost on exit):**

`.env.chromadb.temp`:
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=temp-docs
# No CHROMADB_PERSIST_DIR = in-memory mode
```

```bash
python -m ingestor.cli --env .env.chromadb.temp --glob "documents/*.pdf"
```

**Client/Server (remote ChromaDB server):**

`.env.chromadb.remote`:
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
CHROMADB_AUTH_TOKEN=your-token
CHROMADB_COLLECTION_NAME=documents
```

```bash
python -m ingestor.cli --env .env.chromadb.remote --glob "documents/*.pdf"
```

---

## Advanced Options

### Verbose Logging

Enable detailed logging for debugging:

```bash
# Verbose mode
python -m ingestor.cli --verbose --glob "documents/*.pdf"

# Verbose validation
python -m ingestor.cli --verbose --validate

# Verbose index creation
python -m ingestor.cli --verbose --index-only
```

### No Colors (CI/CD Mode)

Disable colored output for CI/CD pipelines or log files:

```bash
# Plain output without colors
python -m ingestor.cli --no-colors --glob "documents/*.pdf"
```

### Skip Ingestion

Run index operations without document processing:

```bash
# Setup index but skip ingestion
python -m ingestor.cli --setup-index --skip-ingestion

# Delete index and skip any other processing
python -m ingestor.cli --delete-index --skip-ingestion
```

### Clean Artifacts

Clean up blob artifacts:

```bash
# Clean artifacts for specific files
python -m ingestor.cli --clean-artifacts --glob "document.pdf"

# Clean ALL artifacts (WARNING: destructive)
python -m ingestor.cli --clean-all-artifacts
```

---

## Environment File Management

### Using Custom Environment Files

The `--env` flag allows testing different configurations without changing your main `.env` file:

```bash
# Use specific environment file
python -m ingestor.cli --env .env.prod --glob "documents/*.pdf"
python -m ingestor.cli --env-file .env.test --glob "documents/*.pdf"  # alias

# Test different vector stores
python -m ingestor.cli --env .env.azure --glob "test/*.pdf"
python -m ingestor.cli --env .env.chromadb --glob "test/*.pdf"

# Test different embeddings providers
python -m ingestor.cli --env .env.azure_openai --glob "test/*.pdf"
python -m ingestor.cli --env .env.huggingface --glob "test/*.pdf"
python -m ingestor.cli --env .env.cohere --glob "test/*.pdf"
```

### Example Environment Files

**Azure Search + Azure OpenAI (.env.azure):**
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=documents-index

EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**ChromaDB + Hugging Face (.env.chromadb):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_COLLECTION_NAME=documents

EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
```

**Azure Search + Cohere (.env.cohere):**
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service
AZURE_SEARCH_KEY=your-key

EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-key
COHERE_MODEL_NAME=embed-multilingual-v3.0
```

---

## Complete Workflows

### Development Workflow

```bash
# 1. Validate local configuration
python -m ingestor.cli --validate

# 2. Test with sample documents
python -m ingestor.cli --glob "test/*.pdf"

# 3. If using Azure Search, check index
python -m ingestor.cli --check-index

# 4. Process full dataset
python -m ingestor.cli --glob "documents/**/*.pdf"
```

### Production Deployment Workflow

```bash
# 1. Validate production configuration
python -m ingestor.cli --env .env.prod --validate

# 2. Setup/update index
python -m ingestor.cli --env .env.prod --setup-index --skip-ingestion

# 3. Process documents with verbose logging
python -m ingestor.cli --env .env.prod --verbose --glob "production/**/*.pdf"

# 4. Verify index
python -m ingestor.cli --env .env.prod --check-index
```

### Testing Different Configurations

Compare Azure Search vs ChromaDB with same documents:

```bash
# Test with Azure Search
python -m ingestor.cli --env .env.azure --setup-index --glob "test/*.pdf"

# Test with ChromaDB
python -m ingestor.cli --env .env.chromadb --glob "test/*.pdf"

# Compare results and choose best fit
```

Test different embedding providers:

```bash
# Azure OpenAI embeddings
python -m ingestor.cli --env .env.azure_openai --setup-index --glob "test/*.pdf"

# Hugging Face embeddings (free, offline)
python -m ingestor.cli --env .env.huggingface --setup-index --glob "test/*.pdf"

# Cohere embeddings (multilingual)
python -m ingestor.cli --env .env.cohere --setup-index --glob "test/*.pdf"
```

### Reset and Rebuild Workflow

```bash
# 1. Delete existing index
python -m ingestor.cli --delete-index

# 2. Recreate index
python -m ingestor.cli --setup-index --skip-ingestion

# 3. Re-process all documents
python -m ingestor.cli --glob "documents/**/*.pdf"

# Or do it all in one command:
python -m ingestor.cli --force-index --glob "documents/**/*.pdf"
```

### Incremental Updates

```bash
# Add new documents to existing index
python -m ingestor.cli --glob "new_documents/*.pdf"

# Remove specific documents
python -m ingestor.cli --action remove --glob "old_document.pdf"

# Update existing documents (remove then add)
python -m ingestor.cli --action remove --glob "updated_doc.pdf"
python -m ingestor.cli --glob "updated_doc.pdf"
```

---

## All Available Flags

```bash
# Get full help
python -m ingestor.cli --help
```

**Available options:**

| Flag | Description |
|------|-------------|
| `--help`, `-h` | Show help message and exit |
| `--validate`, `--pre-check` | Run pre-check validation, then exit |
| `--env PATH`, `--env-file PATH` | Path to environment file (default: `.env`) |
| `--pdf PATH`, `--file PATH` | Path to single file to process |
| `--glob PATTERN` | Glob pattern for local files (overrides `LOCAL_INPUT_GLOB`) |
| `--action {add,remove,removeall}` | Document action (default: add) |
| `--setup-index` | Deploy/update index before ingestion |
| `--index-only` | Only deploy/update index, skip ingestion |
| `--force-index` | Force delete and recreate index, then exit |
| `--delete-index` | Delete index only |
| `--check-index` | Check if index exists, then exit |
| `--skip-ingestion` | Skip document ingestion pipeline |
| `--verbose` | Enable verbose/debug logging |
| `--no-colors` | Disable colorful console output |
| `--clean-artifacts` | Clean blob artifacts for specified files |
| `--clean-all-artifacts` | Clean ALL blob artifacts (WARNING: destructive) |

---

## Troubleshooting

### Common Issues

**"Index deployment failed: AZURE_SEARCH_ENDPOINT is required"**
```bash
# Check your .env file has correct Azure Search configuration
AZURE_SEARCH_SERVICE=your-service
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=your-index
```

**"No documents found matching pattern"**
```bash
# Verify glob pattern matches files
ls documents/*.pdf

# Try absolute path
python -m ingestor.cli --glob "C:/Work/documents/*.pdf"
```

**"Validation failed: Azure OpenAI embeddings not configured"**
```bash
# Ensure all required Azure OpenAI settings are present
AZURE_OPENAI_ENDPOINT=https://your.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**ChromaDB: "Connection refused"**
```bash
# For client/server mode, ensure ChromaDB server is running
docker run -p 8000:8000 chromadb/chroma

# Or use persistent mode instead
CHROMADB_PERSIST_DIR=./chroma_db
# Remove: CHROMADB_HOST and CHROMADB_PORT
```

---

## Related Documentation

- [Configuration Examples](configuration_examples.md) - All configuration scenarios
- [Environment Reference](../envs/QUICK_REFERENCE.md) - Parameter quick reference
- [Vector Stores Guide](vector_stores.md) - Azure Search and ChromaDB details
- [Embeddings Providers Guide](embeddings_providers.md) - Embedding provider details
- [Index Configuration Guide](INDEX_CONFIGURATION.md) - Azure Search index schema

---

**Last Updated:** 2026-02-17
