# Configuration Reference

Complete reference for all configuration options in ingestor.

---

## Environment Variable Naming

The library uses **standard Azure naming conventions** with `AZURE_` prefix.

All environment variables use the `AZURE_` prefix for consistency with Azure tooling.

---

## Azure Service Principal

```bash
# Required for Key Vault access
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret

# Or use AZURE_ prefix
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

---

## Key Vault

```bash
KEY_VAULT_URI=https://your-keyvault.vault.azure.net/
```

---

## Azure AI Search

```bash
# Option 1: Service name (auto-builds endpoint)
AZURE_SEARCH_SERVICE=your-search-service

# Option 2: Full endpoint
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net

# Required
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name
```

---

## Azure Document Intelligence

```bash
AZURE_DOC_INT_ENDPOINT=https://your-di-service.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key

# Concurrency control (default: 3)
AZURE_DI_MAX_CONCURRENCY=3
```

---

## Azure OpenAI

```bash
# Endpoint and authentication
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Embeddings
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Custom dimensions (text-embedding-3-* only)
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536

# Chat (for figure descriptions)
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini

# Performance
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_OPENAI_MAX_RETRIES=3
```

### Embedding Dimensions

| Model | Support | Range |
|-------|---------|-------|
| text-embedding-ada-002 | Fixed | 1536 |
| text-embedding-3-small | Custom | 512-1536 |
| text-embedding-3-large | Custom | 256-3072 |

---

## Azure Blob Storage

```bash
# Account configuration
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key

# Or use connection string
AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

---

## Input Configuration

```bash
# Mode: local or blob
AZURE_INPUT_MODE=local

# For local files
AZURE_LOCAL_GLOB=./data/*.pdf

# For blob storage
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=input-container
AZURE_BLOB_PREFIX=documents/
```

### Supported File Types

| Extension | Processing |
|-----------|------------|
| `.pdf` | Document Intelligence |
| `.txt`, `.md` | Direct text extraction |
| `.html`, `.htm` | HTML tag stripping |
| `.json` | Pretty-print formatting |
| `.csv` | Markdown table conversion |

---

## Artifacts Storage

```bash
# Mode: local or blob
AZURE_ARTIFACTS_MODE=local
AZURE_ARTIFACTS_DIR=./artifacts

# For blob storage
AZURE_ARTIFACTS_MODE=blob
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

---

## Document Actions

```bash
# Action mode: add, remove, or removeall
AZURE_DOCUMENT_ACTION=add
```

| Action | Description |
|--------|-------------|
| `add` | Process and index documents (default) |
| `remove` | Remove documents by filename |
| `removeall` | Remove ALL documents (⚠️ dangerous) |

---

## Processing Options

```bash
# Media description: gpt4o, content_understanding, or disabled
AZURE_MEDIA_DESCRIBER=gpt4o

# Table rendering: plain or markdown
AZURE_TABLE_RENDER=plain

# Generate table summaries with GPT-4o
AZURE_TABLE_SUMMARIES=false

# Generate per-page PDFs for citations
AZURE_GENERATE_PAGE_PDFS=false

# Embedding mode
# false = client-side embeddings (Azure OpenAI)
# true = integrated vectorization (Azure Search)
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

## Chunking Configuration

```bash
# Maximum tokens per chunk (hard limit)
AZURE_CHUNKING_MAX_TOKENS=500

# Maximum characters per chunk (soft limit)
AZURE_CHUNKING_MAX_CHARS=1000

# Overlap percentage between chunks (0-100)
AZURE_CHUNKING_OVERLAP_PERCENT=10
```

---

## Performance Tuning

```bash
MAX_WORKERS=4
INNER_ANALYZE_WORKERS=1
UPLOAD_DELAY=0.5
EMBED_BATCH_SIZE=128
UPLOAD_BATCH_SIZE=1000
```

---

## CLI Usage

```bash
# Process specific file
python -m ingestor.cli --pdf "document.pdf"

# Process with glob pattern
python -m ingestor.cli --glob "docs/**/*.pdf"

# Remove documents
python -m ingestor.cli --action remove --glob "old_doc.pdf"

# Remove all documents
python -m ingestor.cli --action removeall
```

---

## Related Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Configuration Matrix](../reference/01_CONFIGURATION_MATRIX.md)** - All input/output scenarios
- **[Environment Variables](../reference/12_ENVIRONMENT_VARIABLES.md)** - Complete environment variable reference
- **[Input Sources](../reference/02_INPUT_SOURCES.md)** - Understanding INPUT vs OUTPUT containers
