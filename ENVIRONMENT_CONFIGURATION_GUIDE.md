# Environment Configuration Guide

Complete guide to environment configuration for all usage scenarios.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration Scenarios](#configuration-scenarios)
3. [Environment Variables Reference](#environment-variables-reference)
4. [Validation & Troubleshooting](#validation--troubleshooting)
5. [Common Patterns](#common-patterns)

---

## Quick Start

### Choose Your Scenario

Pick the scenario that best matches your use case:

| Scenario | When to Use | Template File | Setup Time |
|----------|-------------|---------------|------------|
| **Local Development** | Testing locally, no cloud costs | `.env.scenario-development.example` | 5 min |
| **Azure Full Stack** | Production with Azure services | `.env.example` | 30 min |
| **Azure Local Input** | Azure services, local file input | `.env.azure-local-input.example` | 20 min |
| **Azure + ChromaDB** | Azure processing, local storage | `.env.azure-chromadb-hybrid.example` | 15 min |
| **Fully Offline** | Air-gapped/secure environment | `.env.chromadb.example` | 10 min |
| **Offline + Vision** | Offline with optional GPT-4o vision | `.env.offline-with-vision.example` | 10 min |
| **Cost-Optimized** | Azure Search + local embeddings | `.env.hybrid.example` | 20 min |
| **Multilingual** | 100+ languages support | `.env.scenario-multilingual.example` | 15 min |
| **Hybrid Scenarios** | Mix & match components | `.env.hybrid-scenarios.example` | Varies |

### Setup Steps

```bash
# 1. Copy template for your scenario
cp envs/.env.example .env  # Or choose another template

# 2. Edit .env and fill in your credentials
nano .env

# 3. Validate configuration
python -m ingestor.scenario_validator

# 4. Run the pipeline
python -m ingestor.cli --validate  # Pre-check
python -m ingestor.cli --glob "documents/*.pdf"  # Process documents
```

---

## Configuration Scenarios

### Scenario 1: Local Development (No Azure Required)

**Best for:** Quick testing, development, learning the system

**Requirements:**
- No Azure subscription needed
- No internet connection needed (after initial model download)
- Free and fully offline

**Configuration:**
```bash
# Vector Store: ChromaDB (local)
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=dev-documents
# CHROMADB_PERSIST_DIR=./chroma_dev  # Uncomment for persistent storage

# Embeddings: HuggingFace (local)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_DEVICE=cpu

# Input: Local files
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=documents/**/*.pdf

# Artifacts: Local directory
AZURE_ARTIFACTS_DIR=./artifacts

# Document Processing: Offline
AZURE_OFFICE_EXTRACTOR_MODE=markitdown

# Integrated vectorization: Disabled (using local embeddings)
AZURE_USE_INTEGRATED_VECTORIZATION=false

# Dummy values (required by schema but not used)
AZURE_SEARCH_SERVICE=dev-dummy
AZURE_SEARCH_INDEX=dev-index
AZURE_SEARCH_KEY=dummy-key
```

**Setup:**
```bash
# 1. Copy template
cp envs/.env.scenario-development.example .env

# 2. Install dependencies
pip install chromadb sentence-transformers torch

# 3. Run
python -m ingestor.cli --glob "documents/*.pdf"
```

**Pros:**
- ✅ Zero costs
- ✅ Complete data privacy
- ✅ Fast iteration
- ✅ No cloud dependencies

**Cons:**
- ❌ Lower quality extraction (vs Azure DI)
- ❌ No distributed deployment
- ❌ Limited to local machine resources

---

### Scenario 2: Azure Full Stack (Production)

**Best for:** Enterprise production, highest quality extraction

**Requirements:**
- Azure AI Search service
- Azure Document Intelligence service
- Azure OpenAI service with embeddings deployment
- Azure Storage Account (optional, for blob mode)

**Configuration:**
```bash
# Vector Store: Azure AI Search
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=documents
AZURE_SEARCH_KEY=your-search-admin-key

# Embeddings: Azure OpenAI
EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Document Intelligence
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key

# Optional: Azure Storage for blob mode
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_STORAGE_CONTAINER=documents  # Auto-creates input/output containers

# Input mode (local or blob)
AZURE_INPUT_MODE=blob  # or "local" for development

# Office processing
AZURE_OFFICE_EXTRACTOR_MODE=hybrid  # Best quality with fallback

# Integrated vectorization
AZURE_USE_INTEGRATED_VECTORIZATION=true  # or false for client-side embeddings
```

**Setup:**
```bash
# 1. Create Azure resources (see SETUP_GUIDE.md)
az search service create --name your-search --resource-group your-rg --sku standard
az cognitiveservices account create --name your-di --kind FormRecognizer --sku S0
az cognitiveservices account create --name your-openai --kind OpenAI --sku S0
az storage account create --name yourstorageaccount --sku Standard_LRS

# 2. Copy template
cp envs/.env.example .env

# 3. Edit .env with your credentials
nano .env

# 4. Create input container (if using blob mode)
az storage container create --name documents-input --account-name yourstorageaccount

# 5. Validate and run
python -m ingestor.cli --validate
python -m ingestor.cli --setup-index --glob "documents/*.pdf"
```

**Pros:**
- ✅ Highest quality extraction
- ✅ Enterprise-grade search
- ✅ Scalable and distributed
- ✅ Managed infrastructure

**Cons:**
- ❌ Monthly costs (~$300-1000)
- ❌ Requires Azure subscription
- ❌ More complex setup

---

### Scenario 3: Fully Offline (Air-Gapped)

**Best for:** Secure environments, compliance requirements, air-gapped systems

**Requirements:**
- No internet connection (after initial setup)
- No Azure services
- LibreOffice (for Office documents)

**Configuration:**
```bash
# Vector Store: ChromaDB (persistent local storage)
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=offline-documents
CHROMADB_PERSIST_DIR=./chroma_db

# Embeddings: HuggingFace (local)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
HUGGINGFACE_DEVICE=cpu

# Input: Local files only
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=documents/**/*.pdf

# Artifacts: Local storage
AZURE_ARTIFACTS_DIR=./artifacts

# Document Processing: Offline only
AZURE_OFFICE_EXTRACTOR_MODE=markitdown

# Media descriptions: Disabled (offline mode)
AZURE_MEDIA_DESCRIBER=disabled

# Integrated vectorization: Disabled
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Setup:**
```bash
# 1. On internet-connected machine (one-time)
pip install chromadb sentence-transformers torch
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

# 2. Copy models cache to offline machine
# Models are in: ~/.cache/huggingface/

# 3. Install LibreOffice (for Office documents)
# Linux: sudo apt-get install libreoffice
# Mac: brew install --cask libreoffice
# Windows: Download from libreoffice.org

# 4. Copy template and configure
cp envs/.env.chromadb.example .env

# 5. Run offline
python -m ingestor.cli --glob "documents/*.pdf"
```

**Pros:**
- ✅ 100% offline operation
- ✅ Complete data privacy
- ✅ No cloud costs
- ✅ Compliance-friendly

**Cons:**
- ❌ Lower quality extraction
- ❌ Manual model management
- ❌ Limited to local resources

---

### Scenario 4: Cost-Optimized (Hybrid)

**Best for:** High-volume processing, cost optimization, keeping data in Azure

**Requirements:**
- Azure AI Search service
- Local GPU (optional, for faster embeddings)
- No Azure OpenAI needed (saves $$ on embeddings)

**Configuration:**
```bash
# Vector Store: Azure AI Search
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=hybrid-documents
AZURE_SEARCH_KEY=your-search-admin-key

# Embeddings: HuggingFace (local - FREE!)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda  # or cpu, mps
HUGGINGFACE_BATCH_SIZE=64

# IMPORTANT: Disable integrated vectorization
AZURE_USE_INTEGRATED_VECTORIZATION=false

# Optional: Document Intelligence (if needed)
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-di-key

# Storage Account
AZURE_STORAGE_ACCOUNT=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key

# Input mode
AZURE_INPUT_MODE=blob
AZURE_STORAGE_CONTAINER=documents
```

**Cost Comparison:**
```
Before (Azure OpenAI embeddings): ~$0.10 per 1M tokens = $1,000/month for 10M tokens
After (Local HuggingFace):        $0 (only GPU compute) = $0/month

Total Savings: $1,000/month on embeddings!
```

**Setup:**
```bash
# 1. Copy template
cp envs/.env.hybrid.example .env

# 2. Install dependencies
pip install sentence-transformers torch

# 3. For GPU acceleration (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 4. Configure and run
python -m ingestor.cli --setup-index --glob "documents/*.pdf"
```

**Pros:**
- ✅ Zero embedding costs
- ✅ Enterprise Azure Search
- ✅ GPU-accelerated processing
- ✅ High quality embeddings

**Cons:**
- ❌ Requires GPU for best performance
- ❌ Local processing bottleneck
- ❌ Still need Azure Search costs

---

### Scenario 5: Multilingual (100+ Languages)

**Best for:** International documents, multilingual support

**Requirements:**
- Cohere API key OR multilingual HuggingFace model
- Azure AI Search (optional)

**Option A: Cohere Embeddings (Cloud)**
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-api-key
COHERE_MODEL_NAME=embed-multilingual-v3.0
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Option B: HuggingFace Multilingual (Local)**
```bash
VECTOR_STORE_MODE=chromadb
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Setup:**
```bash
# Option A (Cohere):
cp envs/.env.cohere.example .env
pip install cohere

# Option B (HuggingFace):
cp envs/.env.scenario-multilingual.example .env
pip install sentence-transformers
```

---

### Scenario 6: Azure with Local Input

**Best for:** Enterprise OCR/embeddings quality without blob storage complexity

**Requirements:**
- Azure Document Intelligence service
- Azure OpenAI service with embeddings deployment
- Azure AI Search service
- NO Azure Storage Account needed

**Configuration:**
```bash
# Extraction: Azure Document Intelligence
EXTRACTION_MODE=azure_di
AZURE_DI_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DI_KEY=your_di_key
AZURE_DI_MODEL=prebuilt-layout

# Input: Local files (no blob storage)
INPUT_MODE=local

# Embeddings: Azure OpenAI
EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072

# Vector Store: Azure Search
VECTOR_STORE=azure_search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your_key
AZURE_SEARCH_INDEX_NAME=local-input-docs
```

**Setup:**
```bash
# 1. Copy template
cp envs/.env.azure-local-input.example .env

# 2. Create Azure resources (no storage needed!)
az cognitiveservices account create --name your-di --kind FormRecognizer
az cognitiveservices account create --name your-openai --kind OpenAI
az search service create --name your-search --sku basic

# 3. Process local files directly
python -m ingestor.cli --pdf ./my-document.pdf
python -m ingestor.cli --glob "docs/**/*.pdf"
```

**Pros:**
- ✅ Enterprise-grade OCR and extraction
- ✅ No blob storage complexity or costs
- ✅ Read files directly from local disk
- ✅ High-quality embeddings (3072 dims)
- ✅ Cloud-scale search

**Cons:**
- ❌ Still requires Azure subscriptions
- ❌ API costs for processing
- ❌ Not suitable for offline scenarios

---

### Scenario 7: Azure Processing + ChromaDB Storage

**Best for:** Best of both worlds - enterprise processing, local/free storage

**Requirements:**
- Azure Document Intelligence service
- Azure OpenAI service with embeddings deployment
- NO Azure Search needed (huge cost savings!)
- NO Azure Storage Account needed

**Configuration:**
```bash
# Extraction: Azure Document Intelligence (paid)
EXTRACTION_MODE=azure_di
AZURE_DI_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DI_KEY=your_di_key
AZURE_DI_MODEL=prebuilt-layout

# Embeddings: Azure OpenAI (paid)
EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072

# Vector Store: ChromaDB (FREE!)
VECTOR_STORE=chromadb
CHROMADB_MODE=persistent
CHROMADB_PATH=./chroma_db_hybrid
CHROMADB_COLLECTION_NAME=azure-hybrid-docs
VECTOR_SEARCH_DIMENSIONS=3072

# Input: Local files
INPUT_MODE=local
```

**Setup:**
```bash
# 1. Copy template
cp envs/.env.azure-chromadb-hybrid.example .env

# 2. Install ChromaDB
pip install chromadb

# 3. Create Azure processing resources (no search!)
az cognitiveservices account create --name your-di --kind FormRecognizer
az cognitiveservices account create --name your-openai --kind OpenAI

# 4. Process documents
python -m ingestor.cli --pdf ./document.pdf
```

**Pros:**
- ✅ Enterprise OCR quality (Azure DI)
- ✅ High-quality embeddings (Azure OpenAI 3072 dims)
- ✅ FREE vector storage (no Azure Search costs)
- ✅ Data stays local after processing
- ✅ Easy backup (copy ./chroma_db folder)

**Cons:**
- ❌ Not fully offline (needs Azure for processing)
- ❌ Limited search scalability vs Azure Search
- ❌ No semantic ranking feature

**Cost Savings:**
- Azure Search Basic: ~$250/month → $0 (100% savings!)
- Total cost: ~$2-3 per 1000 pages vs ~$10-15 with full Azure

---

### Scenario 8: Fully Offline with Optional Vision

**Best for:** Maximum privacy with optional cloud vision for images

**Requirements:**
- NO Azure services required for base functionality
- Optional: Azure OpenAI GPT-4o for image description
- Local compute resources

**Configuration:**

**Option A: 100% Offline**
```bash
# Extraction: Markitdown (free, local)
EXTRACTION_MODE=markitdown
INPUT_MODE=local
MARKITDOWN_IMAGE_MODE=skip  # Skip images completely

# Embeddings: Hugging Face (free, local)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL=all-mpnet-base-v2
EMBEDDING_DIMENSIONS=768

# Vector Store: ChromaDB (free, local)
VECTOR_STORE=chromadb
CHROMADB_MODE=persistent
CHROMADB_PATH=./chroma_db_offline

# Vision: Disabled (fully offline)
ENABLE_MEDIA_DESCRIPTION=false
```

**Option B: Hybrid with Vision**
```bash
# Same as Option A, but enable vision:
MARKITDOWN_IMAGE_MODE=describe
ENABLE_MEDIA_DESCRIPTION=true

# Azure OpenAI GPT-4o for vision only
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o
VISION_DETAIL_LEVEL=high
```

**Setup:**
```bash
# 1. Copy template
cp envs/.env.offline-with-vision.example .env

# 2. Install dependencies
pip install chromadb sentence-transformers torch markitdown

# 3. Download models (ONE TIME, requires internet)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# 4. Process offline (disconnect internet if desired)
python -m ingestor.cli --pdf ./document.pdf
```

**Pros:**
- ✅ 100% FREE (without vision)
- ✅ Complete data privacy
- ✅ Works without internet (after setup)
- ✅ Optional cloud vision for images
- ✅ GDPR/HIPAA friendly

**Cons:**
- ❌ Lower extraction quality than Azure DI
- ❌ Smaller embedding dimensions (768 vs 3072)
- ❌ Vision requires internet and costs

**Cost:**
- Without vision: $0 forever
- With vision: ~$2-5 per 1000 pages (for images only)

---

### Scenario 9: Mix & Match Hybrid Scenarios

**Best for:** Custom requirements, specific optimization needs

The `.env.hybrid-scenarios.example` file contains 8 pre-configured hybrid scenarios:

1. **Cost-Optimized**: Markitdown + Hugging Face + Azure Search
2. **Quality Extraction + Free Storage**: Azure DI + Hugging Face + ChromaDB
3. **Multilingual**: Markitdown + Cohere + ChromaDB
4. **OpenAI Alternative**: Markitdown + OpenAI + ChromaDB
5. **Maximum Quality**: Azure DI + Azure OpenAI + Azure Search + Vision
6. **Development/Testing**: All free, local, in-memory
7. **Secure/Private**: Azure DI + Hugging Face + ChromaDB
8. **Distributed ChromaDB**: Any extraction/embeddings + Remote ChromaDB

**Component Selection Guide:**

| Priority | Extraction | Embeddings | Vector Store | Vision |
|----------|------------|------------|--------------|--------|
| **Cost** | Markitdown | Hugging Face | ChromaDB | None |
| **Quality** | Azure DI | Azure OpenAI | Azure Search | GPT-4o |
| **Privacy** | Markitdown | Hugging Face | ChromaDB | None |
| **Multilingual** | Markitdown | Cohere/HF | ChromaDB | GPT-4o |
| **Scale** | Azure DI | Azure OpenAI | Azure Search | GPT-4o |

**Setup:**
```bash
# 1. Copy hybrid template
cp envs/.env.hybrid-scenarios.example .env

# 2. Uncomment/configure your chosen scenario section
# 3. Comment out other scenarios
# 4. Validate
python -m ingestor.scenario_validator

# 5. Process
python -m ingestor.cli --pdf ./document.pdf
```

**All Valid Combinations:**

| Extraction | Embeddings | Vector Store | Cost/1000 pages | Quality |
|------------|------------|--------------|-----------------|---------|
| Markitdown | Hugging Face | ChromaDB | FREE | Good |
| Markitdown | Hugging Face | Azure Search | $8 | Good |
| Markitdown | Cohere | ChromaDB | $0.50 | Better |
| Markitdown | Azure OpenAI | ChromaDB | $0.50 | Best |
| Azure DI | Hugging Face | ChromaDB | $1.50 | Better |
| Azure DI | Azure OpenAI | ChromaDB | $2.00 | Best |
| Azure DI | Azure OpenAI | Azure Search | $10-15 | Enterprise |

**Notes:**
- All combinations are supported and tested
- Mix and match based on your requirements
- See `.env.hybrid-scenarios.example` for detailed configs
- Each scenario has specific pros/cons documented

---

## Environment Variables Reference

### Core Configuration

#### Vector Store Selection

| Variable | Values | Default | Required | Description |
|----------|--------|---------|----------|-------------|
| `VECTOR_STORE_MODE` | `azure_search`, `chromadb` | `azure_search` | No* | Which vector database to use |

*Required explicitly for ChromaDB. Azure Search is default if not specified.

#### Embeddings Provider Selection

| Variable | Values | Default | Required | Description |
|----------|--------|---------|----------|-------------|
| `EMBEDDINGS_MODE` | `azure_openai`, `huggingface`, `cohere`, `openai` | `azure_openai` | No* | Which embeddings provider to use |

*Required explicitly for non-Azure providers.

---

### Azure AI Search Configuration

**Required when:** `VECTOR_STORE_MODE=azure_search` (or not set)

| Variable | Example | Required | Description |
|----------|---------|----------|-------------|
| `AZURE_SEARCH_SERVICE` | `my-search-service` | Yes* | Search service name |
| `AZURE_SEARCH_ENDPOINT` | `https://....search.windows.net` | Yes* | Or use endpoint directly |
| `AZURE_SEARCH_INDEX` | `documents` | Yes | Index name |
| `AZURE_SEARCH_KEY` | `your-admin-key` | No** | Admin API key |

*Provide either `AZURE_SEARCH_SERVICE` OR `AZURE_SEARCH_ENDPOINT`
**Optional with managed identity

---

### ChromaDB Configuration

**Required when:** `VECTOR_STORE_MODE=chromadb`

| Variable | Example | Default | Required | Description |
|----------|---------|---------|----------|-------------|
| `CHROMADB_COLLECTION_NAME` | `documents` | `documents` | No | Collection name |
| `CHROMADB_PERSIST_DIR` | `./chroma_db` | None (in-memory) | No | Persistent storage path |
| `CHROMADB_HOST` | `localhost` | None | No* | Server host (client mode) |
| `CHROMADB_PORT` | `8000` | None | No* | Server port (client mode) |
| `CHROMADB_BATCH_SIZE` | `1000` | `1000` | No | Upload batch size |

*Required for client/server mode

---

### Azure OpenAI Configuration

**Required when:** `EMBEDDINGS_MODE=azure_openai` (or not set)

| Variable | Example | Required | Description |
|----------|---------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | `https://....openai.azure.com/` | Yes | OpenAI endpoint |
| `AZURE_OPENAI_KEY` | `your-key` | Yes | API key |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | `text-embedding-ada-002` | Yes* | Deployment name |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | No | API version |
| `AZURE_OPENAI_EMBEDDING_DIMENSIONS` | `1536` | No | For v3 models |

*Not required if `AZURE_USE_INTEGRATED_VECTORIZATION=true`

---

### HuggingFace Configuration

**Required when:** `EMBEDDINGS_MODE=huggingface`

| Variable | Example | Default | Required | Description |
|----------|---------|---------|----------|-------------|
| `HUGGINGFACE_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | (preset) | No | Model identifier |
| `HUGGINGFACE_DEVICE` | `cpu`, `cuda`, `mps` | `cpu` | No | Device to run on |
| `HUGGINGFACE_BATCH_SIZE` | `32` | `32` | No | Batch size |
| `HUGGINGFACE_NORMALIZE` | `true`, `false` | `true` | No | Normalize embeddings |

**Popular Models:**
- `sentence-transformers/all-MiniLM-L6-v2` - 384 dims, fast, English
- `sentence-transformers/all-mpnet-base-v2` - 768 dims, quality, English
- `intfloat/multilingual-e5-large` - 1024 dims, multilingual, SOTA

---

### Cohere Configuration

**Required when:** `EMBEDDINGS_MODE=cohere`

| Variable | Example | Default | Required | Description |
|----------|---------|---------|----------|-------------|
| `COHERE_API_KEY` | `your-key` | None | Yes | Cohere API key |
| `COHERE_MODEL_NAME` | `embed-multilingual-v3.0` | (preset) | No | Model name |
| `COHERE_INPUT_TYPE` | `search_document` | `search_document` | No | Input type |

---

### Azure Document Intelligence

**Required when:** `AZURE_OFFICE_EXTRACTOR_MODE=azure_di` or `hybrid` (default)

| Variable | Example | Required | Description |
|----------|---------|----------|-------------|
| `AZURE_DOC_INT_ENDPOINT` | `https://....cognitiveservices.azure.com/` | Yes* | DI endpoint |
| `AZURE_DOC_INT_KEY` | `your-key` | No** | API key |
| `AZURE_DI_MAX_CONCURRENCY` | `3` | No | Max parallel requests |

*Not required if `AZURE_OFFICE_EXTRACTOR_MODE=markitdown`
**Optional with managed identity

---

### Input Configuration

**Always Required**

| Variable | Example | Default | Required When | Description |
|----------|---------|---------|---------------|-------------|
| `AZURE_INPUT_MODE` | `local`, `blob` | `local` | Always | Input source type |
| `AZURE_LOCAL_GLOB` | `documents/**/*.pdf` | None | `mode=local` | File pattern |
| `AZURE_BLOB_CONTAINER_IN` | `documents-input` | None | `mode=blob` | Input container |
| `AZURE_STORAGE_ACCOUNT` | `mystorageaccount` | None | `mode=blob` | Storage account |
| `AZURE_STORAGE_ACCOUNT_KEY` | `your-key` | None | `mode=blob` | Storage key |

---

### Artifacts Configuration

| Variable | Example | Default | Description |
|----------|---------|---------|-------------|
| `AZURE_ARTIFACTS_DIR` | `./artifacts` | `./artifacts` | Local artifacts directory |
| `AZURE_STORAGE_CONTAINER` | `documents` | None | Base name for containers* |

*Auto-creates: `{name}-pages`, `{name}-chunks`, etc.

---

### Document Processing

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `AZURE_OFFICE_EXTRACTOR_MODE` | `azure_di`, `markitdown`, `hybrid` | `hybrid` | Extraction mode |
| `AZURE_OFFICE_OFFLINE_FALLBACK` | `true`, `false` | `true` | Enable fallback (hybrid only) |
| `AZURE_MEDIA_DESCRIBER` | `gpt4o`, `disabled` | `disabled` | Media descriptions |
| `AZURE_TABLE_RENDER` | `plain`, `markdown`, `html` | `markdown` | Table format |
| `AZURE_USE_INTEGRATED_VECTORIZATION` | `true`, `false` | `false` | Use Azure Search vectorization |

---

### Chunking Configuration

| Variable | Example | Default | Description |
|----------|---------|---------|-------------|
| `CHUNKING_MAX_TOKENS` | `500` | `500` | Max tokens per chunk |
| `CHUNKING_MAX_CHARS` | `2000` | `2000` | Soft char limit |
| `CHUNKING_OVERLAP_PERCENT` | `10` | `10` | Overlap percentage |
| `CHUNKING_CROSS_PAGE_OVERLAP` | `true`, `false` | `false` | Cross-page overlap |

**Note:** Pipeline auto-adjusts limits based on embedding model capacity.

---

### Performance Tuning

| Variable | Example | Default | Description |
|----------|---------|---------|-------------|
| `AZURE_MAX_WORKERS` | `4` | `4` | Parallel workers |
| `AZURE_EMBED_BATCH_SIZE` | `128` | `128` | Embedding batch size |
| `AZURE_UPLOAD_BATCH_SIZE` | `1000` | `1000` | Upload batch size |
| `AZURE_DI_MAX_CONCURRENCY` | `3` | `3` | DI parallel requests |
| `AZURE_OPENAI_MAX_CONCURRENCY` | `5` | `5` | OpenAI parallel requests |

---

### Logging

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | Console log level |
| `LOG_FILE_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `DEBUG` | File log level |
| `LOG_ARTIFACTS` | `true`, `false` | `true` | Write artifact logs |
| `LOG_USE_COLORS` | `true`, `false` | `true` | Colorful console |

---

## Validation & Troubleshooting

### Pre-Flight Validation

Always validate before running:

```bash
# Auto-detect scenario and validate
python -m ingestor.scenario_validator

# Validate specific scenario
python -m ingestor.scenario_validator offline

# Full validation with CLI
python -m ingestor.cli --validate
```

### Common Error Messages & Solutions

#### Error: "AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE is required"

**Cause:** Missing Azure Search configuration

**Solutions:**
1. **If using Azure Search:**
   ```bash
   AZURE_SEARCH_SERVICE=your-search-service
   AZURE_SEARCH_INDEX=your-index
   ```

2. **If using ChromaDB instead:**
   ```bash
   VECTOR_STORE_MODE=chromadb
   CHROMADB_COLLECTION_NAME=documents
   ```

---

#### Error: "AZURE_DOC_INT_ENDPOINT is required"

**Cause:** Document Intelligence required but not configured

**Solutions:**
1. **Use Azure Document Intelligence:**
   ```bash
   AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
   AZURE_DOC_INT_KEY=your-key
   ```

2. **Use offline processing instead:**
   ```bash
   AZURE_OFFICE_EXTRACTOR_MODE=markitdown
   # No AZURE_DOC_INT_ENDPOINT needed
   ```

---

#### Error: "AZURE_OPENAI_ENDPOINT is required"

**Cause:** Azure OpenAI required but not configured

**Solutions:**
1. **Use Azure OpenAI:**
   ```bash
   AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
   AZURE_OPENAI_KEY=your-key
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
   ```

2. **Use HuggingFace instead (local, free):**
   ```bash
   EMBEDDINGS_MODE=huggingface
   HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
   AZURE_USE_INTEGRATED_VECTORIZATION=false
   ```

3. **Use Cohere instead (cloud API):**
   ```bash
   EMBEDDINGS_MODE=cohere
   COHERE_API_KEY=your-cohere-key
   AZURE_USE_INTEGRATED_VECTORIZATION=false
   ```

---

#### Error: "AZURE_LOCAL_GLOB is required"

**Cause:** Local input mode but no file pattern specified

**Solution:**
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=documents/**/*.pdf

# Or use CLI override:
python -m ingestor.cli --glob "documents/**/*.pdf"
```

---

#### Error: "AZURE_BLOB_CONTAINER_IN is required"

**Cause:** Blob input mode but no container specified

**Solutions:**
1. **Simple approach (recommended):**
   ```bash
   AZURE_STORAGE_CONTAINER=documents
   # Auto-creates: documents-input, documents-pages, etc.
   ```

2. **Explicit approach:**
   ```bash
   AZURE_BLOB_CONTAINER_IN=documents-input
   ```

3. **IMPORTANT: Create input container first:**
   ```bash
   az storage container create \
     --name documents-input \
     --account-name your-storage-account
   ```

---

#### Warning: "AZURE_USE_INTEGRATED_VECTORIZATION must be 'false'"

**Cause:** Using non-Azure embeddings with integrated vectorization enabled

**Solution:**
```bash
# When using HuggingFace, Cohere, or OpenAI (non-Azure):
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

### Validation Checklist

Use this checklist to verify your configuration:

#### ✅ All Scenarios
- [ ] `.env` file exists in project root
- [ ] No syntax errors in `.env` (no spaces around `=`)
- [ ] Validated with: `python -m ingestor.scenario_validator`

#### ✅ Azure Search Scenarios
- [ ] `AZURE_SEARCH_SERVICE` or `AZURE_SEARCH_ENDPOINT` set
- [ ] `AZURE_SEARCH_INDEX` set
- [ ] `AZURE_SEARCH_KEY` set (or managed identity configured)

#### ✅ ChromaDB Scenarios
- [ ] `VECTOR_STORE_MODE=chromadb`
- [ ] Installed: `pip install chromadb`

#### ✅ HuggingFace Scenarios
- [ ] `EMBEDDINGS_MODE=huggingface`
- [ ] Installed: `pip install sentence-transformers`
- [ ] `AZURE_USE_INTEGRATED_VECTORIZATION=false`

#### ✅ Blob Input Scenarios
- [ ] `AZURE_STORAGE_ACCOUNT` set
- [ ] `AZURE_STORAGE_ACCOUNT_KEY` or `AZURE_CONNECTION_STRING` set
- [ ] Input container created: `az storage container create ...`
- [ ] Files uploaded to input container

#### ✅ Local Input Scenarios
- [ ] `AZURE_INPUT_MODE=local`
- [ ] `AZURE_LOCAL_GLOB` set or `--glob` provided
- [ ] Files exist at glob path

---

## Common Patterns

### Pattern 1: Switch from Azure to Local Dev

```bash
# Original (Azure):
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=azure_openai
AZURE_SEARCH_SERVICE=...
AZURE_OPENAI_ENDPOINT=...

# Switch to local:
VECTOR_STORE_MODE=chromadb
EMBEDDINGS_MODE=huggingface
CHROMADB_PERSIST_DIR=./chroma_dev
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

### Pattern 2: Reduce Costs (Keep Azure Search, Remove OpenAI)

```bash
# Keep Azure Search for storage:
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service

# Switch to local embeddings:
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda  # GPU acceleration

# Disable integrated vectorization:
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

### Pattern 3: Test Locally, Deploy to Azure

**Local (.env.local):**
```bash
VECTOR_STORE_MODE=chromadb
EMBEDDINGS_MODE=huggingface
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=test_data/*.pdf
```

**Production (.env.production):**
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=azure_openai
AZURE_INPUT_MODE=blob
AZURE_STORAGE_CONTAINER=documents
```

**Switch:**
```bash
# Development:
python -m ingestor.cli --env .env.local

# Production:
python -m ingestor.cli --env .env.production
```

---

## Need Help?

### Quick Links
- **Setup Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Scenario Templates:** [envs/](envs/)
- **Validation Tool:** `python -m ingestor.scenario_validator`
- **Pre-check:** `python -m ingestor.cli --validate`

### Get Support
1. Run validation: `python -m ingestor.scenario_validator`
2. Check error messages (they include solutions!)
3. Review scenario examples in `envs/` directory
4. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step setup

---

**Made with ❤️ for clarity and ease of use**
