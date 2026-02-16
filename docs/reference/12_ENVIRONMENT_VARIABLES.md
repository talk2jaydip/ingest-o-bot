# Environment Variables Guide

Complete reference for all environment variables used in `ingestor`. This guide matches the actual code implementation.

**Note:** Variable names have been updated to a generic naming convention. Old `AZURE_*` prefixed names are deprecated but still supported for backward compatibility through v2.0.

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

**Purpose:** Configure Azure OpenAI for embeddings, vision (media description), and chat (table summaries)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | **Yes** | - | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_KEY` | **Yes** | - | Azure OpenAI API key |
| `AZURE_OPENAI_API_KEY` | No | - | Alternative name for API key (alias) |
| `AZURE_OPENAI_API_VERSION` | No | `2024-12-01-preview` | API version |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | **Yes*** | - | Embedding deployment name |
| `AZURE_OPENAI_EMBEDDING_MODEL` | No | `text-embedding-ada-002` | Embedding model name |
| `AZURE_OPENAI_EMBEDDING_DIMENSIONS` | No | Model default | Custom dimensions for text-embedding-3-* models |
| `AZURE_OPENAI_VISION_DEPLOYMENT` | No | - | Vision model deployment (for media description with MEDIA_DESCRIBER_MODE=gpt4o) |
| `AZURE_OPENAI_VISION_MODEL` | No | - | Vision model name (e.g., gpt-4o, gpt-4o-mini) |
| `AZURE_OPENAI_VISION_DETAIL` | No | `auto` | Vision detail level: `low`, `high`, `auto` |
| `AZURE_OPENAI_VISION_MAX_CONCURRENCY` | No | `10` | Maximum concurrent vision API requests |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | No | - | Chat deployment (for table summaries with TABLE_SUMMARIES_ENABLED=true) |
| `AZURE_OPENAI_MODEL_NAME` | No | - | Chat model name |
| `AZURE_OPENAI_MAX_CONCURRENCY` | No | `5` | Maximum concurrent OpenAI requests (embeddings/chat) |
| `AZURE_OPENAI_MAX_RETRIES` | No | `3` | Maximum retry attempts for API calls |

*Required when EMBEDDINGS_MODE=azure_openai

**Embedding Dimensions:**
- `text-embedding-ada-002`: Fixed 1536 (no custom dimensions)
- `text-embedding-3-small`: 512-1536 (default: 1536)
- `text-embedding-3-large`: 256-3072 (default: 3072)

**Example:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# For embeddings
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# For media description (optional)
AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_VISION_MODEL=gpt-4o-mini
AZURE_OPENAI_VISION_DETAIL=low

# For table summaries (optional)
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_MODEL_NAME=gpt-4o

# Concurrency
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
| `INPUT_MODE` | No | `local` | Input source: `local` or `blob` |
| `LOCAL_INPUT_GLOB` | Conditional* | - | File glob pattern for local mode (e.g., `./data/*.pdf`) |
| `AZURE_BLOB_CONTAINER_IN` | Conditional** | - | Input container name (for blob mode) |
| `AZURE_STORAGE_CONTAINER` | Conditional** | - | Alternative name for input container |
| `AZURE_BLOB_PREFIX` | No | `""` | Blob prefix filter (folder path) |

*Required when `INPUT_MODE=local`
**Required when `INPUT_MODE=blob`

**Deprecated Names (still supported, will be removed in v2.0):**
- `AZURE_INPUT_MODE` → use `INPUT_MODE`
- `AZURE_LOCAL_GLOB` → use `LOCAL_INPUT_GLOB`

**Example - Local Mode:**
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf
```

**Example - Blob Mode:**
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=input-container
AZURE_BLOB_PREFIX=documents/  # Optional: filter to folder
```

---

## Artifacts Storage

**Purpose:** Configure where to store intermediate artifacts (pages, chunks, images)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ARTIFACTS_MODE` | No | Auto-detect* | Storage mode: `local` or `blob` |
| `STORE_ARTIFACTS_TO_BLOB` | No | `false` | Force blob storage (overrides auto-detection) |
| `LOCAL_ARTIFACTS_DIR` | Conditional** | `./artifacts` | Local directory for artifacts |
| `BLOB_CONTAINER_PREFIX` | Conditional*** | `""` | Prefix for all blob container names |
| `AZURE_BLOB_CONTAINER_OUT_PAGES` | Conditional*** | - | Blob container for page artifacts |
| `AZURE_BLOB_CONTAINER_OUT_CHUNKS` | Conditional*** | - | Blob container for chunk artifacts |
| `AZURE_BLOB_CONTAINER_OUT_IMAGES` | Conditional*** | - | Blob container for image artifacts |
| `AZURE_BLOB_CONTAINER_CITATIONS` | No | - | Optional: Separate container for per-page PDFs |

*Auto-detection: Follows input mode (local→local, blob→blob)
**Required when `ARTIFACTS_MODE=local`
***Required when `ARTIFACTS_MODE=blob`

**Deprecated Names (still supported, will be removed in v2.0):**
- `AZURE_ARTIFACTS_MODE` → use `ARTIFACTS_MODE`
- `AZURE_STORE_ARTIFACTS_TO_BLOB` → use `STORE_ARTIFACTS_TO_BLOB`
- `AZURE_ARTIFACTS_DIR` → use `LOCAL_ARTIFACTS_DIR`
- `AZURE_BLOB_CONTAINER_PREFIX` → use `BLOB_CONTAINER_PREFIX`

**Auto-Detection Logic:**
1. If `ARTIFACTS_MODE` is explicitly set → use that
2. Else if `STORE_ARTIFACTS_TO_BLOB=true` → use blob mode
3. Else if input mode is blob → use blob mode
4. Else → use local mode

**Example - Local Mode:**
```bash
ARTIFACTS_MODE=local
LOCAL_ARTIFACTS_DIR=./artifacts
```

**Example - Blob Mode:**
```bash
ARTIFACTS_MODE=blob
BLOB_CONTAINER_PREFIX=my-project
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
| `DOCUMENT_ACTION` | No | `add` | Action mode: `add`, `remove`, or `removeall` |

**Modes:**
- `add` (default): Process and index documents (full replace - deletes existing chunks first)
- `remove`: Remove specific documents from index by filename
- `removeall`: Remove ALL documents from index (⚠️ destructive!)

**Deprecated Names (still supported, will be removed in v2.0):**
- `AZURE_DOCUMENT_ACTION` → use `DOCUMENT_ACTION`

**Example:**
```bash
# Add/update documents (default)
DOCUMENT_ACTION=add

# Remove specific documents
DOCUMENT_ACTION=remove
# Then run with files to remove

# Remove all documents
DOCUMENT_ACTION=removeall
```

---

## Processing Options

**Purpose:** Control document processing behavior

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MEDIA_DESCRIBER_MODE` | No | `disabled` | Image/media describer: `gpt4o`, `content_understanding`, or `disabled` |
| `TABLE_RENDER_FORMAT` | No | `markdown` | Table format: `plain`, `html`, or `markdown` (recommended) |
| `TABLE_SUMMARIES_ENABLED` | No | `false` | Generate LLM summaries for tables (requires AZURE_OPENAI_CHAT_DEPLOYMENT) |
| `GENERATE_PAGE_PDFS` | No | `false` | Generate per-page PDFs for citations |
| `AZURE_USE_INTEGRATED_VECTORIZATION` | No | `false` | Use Azure Search integrated vectorization (server-side embeddings) |

**Media Describer Modes:**
- `gpt4o`: Use Azure OpenAI GPT-4o Vision (requires AZURE_OPENAI_VISION_DEPLOYMENT)
- `content_understanding`: Use Azure AI Vision Content Understanding API
- `disabled`: Skip media description (zero cost, default)

**Table Render Formats:**
- `markdown`: Markdown table format (recommended for readability)
- `html`: HTML table format (for web display)
- `plain`: Plain text representation (legacy)

**Example:**
```bash
# Media description (requires AZURE_OPENAI_VISION_DEPLOYMENT if enabled)
MEDIA_DESCRIBER_MODE=disabled  # Options: disabled, gpt4o, content_understanding

# Table rendering
TABLE_RENDER_FORMAT=markdown  # Options: markdown, html, plain

# Table summaries (requires AZURE_OPENAI_CHAT_DEPLOYMENT if enabled)
TABLE_SUMMARIES_ENABLED=false

# Page PDFs
GENERATE_PAGE_PDFS=false

# Integrated vectorization (Azure Search only)
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

## Chunking Configuration

**Purpose:** Control how documents are split into searchable chunks

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHUNKING_MAX_CHARS` | No | `1000` | Maximum characters per chunk (soft limit) |
| `CHUNKING_MAX_TOKENS` | No | `500` | Maximum tokens per chunk (hard limit) |
| `CHUNKING_OVERLAP_PERCENT` | No | `10` | Overlap percentage between chunks (0-100) |
| `CHUNKING_CROSS_PAGE_OVERLAP` | No | `false` | Allow overlap across page boundaries |
| `CHUNKING_DISABLE_CHAR_LIMIT` | No | `false` | Disable character limit during chunking |
| `CHUNKING_TABLE_LEGEND_BUFFER` | No | `100` | Buffer for table legend/caption context (chars) |
| `CHUNKING_ABSOLUTE_MAX_TOKENS` | No | `8000` | Absolute maximum tokens per chunk (safety limit) |

**Deprecated Names (still supported, will be removed in v2.0):**
- `AZURE_CHUNKING_MAX_CHARS` → use `CHUNKING_MAX_CHARS`
- `AZURE_CHUNKING_MAX_TOKENS` → use `CHUNKING_MAX_TOKENS`
- `AZURE_CHUNKING_OVERLAP_PERCENT` → use `CHUNKING_OVERLAP_PERCENT`
- `AZURE_CHUNKING_CROSS_PAGE_OVERLAP` → use `CHUNKING_CROSS_PAGE_OVERLAP`
- `AZURE_CHUNKING_DISABLE_CHAR_LIMIT` → use `CHUNKING_DISABLE_CHAR_LIMIT`
- `AZURE_CHUNKING_TABLE_LEGEND_BUFFER` → use `CHUNKING_TABLE_LEGEND_BUFFER`
- `AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS` → use `CHUNKING_ABSOLUTE_MAX_TOKENS`

**Example:**
```bash
CHUNKING_MAX_CHARS=1000
CHUNKING_MAX_TOKENS=500
CHUNKING_OVERLAP_PERCENT=10
CHUNKING_CROSS_PAGE_OVERLAP=false
CHUNKING_DISABLE_CHAR_LIMIT=false
CHUNKING_TABLE_LEGEND_BUFFER=100
CHUNKING_ABSOLUTE_MAX_TOKENS=8000
```

---

## Performance Tuning

**Purpose:** Control concurrency and batch sizes

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAX_WORKERS` | No | `4` | Parallel file processing workers |
| `INNER_ANALYZE_WORKERS` | No | `1` | Document Intelligence concurrent workers |
| `UPLOAD_DELAY` | No | `0.5` | Delay between uploads (seconds) |
| `EMBEDDING_BATCH_SIZE` | No | `128` | Embeddings batch size |
| `UPLOAD_BATCH_SIZE` | No | `1000` | Search upload batch size |
| `MAX_IMAGE_CONCURRENCY` | No | `8` | Parallel image descriptions/uploads |
| `MAX_FIGURE_CONCURRENCY` | No | `5` | Parallel figure extractions |
| `MAX_BATCH_UPLOAD_CONCURRENCY` | No | `5` | Parallel search batch uploads |

**Deprecated Names (still supported, will be removed in v2.0):**
- `AZURE_MAX_WORKERS` → use `MAX_WORKERS`
- `AZURE_INNER_ANALYZE_WORKERS` → use `INNER_ANALYZE_WORKERS`
- `AZURE_UPLOAD_DELAY` → use `UPLOAD_DELAY`
- `AZURE_EMBED_BATCH_SIZE` → use `EMBEDDING_BATCH_SIZE`
- `AZURE_UPLOAD_BATCH_SIZE` → use `UPLOAD_BATCH_SIZE`
- `AZURE_MAX_IMAGE_CONCURRENCY` → use `MAX_IMAGE_CONCURRENCY`
- `AZURE_MAX_FIGURE_CONCURRENCY` → use `MAX_FIGURE_CONCURRENCY`
- `AZURE_MAX_BATCH_UPLOAD_CONCURRENCY` → use `MAX_BATCH_UPLOAD_CONCURRENCY`

**Example:**
```bash
MAX_WORKERS=4
INNER_ANALYZE_WORKERS=1
UPLOAD_DELAY=0.5
EMBEDDING_BATCH_SIZE=128
UPLOAD_BATCH_SIZE=1000
MAX_IMAGE_CONCURRENCY=8
MAX_FIGURE_CONCURRENCY=5
MAX_BATCH_UPLOAD_CONCURRENCY=5
```

---

## Azure Content Understanding

**Purpose:** Alternative to GPT-4o for image descriptions (optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_CONTENT_UNDERSTANDING_ENDPOINT` | No | - | Content Understanding endpoint URL |
| `AZURE_CONTENT_UNDERSTANDING_TENANT_ID` | No | - | Content Understanding tenant ID |

**Usage:** Set `MEDIA_DESCRIBER_MODE=content_understanding` to use this service.

---

## Complete Example Configuration

```bash
# Azure Service Principal (optional)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Key Vault (optional)
KEY_VAULT_URI=https://your-keyvault.vault.azure.net/

# Document Intelligence
AZURE_DOC_INT_ENDPOINT=https://your-di-service.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key
AZURE_DI_MAX_CONCURRENCY=3

# Azure AI Search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name

# Azure OpenAI - Embeddings
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_OPENAI_MAX_RETRIES=3

# Azure OpenAI - Vision (optional, for media description)
AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_VISION_MODEL=gpt-4o-mini
AZURE_OPENAI_VISION_DETAIL=low

# Azure OpenAI - Chat (optional, for table summaries)
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_MODEL_NAME=gpt-4o

# Input (Local Mode)
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf

# Artifacts (Local Mode)
ARTIFACTS_MODE=local
LOCAL_ARTIFACTS_DIR=./artifacts

# Processing Options
MEDIA_DESCRIBER_MODE=disabled  # Options: disabled, gpt4o, content_understanding
TABLE_RENDER_FORMAT=markdown   # Options: markdown, html, plain
TABLE_SUMMARIES_ENABLED=false
GENERATE_PAGE_PDFS=false
DOCUMENT_ACTION=add

# Chunking
CHUNKING_MAX_TOKENS=750
CHUNKING_MAX_CHARS=1000
CHUNKING_OVERLAP_PERCENT=20
CHUNKING_CROSS_PAGE_OVERLAP=true
CHUNKING_DISABLE_CHAR_LIMIT=true

# Performance
MAX_WORKERS=4
EMBEDDING_BATCH_SIZE=128
UPLOAD_BATCH_SIZE=1000
MAX_IMAGE_CONCURRENCY=8
```

---

## Troubleshooting

### Common Issues

**❌ Error: `AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE is required`**
- **Fix:** Set `AZURE_SEARCH_SERVICE` or `AZURE_SEARCH_ENDPOINT` when using Azure AI Search

**❌ Error: `AZURE_DOC_INT_ENDPOINT is required`**
- **Fix:** Set `AZURE_DOC_INT_ENDPOINT` when using Azure Document Intelligence extraction

**❌ Error: `AZURE_OPENAI_ENDPOINT is required`**
- **Fix:** Set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` when using Azure OpenAI embeddings

**❌ Error: `LOCAL_INPUT_GLOB is required when INPUT_MODE=local`**
- **Fix:** Set `LOCAL_INPUT_GLOB` (e.g., `./data/*.pdf`) when INPUT_MODE=local

**❌ Error: `Vision deployment not configured`**
- **Fix:** Set `AZURE_OPENAI_VISION_DEPLOYMENT` when MEDIA_DESCRIBER_MODE=gpt4o, or set MEDIA_DESCRIBER_MODE=disabled

**❌ Error: Rate limit exceeded**
- **Fix:** Reduce `AZURE_DI_MAX_CONCURRENCY`, `AZURE_OPENAI_MAX_CONCURRENCY`, and batch sizes

---

## Related Documentation

- **[Quick Start Guide](../guides/QUICKSTART.md)** - Get started in 5 minutes
- **[Configuration Guide](../guides/CONFIGURATION.md)** - Complete configuration reference
- **[Configuration Matrix](01_CONFIGURATION_MATRIX.md)** - All input/output scenarios
