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
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_OPENAI_MAX_RETRIES=3

# Optional: Vision for image descriptions
AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o
AZURE_OPENAI_VISION_MODEL=gpt-4o
MEDIA_DESCRIBER_MODE=gpt4o

# Document Extraction
EXTRACTION_MODE=azure_di  # or: hybrid, markitdown
AZURE_DOC_INT_ENDPOINT=https://your-di.cognitiveservices.azure.com/
AZURE_DOC_INT_KEY=your-key
AZURE_DI_MAX_CONCURRENCY=5

# Input/Output (supports both new and legacy names)
INPUT_MODE=blob  # or: AZURE_INPUT_MODE
AZURE_STORAGE_ACCOUNT=yourstorage
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_BLOB_CONTAINER_PREFIX=production

ARTIFACTS_MODE=blob  # or: AZURE_ARTIFACTS_MODE
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
HUGGINGFACE_MODEL_NAME=jinaai/jina-embeddings-v2-base-en  # Default: 768 dims, 8192 tokens
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
HUGGINGFACE_MODEL_NAME=jinaai/jina-embeddings-v2-base-en
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

---

## 9. Dynamic Chunking with Small Models (256 tokens)

**Best for:** Models with very small token limits (e.g., some distilled models)

**Features:**
- ✅ Automatic chunk size adjustment
- ✅ Prevents truncation and information loss
- ✅ Buffer calculation (15% safety + overlap allowance)
- ✅ Warning messages when limits are adjusted

### Environment Variables

```bash
# Vector Store: ChromaDB
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_COLLECTION_NAME=small-model-docs

# Embeddings: Custom small model
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=sentence-transformers/paraphrase-MiniLM-L3-v2
HUGGINGFACE_DEVICE=cpu

# Chunking: Will auto-adjust based on model's max_seq_length (256 tokens)
# Initial values will be reduced if they exceed model limits
CHUNKING_MAX_TOKENS=500
CHUNKING_MAX_CHARS=2000
CHUNKING_OVERLAP_PERCENT=10

# Alternative: Explicitly set EMBEDDINGS_MAX_SEQ_LENGTH as fallback
# EMBEDDINGS_MAX_SEQ_LENGTH=256
```

### What Happens

When the pipeline starts, you'll see:

```
⚠️  Embedding model max_seq_length (256) is smaller than CHUNKING_MAX_SECTION_TOKENS (750).
    Automatically reducing chunking limit to 187 tokens
    (with 15% buffer and 10% overlap allowance) to prevent truncation.
```

The chunker automatically calculates safe limits:
- **Safety buffer**: 15% (to account for tokenization differences)
- **Overlap allowance**: 10% (from CHUNKING_OVERLAP_PERCENT)
- **Safe limit**: 256 * (1 - 0.15 - 0.10) = 192 tokens

### Benefits
- No manual calculation needed
- Prevents silent truncation
- Maintains overlap for semantic continuity
- Works with any embedding model

---

## 10. Hybrid Mode (Azure Media + Local Embeddings)

**Best for:** Using Azure Document Intelligence for extraction but local embeddings for cost savings

**Features:**
- ✅ Azure Document Intelligence for high-quality PDF extraction
- ✅ Azure Blob Storage for input/artifacts
- ✅ Local Hugging Face embeddings (zero embedding cost)
- ✅ ChromaDB for local vector storage
- ✅ Dynamic chunking based on model limits

### Environment Variables

```bash
# Vector Store: ChromaDB (local)
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_COLLECTION_NAME=hybrid-docs

# Embeddings: Hugging Face (local, free)
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda
HUGGINGFACE_BATCH_SIZE=64

# Azure Document Intelligence (for extraction only)
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-di.cognitiveservices.azure.com
DOCUMENTINTELLIGENCE_KEY=your-key

# Azure Blob Storage (for input/output)
INPUT_MODE=blob
AZURE_STORAGE_ACCOUNT=yourstorage
AZURE_STORAGE_KEY=your-key
AZURE_STORAGE_CONTAINER=documents

ARTIFACTS_MODE=blob
AZURE_ARTIFACTS_CONTAINER=artifacts

# Chunking: Generic parameter names (no "AZURE_" prefix needed)
CHUNKING_MAX_TOKENS=500
CHUNKING_MAX_CHARS=2000
CHUNKING_OVERLAP_PERCENT=10

# Or use Azure-prefixed names (still supported for backward compatibility)
# AZURE_CHUNKING_MAX_TOKENS=500
# AZURE_CHUNKING_MAX_CHARS=2000
# AZURE_CHUNKING_OVERLAP_PERCENT=10

# Processing
AZURE_OFFICE_EXTRACTOR_MODE=azure_di
AZURE_MEDIA_DESCRIBER=disabled
```

### Cost Estimate
- Azure Document Intelligence: ~$10-50/month (per 1K pages)
- Azure Blob Storage: ~$20/month (1TB)
- Hugging Face embeddings: $0 (local)
- ChromaDB: $0 (local)
- **Total: ~$30-70/month** (vs. $1,300+ with Azure OpenAI embeddings)

---

## Dynamic Chunking Feature

All configurations now support **dynamic chunking** that automatically adjusts chunk sizes based on your embedding model's token limit.

### How It Works

1. **Model Detection**: Pipeline queries the embedding provider's `max_seq_length`
2. **Buffer Calculation**: Applies 15% safety buffer + overlap allowance
3. **Auto-Adjustment**: Reduces chunk limits if they exceed safe thresholds
4. **Warning Messages**: Logs adjustments for transparency

### Environment Variable Fallback

If your embedding provider doesn't report `max_seq_length`, you can set it manually:

```bash
EMBEDDINGS_MAX_SEQ_LENGTH=512  # For models with 512 token limit
```

### Generic vs Azure-Prefixed Parameters

Both parameter styles are supported:

**Generic (recommended for new configs):**
```bash
CHUNKING_MAX_TOKENS=500
CHUNKING_MAX_CHARS=2000
CHUNKING_OVERLAP_PERCENT=10
```

**Azure-prefixed (backward compatibility):**
```bash
AZURE_CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_MAX_CHARS=2000
AZURE_CHUNKING_OVERLAP_PERCENT=10
```

### Example Warning Message

```
⚠️  Embedding model max_seq_length (384) is smaller than CHUNKING_MAX_SECTION_TOKENS (750).
    Automatically reducing chunking limit to 281 tokens
    (with 15% buffer and 10% overlap allowance) to prevent truncation.
```

This means:
- Your model supports max 384 tokens
- Your chunking config requested 750 tokens
- System automatically reduced to 281 tokens (safe limit)
- Calculation: 384 * (1 - 0.15 - 0.10) = 288 tokens (rounded down)

---

## Using the --env Flag

The CLI now supports `--env` flag to easily test different configurations:

```bash
# Test offline configuration
ingestor --env envs/.env.chromadb.example --glob "documents/*.pdf"

# Test Cohere configuration
ingestor --env envs/.env.cohere.example --glob "documents/*.pdf"

# Test hybrid configuration
ingestor --env envs/.env.hybrid.example --glob "documents/*.pdf"

# Default (uses .env in current directory)
ingestor --glob "documents/*.pdf"
```

This makes it easy to:
- Test different vector stores without changing your main .env
- Compare embedding providers side-by-side
- Switch between cloud and offline modes
- Validate configurations before deployment

---

## Plugin System

### Creating Custom Vector Store Plugin

Extend Ingestor with custom vector stores:

```python
from ingestor.plugin_registry import register_vector_store
from ingestor.vector_store import VectorStore
from ingestor.config import PipelineConfig

@register_vector_store("my_custom_db")
class MyCustomVectorStore(VectorStore):
    """Custom vector store implementation."""

    def __init__(self, config: PipelineConfig, **kwargs):
        super().__init__(config, **kwargs)
        # Initialize your custom database
        self.client = initialize_my_db()

    async def upload_chunks(self, chunks: list) -> dict:
        """Upload document chunks to your vector store."""
        # Implement upload logic
        for chunk in chunks:
            await self.client.insert(
                id=chunk['id'],
                vector=chunk['embedding'],
                metadata=chunk
            )
        return {"uploaded": len(chunks)}

    async def close(self):
        """Clean up resources."""
        await self.client.disconnect()
```

**Configuration:**
```bash
VECTOR_STORE_MODE=my_custom_db
```

### Creating Custom Embeddings Provider Plugin

Extend Ingestor with custom embedding models:

```python
from ingestor.plugin_registry import register_embeddings_provider
from ingestor.embeddings_provider import EmbeddingsProvider
from ingestor.config import PipelineConfig

@register_embeddings_provider("my_custom_embeddings")
class MyCustomEmbeddings(EmbeddingsProvider):
    """Custom embeddings implementation."""

    def __init__(self, config: PipelineConfig, **kwargs):
        super().__init__(config, **kwargs)
        # Initialize your model
        self.model = load_my_model()

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for input texts."""
        # Implement embedding generation
        embeddings = []
        for text in texts:
            embedding = await self.model.encode(text)
            embeddings.append(embedding.tolist())
        return embeddings

    @property
    def embedding_dimensions(self) -> int:
        """Return embedding vector dimensions."""
        return 768

    @property
    def max_sequence_length(self) -> int:
        """Return max input tokens."""
        return 512
```

**Configuration:**
```bash
EMBEDDINGS_MODE=my_custom_embeddings
```

### Loading Plugins

Plugins are automatically discovered if placed in the `ingestor/` directory or can be manually registered:

```python
from ingestor.plugin_registry import discover_plugins

# Auto-discover plugins in specified directory
discover_plugins("path/to/plugins")

# Or manually import and register
from my_plugins import MyCustomVectorStore, MyCustomEmbeddings
# Registration happens via decorators
```

---

## CLI Validation and Management

### Pre-Check Validation

Validate your configuration before processing:

```bash
# Run full validation check
python -m ingestor.cli --validate

# Output:
# ✅ [Input Source (Local)] Found 12 file(s) matching pattern
# ✅ [Artifacts Storage (Local)] Directory writable
# ✅ [Document Intelligence] Client configured
# ✅ [Azure OpenAI (Embeddings)] Client configured
# ✅ [Azure AI Search] Index accessible (0 documents)
# Summary: 5 passed, 0 failed
```

### Index Management

```bash
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

### Document Operations

```bash
# Process with verbose logging
python -m ingestor.cli --verbose --glob "documents/*.pdf"

# Process without colors (CI/CD)
python -m ingestor.cli --no-colors --glob "documents/*.pdf"

# Remove specific documents
python -m ingestor.cli --action remove --glob "old_doc.pdf"

# Remove all documents (WARNING: clears index)
python -m ingestor.cli --action removeall

# Clean artifacts
python -m ingestor.cli --clean-artifacts --glob "document.pdf"
```

---

## Next Steps

- [Vector Stores Guide](vector_stores.md) - Detailed vector store documentation
- [Embeddings Guide](embeddings_providers.md) - Detailed embeddings documentation
- [Examples](../examples/) - Ready-to-run example scripts
