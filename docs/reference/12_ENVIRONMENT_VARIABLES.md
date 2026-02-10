# Environment Variables Guide

Complete reference for all environment variables used in `ingestor`. This guide matches the actual code implementation.

---

## Quick Start

### Set Up Environment

```bash
# Copy example environment file
cp envs/env.example .env

# Edit .env with your Azure credentials
# Then run the pipeline
python -m ingestor.cli
```

---

## Azure Service Principal

**Purpose:** Authenticate with Azure services using Service Principal credentials (for Key Vault, Azure AD, etc.)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_TENANT_ID` | No | - | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | No | - | Application (client) ID |
| `AZURE_CLIENT_SECRET` | No | - | Application client secret |

**Usage:** Required for Key Vault access and Azure AD authentication.

---

## Key Vault

**Purpose:** Store and retrieve secrets from Azure Key Vault

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KEY_VAULT_URI` | No | - | Key Vault URL (e.g., `https://your-keyvault.vault.azure.net/`) |

---

## Document Intelligence

**Purpose:** Extract text, tables, and figures from PDF documents

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_DOC_INT_ENDPOINT` | **Yes** | - | Document Intelligence endpoint URL |
| `AZURE_DOC_INT_KEY` | No | - | Document Intelligence API key |
| `AZURE_DI_MAX_CONCURRENCY` | No | `3` | Maximum concurrent Document Intelligence requests |

**Example:**
```bash
AZURE_DOC_INT_ENDPOINT=https://your-di-service.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key
AZURE_DI_MAX_CONCURRENCY=3
```

---

## Azure AI Search

**Purpose:** Configure Azure AI Search service and index

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_SEARCH_SERVICE` | **Yes*** | - | Search service name (auto-builds endpoint) |
| `AZURE_SEARCH_ENDPOINT` | **Yes*** | - | Full search endpoint URL (alternative to service name) |
| `AZURE_SEARCH_KEY` | No | - | Search API key |
| `AZURE_SEARCH_INDEX` | **Yes** | - | Index name |

*Either `AZURE_SEARCH_SERVICE` or `AZURE_SEARCH_ENDPOINT` is required.

**Example:**
```bash
# Option 1: Service name (recommended)
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name

# Option 2: Full endpoint
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name
```

---

## Azure OpenAI

**Purpose:** Configure Azure OpenAI for embeddings and chat (figure descriptions)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | **Yes** | - | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_KEY` | **Yes** | - | Azure OpenAI API key |
| `AZURE_OPENAI_API_KEY` | **Yes** | - | Alternative name for API key |
| `AZURE_OPENAI_API_VERSION` | No | `2024-12-01-preview` | API version |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | **Yes** | - | Embedding deployment name |
| `AZURE_OPENAI_EMBEDDING_MODEL` | No | `text-embedding-ada-002` | Embedding model name |
| `AZURE_OPENAI_EMBEDDING_NAME` | No | `text-embedding-ada-002` | Alternative name for embedding model |
| `AZURE_OPENAI_EMBEDDING_DIMENSIONS` | No | Model default | Custom dimensions for text-embedding-3-* models |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | No | - | Chat deployment name (for figure descriptions) |
| `AZURE_OPENAI_MODEL_NAME` | No | - | Chat model name |
| `AZURE_OPENAI_MODEL` | No | - | Alternative name for chat model |
| `AZURE_OPENAI_MAX_CONCURRENCY` | No | `5` | Maximum concurrent OpenAI requests |
| `AZURE_OPENAI_MAX_RETRIES` | No | `3` | Maximum retry attempts for API calls |

**Embedding Dimensions:**
- `text-embedding-ada-002`: Fixed 1536 (no custom dimensions)
- `text-embedding-3-small`: 512-1536 (default: 1536)
- `text-embedding-3-large`: 256-3072 (default: 3072)

**Example:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_OPENAI_MAX_RETRIES=3
```

---

## Azure Storage

**Purpose:** Configure Azure Blob Storage for input documents and artifacts

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_STORAGE_ACCOUNT` | Conditional* | - | Storage account name (auto-builds URL) |
| `AZURE_BLOB_ACCOUNT_URL` | Conditional* | - | Full blob storage URL (alternative to account name) |
| `AZURE_STORAGE_ACCOUNT_KEY` | Conditional* | - | Storage account key |
| `AZURE_CONNECTION_STRING` | Conditional* | - | Storage connection string (alternative to account/key) |

*Required when using blob storage for input or artifacts.

**Example:**
```bash
# Option 1: Account name + key
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key

# Option 2: Full URL + key
AZURE_BLOB_ACCOUNT_URL=https://your-storage-account.blob.core.windows.net
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key

# Option 3: Connection string
AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
```

---

## Input Configuration

**Purpose:** Configure where to read input documents from

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_INPUT_MODE` | No | `local` | Input source: `local` or `blob` |
| `AZURE_LOCAL_GLOB` | Conditional* | - | File glob pattern for local mode (e.g., `./data/*.pdf`) |
| `AZURE_BLOB_CONTAINER_IN` | Conditional** | - | Input container name (for blob mode) |
| `AZURE_STORAGE_CONTAINER` | Conditional** | - | Alternative name for input container |
| `AZURE_BLOB_PREFIX` | No | `""` | Blob prefix filter (folder path) |

*Required when `AZURE_INPUT_MODE=local`  
**Required when `AZURE_INPUT_MODE=blob`

**Example - Local Mode:**
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=./data/*.pdf
```

**Example - Blob Mode:**
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=input-container
AZURE_BLOB_PREFIX=documents/  # Optional: filter to folder
```

---

## Artifacts Storage

**Purpose:** Configure where to store intermediate artifacts (pages, chunks, images)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_ARTIFACTS_MODE` | No | Auto-detect* | Storage mode: `local` or `blob` |
| `AZURE_STORE_ARTIFACTS_TO_BLOB` | No | `false` | Force blob storage (overrides auto-detection) |
| `AZURE_ARTIFACTS_DIR` | Conditional** | `./artifacts` | Local directory for artifacts |
| `AZURE_BLOB_CONTAINER_PREFIX` | Conditional*** | `""` | Prefix for all blob container names |
| `AZURE_BLOB_CONTAINER_OUT_PAGES` | Conditional*** | - | Blob container for page artifacts |
| `AZURE_BLOB_CONTAINER_OUT_CHUNKS` | Conditional*** | - | Blob container for chunk artifacts |
| `AZURE_BLOB_CONTAINER_OUT_IMAGES` | Conditional*** | - | Blob container for image artifacts |
| `AZURE_BLOB_CONTAINER_CITATIONS` | No | - | Optional: Separate container for per-page PDFs |

*Auto-detection: Follows input mode (local→local, blob→blob)  
**Required when `AZURE_ARTIFACTS_MODE=local`  
***Required when `AZURE_ARTIFACTS_MODE=blob`

**Auto-Detection Logic:**
1. If `AZURE_ARTIFACTS_MODE` is explicitly set → use that
2. Else if `AZURE_STORE_ARTIFACTS_TO_BLOB=true` → use blob mode
3. Else if input mode is blob → use blob mode
4. Else → use local mode

**Example - Local Mode:**
```bash
AZURE_ARTIFACTS_MODE=local
AZURE_ARTIFACTS_DIR=./artifacts
```

**Example - Blob Mode:**
```bash
AZURE_ARTIFACTS_MODE=blob
AZURE_BLOB_CONTAINER_PREFIX=my-project
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations  # Optional
```

---

## Document Actions

**Purpose:** Control what operation to perform on documents

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_DOCUMENT_ACTION` | No | `add` | Action mode: `add`, `remove`, or `removeall` |

**Modes:**
- `add` (default): Process and index documents (full replace - deletes existing chunks first)
- `remove`: Remove specific documents from index by filename
- `removeall`: Remove ALL documents from index (⚠️ destructive!)

**Example:**
```bash
# Add/update documents (default)
AZURE_DOCUMENT_ACTION=add

# Remove specific documents
AZURE_DOCUMENT_ACTION=remove
# Then run with files to remove

# Remove all documents
AZURE_DOCUMENT_ACTION=removeall
```

---

## Processing Options

**Purpose:** Control document processing behavior

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_MEDIA_DESCRIBER` | No | `gpt4o` | Figure describer: `gpt4o`, `content_understanding`, or `disabled` |
| `AZURE_TABLE_RENDER` | No | `html` | Table format: `html` (best for frontend), `plain` (text grid), or `markdown` (markdown tables) |
| `AZURE_TABLE_SUMMARIES` | No | `false` | Generate LLM summaries for tables |
| `AZURE_GENERATE_PAGE_PDFS` | No | `false` | Generate per-page PDFs for citations |
| `AZURE_USE_INTEGRATED_VECTORIZATION` | No | `false` | Use Azure Search integrated vectorization (skip client-side embeddings) |

**Example:**
```bash
AZURE_MEDIA_DESCRIBER=gpt4o
AZURE_TABLE_RENDER=html  # Options: html, plain, markdown
AZURE_TABLE_SUMMARIES=false
AZURE_GENERATE_PAGE_PDFS=false
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

## Chunking Configuration

**Purpose:** Control how documents are split into searchable chunks

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_CHUNKING_MAX_CHARS` | No | `1000` | Maximum characters per chunk (soft limit) |
| `AZURE_CHUNKING_MAX_TOKENS` | No | `500` | Maximum tokens per chunk (hard limit) |
| `AZURE_CHUNKING_OVERLAP_PERCENT` | No | `10` | Overlap percentage between chunks (0-100) |

**Example:**
```bash
AZURE_CHUNKING_MAX_CHARS=1000
AZURE_CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_OVERLAP_PERCENT=10
```

---

## Performance Tuning

**Purpose:** Control concurrency and batch sizes

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_MAX_WORKERS` | No | `4` | Parallel file processing workers |
| `AZURE_INNER_ANALYZE_WORKERS` | No | `1` | Document Intelligence concurrent workers |
| `AZURE_UPLOAD_DELAY` | No | `0.5` | Delay between uploads (seconds) |
| `AZURE_EMBED_BATCH_SIZE` | No | `128` | Embeddings batch size |
| `AZURE_UPLOAD_BATCH_SIZE` | No | `1000` | Search upload batch size |

**Example:**
```bash
AZURE_MAX_WORKERS=4
AZURE_INNER_ANALYZE_WORKERS=1
AZURE_UPLOAD_DELAY=0.5
AZURE_EMBED_BATCH_SIZE=128
AZURE_UPLOAD_BATCH_SIZE=1000
```

---

## Azure Content Understanding

**Purpose:** Alternative to GPT-4o for image descriptions (optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_CONTENT_UNDERSTANDING_ENDPOINT` | No | - | Content Understanding endpoint URL |
| `AZURE_CONTENT_UNDERSTANDING_TENANT_ID` | No | - | Content Understanding tenant ID |

**Usage:** Set `AZURE_MEDIA_DESCRIBER=content_understanding` to use this service.

---

## Complete Example Configuration

```bash
# Azure Service Principal
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Key Vault
KEY_VAULT_URI=https://your-keyvault.vault.azure.net/

# Document Intelligence
AZURE_DOC_INT_ENDPOINT=https://your-di-service.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key
AZURE_DI_MAX_CONCURRENCY=3

# Azure AI Search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini

# Input (Local Mode)
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=./data/*.pdf

# Artifacts (Local Mode)
AZURE_ARTIFACTS_MODE=local
AZURE_ARTIFACTS_DIR=./artifacts

# Processing Options
AZURE_MEDIA_DESCRIBER=gpt4o
AZURE_TABLE_RENDER=html  # Options: html, plain, markdown
AZURE_DOCUMENT_ACTION=add

# Chunking
AZURE_CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_MAX_CHARS=1000
AZURE_CHUNKING_OVERLAP_PERCENT=10

# Performance
AZURE_MAX_WORKERS=4
AZURE_OPENAI_MAX_CONCURRENCY=5
```

---

## Troubleshooting

### Common Issues

**❌ Error: `AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE is required`**
- **Fix:** Set `AZURE_SEARCH_SERVICE` or `AZURE_SEARCH_ENDPOINT`

**❌ Error: `AZURE_DOC_INT_ENDPOINT is required`**
- **Fix:** Set `AZURE_DOC_INT_ENDPOINT`

**❌ Error: `AZURE_OPENAI_ENDPOINT is required`**
- **Fix:** Set `AZURE_OPENAI_ENDPOINT`

**❌ Error: `AZURE_LOCAL_GLOB is required when AZURE_INPUT_MODE=local`**
- **Fix:** Set `AZURE_LOCAL_GLOB` (e.g., `./data/*.pdf`)

**❌ Error: Rate limit exceeded**
- **Fix:** Reduce `AZURE_DI_MAX_CONCURRENCY` and `AZURE_OPENAI_MAX_CONCURRENCY`

---

## Related Documentation

- **[Quick Start Guide](../guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Configuration Guide](../guides/CONFIGURATION.md)** - Complete configuration reference
- **[Configuration Matrix](01_CONFIGURATION_MATRIX.md)** - All input/output scenarios
