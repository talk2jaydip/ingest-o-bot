# Playbooks Summary

This document provides a comprehensive overview of all available playbooks, their use cases, and when to use each one.

## What Are Playbooks?

Playbooks are **production-ready, end-to-end workflow examples** that demonstrate complete document processing scenarios. Unlike simple code snippets, playbooks include:

- Complete workflows with all steps
- Proper error handling and recovery
- Detailed configuration examples
- Production best practices
- Monitoring and observability
- Testing and validation steps
- Comprehensive documentation

## Quick Selection Guide

### By Use Case

| If you want to... | Use this playbook |
|-------------------|-------------------|
| Learn the basics | `01_basic_pdf_ingestion.py` |
| Develop locally without cloud costs | `04_local_development.py` |
| Process different document types | `02_multi_stage_pipeline.py` |
| Handle errors robustly | `03_error_handling_recovery.py` |
| Deploy to production | `05_production_deployment.py` |

### By Experience Level

| Level | Playbook | Description |
|-------|----------|-------------|
| **Beginner** | `01_basic_pdf_ingestion.py` | Start here - simple end-to-end workflow |
| **Beginner** | `04_local_development.py` | Free offline development setup |
| **Intermediate** | `02_multi_stage_pipeline.py` | Multiple document types, optimized settings |
| **Advanced** | `03_error_handling_recovery.py` | Production-grade error handling |
| **Advanced** | `05_production_deployment.py` | Enterprise deployment |

### By Environment

| Environment | Playbook | Cost |
|-------------|----------|------|
| **Development** | `04_local_development.py` | FREE |
| **Testing** | `01_basic_pdf_ingestion.py` | $ or FREE |
| **Staging** | `03_error_handling_recovery.py` + Azure test env | $$ |
| **Production** | `05_production_deployment.py` | $$$ |

## Detailed Playbook Comparison

### 01_basic_pdf_ingestion.py

**Purpose:** Learn the fundamentals of document processing

**Best for:**
- First-time users learning the library
- Simple PDF processing needs
- Testing your setup
- Understanding the basic workflow

**Key Features:**
- Step-by-step execution with clear logging
- Works with both cloud (Azure) and offline (ChromaDB)
- Comprehensive error messages
- Next steps guidance

**Time to Run:** 10-30 seconds per PDF
**Complexity:** Low
**Lines of Code:** ~250

**When to use:**
- ✅ You're new to the library
- ✅ You want to test your configuration
- ✅ You have a simple collection of PDFs
- ✅ You want to understand the basic flow

**When NOT to use:**
- ❌ You have diverse document types needing different settings
- ❌ You need advanced error handling
- ❌ You're deploying to production

---

### 02_multi_stage_pipeline.py

**Purpose:** Process different document types with optimized settings per type

**Best for:**
- Mixed document collections
- Different chunking strategies per type
- Organized document workflows
- Comparative analysis across types

**Key Features:**
- Separate processing stages with custom settings
- Type-specific optimization (technical, legal, research, general)
- Aggregate reporting across all stages
- Per-stage performance metrics

**Document Types:**
- **Technical:** 3000 chars, 800 tokens, 15% overlap (preserve code context)
- **Legal:** 1200 chars, 300 tokens, 20% overlap (precision)
- **Research:** 2000 chars, 500 tokens, 12% overlap (academic content)
- **General:** 2000 chars, 500 tokens, 10% overlap (balanced)

**Time to Run:** Varies by document count
**Complexity:** Medium
**Lines of Code:** ~350

**When to use:**
- ✅ You have different document types
- ✅ Each type needs different chunking
- ✅ You want organized workflows
- ✅ You need per-type reporting

**When NOT to use:**
- ❌ All documents can use same settings
- ❌ You have a simple workflow
- ❌ You don't need per-type optimization

---

### 03_error_handling_recovery.py

**Purpose:** Production-grade reliability with retry, checkpoint, and recovery

**Best for:**
- Large document collections
- Production deployments
- Long-running jobs
- Problematic document sets
- Mission-critical workflows

**Key Features:**
- **Automatic retry** with exponential backoff (2^n seconds)
- **Smart retry logic** (only retries transient errors)
- **Checkpointing** every 10 documents
- **Resume from failure** automatically
- **Error classification** by type
- **Detailed error reports** with stack traces

**Retryable Errors:**
- Timeouts
- Connection issues
- Rate limiting (429, 503)
- Throttling errors

**Time to Run:** Varies (includes retry delays)
**Complexity:** High
**Lines of Code:** ~450

**When to use:**
- ✅ Processing 100+ documents
- ✅ You need reliability guarantees
- ✅ You have problematic documents
- ✅ Long-running jobs (hours)
- ✅ Production deployments

**When NOT to use:**
- ❌ Small document sets (<10)
- ❌ Quick development tests
- ❌ Documents are well-formed and reliable

---

### 04_local_development.py

**Purpose:** Complete offline development environment (FREE)

**Best for:**
- Rapid development iteration
- Testing without cloud costs
- Offline/air-gapped environments
- Learning and experimentation
- CI/CD testing

**Key Features:**
- **ChromaDB** for local vector storage
- **Hugging Face** for free embeddings
- **No cloud services** required
- **Artifact inspection** tools
- **Detailed debugging** logs
- **First-run model download** (cached thereafter)

**Technology Stack:**
- Vector Store: ChromaDB (persistent)
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dims, fast)
- Processing: MarkItDown (offline)

**Time to Run:** 5-15 seconds per PDF (after first download)
**Complexity:** Low
**Lines of Code:** ~350
**Cost:** FREE

**When to use:**
- ✅ Developing new features
- ✅ Testing configurations
- ✅ No cloud access
- ✅ Learning the system
- ✅ CI/CD pipelines
- ✅ Cost optimization

**When NOT to use:**
- ❌ Need enterprise Azure features
- ❌ Need best-in-class extraction quality
- ❌ Deploying to production

---

### 05_production_deployment.py

**Purpose:** Enterprise-grade production deployment with Azure

**Best for:**
- Production environments
- Enterprise requirements
- Scalable workflows
- Mission-critical systems
- Compliance needs

**Key Features:**
- **Production readiness checks**
- **Environment validation**
- **Comprehensive monitoring**
- **Production metrics** (JSON reports)
- **Error alerting**
- **Cost tracking**
- **Performance optimization**

**Technology Stack:**
- Vector Store: Azure AI Search (enterprise SLA)
- Embeddings: Azure OpenAI (high quality)
- Processing: Azure Document Intelligence (best extraction)
- Storage: Azure Blob Storage (scalable)

**Production Checks:**
1. Environment variable validation
2. Dependency verification
3. Configuration validation
4. Connectivity tests
5. Resource accessibility

**Time to Run:** 10-30 seconds per PDF
**Complexity:** High
**Lines of Code:** ~450
**Cost:** $$$ (pay-per-use)

**When to use:**
- ✅ Production deployment
- ✅ Need enterprise features
- ✅ Require scalability
- ✅ Need monitoring/alerting
- ✅ Compliance requirements

**When NOT to use:**
- ❌ Development/testing
- ❌ Cost-sensitive scenarios
- ❌ Small-scale usage

---

## Feature Comparison Matrix

| Feature | Basic PDF | Multi-Stage | Error Handling | Local Dev | Production |
|---------|-----------|-------------|----------------|-----------|------------|
| **Step-by-step logging** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Error validation** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Multiple doc types** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Retry logic** | ❌ | ❌ | ✅ | ❌ | Recommended |
| **Exponential backoff** | ❌ | ❌ | ✅ | ❌ | Recommended |
| **Checkpointing** | ❌ | ❌ | ✅ | ❌ | Recommended |
| **Resume capability** | ❌ | ❌ | ✅ | ❌ | Recommended |
| **Offline capable** | Optional | Optional | Optional | ✅ | ❌ |
| **Artifact inspection** | Basic | Basic | Basic | ✅ | Basic |
| **Production metrics** | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Cost tracking** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Readiness checks** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Per-stage reports** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Error classification** | ❌ | ❌ | ✅ | ❌ | Recommended |

---

## Cost Comparison

| Playbook | Cloud Setup | Offline Setup |
|----------|-------------|---------------|
| **Basic PDF** | $ per document | FREE |
| **Multi-Stage** | $ per document | FREE |
| **Error Handling** | $ per document | FREE |
| **Local Dev** | N/A | FREE |
| **Production** | $$$ (enterprise scale) | N/A |

### Azure Cost Breakdown (Approximate)
Based on 100 PDFs/day, average 10 pages each:

- **Document Intelligence:** ~$10/day (~$300/month)
- **Azure OpenAI Embeddings:** ~$50/month
- **Azure AI Search:** $75-250/month (tier dependent)
- **Azure Storage:** ~$1/month (negligible)

**Total:** ~$400-600/month for moderate usage

**Cost optimization:**
- Use hybrid embeddings (Hugging Face instead of Azure OpenAI)
- Disable media descriptions if not needed
- Process during off-peak hours
- Use local development for testing

---

## Common Workflows

### Learning Path

1. **Start:** `01_basic_pdf_ingestion.py`
   - Understand basic concepts
   - Test your setup
   - Process first documents

2. **Develop:** `04_local_development.py`
   - Fast iteration
   - No cloud costs
   - Inspect artifacts

3. **Scale:** `02_multi_stage_pipeline.py`
   - Handle diverse documents
   - Optimize per type
   - Aggregate reporting

4. **Harden:** `03_error_handling_recovery.py`
   - Add reliability
   - Handle failures
   - Resume processing

5. **Deploy:** `05_production_deployment.py`
   - Production deployment
   - Monitoring and metrics
   - Enterprise features

### Development to Production

```
Development → Testing → Staging → Production
     ↓           ↓          ↓          ↓
   04.py      01.py      03.py      05.py
  (Local)    (Azure)   (Azure+    (Azure
             Test Env)  Retry)    Production)
```

### Cost-Optimized Path

1. **Development:** `04_local_development.py` (FREE)
2. **Testing:** `01_basic_pdf_ingestion.py` with ChromaDB (FREE)
3. **Production:** `05_production_deployment.py` with hybrid mode ($)

---

## Environment Configuration Files

Each playbook has a companion `.env.example` file:

- **`.env.basic-pdf.example`** - Basic configuration with both cloud and offline options
- **`.env.production.example`** - Production configuration with enterprise settings

Additional environment files in `envs/`:
- **`.env.example`** - Default Azure setup
- **`.env.chromadb.example`** - Fully offline
- **`.env.cohere.example`** - Azure + Cohere
- **`.env.hybrid.example`** - Cost-optimized hybrid

---

## Performance Characteristics

### Processing Speed (per PDF, average 10 pages)

| Playbook | Cloud (Azure) | Offline (Local) |
|----------|---------------|-----------------|
| **Basic PDF** | 10-30s | 5-15s |
| **Multi-Stage** | 10-30s per type | 5-15s per type |
| **Error Handling** | 10-30s + retries | 5-15s + retries |
| **Local Dev** | N/A | 5-15s |
| **Production** | 10-30s | N/A |

### Throughput (documents per hour)

| Configuration | Conservative | Aggressive |
|---------------|-------------|------------|
| **Azure (DI + OpenAI)** | 120-180 | 300-400 |
| **Offline (Local)** | 240-480 | 600-900 |

*Note: Depends on document size, concurrency settings, service tiers*

---

## Selection Decision Tree

```
START: What's your primary goal?
│
├─ Learning/Testing?
│  └─ 01_basic_pdf_ingestion.py
│
├─ Development?
│  ├─ Need cloud features? → 01_basic_pdf_ingestion.py (Azure test)
│  └─ Want offline/free? → 04_local_development.py
│
├─ Different document types?
│  └─ 02_multi_stage_pipeline.py
│
├─ Need reliability?
│  └─ 03_error_handling_recovery.py
│
└─ Production deployment?
   └─ 05_production_deployment.py
```

---

## Getting Help

### Documentation
- [Playbooks README](README.md) - Comprehensive guide
- [Main README](../../README.md) - Project overview
- [Configuration Guide](../../docs/guides/CONFIGURATION.md) - All settings
- [Examples Overview](../README.md) - Other examples

### Troubleshooting
Each playbook includes:
- Inline error handling
- Detailed error messages
- Troubleshooting sections in companion .env files
- Clear next steps

### Support
- GitHub Issues: Bug reports and features
- Documentation: Comprehensive guides
- Examples: More in `examples/` directory

---

## Contributing

Have a useful playbook idea? We welcome contributions!

Requirements:
- Complete end-to-end workflow
- Proper error handling
- Companion .env.example file
- Comprehensive comments
- Updated documentation

---

**Ready to get started?** Choose a playbook above and dive in!
