# Batch Processing Guide

This guide covers parallel document processing, batch configuration, and performance optimization for processing multiple documents efficiently.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Features](#features)
5. [Examples](#examples)
6. [Performance](#performance)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The ingestor pipeline supports full batch processing with parallel execution for maximum throughput. You can process multiple documents concurrently and parallelize embedding generation within each document.

### Key Capabilities

- **Parallel document processing** - Process N documents concurrently with `max_workers`
- **Parallel embedding batching** - 3-5x faster embeddings with concurrent batch processing
- **Environment-based configuration** - Configure via `.env` files for different environments
- **Per-document tracking** - Individual success/failure tracking for each document
- **Error handling** - Graceful failure with retry logic (3 retries, exponential backoff)
- **Progress monitoring** - Real-time batch progress and performance metrics

---

## Quick Start

### 1. Update Configuration

Add these settings to your `.env` file:

```bash
# Parallel document processing
AZURE_MAX_WORKERS=4

# Parallel embedding batches
AZURE_OPENAI_MAX_CONCURRENCY=10

# Document Intelligence concurrency
AZURE_DI_MAX_CONCURRENCY=5

# Server-side embeddings (recommended for best performance)
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

### 2. Process a Batch

```python
from ingestor import run_pipeline

# Process multiple documents in parallel
status = await run_pipeline(input_glob="documents/**/*.pdf")

print(f"✅ Processed {status.successful_documents} documents")
print(f"📦 Total chunks: {status.total_chunks_indexed}")
```

### 3. Monitor Results

```python
# Check per-document results
for result in status.results:
    icon = "✅" if result.success else "❌"
    print(f"{icon} {result.filename}: {result.processing_time_seconds:.2f}s")
```

---

## Configuration

### Environment Variables

Configure batch processing via environment variables:

```bash
# === Parallel Processing ===
AZURE_MAX_WORKERS=4                          # Number of documents to process concurrently
AZURE_OPENAI_MAX_CONCURRENCY=10              # Parallel embedding batch requests
AZURE_DI_MAX_CONCURRENCY=5                   # Parallel Document Intelligence requests

# === Performance Optimization ===
AZURE_USE_INTEGRATED_VECTORIZATION=true      # Use server-side embeddings (fastest)
AZURE_EMBED_BATCH_SIZE=16                    # Embeddings per batch
AZURE_UPLOAD_BATCH_SIZE=1000                 # Documents per upload batch

# === Input Configuration ===
AZURE_INPUT_MODE=local                       # Input source: 'local' or 'blob'
AZURE_LOCAL_GLOB=documents/**/*.pdf          # Glob pattern for local files

# === Output Configuration ===
AZURE_ARTIFACTS_MODE=blob                    # Store artifacts: 'blob' or 'local'
AZURE_BLOB_CONTAINER_OUT=artifacts           # Output container name
```

See [Configuration Guide](CONFIGURATION.md) for complete reference.

### Configuration Profiles

Create different `.env` files for different scenarios:

**Development (.env.development):**
```bash
AZURE_MAX_WORKERS=2
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_DI_MAX_CONCURRENCY=3
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

**Production (.env.production):**
```bash
AZURE_MAX_WORKERS=8
AZURE_OPENAI_MAX_CONCURRENCY=15
AZURE_DI_MAX_CONCURRENCY=8
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

**Load specific environment:**
```python
from dotenv import load_dotenv
from ingestor import PipelineConfig

# Load production config
load_dotenv(".env.production")
config = PipelineConfig.from_env()
```

---

## Features

### 1. Parallel Document Processing

Process multiple documents concurrently:

```python
from ingestor import run_pipeline

status = await run_pipeline(
    input_glob="documents/**/*.pdf",
    performance_max_workers=4           # Process 4 documents at once
)
```

**Impact**: Process 4 documents in the time it takes to process 1

### 2. Parallel Embedding Batching

Embedding batches process concurrently within each document:

```python
status = await run_pipeline(
    input_glob="large_document.pdf",
    azure_openai_max_concurrency=10     # 10 embedding batches in parallel
)
```

**Impact**: 3-5x faster embedding generation

### 3. Per-Document Results

Track individual document success/failure:

```python
status = await run_pipeline(input_glob="docs/*.pdf")

for result in status.results:
    print(f"{result.filename}: {result.processing_time_seconds:.2f}s")
    print(f"  Chunks: {result.chunks_indexed}")
    if not result.success:
        print(f"  Error: {result.error_message}")
```

### 4. Error Handling

Graceful failure handling with retry logic:

```python
status = await run_pipeline(input_glob="documents/**/*.pdf")

# Handle failures
if status.failed_documents > 0:
    print(f"⚠️ {status.failed_documents} documents failed")

    # Retry failed documents with conservative settings
    failed_files = [r.filename for r in status.results if not r.success]
    for file in failed_files:
        retry_status = await run_pipeline(
            input_glob=file,
            performance_max_workers=1,
            azure_openai_max_concurrency=3
        )
```

### 5. Progress Monitoring

Real-time batch progress tracking:

```python
import time

start = time.time()
status = await run_pipeline(
    input_glob="documents/**/*.pdf",
    performance_max_workers=4
)
elapsed = time.time() - start

print(f"\n📊 Batch Processing Results:")
print(f"Total time: {elapsed:.2f}s")
print(f"Documents: {status.successful_documents}/{status.total_documents}")
print(f"Success rate: {status.success_rate:.1%}")
print(f"Avg time per doc: {elapsed / status.successful_documents:.2f}s")
print(f"Throughput: {status.total_chunks_indexed / elapsed:.2f} chunks/sec")
```

---

## Examples

### Example 1: Simple Batch Processing

```python
from ingestor import run_pipeline

# Process all PDFs in a directory
status = await run_pipeline(input_glob="documents/**/*.pdf")

print(f"✅ Processed {status.successful_documents} documents")
print(f"❌ Failed {status.failed_documents} documents")
```

### Example 2: Optimized Batch Processing

```python
from ingestor import run_pipeline

# Optimized for maximum throughput
status = await run_pipeline(
    input_glob="documents/**/*.pdf",

    # Parallel processing
    performance_max_workers=4,

    # High concurrency
    azure_openai_max_concurrency=10,
    azure_di_max_concurrency=5,

    # Server-side embeddings (fastest)
    use_integrated_vectorization=True
)

print(f"🚀 Processed {status.successful_documents} docs with optimizations")
```

### Example 3: Environment-Based Configuration

```python
from dotenv import load_dotenv
from ingestor import PipelineConfig, Pipeline

# Load configuration from .env
load_dotenv()
config = PipelineConfig.from_env()

# Process batch
pipeline = Pipeline(config)
try:
    status = await pipeline.run()
    print(f"✅ Batch complete: {status.successful_documents} docs")
finally:
    await pipeline.close()
```

### Example 4: Multiple Environments

```python
from dotenv import load_dotenv
from ingestor import PipelineConfig

# Switch between environments
env_file = ".env.production" if is_production else ".env.development"
load_dotenv(env_file)

config = PipelineConfig.from_env()
# ... use config
```

### Example 5: Performance Comparison

```python
import time

configs = [
    {"name": "Sequential", "max_workers": 1, "concurrency": 1},
    {"name": "Parallel", "max_workers": 4, "concurrency": 10}
]

for config in configs:
    start = time.time()
    status = await run_pipeline(
        input_glob="docs/*.pdf",
        performance_max_workers=config["max_workers"],
        azure_openai_max_concurrency=config["concurrency"]
    )
    elapsed = time.time() - start
    print(f"{config['name']}: {elapsed:.2f}s ({status.successful_documents} docs)")
```

---

## Performance

### Performance Numbers

#### Single Document (100-page PDF)

| Configuration | Time | Improvement |
|---------------|------|-------------|
| Default (sequential) | 60-90s | Baseline |
| With parallel batching | 30-40s | 50-60% faster |
| With integrated vectorization | 25-35s | 60-70% faster |

#### Batch (4 x 100-page PDFs)

| Configuration | Time | Improvement |
|---------------|------|-------------|
| Sequential | 4-6 minutes | Baseline |
| Parallel (max_workers=4) | 60-90 seconds | 75-80% faster |
| Parallel + integrated vectorization | 40-60 seconds | 80-85% faster |

#### Batch (20 x 50-page PDFs)

| Configuration | Time |
|---------------|------|
| Sequential | 15-20 minutes |
| Parallel (max_workers=4) | 4-6 minutes |
| Parallel + integrated vectorization | 3-4 minutes |

### Recommended Settings

**For Single Large PDF (Optimize Latency):**
```bash
AZURE_MAX_WORKERS=1                     # Single document
AZURE_OPENAI_MAX_CONCURRENCY=10         # High parallelism for batches
AZURE_DI_MAX_CONCURRENCY=5
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

**For Multiple PDFs (Optimize Throughput):**
```bash
AZURE_MAX_WORKERS=4                     # Process 4 documents concurrently
AZURE_OPENAI_MAX_CONCURRENCY=10
AZURE_DI_MAX_CONCURRENCY=5
AZURE_USE_INTEGRATED_VECTORIZATION=true
```

**Conservative (Safe Start):**
```bash
AZURE_MAX_WORKERS=2
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_DI_MAX_CONCURRENCY=3
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

## Troubleshooting

### Rate Limiting

**Symptoms:**
```
⚠️ Rate limited on embeddings API (attempt 1/3), sleeping...
```

**Solution:** Reduce concurrency settings
```bash
AZURE_OPENAI_MAX_CONCURRENCY=5          # Down from 10
AZURE_DI_MAX_CONCURRENCY=3              # Down from 5
```

### Out of Memory

**Symptoms:** Python crashes or memory errors during batch processing

**Solution:** Reduce parallel workers
```bash
AZURE_MAX_WORKERS=2                     # Down from 4
```

### Slow Performance

**Symptoms:** Batch processing not seeing expected speedup

**Checklist:**
1. ✅ Enable integrated vectorization: `AZURE_USE_INTEGRATED_VECTORIZATION=true`
2. ✅ Increase concurrency: `AZURE_OPENAI_MAX_CONCURRENCY=10`
3. ✅ Check Azure quota limits
4. ✅ Monitor logs for retry messages (indicates rate limiting)

### Monitoring Performance

**Healthy logs:**
```
✓ "Split into 10 batches for parallel processing (max_concurrency=10)"
✓ "Generated 150 embeddings total using parallel batching"
✓ "Processing up to 4 documents in parallel"
✓ "Successfully processed doc1.pdf: 100 chunks in 35.2s"
```

**Warning signs:**
```
⚠️ "Rate limited on embeddings API (attempt 1/3), sleeping..."
⚠️ "Document Intelligence request failed (attempt 1/3), sleeping..."
```

---

## Related Documentation

- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Quick Start Guide](QUICKSTART.md) - Getting started
- [Performance Tuning Guide](PERFORMANCE_TUNING.md) - Advanced optimization
- [Environment Variables](../reference/12_ENVIRONMENT_VARIABLES.md) - All environment variables

---

## Jupyter Notebooks

Interactive examples in the notebooks:

1. **[01_quickstart.ipynb](../../examples/notebooks/01_quickstart.ipynb)** - Basic batch processing
2. **[08_batch_processing.ipynb](../../examples/notebooks/08_batch_processing.ipynb)** - Complete batch guide

---

**Last Updated**: 2026-02-07
