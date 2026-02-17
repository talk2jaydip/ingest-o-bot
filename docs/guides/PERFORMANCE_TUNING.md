# Performance Tuning Guide

This guide covers performance optimization strategies, parallel processing configuration, and tuning for throughput and latency.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Optimization Strategies](#optimization-strategies)
4. [Configuration Tuning](#configuration-tuning)
5. [Performance Analysis](#performance-analysis)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The ingestor pipeline includes several performance optimizations that can significantly improve processing speed:

- **Parallel embedding batching** - 3-5x faster embedding generation
- **Parallel document processing** - Process multiple documents concurrently
- **Integrated vectorization** - Server-side embeddings for maximum speed
- **Intelligent retry logic** - 3 retries with exponential backoff
- **Concurrency control** - Semaphores prevent API overload

### Performance Improvements

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| Single 100-page PDF | 60-90s | 25-35s | 60-70% faster |
| 4 x 100-page PDFs | 4-6 min | 40-60s | 80-85% faster |
| 20 x 50-page PDFs | 15-20 min | 3-4 min | 75-80% faster |

---

## Quick Start

### 1. Enable Optimizations

Add these 4 lines to your `.env` file:

```bash
MAX_WORKERS=4
AZURE_OPENAI_MAX_CONCURRENCY=10
AZURE_DI_MAX_CONCURRENCY=5
USE_INTEGRATED_VECTORIZATION=true
```

### 2. Run Your Existing Code

No code changes needed - optimizations are automatic:

```python
from ingestor import run_pipeline

# Your existing code works unchanged
status = await run_pipeline(input_glob="docs/*.pdf")

# Now 50-85% faster!
```

### 3. Verify Performance

Check logs for parallel processing indicators:

```
✓ "Split into 10 batches for parallel processing"
✓ "Generated 150 embeddings using parallel batching"
✓ "Processing up to 4 documents in parallel"
```

---

## Optimization Strategies

### 1. Parallel Embedding Batching

**What it does:** Process all embedding batches concurrently instead of sequentially

**Configuration:**
```bash
AZURE_OPENAI_MAX_CONCURRENCY=10
```

**Impact:** 3-5x faster embedding generation

**How it works:**
```
BEFORE (Sequential):
[Batch 1] → [Batch 2] → [Batch 3] → [Batch 4] → ...
  5s         5s          5s          5s         = 20s total

AFTER (Parallel):
[Batch 1] ↘
[Batch 2] → [All process concurrently] → Done
[Batch 3] ↗
[Batch 4] ↗
              5s total (with 4 batches in parallel)
```

### 2. Parallel Document Processing

**What it does:** Process multiple documents concurrently

**Configuration:**
```bash
MAX_WORKERS=4
```

**Impact:** Nx faster for N documents (with max_workers=N)

**How it works:**
```
BEFORE (Sequential):
Doc1 → Doc2 → Doc3 → Doc4
60s    60s    60s    60s    = 240s total

AFTER (Parallel):
Doc1 ↘
Doc2 → [All process concurrently] → Done
Doc3 ↗
Doc4 ↗
       60s total (with 4 docs in parallel)
```

### 3. Integrated Vectorization

**What it does:** Generate embeddings on Azure Search server instead of client-side

**Configuration:**
```bash
USE_INTEGRATED_VECTORIZATION=true
```

**Impact:**
- Eliminates embedding generation time on client
- Reduces network transfer (no embedding vectors sent)
- Server-side optimization and caching

**Best for:**
- Large batch processing
- Network-constrained environments
- Maximum throughput

### 4. Intelligent Retry Logic

**What it does:** Automatically retry failed API calls with exponential backoff

**Built-in configuration:**
- Document Intelligence: 3 retries, 5-30s wait
- OpenAI Embeddings: 3 retries, 15-60s wait
- Exponential backoff prevents thundering herd

**Impact:** Graceful handling of transient failures and rate limits

---

## Configuration Tuning

### Profile: Maximum Performance

**For:** Production workloads with good Azure quota

```bash
# Aggressive parallelism
MAX_WORKERS=8
AZURE_OPENAI_MAX_CONCURRENCY=15
AZURE_DI_MAX_CONCURRENCY=8

# Server-side embeddings
USE_INTEGRATED_VECTORIZATION=true

# Optimized batch sizes
EMBEDDING_BATCH_SIZE=16
UPLOAD_BATCH_SIZE=1000
```

**Expected:** Maximum throughput, 80-85% faster

### Profile: Balanced

**For:** Most production workloads

```bash
# Moderate parallelism
MAX_WORKERS=4
AZURE_OPENAI_MAX_CONCURRENCY=10
AZURE_DI_MAX_CONCURRENCY=5

# Server-side embeddings
USE_INTEGRATED_VECTORIZATION=true

# Default batch sizes
EMBEDDING_BATCH_SIZE=16
UPLOAD_BATCH_SIZE=1000
```

**Expected:** Good performance, 75-80% faster, low risk

### Profile: Conservative

**For:** Testing, development, low quota

```bash
# Low parallelism
MAX_WORKERS=2
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_DI_MAX_CONCURRENCY=3

# Client-side embeddings
USE_INTEGRATED_VECTORIZATION=false

# Smaller batches
EMBEDDING_BATCH_SIZE=8
UPLOAD_BATCH_SIZE=500
```

**Expected:** Safe start, 50-60% faster, very low risk

### Profile: Single Large Document

**For:** Processing one large PDF (100+ pages)

```bash
# Single document
MAX_WORKERS=1

# High embedding concurrency
AZURE_OPENAI_MAX_CONCURRENCY=15
AZURE_DI_MAX_CONCURRENCY=5

# Server-side embeddings
USE_INTEGRATED_VECTORIZATION=true
```

**Expected:** Optimized for latency, 60-70% faster

### Profile: Batch Processing

**For:** Processing many documents

```bash
# High document parallelism
MAX_WORKERS=8

# Moderate embedding concurrency per doc
AZURE_OPENAI_MAX_CONCURRENCY=8
AZURE_DI_MAX_CONCURRENCY=5

# Server-side embeddings
USE_INTEGRATED_VECTORIZATION=true
```

**Expected:** Optimized for throughput, 80-85% faster

---

## Performance Analysis

### Bottleneck Identification

Use the performance analysis approach to identify bottlenecks:

#### 1. Measure Baseline

```python
import time

start = time.time()
status = await run_pipeline(
    input_glob="test.pdf",
    performance_max_workers=1,
    azure_openai_max_concurrency=1
)
baseline = time.time() - start
print(f"Baseline: {baseline:.2f}s")
```

#### 2. Test Embedding Parallelism

```python
start = time.time()
status = await run_pipeline(
    input_glob="test.pdf",
    performance_max_workers=1,
    azure_openai_max_concurrency=10  # Changed
)
parallel_embed = time.time() - start
print(f"With parallel embeddings: {parallel_embed:.2f}s")
print(f"Improvement: {(1 - parallel_embed/baseline) * 100:.1f}%")
```

#### 3. Test Document Parallelism

```python
start = time.time()
status = await run_pipeline(
    input_glob="docs/*.pdf",  # Multiple docs
    performance_max_workers=4,  # Changed
    azure_openai_max_concurrency=10
)
parallel_docs = time.time() - start
print(f"With parallel documents: {parallel_docs:.2f}s")
```

#### 4. Test Integrated Vectorization

```python
start = time.time()
status = await run_pipeline(
    input_glob="docs/*.pdf",
    performance_max_workers=4,
    azure_openai_max_concurrency=10,
    use_integrated_vectorization=True  # Changed
)
integrated = time.time() - start
print(f"With integrated vectorization: {integrated:.2f}s")
print(f"Total improvement: {(1 - integrated/baseline) * 100:.1f}%")
```

### Performance Metrics

Track these metrics for optimization:

```python
status = await run_pipeline(input_glob="docs/*.pdf")

# Overall metrics
print(f"Total documents: {status.total_documents}")
print(f"Successful: {status.successful_documents}")
print(f"Failed: {status.failed_documents}")
print(f"Success rate: {status.success_rate:.1%}")

# Throughput metrics
print(f"Total chunks: {status.total_chunks_indexed}")
print(f"Processing time: {total_time:.2f}s")
print(f"Throughput: {status.total_chunks_indexed / total_time:.2f} chunks/sec")

# Per-document metrics
for result in status.results:
    print(f"{result.filename}:")
    print(f"  Time: {result.processing_time_seconds:.2f}s")
    print(f"  Chunks: {result.chunks_indexed}")
    print(f"  Throughput: {result.chunks_indexed / result.processing_time_seconds:.2f} chunks/sec")
```

---

## Monitoring

### Healthy Performance

Look for these indicators in logs:

```
✓ "Split into 10 batches for parallel processing (max_concurrency=10)"
✓ "Generated 150 embeddings total using parallel batching"
✓ "Processing up to 4 documents in parallel"
✓ "Successfully processed doc1.pdf: 100 chunks in 35.2s"
```

**No retry messages = perfectly tuned concurrency**

### Warning Signs

Watch for these issues:

#### Rate Limiting

```
⚠️ "Rate limited on embeddings API (attempt 1/3), sleeping..."
⚠️ "Document Intelligence request failed (attempt 1/3), sleeping..."
```

**Action:** Reduce concurrency settings
```bash
AZURE_OPENAI_MAX_CONCURRENCY=5  # Down from 10
AZURE_DI_MAX_CONCURRENCY=3      # Down from 5
```

#### Memory Issues

```
⚠️ "MemoryError" or Python crashes
```

**Action:** Reduce parallel workers
```bash
MAX_WORKERS=2  # Down from 4
```

#### Slow Performance

```
✓ Processing completes but takes longer than expected
```

**Checklist:**
1. ✅ Check `USE_INTEGRATED_VECTORIZATION=true` is set
2. ✅ Verify concurrency settings are not too low
3. ✅ Check Azure quota limits
4. ✅ Review network latency to Azure services
5. ✅ Monitor retry messages in logs

---

## Troubleshooting

### Issue: No Performance Improvement

**Symptoms:** After enabling optimizations, performance is the same

**Diagnosis:**
1. Check logs for "parallel processing" messages
2. Verify environment variables are loaded
3. Test with known-working configuration

**Solution:**
```python
# Explicitly pass config to verify
status = await run_pipeline(
    input_glob="docs/*.pdf",
    performance_max_workers=4,
    azure_openai_max_concurrency=10,
    use_integrated_vectorization=True
)
```

### Issue: Frequent Rate Limiting

**Symptoms:** Many retry messages in logs

**Diagnosis:** Concurrency exceeds Azure quota

**Solution:** Gradually reduce concurrency until retries stop
```bash
# Start here
AZURE_OPENAI_MAX_CONCURRENCY=10
AZURE_DI_MAX_CONCURRENCY=5

# If rate limited, reduce to:
AZURE_OPENAI_MAX_CONCURRENCY=5
AZURE_DI_MAX_CONCURRENCY=3

# If still rate limited, reduce to:
AZURE_OPENAI_MAX_CONCURRENCY=3
AZURE_DI_MAX_CONCURRENCY=2
```

### Issue: Inconsistent Performance

**Symptoms:** Same workload has varying processing times

**Possible causes:**
1. Azure service throttling
2. Network latency variation
3. Document complexity variation
4. Resource contention on client

**Solution:**
- Run multiple tests and average results
- Monitor Azure service health
- Use consistent test documents

### Issue: Out of Memory

**Symptoms:** Python crashes during batch processing

**Solution:**
1. Reduce `MAX_WORKERS` (fewer concurrent documents)
2. Reduce batch sizes:
   ```bash
   EMBEDDING_BATCH_SIZE=8
   UPLOAD_BATCH_SIZE=500
   ```
3. Process documents in smaller batches

---

## Advanced Tuning

### Finding Optimal Settings

Use binary search to find optimal concurrency:

```python
# Test different concurrency levels
concurrency_levels = [3, 5, 8, 10, 15, 20]

results = {}
for concurrency in concurrency_levels:
    start = time.time()
    status = await run_pipeline(
        input_glob="test.pdf",
        azure_openai_max_concurrency=concurrency
    )
    elapsed = time.time() - start
    results[concurrency] = elapsed
    print(f"Concurrency {concurrency}: {elapsed:.2f}s")

# Find optimal (minimum time before rate limiting)
optimal = min(results, key=results.get)
print(f"Optimal concurrency: {optimal}")
```

### Environment-Specific Tuning

Different Azure environments may have different limits:

```python
# Load environment-specific config
import os
from dotenv import load_dotenv

environment = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{environment}")

# Environments have different performance profiles
# - Development: Conservative settings
# - Staging: Moderate settings
# - Production: Aggressive settings
```

---

## Related Documentation

- [Batch Processing Guide](BATCH_PROCESSING.md) - Batch processing features
- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Environment Variables](../reference/12_ENVIRONMENT_VARIABLES.md) - All environment variables

---

## Test Scripts

Verify performance optimizations:

```bash
# Quick test (30 seconds)
python examples/scripts/test_parallel_quick.py

# Full performance tests (5 minutes)
python examples/scripts/test_parallel_performance.py
```

---

**Last Updated**: 2026-02-07
