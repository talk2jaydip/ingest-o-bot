# Configuration Matrix: All Input/Output Combinations

Complete guide showing every possible combination of where to read files FROM (input) and where to store artifacts TO (output).

---

## Quick Reference Table

| Scenario | Read From | Store To | Auto-Detect? | Override Needed? |
|----------|-----------|----------|--------------|------------------|
| 1 | Local files | Local disk | ✅ Yes | ❌ No |
| 2 | Blob storage | Blob storage | ✅ Yes | ❌ No |
| 3 | Local files | Blob storage | ❌ No | ✅ Yes (override) |
| 4 | Blob storage | Local disk | ❌ No | ✅ Yes (override) |

---

## Scenario 1: Local Input → Local Artifacts (DEFAULT)

**Use case**: Local development, debugging, no Azure Blob Storage needed

### What happens:
- ✅ Reads files from local filesystem
- ✅ Stores all artifacts (pages, chunks, images) to local disk
- ✅ No blob storage required
- ✅ Auto-detected (no override needed)

### Required environment variables:

```bash
# ==========================================
# Input: Local Files (NEW NAMES)
# ==========================================
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf
# Examples:
# - Single file: LOCAL_INPUT_GLOB=samples/sample.pdf
# - All PDFs: LOCAL_INPUT_GLOB=./documents/*.pdf
# - All files: LOCAL_INPUT_GLOB=./documents/**/*
# - Multiple types: LOCAL_INPUT_GLOB=./documents/**/*.{pdf,txt,md}

# ==========================================
# Artifacts: Auto-detected as LOCAL
# ==========================================
# No configuration needed! Automatically uses local storage.
# Optional: Customize local directory
LOCAL_ARTIFACTS_DIR=./artifacts

# Deprecated names (still supported, will be removed in v2.0):
# INPUT_MODE formerly: AZURE_INPUT_MODE
# LOCAL_INPUT_GLOB formerly: AZURE_LOCAL_GLOB
# LOCAL_ARTIFACTS_DIR formerly: AZURE_ARTIFACTS_DIR

# ==========================================
# Azure Services (still required)
# ==========================================
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=...
AZURE_SEARCH_SERVICE=...
AZURE_SEARCH_KEY=...
AZURE_SEARCH_INDEX=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...
```

### What you DON'T need:
- ❌ `AZURE_STORAGE_ACCOUNT` (not used)
- ❌ `AZURE_STORAGE_ACCOUNT_KEY` (not used)
- ❌ `AZURE_BLOB_CONTAINER_IN` (not used)
- ❌ `AZURE_BLOB_CONTAINER_PREFIX` (not used)
- ❌ `AZURE_BLOB_CONTAINER_OUT_*` (not used)

### Output structure:
```
./artifacts/
├── document1/
│   ├── page-0001.json
│   ├── page-0002.json
│   ├── page-0001/
│   │   ├── chunk-000001.json
│   │   └── chunk-000002.json
│   ├── page_01_fig_01.png
│   └── manifest.json
└── status/
    └── pipeline_status_20260113_120000.json
```

---

## Scenario 2: Blob Input → Blob Artifacts (PRODUCTION)

**Use case**: Production deployment, all processing in Azure

### What happens:
- ✅ Reads files from Azure Blob Storage INPUT container
- ✅ Stores all artifacts to Azure Blob Storage OUTPUT containers
- ✅ Auto-detected (no override needed)
- ✅ OUTPUT containers auto-created
- ⚠️ INPUT container must be pre-created by you

### Required environment variables:

```bash
# ==========================================
# Input: Blob Storage (NEW NAMES)
# ==========================================
INPUT_MODE=blob

# Storage account
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key-here
# Or use connection string:
# AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# INPUT container (MUST PRE-EXIST!)
AZURE_BLOB_CONTAINER_IN=my-improvement-index

# Optional: Filter to subfolder
# AZURE_BLOB_PREFIX=documents/2024/

# ==========================================
# Artifacts: Auto-detected as BLOB
# ==========================================
# No override needed! Automatically uses blob storage.

# OUTPUT containers (auto-created by pipeline)
BLOB_CONTAINER_PREFIX=my-prod
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images

# Optional: Per-page PDFs for citations
AZURE_BLOB_CONTAINER_CITATIONS=citations
GENERATE_PAGE_PDFS=true

# Deprecated names (still supported, will be removed in v2.0):
# INPUT_MODE formerly: AZURE_INPUT_MODE
# BLOB_CONTAINER_PREFIX formerly: AZURE_BLOB_CONTAINER_PREFIX
# GENERATE_PAGE_PDFS formerly: AZURE_GENERATE_PAGE_PDFS

# ==========================================
# Azure Services
# ==========================================
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=...
AZURE_SEARCH_SERVICE=...
AZURE_SEARCH_KEY=...
AZURE_SEARCH_INDEX=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...
```

### What you DON'T need:
- ❌ `AZURE_ARTIFACTS_MODE` (auto-detected as blob)
- ❌ `AZURE_ARTIFACTS_DIR` (not used in blob mode)
- ❌ `AZURE_STORE_ARTIFACTS_TO_BLOB` (not needed, already blob input)

### Output structure (in Azure Blob Storage):

**Container: `my-prod-pages`**
```
document1/
├── page-0001.json
└── page-0002.json
```

**Container: `my-prod-chunks`**
```
document1/
├── page-0001/
│   ├── chunk-000001.json
│   └── chunk-000002.json
└── page-0002/
    └── chunk-000001.json
```

**Container: `my-prod-images`**
```
document1/
├── page_01_fig_01.png
└── page_02_fig_01.png
```

**Container: `my-prod-citations`** (if enabled)
```
document1/
├── page-0001.pdf
└── page-0002.pdf
```

### Before running:
```bash
# Create INPUT container and upload files
az storage container create \
  --name my-improvement-index \
  --account-name mystorageaccount

az storage blob upload-batch \
  --destination my-improvement-index \
  --source ./local-docs/ \
  --account-name mystorageaccount
```

---

## Scenario 3: Local Input → Blob Artifacts (HYBRID/TEST)

**Use case**: Testing locally but want artifacts in blob for review/sharing

### What happens:
- ✅ Reads files from local filesystem
- ✅ Stores artifacts to Azure Blob Storage
- ⚠️ **Requires override** - not auto-detected!
- ✅ OUTPUT containers auto-created

### Required environment variables:

```bash
# ==========================================
# Input: Local Files (NEW NAMES)
# ==========================================
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf

# ==========================================
# Artifacts: OVERRIDE to use blob (NEW NAMES)
# ==========================================
# Option A: Use override flag (RECOMMENDED)
STORE_ARTIFACTS_TO_BLOB=true

# Option B: Explicit mode
# ARTIFACTS_MODE=blob

# Storage account (required for blob artifacts)
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key-here

# OUTPUT containers (auto-created)
BLOB_CONTAINER_PREFIX=my-test
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images

# Optional: Per-page PDFs
AZURE_BLOB_CONTAINER_CITATIONS=citations
GENERATE_PAGE_PDFS=true

# Deprecated names (still supported, will be removed in v2.0):
# INPUT_MODE formerly: AZURE_INPUT_MODE
# LOCAL_INPUT_GLOB formerly: AZURE_LOCAL_GLOB
# STORE_ARTIFACTS_TO_BLOB formerly: AZURE_STORE_ARTIFACTS_TO_BLOB
# ARTIFACTS_MODE formerly: AZURE_ARTIFACTS_MODE
# BLOB_CONTAINER_PREFIX formerly: AZURE_BLOB_CONTAINER_PREFIX
# GENERATE_PAGE_PDFS formerly: AZURE_GENERATE_PAGE_PDFS

# ==========================================
# Azure Services
# ==========================================
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=...
AZURE_SEARCH_SERVICE=...
AZURE_SEARCH_KEY=...
AZURE_SEARCH_INDEX=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...
```

### What you DON'T need:
- ❌ `AZURE_BLOB_CONTAINER_IN` (not reading from blob)
- ❌ `AZURE_ARTIFACTS_DIR` (not using local storage)

### Why use this?
- ✅ Test with local files (easier to manage)
- ✅ Artifacts stored in blob for team review
- ✅ Closer to production environment
- ✅ Can inspect artifacts via Azure Portal/Storage Explorer

---

## Scenario 4: Blob Input → Local Artifacts (DEBUGGING)

**Use case**: Processing production blobs but want artifacts locally for debugging

### What happens:
- ✅ Reads files from Azure Blob Storage
- ✅ Stores artifacts to local disk
- ⚠️ **Requires override** - not auto-detected!
- ⚠️ INPUT container must be pre-created

### Required environment variables:

```bash
# ==========================================
# Input: Blob Storage (NEW NAMES)
# ==========================================
INPUT_MODE=blob

# Storage account
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-key-here

# INPUT container (MUST PRE-EXIST!)
AZURE_BLOB_CONTAINER_IN=my-improvement-index

# Optional: Filter
# AZURE_BLOB_PREFIX=documents/

# ==========================================
# Artifacts: OVERRIDE to use local (NEW NAMES)
# ==========================================
ARTIFACTS_MODE=local
LOCAL_ARTIFACTS_DIR=./debug_artifacts

# Deprecated names (still supported, will be removed in v2.0):
# INPUT_MODE formerly: AZURE_INPUT_MODE
# ARTIFACTS_MODE formerly: AZURE_ARTIFACTS_MODE
# LOCAL_ARTIFACTS_DIR formerly: AZURE_ARTIFACTS_DIR

# ==========================================
# Azure Services
# ==========================================
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=...
AZURE_SEARCH_SERVICE=...
AZURE_SEARCH_KEY=...
AZURE_SEARCH_INDEX=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...
```

### What you DON'T need:
- ❌ `AZURE_BLOB_CONTAINER_PREFIX` (not using blob output)
- ❌ `AZURE_BLOB_CONTAINER_OUT_*` (not using blob output)
- ❌ `AZURE_STORE_ARTIFACTS_TO_BLOB` (not needed)

### Why use this?
- ✅ Debug production files locally
- ✅ Faster artifact inspection (no Azure Portal needed)
- ✅ Easier to grep/search through JSON files
- ✅ Lower blob storage costs

### Before running:
```bash
# INPUT container must exist with files
az storage container list \
  --account-name mystorageaccount \
  --query "[?name=='my-improvement-index']"
```

---

## Configuration Priority Logic

The system determines artifacts storage mode in this order:

```
1. EXPLICIT MODE
   If AZURE_ARTIFACTS_MODE is set → use that (blob or local)

2. OVERRIDE FLAG
   Else if AZURE_STORE_ARTIFACTS_TO_BLOB=true → use blob

3. AUTO-DETECT
   Else if AZURE_INPUT_MODE=blob → use blob (follow input)
   Else if AZURE_INPUT_MODE=local → use local (follow input)

4. DEFAULT
   Else → use local
```

---

## Complete Examples

### Example 1: Local Development (Minimal Config)

```bash
# .env
INPUT_MODE=local
LOCAL_INPUT_GLOB=samples/*.pdf

# That's it for storage! Artifacts auto-stored locally.

# Required services
AZURE_DOC_INT_ENDPOINT=https://mydocint.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=xxx
AZURE_SEARCH_SERVICE=mysearchservice
AZURE_SEARCH_KEY=xxx
AZURE_SEARCH_INDEX=my-dev-index
AZURE_OPENAI_ENDPOINT=https://myopenai.openai.azure.com/
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Example 2: Production (Full Blob)

```bash
# .env
INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=xxx

# INPUT (pre-created)
AZURE_BLOB_CONTAINER_IN=my-improvement-index

# OUTPUT (auto-created)
BLOB_CONTAINER_PREFIX=my-prod
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images

# Services
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=xxx
AZURE_SEARCH_SERVICE=mysearchservice
AZURE_SEARCH_KEY=xxx
AZURE_SEARCH_INDEX=my-prod-index
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Example 3: Hybrid Testing (Local Input, Blob Artifacts)

```bash
# .env
INPUT_MODE=local
LOCAL_INPUT_GLOB=./test-data/*.pdf

# Override to force blob storage
STORE_ARTIFACTS_TO_BLOB=true

# Storage (for artifacts)
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=xxx

# OUTPUT (auto-created)
BLOB_CONTAINER_PREFIX=my-test
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images

# Services
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=xxx
AZURE_SEARCH_SERVICE=mysearchservice
AZURE_SEARCH_KEY=xxx
AZURE_SEARCH_INDEX=my-test-index
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Example 4: Debugging Production (Blob Input, Local Artifacts)

```bash
# .env
INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=xxx

# INPUT (pre-created)
AZURE_BLOB_CONTAINER_IN=my-improvement-index

# Override to force local storage
ARTIFACTS_MODE=local
LOCAL_ARTIFACTS_DIR=./debug_artifacts

# Services
AZURE_DOC_INT_ENDPOINT=https://...
AZURE_DOC_INT_KEY=xxx
AZURE_SEARCH_SERVICE=mysearchservice
AZURE_SEARCH_KEY=xxx
AZURE_SEARCH_INDEX=my-prod-index
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

---

## Environment Variable Quick Reference

### Input Configuration (NEW NAMES)

| Variable | Required When | Purpose | Example | Deprecated |
|----------|---------------|---------|---------|-----------|
| `INPUT_MODE` | Always | Where to read files from | `local` or `blob` | `AZURE_INPUT_MODE` |
| `LOCAL_INPUT_GLOB` | Input=local | File pattern to match | `./data/*.pdf` | `AZURE_LOCAL_GLOB` |
| `AZURE_BLOB_CONTAINER_IN` | Input=blob | INPUT container name | `my-improvement-index` | - |
| `AZURE_BLOB_PREFIX` | Input=blob (optional) | Subfolder filter | `documents/2024/` | - |

### Storage Account (for Blob Operations)

| Variable | Required When | Purpose |
|----------|---------------|---------|
| `AZURE_STORAGE_ACCOUNT` | Any blob operation | Storage account name |
| `AZURE_STORAGE_ACCOUNT_KEY` | Any blob operation | Storage account key |
| `AZURE_CONNECTION_STRING` | Any blob operation | Alternative to account+key |

### Artifacts Configuration (NEW NAMES)

| Variable | Required When | Purpose | Example | Deprecated |
|----------|---------------|---------|---------|-----------|
| `ARTIFACTS_MODE` | Override needed | Explicit mode | `local` or `blob` | `AZURE_ARTIFACTS_MODE` |
| `STORE_ARTIFACTS_TO_BLOB` | Local→Blob override | Force blob artifacts | `true` | `AZURE_STORE_ARTIFACTS_TO_BLOB` |
| `LOCAL_ARTIFACTS_DIR` | Artifacts=local | Local directory path | `./artifacts` | `AZURE_ARTIFACTS_DIR` |
| `BLOB_CONTAINER_PREFIX` | Artifacts=blob | Container prefix | `my-prod` | `AZURE_BLOB_CONTAINER_PREFIX` |
| `AZURE_BLOB_CONTAINER_OUT_PAGES` | Artifacts=blob | Pages container suffix | `pages` | - |
| `AZURE_BLOB_CONTAINER_OUT_CHUNKS` | Artifacts=blob | Chunks container suffix | `chunks` | - |
| `AZURE_BLOB_CONTAINER_OUT_IMAGES` | Artifacts=blob | Images container suffix | `images` | - |
| `AZURE_BLOB_CONTAINER_CITATIONS` | Artifacts=blob (optional) | Citations container suffix | `citations` | - |

---

## Decision Tree

```
START: Where are your files?
│
├─ FILES ON LOCAL DISK
│  │
│  └─ Where do you want artifacts?
│     │
│     ├─ LOCAL DISK (default)
│     │  → Scenario 1: Local→Local
│     │  Set: AZURE_INPUT_MODE=local, AZURE_LOCAL_GLOB=...
│     │
│     └─ BLOB STORAGE
│        → Scenario 3: Local→Blob
│        Set: AZURE_INPUT_MODE=local, AZURE_LOCAL_GLOB=...
│        Set: AZURE_STORE_ARTIFACTS_TO_BLOB=true
│        Set: AZURE_STORAGE_ACCOUNT=..., AZURE_BLOB_CONTAINER_PREFIX=...
│
└─ FILES IN BLOB STORAGE
   │
   └─ Where do you want artifacts?
      │
      ├─ BLOB STORAGE (default)
      │  → Scenario 2: Blob→Blob
      │  Set: AZURE_INPUT_MODE=blob, AZURE_BLOB_CONTAINER_IN=...
      │  Set: AZURE_STORAGE_ACCOUNT=..., AZURE_BLOB_CONTAINER_PREFIX=...
      │
      └─ LOCAL DISK
         → Scenario 4: Blob→Local
         Set: AZURE_INPUT_MODE=blob, AZURE_BLOB_CONTAINER_IN=...
         Set: AZURE_ARTIFACTS_MODE=local, AZURE_ARTIFACTS_DIR=...
```

---

## Common Mistakes

### ❌ Mistake 1: Forgetting to create INPUT container

```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-docs  # Container doesn't exist!
```

**Error**: `ResourceNotFoundError: The specified container does not exist`

**Fix**: Create container first:
```bash
az storage container create --name my-docs --account-name ...
```

### ❌ Mistake 2: Expecting INPUT container to be auto-created

Only OUTPUT containers are auto-created. INPUT containers must exist.

### ❌ Mistake 3: Missing storage account when using blob artifacts

```bash
AZURE_INPUT_MODE=local
AZURE_STORE_ARTIFACTS_TO_BLOB=true
# Missing: AZURE_STORAGE_ACCOUNT, AZURE_BLOB_CONTAINER_PREFIX!
```

**Fix**: Add storage configuration

### ❌ Mistake 4: Confusing INPUT and OUTPUT containers

- **INPUT** (`AZURE_BLOB_CONTAINER_IN`): You create, you manage
- **OUTPUT** (`AZURE_BLOB_CONTAINER_PREFIX` + suffix): Pipeline creates

---

## Related Documentation

- [Configuration Guide](../guides/CONFIGURATION.md) - Complete configuration reference
- [INPUT Container Lifecycle Guide](INPUT_CONTAINER_GUIDE.md) - INPUT vs OUTPUT explained
- [Environment Variables Reference](07_ENVIRONMENT_VARIABLES.md) - All variables documented
- [Blob Container Naming](BLOB_CONTAINER_NAMING.md) - Container naming conventions
