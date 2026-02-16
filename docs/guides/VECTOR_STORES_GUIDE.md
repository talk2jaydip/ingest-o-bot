# Vector Stores Guide

This guide covers all supported vector database implementations in the ingest-o-bot pipeline.

## Overview

The pipeline supports multiple vector databases through a pluggable architecture:

- **Azure AI Search** - Microsoft's cloud search service with integrated vectorization
- **ChromaDB** - Open-source embedding database with local and remote options
- **More coming** - Pinecone, Weaviate, Qdrant (planned)

## Azure AI Search

### Features
- ✅ Cloud-based, fully managed
- ✅ Integrated vectorization (server-side embeddings)
- ✅ Hybrid search (vector + keyword + semantic)
- ✅ Enterprise features (security, compliance, SLA)
- ✅ Automatic scaling

### Configuration

**Environment Variables:**
```bash
VECTOR_STORE_MODE=azure_search  # Optional, auto-detected
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-admin-key
AZURE_SEARCH_INDEX=your-index-name
```

Or:
```bash
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX=your-index-name
AZURE_SEARCH_KEY=your-admin-key
```

**Programmatic Configuration:**
```python
from ingestor import ConfigBuilder

config = (
    ConfigBuilder()
    .with_local_files("docs/*.pdf")
    .with_azure_search(
        service_name="my-search",
        index_name="documents",
        api_key="your-key"
    )
    .with_azure_openai(...)
    .build()
)
```

### When to Use
- ✅ Need enterprise features and SLA
- ✅ Want managed service (no infrastructure management)
- ✅ Need hybrid search (vector + keyword)
- ✅ Want integrated vectorization (server-side embeddings)
- ❌ Need fully offline solution
- ❌ Have strict data residency requirements

---

## ChromaDB

### Features
- ✅ Open-source, self-hosted
- ✅ Three deployment modes (persistent, in-memory, client/server)
- ✅ Fully offline capable
- ✅ No API costs
- ✅ Fast local development
- ❌ No integrated vectorization (requires client-side embeddings)
- ❌ Limited enterprise features

### Deployment Modes

#### 1. Persistent Local Storage

Stores data on disk for persistence between runs.

**Environment Variables:**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=documents
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_BATCH_SIZE=1000  # Optional
```

**Use Case:**
- Local development and testing
- Production deployments on single machine
- Air-gapped environments

**Example:**
```python
from ingestor import ConfigBuilder

config = (
    ConfigBuilder()
    .with_local_files("documents/*.pdf")
    .with_chromadb(
        collection_name="my-docs",
        persist_directory="./vector_db"
    )
    .with_huggingface_embeddings(
        model_name="intfloat/multilingual-e5-large",
        device="cpu"
    )
    .build()
)
```

#### 2. In-Memory (Ephemeral)

Stores data in memory only. Data is lost when process ends.

**Environment Variables:**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=temp-docs
# No CHROMADB_PERSIST_DIR = in-memory mode
```

**Use Case:**
- Quick testing and experimentation
- CI/CD pipelines
- Temporary data processing

**Example:**
```python
config = (
    ConfigBuilder()
    .with_local_files("test/*.pdf")
    .with_chromadb(collection_name="temp-test")  # No persist_directory
    .with_huggingface_embeddings(...)
    .build()
)
```

#### 3. Client/Server Mode

Connects to a remote ChromaDB server.

**Environment Variables:**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_COLLECTION_NAME=shared-docs
CHROMADB_HOST=chromadb.example.com
CHROMADB_PORT=8000
CHROMADB_AUTH_TOKEN=secret-token  # Optional
```

**Use Case:**
- Shared development environments
- Multiple clients accessing same data
- Distributed systems

**Example:**
```python
config = (
    ConfigBuilder()
    .with_local_files("docs/*.pdf")
    .with_chromadb(
        collection_name="shared-collection",
        host="chromadb.example.com",
        port=8000
    )
    .with_cohere_embeddings(api_key="...")
    .build()
)
```

### Installation

```bash
pip install -r requirements-chromadb.txt
```

Or:
```bash
pip install chromadb
```

### When to Use ChromaDB
- ✅ Need fully offline solution
- ✅ Want to avoid cloud API costs
- ✅ Developing locally
- ✅ Need simple setup and deployment
- ✅ Data must stay on-premises
- ❌ Need integrated vectorization
- ❌ Need advanced search features (hybrid search)
- ❌ Need enterprise SLA

---

## Comparison Table

| Feature | Azure AI Search | ChromaDB |
|---------|----------------|----------|
| **Deployment** | Cloud (managed) | Local or self-hosted |
| **Integrated Vectorization** | ✅ Yes | ❌ No (client-side required) |
| **Offline Capable** | ❌ No | ✅ Yes |
| **Hybrid Search** | ✅ Yes | ❌ No |
| **Scaling** | Automatic | Manual |
| **Setup Complexity** | Medium | Low |
| **Cost** | Pay per use | Free (infrastructure only) |
| **Enterprise Features** | ✅ Full | Limited |
| **Data Residency** | Azure regions | Your control |

---

## Migration Between Vector Stores

### From Azure Search to ChromaDB

**Before:**
```bash
AZURE_SEARCH_SERVICE=my-service
AZURE_SEARCH_INDEX=docs
AZURE_SEARCH_KEY=key
```

**After:**
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_COLLECTION_NAME=docs
```

Note: You'll need to re-index all documents as data formats differ.

### From ChromaDB to Azure Search

**Before:**
```bash
CHROMADB_PERSIST_DIR=./chroma_db
```

**After:**
```bash
VECTOR_STORE_MODE=azure_search
AZURE_SEARCH_SERVICE=my-service
AZURE_SEARCH_INDEX=docs
```

---

## Dynamic Chunking Support

All vector stores now work seamlessly with **dynamic chunking** that automatically adjusts chunk sizes based on your embedding model's token limit.

### How It Works

1. Pipeline queries embedding provider's `max_seq_length`
2. Chunker automatically adjusts limits if needed
3. Prevents truncation and information loss
4. Works with any vector store + embedding provider combination

### Benefits

- ✅ No manual configuration needed
- ✅ Prevents silent data loss from truncation
- ✅ Maintains semantic overlap between chunks
- ✅ Works with any embedding model (Azure OpenAI, Hugging Face, Cohere, OpenAI)

### Example

```bash
# ChromaDB + Small Hugging Face model (256 tokens)
VECTOR_STORE_MODE=chromadb
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=all-MiniLM-L6-v2  # max_seq_length = 256

# Initial chunking config
CHUNKING_MAX_TOKENS=500

# Pipeline automatically adjusts to:
# → 192 tokens (safe limit with 15% buffer + 10% overlap)

# Note: Default model (jina-embeddings-v2-base-en) has 8192 token limit,
# so no adjustment needed for most chunking configurations
```

See the [Embeddings Providers Guide](embeddings_providers.md#dynamic-chunking-feature) for full details.

---

## Troubleshooting

### ChromaDB: "chromadb is required"

**Error:**
```
ImportError: chromadb is required for ChromaDB vector store.
```

**Solution:**
```bash
pip install chromadb
```

### ChromaDB: "Dimensions not yet inferred"

**Error:**
```
ValueError: Dimensions not yet inferred. Upload documents first.
```

**Cause:** Trying to get dimensions before uploading any documents.

**Solution:** Ensure embeddings are generated and documents are uploaded before calling `get_dimensions()`.

### Azure Search: Integrated vectorization with ChromaDB

**Error:**
```
ValueError: ChromaDB requires client-side embeddings.
```

**Cause:** `use_integrated_vectorization=True` is set but ChromaDB doesn't support it.

**Solution:**
```bash
AZURE_USE_INTEGRATED_VECTORIZATION=false  # or omit entirely
```

---

## Performance Tuning

### ChromaDB Batch Size

Control upload batch size:
```bash
CHROMADB_BATCH_SIZE=1000  # Default
```

Recommendations:
- Small documents (<1KB): Use 1000-2000
- Large documents (>10KB): Use 100-500
- Limited memory: Reduce batch size

### Azure Search Concurrency

Control concurrent batch uploads:
```bash
AZURE_SEARCH_MAX_CONCURRENCY=5  # Default
```

Recommendations:
- More concurrency = faster uploads but more API pressure
- Default (5) works well for most cases
- Reduce if hitting rate limits

---

## Next Steps

- [Embeddings Providers Guide](embeddings_providers.md) - Choose your embedding model
- [Configuration Examples](configuration_examples.md) - See all combinations
- [Examples](../examples/) - Ready-to-run scripts
