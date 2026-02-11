# Configuration Examples

This guide provides ready-to-use configuration examples for all supported combinations of vector stores and embeddings providers.

## Quick Reference

| Scenario | Vector Store | Embeddings | Offline | Cost |
|----------|--------------|------------|---------|------|
| [Production Cloud](#1-production-cloud-azure--azure) | Azure Search | Azure OpenAI | ❌ | $$$ |
| [Offline Development](#2-offline-development-chromadb--hugging-face) | ChromaDB | Hugging Face | ✅ | Free |
| [Multilingual](#3-multilingual-chromadb--hugging-face-multilingual) | ChromaDB | HF Multilingual | ✅ | Free |
| [Hybrid Cloud/Local](#4-hybrid-cloudlocal-azure--hugging-face) | Azure Search | Hugging Face | ❌ | $$ |
| [Cost Optimized](#5-cost-optimized-chromadb--cohere) | ChromaDB | Cohere | ❌ | $ |
| [Simple Cloud](#6-simple-cloud-azure--cohere) | Azure Search | Cohere | ❌ | $$$ |

---

## 1. Production Cloud (Azure + Azure)

**Best for:** Enterprise deployments with SLA requirements

**Features:**
- ✅ Enterprise SLA and compliance
- ✅ Integrated vectorization (server-side embeddings)
- ✅ Fully managed services
- ✅ Automatic scaling

### Environment Variables

```bash
# Vector Store: Azure AI Search
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=production-docs
AZURE_SEARCH_KEY=your-admin-key

# Embeddings: Azure OpenAI
EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Optional: Use integrated vectorization (server-side embeddings)
AZURE_USE_INTEGRATED_VECTORIZATION=true

# Input/Output
INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=yourstorage
AZURE_STORAGE_KEY=your-key
AZURE_STORAGE_CONTAINER=documents

ARTIFACTS_MODE=blob
AZURE_ARTIFACTS_CONTAINER=artifacts
```

### Cost Estimate
- Azure Search: ~$250-500/month (standard tier)
- Azure OpenAI: ~$0.10 per 1M tokens
- Azure Storage: ~$20/month (1TB)
- **Total: ~$300-600/month**

---

## 2. Offline Development (ChromaDB + Hugging Face)

**Best for:** Local development, air-gapped environments

**Features:**
- ✅ Fully offline, no internet required
- ✅ Zero API costs
- ✅ Fast local development
- ✅ Complete data privacy

### Environment Variables

```bash
# Vector Store: ChromaDB (persistent)
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=dev-documents
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_BATCH_SIZE=1000

# Embeddings: Hugging Face (local model)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_DEVICE=cpu
HUGGINGFACE_BATCH_SIZE=32

# Input/Output (local files)
INPUT_MODE=local
LOCAL_INPUT_GLOB=./documents/**/*.pdf

ARTIFACTS_MODE=local
LOCAL_ARTIFACTS_DIR=./artifacts

# Document Intelligence: Use offline mode
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
```

### Installation

```bash
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt
```

### Cost Estimate
- **Total: $0/month** (compute costs only)

---

## 3. Multilingual (ChromaDB + Hugging Face Multilingual)

**Best for:** Multi-language documents, international content

**Features:**
- ✅ 100+ languages supported
- ✅ SOTA multilingual model
- ✅ Fully offline
- ✅ GPU acceleration support

### Environment Variables

```bash
# Vector Store: ChromaDB
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=multilingual-docs
CHROMADB_PERSIST_DIR=./vector_db

# Embeddings: Hugging Face (multilingual model)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda  # or cpu, mps
HUGGINGFACE_BATCH_SIZE=64  # Increase for GPU
HUGGINGFACE_NORMALIZE=true

# Input
INPUT_MODE=local
LOCAL_INPUT_GLOB=./multilingual_docs/**/*.pdf

ARTIFACTS_MODE=local
```

### GPU Acceleration

**NVIDIA GPU (CUDA):**
```bash
HUGGINGFACE_DEVICE=cuda
HUGGINGFACE_BATCH_SIZE=64  # 5-10x faster
```

**Apple Silicon (M1/M2/M3):**
```bash
HUGGINGFACE_DEVICE=mps
HUGGINGFACE_BATCH_SIZE=48  # 3-5x faster
```

### Model Size
- multilingual-e5-large: ~2.2GB
- First run downloads model, subsequent runs use cache

### Cost Estimate
- **Total: $0/month** (GPU compute costs if using cloud GPU)

---

## 4. Hybrid Cloud/Local (Azure + Hugging Face)

**Best for:** Azure infrastructure with local embeddings

**Features:**
- ✅ Azure Search for storage/search
- ✅ Local embeddings (no embedding API costs)
- ✅ GPU-accelerated embeddings
- ✅ Best multilingual quality

### Environment Variables

```bash
# Vector Store: Azure AI Search
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_INDEX=hybrid-docs
AZURE_SEARCH_KEY=your-key

# Embeddings: Hugging Face (local)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda
HUGGINGFACE_BATCH_SIZE=64

# Important: Disable integrated vectorization
AZURE_USE_INTEGRATED_VECTORIZATION=false

# Input/Output
INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=yourstorage
AZURE_STORAGE_KEY=your-key
```

### Cost Estimate
- Azure Search: ~$250-500/month
- Azure Storage: ~$20/month
- Embeddings: $0 (local)
- **Total: ~$270-520/month** (save on embedding costs)

---

## 5. Cost Optimized (ChromaDB + Cohere)

**Best for:** Budget-conscious deployments with good quality

**Features:**
- ✅ Low storage costs (local)
- ✅ Competitive embedding costs
- ✅ Good multilingual support
- ✅ Simple setup

### Environment Variables

```bash
# Vector Store: ChromaDB
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=cost-optimized
CHROMADB_PERSIST_DIR=./chroma_db

# Embeddings: Cohere (API)
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-key
COHERE_MODEL_NAME=embed-multilingual-light-v3.0  # Faster, cheaper
COHERE_INPUT_TYPE=search_document

# Input
INPUT_MODE=local
LOCAL_INPUT_GLOB=./documents/**/*.pdf

ARTIFACTS_MODE=local
```

### Installation

```bash
pip install -r requirements-chromadb.txt
pip install cohere
```

### Cost Estimate
- ChromaDB: $0
- Cohere: ~$0.10 per 1M tokens
- **Total: ~$10-50/month** (depending on volume)

---

## 6. Simple Cloud (Azure + Cohere)

**Best for:** Azure infrastructure with Cohere embeddings

**Features:**
- ✅ Azure Search for storage
- ✅ Cohere for embeddings
- ✅ Good multilingual support
- ✅ Competitive pricing

### Environment Variables

```bash
# Vector Store: Azure AI Search
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-search
AZURE_SEARCH_INDEX=cohere-docs
AZURE_SEARCH_KEY=your-key

# Embeddings: Cohere
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-key
COHERE_MODEL_NAME=embed-multilingual-v3.0

# Important: Disable integrated vectorization
AZURE_USE_INTEGRATED_VECTORIZATION=false

# Input/Output
INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=yourstorage
```

### Cost Estimate
- Azure Search: ~$250-500/month
- Cohere: ~$50-100/month
- **Total: ~$300-600/month**

---

## 7. OpenAI Native (ChromaDB + OpenAI)

**Best for:** Prefer native OpenAI over Azure

**Features:**
- ✅ Latest OpenAI models
- ✅ Simple setup
- ✅ Local vector storage

### Environment Variables

```bash
# Vector Store: ChromaDB
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=openai-docs
CHROMADB_PERSIST_DIR=./chroma_db

# Embeddings: OpenAI (native API)
EMBEDDINGS_MODE=openai
OPENAI_API_KEY=your-openai-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536

# Input
INPUT_MODE=local
```

### Cost Estimate
- ChromaDB: $0
- OpenAI: ~$0.02 per 1M tokens
- **Total: ~$20-100/month**

---

## 8. Testing/CI (ChromaDB In-Memory + Hugging Face)

**Best for:** CI/CD pipelines, temporary testing

**Features:**
- ✅ Ephemeral storage (data lost on exit)
- ✅ Fast setup
- ✅ Zero persistence overhead

### Environment Variables

```bash
# Vector Store: ChromaDB (in-memory)
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=test-docs
# No CHROMADB_PERSIST_DIR = in-memory mode

# Embeddings: Hugging Face
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=all-MiniLM-L6-v2
HUGGINGFACE_DEVICE=cpu
HUGGINGFACE_BATCH_SIZE=32

# Input
INPUT_MODE=local
LOCAL_INPUT_GLOB=./test_data/*.pdf
```

---

## Advanced: Mixed Cloud Providers

### Azure Search + OpenAI (non-Azure)

```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=...

EMBEDDINGS_MODE=openai
OPENAI_API_KEY=...
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

### ChromaDB Client/Server + Cohere

```bash
# ChromaDB server running remotely
VECTOR_STORE_MODE=chromadb
CHROMADB_HOST=chromadb.example.com
CHROMADB_PORT=8000
CHROMADB_COLLECTION_NAME=shared-docs

EMBEDDINGS_MODE=cohere
COHERE_API_KEY=...
```

---

## Common Configuration Patterns

### Retry and Concurrency

```bash
# Azure OpenAI
AZURE_OPENAI_MAX_RETRIES=3
AZURE_OPENAI_MAX_CONCURRENCY=5

# OpenAI
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=60

# ChromaDB
CHROMADB_BATCH_SIZE=1000

# Azure Search
AZURE_SEARCH_MAX_CONCURRENCY=5
```

### Document Processing

```bash
# Processing mode (all documents)
AZURE_OFFICE_EXTRACTOR_MODE=hybrid  # or azure_di, markitdown

# Chunking
AZURE_CHUNKING_MAX_CHARS=2000
AZURE_CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_OVERLAP_PERCENT=10

# Media description
AZURE_MEDIA_DESCRIBER=gpt4o  # or content_understanding, disabled
```

---

## Troubleshooting

### Can't connect to vector store

**Azure Search:**
```bash
# Check endpoint
curl https://your-search.search.windows.net

# Verify key has admin permissions
```

**ChromaDB:**
```bash
# Check if persistent directory exists and is writable
ls -la ./chroma_db

# For client/server mode, verify server is running
curl http://chromadb.example.com:8000/api/v1/heartbeat
```

### Embedding generation fails

**Check dependencies:**
```bash
# Hugging Face
pip list | grep sentence-transformers

# Cohere
pip list | grep cohere

# OpenAI
pip list | grep openai
```

### Dimension mismatch

Delete vector store and re-index:
```bash
# ChromaDB
rm -rf ./chroma_db/*

# Azure Search
# Use Azure Portal to delete and recreate index
```

---

## Next Steps

- [Vector Stores Guide](vector_stores.md) - Detailed vector store documentation
- [Embeddings Guide](embeddings_providers.md) - Detailed embeddings documentation
- [Examples](../examples/) - Ready-to-run example scripts
