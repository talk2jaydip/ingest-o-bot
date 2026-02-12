# Environment Variables Quick Reference

Quick lookup for all environment variables organized by scenario.

## Quick Scenario Selector

| What I Need | Scenario | Key Variables |
|-------------|----------|---------------|
| Test locally, no costs | Local Dev | `VECTOR_STORE_MODE=chromadb`, `EMBEDDINGS_MODE=huggingface` |
| Enterprise production | Azure Full | `AZURE_SEARCH_SERVICE`, `AZURE_OPENAI_ENDPOINT` |
| Reduce embedding costs | Cost-Optimized | `AZURE_SEARCH_SERVICE`, `EMBEDDINGS_MODE=huggingface` |
| Air-gapped environment | Fully Offline | `VECTOR_STORE_MODE=chromadb`, `AZURE_INPUT_MODE=local` |
| Multilingual (100+ langs) | Multilingual | `EMBEDDINGS_MODE=cohere` or `HUGGINGFACE_MODEL=multilingual-e5` |

---

## Core Variables (Always Check These First)

| Variable | Values | When Required | Purpose |
|----------|--------|---------------|---------|
| `VECTOR_STORE_MODE` | `azure_search`, `chromadb` | Always* | Choose vector database |
| `EMBEDDINGS_MODE` | `azure_openai`, `huggingface`, `cohere` | Always* | Choose embeddings provider |
| `AZURE_INPUT_MODE` | `local`, `blob` | Always | Where to read documents |
| `AZURE_USE_INTEGRATED_VECTORIZATION` | `true`, `false` | Always** | Critical for non-Azure embeddings |

*Default: `azure_search` and `azure_openai` if not set
**Must be `false` for HuggingFace, Cohere, non-Azure providers

---

## Scenario: Local Development

```bash
# Vector Store
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=dev-documents

# Embeddings
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_DEVICE=cpu

# Input/Output
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=documents/**/*.pdf
AZURE_ARTIFACTS_DIR=./artifacts

# Processing
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Required:** Only the variables above
**Optional:** None
**Cost:** $0/month

---

## Scenario: Azure Full Stack

```bash
# Vector Store
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
AZURE_SEARCH_KEY=your-key

# Embeddings
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Document Processing
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-key

# Storage (for blob mode)
AZURE_STORAGE_ACCOUNT=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_STORAGE_CONTAINER=documents

# Input/Output
AZURE_INPUT_MODE=blob  # or local for dev
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

**Required:** All variables above
**Optional:** Media descriptions, table summaries
**Cost:** ~$300-1000/month

---

## Scenario: Cost-Optimized

```bash
# Vector Store (Azure)
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
AZURE_SEARCH_KEY=your-key

# Embeddings (Local - FREE!)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda

# Critical!
AZURE_USE_INTEGRATED_VECTORIZATION=false

# Storage
AZURE_STORAGE_ACCOUNT=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_INPUT_MODE=blob
AZURE_STORAGE_CONTAINER=documents
```

**Required:** Variables above
**Savings:** ~$1,000/month on embeddings
**Cost:** ~$250-500/month (Azure Search + Storage only)

---

## Scenario: Fully Offline

```bash
# Vector Store
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=offline-documents
CHROMADB_PERSIST_DIR=./chroma_db

# Embeddings
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2

# Input/Output
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=documents/**/*.pdf
AZURE_ARTIFACTS_DIR=./artifacts

# Processing
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
AZURE_MEDIA_DESCRIBER=disabled
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Required:** Only variables above
**Internet:** Not needed after initial setup
**Cost:** $0/month

---

## Variable Categories

### Vector Store: Azure AI Search

| Variable | Required | Example |
|----------|----------|---------|
| `AZURE_SEARCH_SERVICE` | Yes* | `my-search-service` |
| `AZURE_SEARCH_ENDPOINT` | Yes* | `https://....search.windows.net` |
| `AZURE_SEARCH_INDEX` | Yes | `documents` |
| `AZURE_SEARCH_KEY` | No** | `your-admin-key` |

*Either SERVICE or ENDPOINT
**Optional with managed identity

---

### Vector Store: ChromaDB

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `VECTOR_STORE_MODE` | Yes | `chromadb` | Must be set |
| `CHROMADB_COLLECTION_NAME` | No | `documents` | Default: documents |
| `CHROMADB_PERSIST_DIR` | No | `./chroma_db` | Omit for in-memory |
| `CHROMADB_HOST` | No | `localhost` | For client/server |
| `CHROMADB_PORT` | No | `8000` | For client/server |

---

### Embeddings: Azure OpenAI

| Variable | Required | Example |
|----------|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | Yes | `https://....openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Yes | `your-key` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Yes* | `text-embedding-ada-002` |

*Not required if integrated vectorization enabled

---

### Embeddings: HuggingFace

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `EMBEDDINGS_MODE` | Yes | `huggingface` | Must be set |
| `HUGGINGFACE_MODEL_NAME` | No | `all-MiniLM-L6-v2` | Has default |
| `HUGGINGFACE_DEVICE` | No | `cpu`, `cuda`, `mps` | Default: cpu |
| `AZURE_USE_INTEGRATED_VECTORIZATION` | Yes | `false` | MUST be false |

---

### Embeddings: Cohere

| Variable | Required | Example |
|----------|----------|---------|
| `EMBEDDINGS_MODE` | Yes | `cohere` |
| `COHERE_API_KEY` | Yes | `your-key` |
| `COHERE_MODEL_NAME` | No | `embed-multilingual-v3.0` |
| `AZURE_USE_INTEGRATED_VECTORIZATION` | Yes | `false` |

---

### Input Source: Local Files

| Variable | Required | Example |
|----------|----------|---------|
| `AZURE_INPUT_MODE` | Yes | `local` |
| `AZURE_LOCAL_GLOB` | Yes | `documents/**/*.pdf` |

---

### Input Source: Azure Blob

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `AZURE_INPUT_MODE` | Yes | `blob` | |
| `AZURE_STORAGE_ACCOUNT` | Yes | `mystorageaccount` | |
| `AZURE_STORAGE_ACCOUNT_KEY` | Yes* | `your-key` | *Or connection string |
| `AZURE_STORAGE_CONTAINER` | Yes** | `documents` | **Or explicit container |
| `AZURE_BLOB_CONTAINER_IN` | Yes** | `documents-input` | **Or base container |

---

### Document Processing

| Variable | Values | Default | Notes |
|----------|--------|---------|-------|
| `AZURE_DOC_INT_ENDPOINT` | URL | None | Not needed for markitdown mode |
| `AZURE_DOC_INT_KEY` | Key | None | Optional with managed identity |
| `AZURE_OFFICE_EXTRACTOR_MODE` | `azure_di`, `markitdown`, `hybrid` | `hybrid` | Extraction mode |
| `AZURE_OFFICE_OFFLINE_FALLBACK` | `true`, `false` | `true` | Hybrid mode only |

---

### Media & Tables

| Variable | Values | Default |
|----------|--------|---------|
| `AZURE_MEDIA_DESCRIBER` | `gpt4o`, `disabled` | `disabled` |
| `AZURE_TABLE_RENDER` | `plain`, `markdown`, `html` | `markdown` |
| `AZURE_TABLE_SUMMARIES` | `true`, `false` | `false` |

---

### Chunking

| Variable | Example | Default | Notes |
|----------|---------|---------|-------|
| `CHUNKING_MAX_TOKENS` | `500` | `500` | Auto-adjusted by model |
| `CHUNKING_MAX_CHARS` | `2000` | `2000` | Soft limit |
| `CHUNKING_OVERLAP_PERCENT` | `10` | `10` | Overlap between chunks |

---

### Performance

| Variable | Example | Default | Use Case |
|----------|---------|---------|----------|
| `AZURE_MAX_WORKERS` | `4` | `4` | Parallel documents |
| `AZURE_EMBED_BATCH_SIZE` | `128` | `128` | Embedding batching |
| `AZURE_UPLOAD_BATCH_SIZE` | `1000` | `1000` | Upload batching |

---

### Logging

| Variable | Values | Default |
|----------|--------|---------|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FILE_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `DEBUG` |
| `LOG_ARTIFACTS` | `true`, `false` | `true` |
| `LOG_USE_COLORS` | `true`, `false` | `true` |

---

## Common Mistakes & Fixes

### ❌ Mistake: Using HuggingFace with integrated vectorization enabled

```bash
# WRONG:
EMBEDDINGS_MODE=huggingface
AZURE_USE_INTEGRATED_VECTORIZATION=true  # ❌ ERROR!
```

```bash
# CORRECT:
EMBEDDINGS_MODE=huggingface
AZURE_USE_INTEGRATED_VECTORIZATION=false  # ✅
```

---

### ❌ Mistake: Missing VECTOR_STORE_MODE for ChromaDB

```bash
# WRONG:
CHROMADB_COLLECTION_NAME=documents  # ❌ Won't use ChromaDB!
```

```bash
# CORRECT:
VECTOR_STORE_MODE=chromadb  # ✅ Explicitly set
CHROMADB_COLLECTION_NAME=documents
```

---

### ❌ Mistake: Blob input without container

```bash
# WRONG:
AZURE_INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=myaccount  # ❌ No container!
```

```bash
# CORRECT (Option 1 - Simple):
AZURE_INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=myaccount
AZURE_STORAGE_CONTAINER=documents  # ✅ Auto-creates input/output

# CORRECT (Option 2 - Explicit):
AZURE_INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=myaccount
AZURE_BLOB_CONTAINER_IN=documents-input  # ✅ Explicit
```

---

### ❌ Mistake: Azure DI with markitdown mode

```bash
# WRONG:
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
AZURE_DOC_INT_ENDPOINT=https://...  # ❌ Not needed!
```

```bash
# CORRECT:
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
# No AZURE_DOC_INT_ENDPOINT needed ✅
```

---

## Validation Commands

```bash
# Check current configuration
python -m ingestor.scenario_validator

# Validate specific scenario
python -m ingestor.scenario_validator offline
python -m ingestor.scenario_validator azure_full

# Full pre-check
python -m ingestor.cli --validate
```

---

## Need More Help?

- **Complete Guide:** [ENVIRONMENT_CONFIGURATION_GUIDE.md](ENVIRONMENT_CONFIGURATION_GUIDE.md)
- **Setup Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Templates:** [envs/](envs/) directory
- **Validator:** `python -m ingestor.scenario_validator`

---

**Quick Copy-Paste Templates:**

```bash
# Local Dev (Free)
cp envs/.env.scenario-development.example .env

# Azure Full Stack
cp envs/.env.example .env

# Cost-Optimized
cp envs/.env.hybrid.example .env

# Fully Offline
cp envs/.env.chromadb.example .env
```
