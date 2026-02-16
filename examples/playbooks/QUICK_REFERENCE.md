# Playbooks Quick Reference Card

One-page quick reference for all playbooks.

## At a Glance

| # | Playbook | Level | Time | Cost | Best For |
|---|----------|-------|------|------|----------|
| 01 | Basic PDF Ingestion | Beginner | 10-30s/PDF | $ or FREE | Learning, simple workflows |
| 02 | Multi-Stage Pipeline | Intermediate | Varies | $ or FREE | Different doc types |
| 03 | Error Handling | Advanced | Varies | $ or FREE | Production reliability |
| 04 | Local Development | Beginner | 5-15s/PDF | FREE | Development, testing |
| 05 | Production Deploy | Advanced | 10-30s/PDF | $$$ | Enterprise production |

## Quick Start

```bash
# 1. Choose playbook
cd examples/playbooks

# 2. Copy environment config
cp .env.basic-pdf.example ../../.env

# 3. Edit credentials
nano ../../.env

# 4. Run playbook
python 01_basic_pdf_ingestion.py
```

## When to Use What

### I want to...

| Goal | Use This |
|------|----------|
| Learn the basics | 01 |
| Test locally for FREE | 04 |
| Process tech docs, legal docs, papers separately | 02 |
| Handle failures gracefully | 03 |
| Deploy to production | 05 |

### My situation is...

| Situation | Use This |
|-----------|----------|
| First time using library | 01 or 04 |
| Developing a feature | 04 |
| Testing before prod | 01 + 03 |
| Running in production | 05 |
| Have problematic docs | 03 |
| Multiple doc types | 02 |

## Environment Configurations

### Offline (FREE)
```bash
VECTOR_STORE_MODE=chromadb
EMBEDDINGS_MODE=huggingface
CHROMADB_PERSIST_DIR=./chroma_db
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
INPUT_MODE=local
ARTIFACTS_MODE=local
```

### Cloud (Azure)
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=azure_openai
AZURE_SEARCH_SERVICE=your-service
AZURE_SEARCH_KEY=your-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_KEY=your-key
INPUT_MODE=blob
ARTIFACTS_MODE=blob
```

### Hybrid (Cost-Optimized)
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=huggingface
AZURE_SEARCH_SERVICE=your-service
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

## Key Features by Playbook

### 01: Basic PDF Ingestion
- ✅ Step-by-step workflow
- ✅ Both cloud and offline support
- ✅ Clear error messages
- ✅ Beginner-friendly

### 02: Multi-Stage Pipeline
- ✅ Type-specific optimization
- ✅ Separate processing stages
- ✅ Aggregate reporting
- ✅ Performance metrics

### 03: Error Handling & Recovery
- ✅ Automatic retry (exponential backoff)
- ✅ Checkpoint every 10 docs
- ✅ Resume from failure
- ✅ Error classification
- ✅ Detailed reports

### 04: Local Development
- ✅ 100% offline
- ✅ FREE (no cloud costs)
- ✅ Artifact inspection
- ✅ Fast iteration
- ✅ Debugging tools

### 05: Production Deployment
- ✅ Readiness checks
- ✅ Production metrics
- ✅ Error alerting
- ✅ Cost tracking
- ✅ Enterprise features

## Common Commands

```bash
# Run a playbook
python 01_basic_pdf_ingestion.py

# With custom .env file
ENV_FILE=.env.custom python 01_basic_pdf_ingestion.py

# Resume from checkpoint (playbook 03)
python 03_error_handling_recovery.py

# Check Python version
python --version  # Requires 3.10+

# Install dependencies
pip install -r ../../requirements.txt
pip install -r ../../requirements-chromadb.txt
pip install -r ../../requirements-embeddings.txt
```

## Directory Structure

```
examples/playbooks/
├── 01_basic_pdf_ingestion.py
├── 02_multi_stage_pipeline.py
├── 03_error_handling_recovery.py
├── 04_local_development.py
├── 05_production_deployment.py
├── .env.basic-pdf.example
├── .env.production.example
└── README.md (comprehensive guide)

documents/              # Place PDFs here
artifacts/              # Generated artifacts
chroma_db/             # ChromaDB (if offline)
```

## Performance Settings

### Development (Fast Iteration)
```bash
AZURE_CHUNKING_MAX_WORKERS=2
CHUNKING_MAX_CHARS=1500
CHUNKING_MAX_TOKENS=400
```

### Production (High Throughput)
```bash
AZURE_CHUNKING_MAX_WORKERS=8
AZURE_DI_MAX_CONCURRENCY=10
AZURE_OPENAI_MAX_CONCURRENCY=15
```

### Debugging (Slow & Careful)
```bash
AZURE_CHUNKING_MAX_WORKERS=1
LOG_LEVEL=DEBUG
AZURE_OFFICE_VERBOSE=true
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| "No documents found" | Check `LOCAL_INPUT_GLOB` pattern |
| "Authentication failed" | Verify API keys in .env |
| "Validation failed" | Install dependencies |
| "Rate limit exceeded" | Reduce concurrency settings |
| "Out of memory" | Reduce workers and batch sizes |

## Cost Estimates (Azure)

| Volume | Monthly Cost |
|--------|-------------|
| 100 PDFs/day (1,000 pages) | ~$400-600 |
| 500 PDFs/day (5,000 pages) | ~$1,500-2,000 |
| 1,000 PDFs/day (10,000 pages) | ~$3,000-4,000 |

*Includes Document Intelligence, Azure OpenAI, Azure Search*

## Support & Resources

- **Comprehensive Guide:** [README.md](README.md)
- **Main Docs:** [../../docs/INDEX.md](../../docs/INDEX.md)
- **GitHub Issues:** Report bugs and request features

## Quick Decision Guide

```
Need production reliability? → 03 or 05
Need FREE solution? → 04
Learning? → 01
Multiple doc types? → 02
Enterprise deployment? → 05
```

---

**Print this page for quick reference while working with playbooks!**
