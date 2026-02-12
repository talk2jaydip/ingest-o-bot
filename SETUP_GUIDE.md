# Complete Setup Guide

> Step-by-step guide to set up and run the ingestor pipeline from scratch

This guide walks you through everything: installation, choosing your scenario, Azure resource setup (if needed), environment configuration, and running the pipeline.

**✨ New Feature:** Use `--env-file` parameter to switch between multiple configurations without copying files. No more `.env` juggling!

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Choose Your Scenario](#choose-your-scenario)
4. [Azure Resources Setup](#azure-resources-setup)
5. [Environment Configuration](#environment-configuration)
6. [Running the Pipeline](#running-the-pipeline)
7. [Verification & Troubleshooting](#verification--troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.10+**
- **Git** (for cloning repository)
- **pip** (Python package manager)

### Optional Software
- **Azure CLI** (for Azure resource management)
- **Azure Storage Explorer** (GUI for blob storage)

### Azure Resources (Scenario-Dependent)

Different scenarios require different Azure resources. See [Choose Your Scenario](#choose-your-scenario) for details.

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/ingest-o-bot.git
cd ingest-o-bot
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

The project uses modular requirements files. Choose based on your needs:

**Core Installation (Required):**
```bash
pip install -r requirements.txt
```

**Optional Features:**
```bash
# Gradio Web UI
pip install -r requirements-gradio.txt

# ChromaDB (local vector store)
pip install -r requirements-chromadb.txt

# Alternative embeddings (Hugging Face + Cohere)
pip install -r requirements-embeddings.txt

# Install everything
pip install -r requirements.txt -r requirements-gradio.txt -r requirements-chromadb.txt -r requirements-embeddings.txt
```

**GPU Support (Optional):**

For GPU-accelerated local embeddings:
```bash
# NVIDIA GPU (CUDA 11.8)
pip install torch>=2.0.0+cu118 --index-url https://download.pytorch.org/whl/cu118

# NVIDIA GPU (CUDA 12.1)
pip install torch>=2.0.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# Apple Silicon (M1/M2/M3)
pip install torch>=2.0.0
# Set HUGGINGFACE_DEVICE=mps in .env
```

### Step 4: Verify Installation

```bash
# Check CLI is available
python -m ingestor.cli --help

# Launch UI (if installed Gradio)
python -m ingestor.gradio_app
# OR use launcher scripts
scripts\launch_ui.bat      # Windows
./scripts/launch_ui.sh     # Linux/Mac
```

---

## Choose Your Scenario

Pick the scenario that matches your use case:

| Scenario | Cloud Services | Local Components | Cost | Setup Time | Env File |
|----------|----------------|------------------|------|------------|----------|
| **Azure Full Stack** | AI Search + DI + OpenAI | None | $$$ | 30 min | `.env.example` |
| **Azure Local Input** | AI Search + DI + OpenAI | Local files | $$$ | 20 min | `.env.azure-local-input.example` |
| **Azure + ChromaDB** | DI + OpenAI | ChromaDB storage | $$ | 15 min | `.env.azure-chromadb-hybrid.example` |
| **Cost-Optimized** | AI Search only | Local embeddings | $ | 20 min | `.env.scenario-cost-optimized.example` |
| **Development Mode** | None | ChromaDB + MarkItDown | Free | 10 min | `.env.scenario-development.example` |
| **Fully Offline** | None | ChromaDB + HuggingFace | Free | 10 min | `.env.chromadb.example` |
| **Offline + Vision** | None (+ optional GPT-4o) | ChromaDB + HuggingFace | Free/$ | 10 min | `.env.offline-with-vision.example` |
| **Multilingual** | AI Search + DI + Cohere | None | $$$ | 15 min | `.env.scenario-multilingual.example` |

**Cost Guide:**
- **Free**: No Azure costs
- **$**: ~$1-3 per 1000 pages
- **$$**: ~$5-8 per 1000 pages
- **$$$**: ~$10-15 per 1000 pages

**See Also:**
- [Environment & Secrets Guide](docs/guides/ENVIRONMENT_AND_SECRETS.md)
- [Configuration Guide](docs/guides/CONFIGURATION.md)

---

## Azure Resources Setup

> **Note:** Required Azure resources depend on your chosen scenario. Skip Azure setup for offline/development modes.

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

### Two Approaches: Copy vs Direct Use

#### **Approach 1: Copy to .env (Traditional)**

Copy the template to `.env` and edit:

```bash
# Windows
copy envs\.env.azure-local-input.example .env
notepad .env

# Linux/Mac
cp envs/.env.azure-local-input.example .env
nano .env
```

#### **Approach 2: Use --env-file (Recommended)**

Edit templates directly, no copying needed:

```bash
# 1. Edit the template file with your credentials
notepad envs\.env.azure-local-input.example   # Windows
nano envs/.env.azure-local-input.example      # Linux/Mac

# 2. Use --env-file parameter to specify which config to use
python -m ingestor.cli --validate --env-file envs/.env.azure-local-input.example
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.example

# 3. Switch scenarios easily - just change --env-file!
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.chromadb.example
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.offline-with-vision.example
```

**Benefits of --env-file approach:**
- ✅ Keep multiple configurations ready
- ✅ Switch between scenarios instantly
- ✅ No copying/overwriting .env
- ✅ Test different setups without conflicts

---

### Step 1: Choose Your Environment File

Based on your scenario from above:

```bash
# Azure full stack
envs/.env.example

# Azure services with local file input
envs/.env.azure-local-input.example

# Azure processing + ChromaDB storage
envs/.env.azure-chromadb-hybrid.example

# Cost-optimized (Azure Search + local embeddings)
envs/.env.scenario-cost-optimized.example

# Development mode (no Azure)
envs/.env.scenario-development.example

# Fully offline
envs/.env.chromadb.example

# Offline with optional GPT-4o vision
envs/.env.offline-with-vision.example

# Multilingual with Cohere
envs/.env.scenario-multilingual.example
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

### Step 4: Validate Configuration

**Method 1: CLI Validation (Recommended)**

```bash
# Validate default .env file
python -m ingestor.cli --validate

# Validate specific environment file
python -m ingestor.cli --validate --env-file envs/.env.azure-local-input.example

# Pre-flight check (validates + checks Azure connectivity)
python -m ingestor.cli --validate --env-file envs/.env.chromadb.example
```

**Expected output:**
```
✅ Input Source: Files exist and accessible
✅ Artifacts Storage: Directory writable
✅ Document Intelligence: Endpoint configured (skipped for MarkItDown mode)
✅ Azure OpenAI: Embeddings configured
✅ Azure AI Search: Service accessible, index exists
✅ Python Dependencies: All required packages installed

✓ Configuration is valid!
```

**Method 2: Gradio UI Validation**

```bash
# Launch web UI
python -m ingestor.gradio_app

# OR use launcher scripts
scripts\launch_ui.bat      # Windows
./scripts/launch_ui.sh     # Linux/Mac
```

**Navigate to "Environment Variables" tab:**
- Check all required variables are set
- Click "Validate Configuration" button
- Review validation results
- Fix any missing variables

---

## Running the Pipeline

### 1. Validate Configuration (Pre-Flight Check)

```bash
# Validate configuration before running
python -m ingestor.cli --validate --env-file envs/.env.azure-local-input.example
```

---

### 2. Verify Index Exists

```bash
# Check if index exists (uses .env by default)
python -m ingestor.cli --check-index

# OR with specific env file
python -m ingestor.cli --check-index --env-file envs/.env.azure-local-input.example

# Create/update index if needed
python -m ingestor.cli --setup-index --env-file envs/.env.azure-local-input.example
```

**Expected output:**
```
✅ Index 'my-documents-index' exists
✅ Index field count: 25
✅ Index is ready
```

---

### 3. Run Document Ingestion

**Using .env file (traditional):**
```bash
# Basic run
python -m ingestor.cli

# Setup index first, then ingest
python -m ingestor.cli --setup-index

# Process specific files
python -m ingestor.cli --glob "documents/specific*.pdf"
```

**Using --env-file parameter (recommended):**
```bash
# Process with specific environment
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.example

# Process multiple files
python -m ingestor.cli --glob "docs/*.pdf" --env-file envs/.env.chromadb.example

# Setup index and process
python -m ingestor.cli --setup-index --glob "docs/*.pdf" --env-file envs/.env.azure-local-input.example

# Switch scenarios instantly
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.chromadb.example
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.example
```

**Other useful options:**
```bash
# Dry run (validate without indexing)
python -m ingestor.cli --dry-run --env-file envs/.env.azure-local-input.example

# Verbose logging
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.chromadb.example --verbose
```

---

### 4. Monitor Progress

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

> **Note:** Required variables depend on your scenario. Not all variables are needed for all scenarios.

**Azure AI Search (Required for Azure scenarios):**
- [ ] `AZURE_SEARCH_SERVICE`
- [ ] `AZURE_SEARCH_KEY`
- [ ] `AZURE_SEARCH_INDEX`

**Document Processing (Scenario-Dependent):**
- [ ] `AZURE_DOC_INT_ENDPOINT` (if using Azure DI)
- [ ] `AZURE_DOC_INT_KEY` (if using Azure DI)
- [ ] `USE_MARKITDOWN=true` (if using MarkItDown instead of Azure DI)

**Embeddings (Scenario-Dependent):**
- [ ] `AZURE_OPENAI_ENDPOINT` (if using Azure OpenAI)
- [ ] `AZURE_OPENAI_KEY` (if using Azure OpenAI)
- [ ] `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (if using Azure OpenAI)
- [ ] `HUGGINGFACE_EMBEDDING_MODEL` (if using Hugging Face)
- [ ] `COHERE_API_KEY` (if using Cohere)

**Storage (Scenario-Dependent):**
- [ ] `AZURE_STORAGE_ACCOUNT` (for blob mode)
- [ ] `AZURE_STORAGE_ACCOUNT_KEY` or `AZURE_CONNECTION_STRING` (for blob mode)
- [ ] `AZURE_STORAGE_CONTAINER` (simple) OR `AZURE_BLOB_CONTAINER_IN` (explicit)
- [ ] `CHROMADB_DIR` (for ChromaDB mode)

**Input Source:**
- [ ] `AZURE_INPUT_MODE=local` or `AZURE_INPUT_MODE=blob`
- [ ] `AZURE_LOCAL_GLOB=./path/to/files` (for local mode)

**See Also:**
- [Configuration Matrix](docs/reference/01_CONFIGURATION_MATRIX.md) - Full variable reference
- [Environment Guide](docs/guides/ENVIRONMENT_AND_SECRETS.md) - Detailed scenarios

---

### Command Quick Reference

```bash
# Validation
python -m ingestor.cli --validate                                      # Validate .env
python -m ingestor.cli --validate --env-file envs/.env.example        # Validate specific file

# Setup & verification
python -m ingestor.cli --check-index                                  # Check if index exists
python -m ingestor.cli --setup-index                                  # Create/update index
python -m ingestor.cli --check-index --env-file envs/.env.example    # Check with specific env

# Document operations (using .env)
python -m ingestor.cli                                                # Index documents (default)
python -m ingestor.cli --glob "*.pdf"                                # Index specific files
python -m ingestor.cli --pdf test.pdf                                # Index single file
python -m ingestor.cli --action remove                               # Remove documents
python -m ingestor.cli --action removeall                            # Remove all documents

# Document operations (using --env-file)
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.example
python -m ingestor.cli --glob "docs/*.pdf" --env-file envs/.env.chromadb.example
python -m ingestor.cli --setup-index --glob "docs/*.pdf" --env-file envs/.env.example

# Utilities
python -m ingestor.cli --clean-artifacts                             # Clean local artifacts
python -m ingestor.gradio_app                                        # Launch web UI
scripts\launch_ui.bat                                                # Launch UI (Windows)
./scripts/launch_ui.sh                                               # Launch UI (Linux/Mac)
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

---

**Last Updated:** February 12, 2026
- Added installation section with modular requirements.txt structure
- Added scenario selection guide (8 scenarios)
- Updated to use --env-file workflow
- Added validation workflow (--validate flag)
- Updated environment file references to current structure
- Added ChromaDB and offline mode setup
- Added launcher script references (launch_ui.bat/sh)
