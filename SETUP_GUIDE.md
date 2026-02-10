# Complete Setup Guide

> Step-by-step guide to set up and run the ingestor pipeline from scratch

This guide walks you through everything: Azure resource setup, container configuration, environment setup, and running the pipeline.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Resources Setup](#azure-resources-setup)
3. [Container Configuration](#container-configuration)
4. [Environment Configuration](#environment-configuration)
5. [Running the Pipeline](#running-the-pipeline)
6. [Verification & Troubleshooting](#verification--troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.10+**
- **Git** (for cloning repository)
- **Azure CLI** (optional, for container management)

### Azure Resources Required
- Azure AI Search service
- Azure Document Intelligence service
- Azure OpenAI service
- Azure Storage Account (for blob mode)

---

## Azure Resources Setup

### 1. Azure AI Search

**Create service:**
```bash
az search service create \
  --name your-search-service \
  --resource-group your-rg \
  --sku standard \
  --location eastus
```

**Get credentials:**
```bash
# Get admin key
az search admin-key show \
  --service-name your-search-service \
  --resource-group your-rg
```

**Configure in .env:**
```bash
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=<admin-key-from-above>
AZURE_SEARCH_INDEX=my-documents-index  # Choose your index name
```

---

### 2. Azure Document Intelligence

**Create service:**
```bash
az cognitiveservices account create \
  --name your-di-service \
  --resource-group your-rg \
  --kind FormRecognizer \
  --sku S0 \
  --location eastus
```

**Get credentials:**
```bash
# Get endpoint
az cognitiveservices account show \
  --name your-di-service \
  --resource-group your-rg \
  --query "properties.endpoint" -o tsv

# Get key
az cognitiveservices account keys list \
  --name your-di-service \
  --resource-group your-rg \
  --query "key1" -o tsv
```

**Configure in .env:**
```bash
AZURE_DOC_INT_ENDPOINT=https://your-di-service.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=<key-from-above>
```

---

### 3. Azure OpenAI

**Create service and deploy models:**
```bash
# Create OpenAI service
az cognitiveservices account create \
  --name your-openai-service \
  --resource-group your-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy embedding model
az cognitiveservices account deployment create \
  --name your-openai-service \
  --resource-group your-rg \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 120 \
  --sku-name Standard
```

**Get credentials:**
```bash
# Get endpoint
az cognitiveservices account show \
  --name your-openai-service \
  --resource-group your-rg \
  --query "properties.endpoint" -o tsv

# Get key
az cognitiveservices account keys list \
  --name your-openai-service \
  --resource-group your-rg \
  --query "key1" -o tsv
```

**Configure in .env:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=<key-from-above>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
```

---

### 4. Azure Storage Account (for blob mode)

**Create storage account:**
```bash
az storage account create \
  --name yourstorageaccount \
  --resource-group your-rg \
  --location eastus \
  --sku Standard_LRS
```

**Get credentials:**
```bash
# Get connection string
az storage account show-connection-string \
  --name yourstorageaccount \
  --resource-group your-rg \
  --query "connectionString" -o tsv

# Get account key
az storage account keys list \
  --account-name yourstorageaccount \
  --resource-group your-rg \
  --query "[0].value" -o tsv
```

**Configure in .env:**
```bash
AZURE_STORAGE_ACCOUNT=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=<key-from-above>
AZURE_CONNECTION_STRING=<connection-string-from-above>
```

---

## Container Configuration

### Understanding Container Naming

The ingestor supports **two approaches** for container configuration:

#### **Approach 1: Simple (RECOMMENDED)** - Use Base Container Name

Set one variable, auto-generates all container names:

```bash
AZURE_STORAGE_CONTAINER=my-documents
```

**Auto-generates:**
- Input: `my-documents-input` (you must create this)
- Output: `my-documents-pages` (auto-created)
- Output: `my-documents-chunks` (auto-created)
- Output: `my-documents-images` (auto-created)
- Output: `my-documents-citations` (auto-created)

#### **Approach 2: Explicit** - Full Control

Manually specify each container:

```bash
AZURE_BLOB_CONTAINER_IN=my-custom-input
AZURE_BLOB_CONTAINER_PREFIX=my-prod
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

---

### Creating Containers

#### Method 1: Azure CLI

**Using simple approach (base container name):**
```bash
# Create input container (REQUIRED - you must do this)
az storage container create \
  --name my-documents-input \
  --account-name yourstorageaccount \
  --auth-mode key

# Output containers are auto-created by the pipeline - no action needed!
```

**Using explicit approach:**
```bash
# Create input container
az storage container create \
  --name my-custom-input \
  --account-name yourstorageaccount

# Output containers auto-created by pipeline
```

#### Method 2: Azure Portal

1. Go to Azure Portal → Storage Account
2. Navigate to **Containers** under "Data storage"
3. Click **+ Container**
4. Name: `my-documents-input` (or your chosen name)
5. Public access level: **Private**
6. Click **Create**

#### Method 3: Python Script

```python
from azure.storage.blob import BlobServiceClient

connection_string = "your-connection-string"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Create input container
container_name = "my-documents-input"
try:
    blob_service_client.create_container(container_name)
    print(f"✅ Created container: {container_name}")
except Exception as e:
    print(f"Container exists or error: {e}")
```

---

### Uploading Files to Input Container

**Using Azure CLI:**
```bash
# Upload single file
az storage blob upload \
  --container-name my-documents-input \
  --file ./documents/sample.pdf \
  --name sample.pdf \
  --account-name yourstorageaccount

# Upload entire directory
az storage blob upload-batch \
  --destination my-documents-input \
  --source ./documents/ \
  --account-name yourstorageaccount
```

**Using Azure Storage Explorer (GUI):**
1. Download Azure Storage Explorer
2. Connect to your storage account
3. Navigate to container
4. Click "Upload" → Select files
5. Click "Upload"

**Using Azure Portal:**
1. Go to Storage Account → Containers → your-input-container
2. Click "Upload"
3. Select files and upload

---

## Environment Configuration

### Step 1: Copy Environment Template

**Choose your scenario:**

```bash
# Local development (no blob storage required)
cp envs/env.scenario1-local-dev.example .env

# Production blob deployment
cp envs/env.scenario2-blob-prod.example .env

# Local input, blob output (testing)
cp envs/env.scenario3-local-to-blob.example .env

# Blob input, local output (debugging)
cp envs/env.scenario4-blob-to-local.example .env
```

---

### Step 2: Configure Required Variables

Edit `.env` and set these **required variables**:

```bash
# Azure AI Search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=my-documents-index

# Document Intelligence
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Storage Account (for blob mode)
AZURE_STORAGE_ACCOUNT=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_CONNECTION_STRING=your-connection-string
```

---

### Step 3: Configure Input/Output

**For Local Input Mode:**
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=./documents/*.pdf
AZURE_ARTIFACTS_DIR=./artifacts
```

**For Blob Input Mode (Simple Approach - RECOMMENDED):**
```bash
AZURE_INPUT_MODE=blob
AZURE_STORAGE_CONTAINER=my-documents  # Base name for all containers

# Optional: Store artifacts locally for debugging
# AZURE_ARTIFACTS_DIR=./artifacts
```

**For Blob Input Mode (Explicit Approach):**
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-documents-input

# Output containers
AZURE_BLOB_CONTAINER_PREFIX=my-documents
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
AZURE_BLOB_CONTAINER_CITATIONS=citations
```

---

### Step 4: Verify Configuration

**Use the environment editor UI:**
```bash
# Launch web UI
python -m ingestor.gradio_app

# Or use the installed command
ingestor-ui
```

**Navigate to "Environment Variables" tab:**
- Check all required variables are set
- Click "Validate" button to check configuration
- Fix any missing variables

---

## Running the Pipeline

### 1. Verify Index Exists

```bash
# Check if index exists
python -m ingestor.cli --check-index

# Create/update index if needed
python -m ingestor.cli --setup-index
```

**Expected output:**
```
✅ Index 'my-documents-index' exists
✅ Index field count: 25
✅ Index is ready
```

---

### 2. Run Document Ingestion

**Basic run:**
```bash
python -m ingestor.cli
```

**With options:**
```bash
# Setup index first, then ingest
python -m ingestor.cli --setup-index

# Process specific files
python -m ingestor.cli --glob "documents/specific*.pdf"

# Dry run (validate without indexing)
python -m ingestor.cli --dry-run
```

---

### 3. Monitor Progress

The CLI will show:
- Document processing status
- Extraction progress
- Chunking results
- Embedding generation
- Upload progress

**Example output:**
```
🚀 Starting pipeline
📂 Input mode: blob
📦 Found 5 documents to process

Processing document 1/5: sample.pdf
  ✅ Extracted 10 pages
  ✅ Generated 45 chunks
  ✅ Created embeddings
  ✅ Uploaded to index

✅ Pipeline completed
📊 Summary:
  - Processed: 5 documents
  - Total chunks: 225
  - Total indexed: 225
  - Failed: 0
```

---

## Verification & Troubleshooting

### Check Indexed Documents

**Using CLI:**
```bash
# Check index status
python -m ingestor.cli --check-index

# Count documents in index
python -m ingestor.cli --count-documents
```

**Using Azure Portal:**
1. Go to Azure Portal → AI Search service
2. Navigate to "Indexes" → your index
3. Click "Search explorer"
4. Run query: `*` to see all documents

---

### Common Issues & Solutions

#### Issue: "AZURE_BLOB_CONTAINER_IN is required"

**Cause:** Missing container configuration

**Solution:**
```bash
# Add to .env:
AZURE_STORAGE_CONTAINER=my-documents
# OR
AZURE_BLOB_CONTAINER_IN=my-documents-input
```

---

#### Issue: "Container does not exist"

**Cause:** Input container not created

**Solution:**
```bash
# Create the input container
az storage container create \
  --name my-documents-input \
  --account-name yourstorageaccount
```

---

#### Issue: "AZURE_DOC_INT_ENDPOINT is required"

**Cause:** Wrong variable name in .env

**Fix:** Use correct variable names:
- ✅ `AZURE_DOC_INT_ENDPOINT` (correct)
- ❌ `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` (old, wrong)

---

#### Issue: No documents found

**Check:**
1. Files are uploaded to input container
2. `AZURE_BLOB_PREFIX` is not filtering out files
3. File extensions are supported (.pdf, .docx, .txt, etc.)

**Verify:**
```bash
# List files in container
az storage blob list \
  --container-name my-documents-input \
  --account-name yourstorageaccount \
  --query "[].name" -o table
```

---

#### Issue: Authentication errors

**Check:**
1. Storage account key is correct
2. Connection string is properly formatted
3. Container has correct permissions

**Test connection:**
```bash
# Test storage account access
az storage container list \
  --account-name yourstorageaccount \
  --account-key your-key
```

---

### Verify Artifacts

**For local artifacts:**
```bash
ls -la ./artifacts/
```

**For blob artifacts:**
```bash
# List all containers
az storage container list \
  --account-name yourstorageaccount \
  --query "[].name" -o table

# Should see:
# - my-documents-input
# - my-documents-pages
# - my-documents-chunks
# - my-documents-images
# - my-documents-citations
```

---

## Quick Reference

### Environment Variable Checklist

**Required for all modes:**
- [ ] `AZURE_SEARCH_SERVICE`
- [ ] `AZURE_SEARCH_KEY`
- [ ] `AZURE_SEARCH_INDEX`
- [ ] `AZURE_DOC_INT_ENDPOINT`
- [ ] `AZURE_OPENAI_ENDPOINT`
- [ ] `AZURE_OPENAI_KEY`
- [ ] `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

**Additional for blob mode:**
- [ ] `AZURE_STORAGE_ACCOUNT`
- [ ] `AZURE_STORAGE_ACCOUNT_KEY` or `AZURE_CONNECTION_STRING`
- [ ] `AZURE_STORAGE_CONTAINER` (simple) OR `AZURE_BLOB_CONTAINER_IN` (explicit)

**Additional for local mode:**
- [ ] `AZURE_INPUT_MODE=local`
- [ ] `AZURE_LOCAL_GLOB=./path/to/files`

---

### Command Quick Reference

```bash
# Setup & verification
python -m ingestor.cli --check-index      # Check if index exists
python -m ingestor.cli --setup-index      # Create/update index

# Document operations
python -m ingestor.cli                    # Index documents (default)
python -m ingestor.cli --glob "*.pdf"     # Index specific files
python -m ingestor.cli --action remove    # Remove documents
python -m ingestor.cli --action removeall # Remove all documents

# Utilities
python -m ingestor.cli --clean-artifacts  # Clean local artifacts
ingestor-ui                               # Launch web UI
```

---

## Next Steps

1. **Read the configuration guide**: [docs/guides/CONFIGURATION.md](docs/guides/CONFIGURATION.md)
2. **Explore examples**: [examples/](examples/)
3. **Performance tuning**: [docs/guides/PERFORMANCE_TUNING.md](docs/guides/PERFORMANCE_TUNING.md)
4. **Batch processing**: [docs/guides/BATCH_PROCESSING.md](docs/guides/BATCH_PROCESSING.md)

---

## Need Help?

- **Documentation Hub**: [docs/INDEX.md](docs/INDEX.md)
- **Quick Reference**: [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)
- **Environment Guide**: [docs/guides/ENVIRONMENT_AND_SECRETS.md](docs/guides/ENVIRONMENT_AND_SECRETS.md)
- **Configuration Matrix**: [docs/reference/01_CONFIGURATION_MATRIX.md](docs/reference/01_CONFIGURATION_MATRIX.md)

---

**Made with ❤️ for the Azure AI community**
