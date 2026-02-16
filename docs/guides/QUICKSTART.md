# Quick Start Guide

Get up and running with `ingestor` in 5 minutes.

> **📖 Need detailed setup instructions?** See [SETUP_GUIDE.md](../../SETUP_GUIDE.md) for complete step-by-step guide including Azure resource setup, container creation, and troubleshooting.

---

## Step 1: Choose Your Scenario

| Scenario | When to Use | Config File to Copy |
|----------|-------------|---------------------|
| **Local Dev** | Development, no blob storage | `envs/env.scenario1-local-dev.example` |
| **Production** | Blob input & output | `envs/env.scenario2-blob-prod.example` |
| **Debugging** | Blob input, local artifacts | `envs/env.scenario4-blob-to-local.example` |

---

## Step 2: Set Up Your Environment

### Option A: Local Development (Easiest)

```bash
# 1. Copy example environment
cp envs/env.example .env

# 2. Edit .env with your Azure credentials
# Set AZURE_SEARCH_SERVICE, AZURE_OPENAI_ENDPOINT, etc.

# 3. Configure for local input
# Set INPUT_MODE=local
# Set LOCAL_INPUT_GLOB=./samples/*.pdf

# 4. Add your files to test with
mkdir -p samples
# Copy your PDF files to samples/ directory

# 5. Run the pipeline
python -m ingestor.cli
```

**What happens:**
- ✅ Reads PDFs from `samples/` folder
- ✅ Stores artifacts to `./test_artifacts/` locally
- ✅ Uploads to Azure AI Search index
- ✅ No blob storage required

---

### Option B: Production Deployment (Blob Storage)

```bash
# 1. Copy production example
cp envs/env.scenario2-blob-prod.example .env

# 2. Edit .env with your Azure credentials
# Set AZURE_STORAGE_ACCOUNT, AZURE_SEARCH_SERVICE, etc.

# 3. Configure container names (SIMPLE APPROACH - RECOMMENDED)
# Set AZURE_STORAGE_CONTAINER=my-documents
# This auto-generates:
#   - my-documents-input  (INPUT - you must create this)
#   - my-documents-pages   (OUTPUT - auto-created)
#   - my-documents-chunks  (OUTPUT - auto-created)
#   - my-documents-images  (OUTPUT - auto-created)
#   - my-documents-citations (OUTPUT - auto-created)

# 4. Create INPUT container in Azure Storage (REQUIRED)
az storage container create \
  --name my-documents-input \
  --account-name YOUR_STORAGE_ACCOUNT \
  --auth-mode key

# 5. Upload your files to the INPUT container
az storage blob upload-batch \
  --destination my-documents-input \
  --source ./your-documents/ \
  --account-name YOUR_STORAGE_ACCOUNT

# 6. Run the pipeline
python -m ingestor.cli --setup-index  # Create index first
python -m ingestor.cli                 # Process documents
```

**What happens:**
- ✅ Reads files from Azure Blob Storage INPUT container
- ✅ Stores artifacts to blob OUTPUT containers (auto-created)
- ✅ Uploads chunks to Azure AI Search index
- ✅ Full production setup

**Alternative: Explicit Container Names**
```bash
# Instead of AZURE_STORAGE_CONTAINER, use:
AZURE_BLOB_CONTAINER_IN=custom-input-name
AZURE_BLOB_CONTAINER_PREFIX=custom-prefix
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

---

## Step 3: Verify Your Configuration

Before running, check that these are configured:

```bash
# Required Azure services
AZURE_DOC_INT_ENDPOINT=https://...           # Document Intelligence
AZURE_SEARCH_SERVICE=...                     # AI Search
AZURE_SEARCH_INDEX=...                       # Index name
AZURE_OPENAI_ENDPOINT=https://...            # OpenAI
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...        # Embedding model
```

---

## Step 4: Run the Pipeline

### Basic Commands

```bash
# Index documents (default)
python -m ingestor.cli

# Check if index exists
python -m ingestor.cli --check-index

# Remove specific documents
python -m ingestor.cli --action remove --glob "document.pdf"

# Remove all documents from index
python -m ingestor.cli --action removeall
```

### Advanced Operations

```bash
# Clean artifacts for specific files while removing
python -m ingestor.cli --action remove --glob "doc.pdf" --clean-artifacts

# Delete all artifacts from blob storage
python -m ingestor.cli --clean-all-artifacts

# Use different environment file
cp envs/env.production .env
python -m ingestor.cli
```

---

## Configuration Scenarios Cheat Sheet

### Scenario 1: Local → Local (Development)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf
LOCAL_ARTIFACTS_DIR=./artifacts
```

### Scenario 2: Blob → Blob (Production) - Simple
```bash
INPUT_MODE=blob
AZURE_STORAGE_CONTAINER=my-documents
# Auto-generates: my-documents-input, my-documents-pages, etc.
# Remember to create my-documents-input container!
```

### Scenario 2: Blob → Blob (Production) - Explicit
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-docs-input
AZURE_BLOB_CONTAINER_PREFIX=my-prod
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

### Scenario 3: Local → Blob (Testing)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf
STORE_ARTIFACTS_TO_BLOB=true
AZURE_STORAGE_CONTAINER=test-docs
```

### Scenario 4: Blob → Local (Debugging)
```bash
INPUT_MODE=blob
AZURE_STORAGE_CONTAINER=my-documents
LOCAL_ARTIFACTS_DIR=./debug_artifacts  # Force local storage
```

### Scenario 3: Local → Blob (Hybrid Test)
```bash
INPUT_MODE=local
LOCAL_INPUT_GLOB=./data/*.pdf
STORE_ARTIFACTS_TO_BLOB=true
AZURE_BLOB_CONTAINER_PREFIX=my-test
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
```

### Scenario 4: Blob → Local (Debug)
```bash
INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-docs
ARTIFACTS_MODE=local
LOCAL_ARTIFACTS_DIR=./debug_artifacts
```

**See [Configuration Matrix](../reference/01_CONFIGURATION_MATRIX.md) for complete details.**

---

## Common Issues

### ❌ "No files found to process"

**Cause:** INPUT container is empty or glob pattern doesn't match files

**Fix:**
```bash
# For local mode - check files exist
ls ./data/*.pdf

# For blob mode - check container exists and has files
az storage blob list \
  --container-name myproject \
  --account-name YOUR_STORAGE_ACCOUNT
```

---

### ❌ "Container does not exist"

**Cause:** INPUT container not created in Azure Storage

**Fix:**
```bash
# Create the container first
az storage container create \
  --name myproject \
  --account-name YOUR_STORAGE_ACCOUNT

# Upload files
az storage blob upload-batch \
  --destination myproject \
  --source ./docs/
```

**Important:** Only INPUT containers need to be pre-created. OUTPUT containers (for artifacts) are auto-created by the pipeline.

---

### ❌ "Index does not exist"

**Cause:** Search index not deployed yet

**Fix:**
```bash
# Check index status
python -m ingestor.cli --check-index

# Deploy index using index.py
python index.py --mode deploy --force
```

---

## File Organization

```
ingestor/
├── .env                    # Your active configuration
├── envs/
│   ├── env.test           # Template for local development
│   └── env.production     # Template for production
├── samples/               # Sample files for testing
│   └── sample_pages_test.pdf
├── data/                  # Your local documents (create if needed)
├── artifacts/             # Local artifacts (auto-created)
└── docs/                  # Documentation
    ├── INDEX.md           # Documentation index
    ├── guides/            # User guides
    └── reference/         # Technical reference
```

---

## Environment File Selection

The pipeline uses `.env` in the root directory:

```bash
# Copy example and customize
cp envs/env.example .env

# Edit .env with your Azure credentials and configuration
```

---

## Next Steps

Once you have the pipeline running:

1. **Customize chunking** - See [Configuration Guide](CONFIGURATION.md)
2. **Add media descriptions** - Enable GPT-4o figure descriptions
3. **Enable citations** - Generate per-page PDFs for direct citations
4. **Scale up** - Adjust concurrency and batch sizes

---

## Complete Documentation

- **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
- **[Configuration Matrix](../reference/01_CONFIGURATION_MATRIX.md)** - All input/output combinations with exact env vars
- **[Input Sources](../reference/02_INPUT_SOURCES.md)** - Understanding INPUT vs OUTPUT containers
- **[Environment Variables](../reference/12_ENVIRONMENT_VARIABLES.md)** - Complete reference

---

## Getting Help

```bash
# Check configuration
python -m ingestor.cli --help

# Verify index exists
python -m ingestor.cli --check-index

# Test with sample file first
INPUT_MODE=local \
LOCAL_INPUT_GLOB=samples/sample_pages_test.pdf \
python -m ingestor.cli
```

---

## Pre-Flight Checklist

Before running the pipeline, verify:

### Required Environment Variables
- [ ] `AZURE_SEARCH_SERVICE` - Search service name
- [ ] `AZURE_SEARCH_KEY` - Search service API key
- [ ] `AZURE_SEARCH_INDEX` - Index name
- [ ] `AZURE_DOC_INT_ENDPOINT` - Document Intelligence endpoint
- [ ] `AZURE_OPENAI_ENDPOINT` - OpenAI endpoint
- [ ] `AZURE_OPENAI_KEY` - OpenAI API key
- [ ] `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Embedding deployment name

### For Blob Mode (Additional)
- [ ] `AZURE_STORAGE_ACCOUNT` - Storage account name
- [ ] `AZURE_STORAGE_ACCOUNT_KEY` or `AZURE_CONNECTION_STRING` - Storage credentials
- [ ] `AZURE_STORAGE_CONTAINER` (simple) OR `AZURE_BLOB_CONTAINER_IN` (explicit)
- [ ] INPUT container created in Azure Storage
- [ ] Files uploaded to INPUT container

### For Local Mode (Additional)
- [ ] `INPUT_MODE=local`
- [ ] `LOCAL_INPUT_GLOB` - Path pattern to files
- [ ] Files exist at the specified glob pattern

**Quick validation:**
```bash
# Use the web UI to validate
ingestor-ui
# Navigate to "Environment Variables" tab → Click "Validate"

# Or check from CLI
python -m ingestor.cli --check-index
```

---

## Summary: 3 Steps to Success

1. **Setup Azure resources** (see [SETUP_GUIDE.md](../../SETUP_GUIDE.md) for details)
2. **Configure .env** with credentials and container names
3. **Create INPUT container** (if using blob mode) and upload files
4. **Run pipeline**: `python -m ingestor.cli --setup-index && python -m ingestor.cli`

That's it! The pipeline will:
- ✅ Extract text and tables from documents
- ✅ Generate embeddings
- ✅ Upload to Azure AI Search
- ✅ Store artifacts (pages, chunks, images)
- ✅ Provide detailed logging

---

## Need More Help?

- **Complete setup guide**: [SETUP_GUIDE.md](../../SETUP_GUIDE.md) - Step-by-step from scratch
- **Configuration guide**: [CONFIGURATION.md](CONFIGURATION.md) - All configuration options
- **Environment guide**: [ENVIRONMENT_AND_SECRETS.md](ENVIRONMENT_AND_SECRETS.md) - Managing multiple environments
- **Troubleshooting**: See [SETUP_GUIDE.md](../../SETUP_GUIDE.md#verification--troubleshooting)

Happy indexing! 🚀
