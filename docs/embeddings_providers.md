# Embeddings Providers Guide

This guide covers all supported embedding model providers in the ingest-o-bot pipeline.

## Overview

The pipeline supports multiple embedding providers through a pluggable architecture:

- **Azure OpenAI** - Microsoft's Azure-hosted OpenAI models (default)
- **Hugging Face** - Local models via sentence-transformers (multilingual)
- **Cohere** - Cohere's v3 API models (multilingual, 100+ languages)
- **OpenAI** - Native OpenAI API (non-Azure)

---

## Azure OpenAI

### Features
- ✅ Enterprise-grade API with SLA
- ✅ Data stays in Azure region
- ✅ Supports integrated vectorization (server-side)
- ✅ Latest embedding models (text-embedding-3)
- ✅ Custom dimensions for v3 models

### Supported Models
- `text-embedding-ada-002` - 1536 dims (default)
- `text-embedding-3-small` - 1536 dims (customizable)
- `text-embedding-3-large` - 3072 dims (customizable)

### Configuration

**Environment Variables:**
```bash
EMBEDDINGS_MODE=azure_openai  # Optional, auto-detected
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536  # Optional for v3 models
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_OPENAI_MAX_RETRIES=3
```

**Programmatic:**
```python
from ingestor import ConfigBuilder

config = (
    ConfigBuilder()
    .with_azure_openai(
        endpoint="https://your-openai.openai.azure.com/",
        api_key="your-key",
        embedding_deployment="text-embedding-ada-002",
        embedding_model="text-embedding-ada-002"
    )
    .build()
)
```

### When to Use
- ✅ Need enterprise SLA and compliance
- ✅ Already using Azure infrastructure
- ✅ Want integrated vectorization with Azure Search
- ✅ Need consistent performance and uptime
- ❌ Need fully offline solution
- ❌ Want to minimize costs

---

## Hugging Face (sentence-transformers)

### Features
- ✅ Fully offline, local execution
- ✅ No API costs
- ✅ Latest multilingual models
- ✅ GPU acceleration support
- ✅ Wide model selection
- ❌ Requires local compute resources
- ❌ No integrated vectorization support

### Supported Models

#### English Models
| Model | Dimensions | Size | Speed | Quality |
|-------|-----------|------|-------|---------|
| `all-MiniLM-L6-v2` | 384 | 90MB | ⚡⚡⚡ Fast | ⭐⭐⭐ Good |
| `all-mpnet-base-v2` | 768 | 420MB | ⚡⚡ Medium | ⭐⭐⭐⭐ Better |
| `BAAI/bge-large-en-v1.5` | 1024 | 1.3GB | ⚡ Slower | ⭐⭐⭐⭐⭐ Best |

#### Multilingual Models (100+ languages)
| Model | Dimensions | Size | Speed | Quality |
|-------|-----------|------|-------|---------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 470MB | ⚡⚡⚡ Fast | ⭐⭐⭐ Good |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | 1GB | ⚡⚡ Medium | ⭐⭐⭐⭐ Better |
| `intfloat/multilingual-e5-large` | 1024 | 2.2GB | ⚡ Slower | ⭐⭐⭐⭐⭐ Best |

### Configuration

**Environment Variables:**
```bash
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cpu  # or cuda, mps
HUGGINGFACE_BATCH_SIZE=32
HUGGINGFACE_NORMALIZE=true
```

**Programmatic:**
```python
config = (
    ConfigBuilder()
    .with_huggingface_embeddings(
        model_name="intfloat/multilingual-e5-large",
        device="cuda",  # GPU acceleration
        batch_size=32
    )
    .build()
)
```

### Installation

```bash
pip install -r requirements-embeddings.txt
```

Or:
```bash
pip install sentence-transformers torch
```

### Device Selection

**CPU:**
```bash
HUGGINGFACE_DEVICE=cpu
```
- Works on any machine
- Slower but consistent
- No GPU required

**CUDA (NVIDIA GPU):**
```bash
HUGGINGFACE_DEVICE=cuda
```
- Requires NVIDIA GPU
- 5-10x faster than CPU
- Requires CUDA toolkit

**MPS (Apple Silicon):**
```bash
HUGGINGFACE_DEVICE=mps
```
- For M1/M2/M3 Macs
- 3-5x faster than CPU
- Automatic on Apple Silicon

### Model Caching

Models are automatically downloaded and cached in:
```
~/.cache/huggingface/hub/
```

First run downloads the model (~1-2GB), subsequent runs are instant.

### When to Use Hugging Face
- ✅ Need fully offline solution
- ✅ Want to avoid API costs
- ✅ Need multilingual support
- ✅ Have GPU available for acceleration
- ✅ Can handle model storage (~1-2GB per model)
- ❌ Need integrated vectorization
- ❌ Have limited disk space
- ❌ Need guaranteed performance SLA

---

## Cohere

### Features
- ✅ Latest v3 multilingual models
- ✅ 100+ languages supported
- ✅ Optimized for semantic search
- ✅ Simple API, good documentation
- ✅ Competitive pricing
- ❌ Cloud-based (API calls)
- ❌ No integrated vectorization

### Supported Models

| Model | Dimensions | Languages | Speed | Cost |
|-------|-----------|-----------|-------|------|
| `embed-english-v3.0` | 1024 | English | ⚡⚡⚡ Fast | $ |
| `embed-multilingual-v3.0` | 1024 | 100+ | ⚡⚡⚡ Fast | $ |
| `embed-english-light-v3.0` | 384 | English | ⚡⚡⚡⚡ Faster | $ |
| `embed-multilingual-light-v3.0` | 384 | 100+ | ⚡⚡⚡⚡ Faster | $ |

### Configuration

**Environment Variables:**
```bash
EMBEDDINGS_MODE=cohere
COHERE_API_KEY=your-cohere-api-key
COHERE_MODEL_NAME=embed-multilingual-v3.0
COHERE_INPUT_TYPE=search_document  # or search_query
COHERE_TRUNCATE=END
```

**Programmatic:**
```python
config = (
    ConfigBuilder()
    .with_cohere_embeddings(
        api_key="your-key",
        model_name="embed-multilingual-v3.0"
    )
    .build()
)
```

### Installation

```bash
pip install cohere
```

### API Limits
- Up to 96 texts per API request
- Automatic batching handled internally
- Rate limits: Contact Cohere for details

### When to Use Cohere
- ✅ Need multilingual support (100+ languages)
- ✅ Want simple API with good docs
- ✅ Need competitive pricing
- ✅ Want optimized semantic search
- ❌ Need fully offline solution
- ❌ Already have Azure infrastructure

---

## OpenAI (Native API)

### Features
- ✅ Native OpenAI API (non-Azure)
- ✅ Latest embedding models
- ✅ Custom dimensions for v3 models
- ✅ Simple setup
- ❌ Cloud-based (API calls)
- ❌ No integrated vectorization

### Supported Models

| Model | Dimensions | Quality | Cost |
|-------|-----------|---------|------|
| `text-embedding-ada-002` | 1536 | ⭐⭐⭐⭐ Good | $$ |
| `text-embedding-3-small` | 1536* | ⭐⭐⭐⭐ Good | $ |
| `text-embedding-3-large` | 3072* | ⭐⭐⭐⭐⭐ Best | $$$ |

*Customizable dimensions for v3 models

### Configuration

**Environment Variables:**
```bash
EMBEDDINGS_MODE=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536  # Optional for v3
OPENAI_MAX_RETRIES=3
```

**Programmatic:**
```python
config = (
    ConfigBuilder()
    .with_openai_embeddings(
        api_key="your-key",
        model_name="text-embedding-3-large",
        dimensions=1024  # Reduce dimensions for efficiency
    )
    .build()
)
```

### Installation

Already included in base requirements (openai package).

### When to Use OpenAI
- ✅ Prefer native OpenAI over Azure
- ✅ Want latest models quickly
- ✅ Simple setup without Azure
- ❌ Need enterprise compliance (use Azure OpenAI)
- ❌ Need fully offline solution

---

## Comparison Table

| Provider | Offline | Languages | API Cost | Setup | SLA |
|----------|---------|-----------|----------|-------|-----|
| **Azure OpenAI** | ❌ | English++ | $$$ | Medium | ✅ Yes |
| **Hugging Face** | ✅ | 100+ | Free | Easy | ❌ No |
| **Cohere** | ❌ | 100+ | $$ | Easy | ✅ Yes |
| **OpenAI** | ❌ | English++ | $$-$$$ | Easy | ✅ Yes |

### Dimension Comparison

| Provider | Min Dims | Max Dims | Customizable |
|----------|----------|----------|--------------|
| Azure OpenAI | 1536 | 3072 | v3 only |
| Hugging Face | 384 | 1024+ | Per model |
| Cohere | 384 | 1024 | No |
| OpenAI | 1536 | 3072 | v3 only |

---

## Recommended Combinations

### Best for Production (Cloud)
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=azure_openai
```
- Enterprise SLA
- Integrated vectorization
- Scalable and managed

### Best for Development (Offline)
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=all-MiniLM-L6-v2
HUGGINGFACE_DEVICE=cpu
```
- Fully offline
- No API costs
- Fast setup

### Best for Multilingual (Cloud + Local Hybrid)
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=intfloat/multilingual-e5-large
HUGGINGFACE_DEVICE=cuda
```
- Best multilingual quality
- GPU-accelerated embeddings
- Azure Search for storage

### Best for Cost Optimization
```bash
VECTOR_STORE_MODE=chromadb
CHROMADB_PERSIST_DIR=./chroma_db
EMBEDDINGS_MODE=huggingface
HUGGINGFACE_MODEL_NAME=all-MiniLM-L6-v2
```
- Zero API costs
- Local storage
- Good quality

---

## Performance Tuning

### Batch Size Optimization

**Azure OpenAI:**
- Default: Auto (based on token limits)
- Don't change unless needed

**Hugging Face:**
```bash
HUGGINGFACE_BATCH_SIZE=32  # Default
```
- CPU: Use 8-32
- GPU: Use 64-128
- Limited RAM: Use 8-16

**Cohere:**
- Automatic (96 texts per request)
- No configuration needed

### Concurrency

**Azure OpenAI:**
```bash
AZURE_OPENAI_MAX_CONCURRENCY=5  # Default
```
- Increase for faster processing
- Watch for rate limits

**Hugging Face:**
- Single-threaded by default
- Uses async executor for non-blocking

---

## Troubleshooting

### Hugging Face: Model Download Fails

**Error:**
```
Unable to download model from HuggingFace Hub
```

**Solutions:**
1. Check internet connection
2. Verify model name is correct
3. Check HuggingFace Hub status
4. Try different mirror: `export HF_ENDPOINT=https://hf-mirror.com`

### Cohere: API Key Invalid

**Error:**
```
ValueError: COHERE_API_KEY environment variable required
```

**Solution:**
Get API key from https://dashboard.cohere.com/api-keys

### Dimension Mismatch

**Error:**
```
Vector dimensions don't match (expected 1536, got 768)
```

**Cause:** Changing embedding model without recreating vector store.

**Solution:**
1. Delete existing vector store data
2. Re-index all documents with new model

---

## Next Steps

- [Vector Stores Guide](vector_stores.md) - Choose your vector database
- [Configuration Examples](configuration_examples.md) - See all combinations
- [Examples](../examples/) - Ready-to-run scripts
