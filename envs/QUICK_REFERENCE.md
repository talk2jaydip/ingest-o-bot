# Environment Configuration Quick Reference

**Looking for complete scenarios? See [SCENARIOS_GUIDE.md](SCENARIOS_GUIDE.md)**

This is a quick reference card for common configuration patterns and parameter combinations.

---

## 🎯 Choose Your Path

```
Need offline/air-gapped? ───────────────▶ .env.offline
Processing 100K+ pages/month? ──────────▶ .env.scenario-cost-optimized.example
Multiple languages (100+)? ─────────────▶ .env.scenario-multilingual.example
Just testing/development? ──────────────▶ .env.scenario-development.example
Want simplest Azure setup? ─────────────▶ .env.scenario-azure-openai-default.example
Need cloud but not Azure OpenAI? ───────▶ .env.scenario-azure-cohere.example
```

---

## 📋 Common Configuration Patterns

### Pattern 1: Fully Offline (Zero Cost)
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
INPUT_MODE=local  # or: AZURE_INPUT_MODE
LOCAL_INPUT_GLOB=data/**/*.pdf  # or: AZURE_LOCAL_GLOB
EXTRACTION_MODE=markitdown
MEDIA_DESCRIBER_MODE=disabled
```

### Pattern 2: Azure + Local Embeddings (Cost-Optimized)
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda  # GPU
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

### Pattern 3: Full Azure Stack (Enterprise)
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service
EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_USE_INTEGRATED_VECTORIZATION=false  # or true
```

### Pattern 4: Azure + Cohere (Multilingual Cloud)
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-key
COHERE_MODEL_NAME=embed-multilingual-v3.0
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

## 🔧 Key Parameters by Category

### Vector Store Configuration

**Azure AI Search:**
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=your-service-name
AZURE_SEARCH_KEY=your-admin-key
AZURE_SEARCH_INDEX=your-index-name
```

**ChromaDB (Persistent):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=documents
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_BATCH_SIZE=100
```

**ChromaDB (In-Memory):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=temp-docs
# No CHROMADB_PERSIST_DIR = in-memory
```

**ChromaDB (Client/Server):**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
CHROMADB_AUTH_TOKEN=your-token
CHROMADB_COLLECTION_NAME=documents
```

### Embedding Provider Configuration

**Azure OpenAI:**
```bash
EMBEDDINGS_MODE=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536  # Optional, for text-embedding-3-*
# Optional: Vision/GPT-4o for image descriptions
AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o
AZURE_OPENAI_VISION_MODEL=gpt-4o
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_OPENAI_MAX_RETRIES=3
```

**Hugging Face (CPU):**
```bash
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
HUGGINGFACE_DEVICE=cpu
HUGGINGFACE_BATCH_SIZE=32
HUGGINGFACE_NORMALIZE=true
```

**Hugging Face (GPU - NVIDIA):**
```bash
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda
HUGGINGFACE_BATCH_SIZE=64
HUGGINGFACE_NORMALIZE=true
```

**Hugging Face (Apple Silicon):**
```bash
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
HUGGINGFACE_DEVICE=mps
HUGGINGFACE_BATCH_SIZE=48
HUGGINGFACE_NORMALIZE=true
```

**Cohere API:**
```bash
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-key
COHERE_MODEL_NAME=embed-multilingual-v3.0
COHERE_INPUT_TYPE=search_document
COHERE_TRUNCATE=END
```

### Input/Output Configuration

**Local Input + Local Artifacts:**
```bash
# New parameter names (preferred)
INPUT_MODE=local
LOCAL_INPUT_GLOB=data/**/*.pdf
LOCAL_ARTIFACTS_DIR=./artifacts

# Legacy parameter names (still supported for backward compatibility)
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=data/**/*.pdf
AZURE_ARTIFACTS_DIR=./artifacts
```

**Blob Input + Blob Artifacts:**
```bash
INPUT_MODE=blob  # or: AZURE_INPUT_MODE
AZURE_STORAGE_ACCOUNT=your-account
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_BLOB_CONTAINER_PREFIX=project
ARTIFACTS_MODE=blob  # or: AZURE_ARTIFACTS_MODE
```

**Local Input + Blob Artifacts:**
```bash
INPUT_MODE=local  # or: AZURE_INPUT_MODE
LOCAL_INPUT_GLOB=data/**/*.pdf  # or: AZURE_LOCAL_GLOB
ARTIFACTS_MODE=blob  # or: AZURE_ARTIFACTS_MODE
AZURE_STORAGE_ACCOUNT=your-account
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_BLOB_CONTAINER_PREFIX=project
```

### Document Processing Configuration

**Azure DI (Best Quality):**
```bash
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-key
EXTRACTION_MODE=hybrid  # azure_di, markitdown, or hybrid
AZURE_DI_MAX_CONCURRENCY=3
```

**MarkItDown Only (Offline):**
```bash
EXTRACTION_MODE=markitdown
# Optional: LibreOffice for DOC files
AZURE_OFFICE_LIBREOFFICE_PATH=/usr/bin/soffice
```

**Media Descriptions:**
```bash
# Enabled (costs extra)
AZURE_MEDIA_DESCRIBER=gpt4o
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini

# Disabled (free)
AZURE_MEDIA_DESCRIBER=disabled
```

### Chunking Configuration

**Conservative (Small Model):**
```bash
CHUNKING_MAX_TOKENS=192  # For 256-token models
CHUNKING_MAX_CHARS=1000
CHUNKING_OVERLAP_PERCENT=10
```

**Balanced (Medium Model):**
```bash
CHUNKING_MAX_TOKENS=384  # For 512-token models
CHUNKING_MAX_CHARS=2000
CHUNKING_OVERLAP_PERCENT=10
```

**Generous (Large Model):**
```bash
CHUNKING_MAX_TOKENS=1000  # For 8192-token models
CHUNKING_MAX_CHARS=5000
CHUNKING_OVERLAP_PERCENT=10
```

---

## 🎨 Embedding Model Recommendations

### English-Only Documents

**Fastest (Low Memory):**
```bash
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
# 384 dims, 256 tokens, ~90MB
CHUNKING_MAX_TOKENS=192
```

**Balanced (Good Quality):**
```bash
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
# 768 dims, 384 tokens, ~420MB
CHUNKING_MAX_TOKENS=288
```

**Best Quality:**
```bash
HUGGINGFACE_MODEL_NAME=BAAI/bge-large-en-v1.5
# 1024 dims, 512 tokens, ~1.3GB
CHUNKING_MAX_TOKENS=384
```

### Multilingual Documents (100+ Languages)

**Lightweight:**
```bash
HUGGINGFACE_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# 384 dims, 128 tokens, ~470MB
CHUNKING_MAX_TOKENS=96
```

**Balanced:**
```bash
HUGGINGFACE_MODEL_NAME=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
# 768 dims, 384 tokens, ~1GB
CHUNKING_MAX_TOKENS=288
```

**Best Quality (Recommended):**
```bash
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
# 1024 dims, 512 tokens, ~2.2GB
CHUNKING_MAX_TOKENS=384
```

**Best for CJK (Chinese/Japanese/Korean):**
```bash
HUGGINGFACE_MODEL_NAME=BAAI/bge-m3
# 1024 dims, 8192 tokens, ~2.2GB
CHUNKING_MAX_TOKENS=6000
```

---

## 💰 Cost Optimization Strategies

### Strategy 1: Zero-Cost Setup
- ✅ Use ChromaDB (not Azure Search)
- ✅ Use Hugging Face embeddings (not Azure OpenAI)
- ✅ Use MarkItDown (not Azure DI)
- ✅ Disable media descriptions
- ✅ Local file storage (not blob)
- **Result: $0/month**

### Strategy 2: Minimize Azure Costs
- ✅ Use Azure Search (need enterprise features)
- ✅ Use Hugging Face embeddings (not Azure OpenAI)
- ✅ Use Azure DI for quality
- ⚠️ Disable media descriptions OR use gpt-4o-mini
- ✅ Use blob storage sparingly
- **Result: $280-700/month (vs $380-950)**
- **Savings: 26-50%**

### Strategy 3: High-Volume Optimization
- ✅ Local Hugging Face embeddings (GPU)
- ✅ Azure Search for infrastructure
- ✅ Process 1M+ pages/month
- **Traditional cost: $1,500+/month**
- **Optimized cost: $280-700/month**
- **Savings: $800-1,200/month**

---

## ⚡ Performance Tuning

### CPU-Optimized
```bash
HUGGINGFACE_DEVICE=cpu
HUGGINGFACE_BATCH_SIZE=16
AZURE_CHUNKING_MAX_WORKERS=2
AZURE_CHUNKING_MAX_IMAGE_CONCURRENCY=4
```

### GPU-Optimized (NVIDIA)
```bash
HUGGINGFACE_DEVICE=cuda
HUGGINGFACE_BATCH_SIZE=64
AZURE_CHUNKING_MAX_WORKERS=4
AZURE_CHUNKING_MAX_IMAGE_CONCURRENCY=8
AZURE_EMBED_BATCH_SIZE=128
```

### Apple Silicon (M1/M2/M3)
```bash
HUGGINGFACE_DEVICE=mps
HUGGINGFACE_BATCH_SIZE=48
AZURE_CHUNKING_MAX_WORKERS=4
```

### Low Memory Systems
```bash
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_DEVICE=cpu
HUGGINGFACE_BATCH_SIZE=8
AZURE_CHUNKING_MAX_WORKERS=1
CHUNKING_MAX_TOKENS=192
```

---

## 🔍 Troubleshooting Quick Fixes

### "CUDA out of memory"
```bash
# Reduce batch size
HUGGINGFACE_BATCH_SIZE=16  # or 8

# Or switch to CPU
HUGGINGFACE_DEVICE=cpu
```

### "Chunking limits reduced" warning
```bash
# This is normal! Pipeline auto-adjusts for model limits
# To eliminate warning, set lower limits:
CHUNKING_MAX_TOKENS=288  # Adjust based on your model
```

### Slow processing on CPU
```bash
# Use faster model
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Or enable GPU
HUGGINGFACE_DEVICE=cuda  # or mps for Apple
```

### Azure quota exceeded
```bash
# Reduce concurrency
AZURE_DI_MAX_CONCURRENCY=1
AZURE_OPENAI_MAX_CONCURRENCY=2
AZURE_CHUNKING_MAX_WORKERS=2
```

### ChromaDB connection refused
```bash
# For persistent mode, ensure directory exists
mkdir -p ./chroma_db

# For client/server mode, check host/port
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
```

---

## 📦 Required Dependencies by Scenario

### Azure Full Stack
```bash
pip install -r requirements.txt
```

### Offline/ChromaDB
```bash
pip install -r requirements.txt
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt
```

### Cohere
```bash
pip install -r requirements.txt
pip install cohere
```

### All Features
```bash
pip install -r requirements.txt
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt
pip install cohere
```

---

## 🖥️ CLI Quick Commands

### Validation & Index Management
```bash
# Validate configuration (pre-check before processing)
python -m ingestor.cli --validate

# Check if index exists
python -m ingestor.cli --check-index

# Deploy/update index only (no ingestion)
python -m ingestor.cli --index-only

# Setup index and process documents
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# Force recreate index (WARNING: destroys data)
python -m ingestor.cli --force-index

# Delete index
python -m ingestor.cli --delete-index
```

### Processing Documents
```bash
# Process documents with glob pattern
python -m ingestor.cli --glob "documents/**/*.pdf"

# Process single file
python -m ingestor.cli --pdf "document.pdf"

# Use specific environment file
python -m ingestor.cli --env .env.chromadb --glob "documents/*.pdf"

# Remove specific documents from index
python -m ingestor.cli --action remove --glob "old_doc.pdf"

# Remove ALL documents (WARNING: clears index)
python -m ingestor.cli --action removeall
```

### Options
```bash
# Verbose logging
python -m ingestor.cli --verbose --glob "documents/*.pdf"

# No colors (for CI/CD)
python -m ingestor.cli --no-colors --glob "documents/*.pdf"

# Skip ingestion (only run index operations)
python -m ingestor.cli --setup-index --skip-ingestion

# Clean artifacts for specific files
python -m ingestor.cli --clean-artifacts --glob "document.pdf"
```

---

## 🚀 One-Line Setups

### Quick Test (Offline)
```bash
cp .env.offline .env && mkdir -p data && python -m ingestor.cli
```

### Development
```bash
cp envs/.env.scenario-development.example .env && mkdir -p data/test && python -m ingestor.cli
```

### Production Azure
```bash
cp envs/.env.scenario-azure-openai-default.example .env && python -m ingestor.cli --setup-index && python -m ingestor.cli
```

### Cost-Optimized
```bash
cp envs/.env.scenario-cost-optimized.example .env && python -m ingestor.cli --setup-index && python -m ingestor.cli
```

---

## 📚 More Information

- **[Complete Scenarios Guide](SCENARIOS_GUIDE.md)** - Detailed scenarios with examples
- **[Configuration Flags Guide](CONFIGURATION_FLAGS_GUIDE.md)** - All parameters explained
- **[Environment Variables Reference](../docs/reference/12_ENVIRONMENT_VARIABLES.md)** - Complete reference
- **[Vector Stores Guide](../docs/vector_stores.md)** - Vector database details
- **[Embeddings Providers Guide](../docs/embeddings_providers.md)** - Embedding provider details

---

**Last Updated:** 2024-02-11
