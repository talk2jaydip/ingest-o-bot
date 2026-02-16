# Environment Configuration Scenarios Guide

This guide helps you choose the right environment configuration for your use case. Each scenario is optimized for specific requirements like cost, performance, language support, or deployment environment.

---

## 🎯 Quick Scenario Selector

| Scenario | Vector Store | Embeddings | Cost | Languages | Best For |
|----------|--------------|------------|------|-----------|----------|
| [Azure Full Stack](#scenario-1-azure-full-stack-default) | Azure Search | Azure OpenAI | $$$ | English++ | Enterprise production |
| [Cost-Optimized](#scenario-2-cost-optimized-hybrid) | Azure Search | Hugging Face | $$ | 100+ | High-volume processing |
| [Fully Offline](#scenario-3-fully-offline) | ChromaDB | Hugging Face | Free | 100+ | Air-gapped, development |
| [Development](#scenario-4-local-development) | ChromaDB | Hugging Face | Free | English++ | Local dev, testing |
| [Multilingual](#scenario-5-multilingual-global) | ChromaDB/Azure | Hugging Face | Free-$$ | 100+ | International content |
| [Azure + Cohere](#scenario-6-azure--cohere-api) | Azure Search | Cohere API | $$-$$$ | 100+ | Cloud-native multilingual |

**Cost Key:**
- Free: $0/month
- $: $50-250/month
- $$: $250-500/month
- $$$: $500-1000/month

---

## 📋 Detailed Scenarios

### Scenario 1: Azure Full Stack (Default)

**Configuration File:** `.env.scenario-azure-openai-default.example`

**Description:**
Complete Azure-based solution with all Microsoft services. Classic enterprise configuration with integrated services and Azure SLA.

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Azure Blob     │───▶│  Azure Document  │───▶│  Azure OpenAI   │
│  Storage        │    │  Intelligence    │    │  (Embeddings)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────────────────────────┐
                       │     Azure AI Search (Vector DB)      │
                       └──────────────────────────────────────┘
```

**Use Cases:**
- ✅ Production enterprise deployments
- ✅ Teams already using Azure infrastructure
- ✅ Need Azure SLA and enterprise support
- ✅ Compliance requirements (data stays in Azure)
- ✅ Want simplest Azure integration

**Pros:**
- Complete integration with Azure ecosystem
- Enterprise SLA and support
- Integrated vectorization option (server-side embeddings)
- Automatic scaling
- Hybrid search (vector + keyword + semantic)

**Cons:**
- Highest cost option
- Requires Azure subscription for everything
- Azure OpenAI quota limitations by region
- Not suitable for offline scenarios

**Cost Estimate:** $380-950/month
- Azure Search: $250-500
- Azure OpenAI: $100-300
- Document Intelligence: $10-100
- Blob Storage: $20-50

**Setup:**
```bash
cp envs/.env.scenario-azure-openai-default.example .env
# Fill in Azure credentials
python -m ingestor.cli --setup-index
python -m ingestor.cli
```

---

### Scenario 2: Cost-Optimized (Hybrid)

**Configuration File:** `.env.scenario-cost-optimized.example`

**Description:**
Hybrid configuration using Azure Search for storage but local Hugging Face embeddings to eliminate embedding API costs. Best cost/performance ratio for high-volume processing.

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Azure Blob     │───▶│  Azure Document  │───▶│  Hugging Face   │
│  Storage        │    │  Intelligence    │    │  (Local GPU)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────────────────────────┐
                       │     Azure AI Search (Vector DB)      │
                       └──────────────────────────────────────┘
```

**Use Cases:**
- ✅ Cost-conscious production deployments
- ✅ High-volume processing (100K+ pages/month)
- ✅ Need Azure Search but want to reduce OpenAI costs
- ✅ Have GPU available (cloud or on-prem)

**Pros:**
- 26-50% cost reduction vs full Azure
- Zero embedding API costs
- Keep Azure Search enterprise features
- GPU-accelerated local embeddings
- State-of-the-art multilingual models

**Cons:**
- Need to manage embedding infrastructure
- No integrated vectorization
- Requires GPU for best performance
- Slightly more complex setup

**Cost Estimate:** $280-700/month (vs $380-950 for full Azure)
- Azure Search: $250-500
- Azure OpenAI: $0 (embeddings) or $20-50 (optional image descriptions)
- Document Intelligence: $10-100
- Blob Storage: $20-50
- Local embeddings: $0

**High-Volume Savings:**
- Traditional (1M pages): $1,000+ in embedding costs
- This configuration: $0 in embedding costs
- **Savings: $1,000+/month**

**Setup:**
```bash
pip install sentence-transformers torch
cp envs/.env.scenario-cost-optimized.example .env
# Fill in Azure credentials
python -m ingestor.cli --setup-index
python -m ingestor.cli
```

---

### Scenario 3: Fully Offline

**Configuration File:** `.env.offline` (in root directory)

**Description:**
100% offline configuration with zero cloud dependencies. Uses ChromaDB for local vector storage and Hugging Face for local embeddings. Perfect for air-gapped environments, development, and complete data privacy.

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Local Files    │───▶│  MarkItDown      │───▶│  Hugging Face   │
│  (Filesystem)   │    │  (Python PDF)    │    │  (Local CPU)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────────────────────────┐
                       │      ChromaDB (Local Persistent)     │
                       └──────────────────────────────────────┘
```

**Use Cases:**
- ✅ Air-gapped environments (no internet after initial setup)
- ✅ Complete data privacy (data never leaves machine)
- ✅ Development and testing
- ✅ Cost-conscious deployments
- ✅ Prototyping and POCs

**Pros:**
- Zero API costs (100% free)
- No cloud dependencies
- Complete data privacy
- Works offline (after model download)
- Simple setup

**Cons:**
- No enterprise search features
- Limited to single machine (or ChromaDB server)
- No Azure Document Intelligence (uses MarkItDown)
- Requires local compute resources

**Cost Estimate:** $0/month (free!)

**Performance:**
- CPU: 2-3 minutes per 100-page PDF
- GPU: 1-2 minutes per 100-page PDF

**Setup:**
```bash
pip install chromadb sentence-transformers torch
cp .env.offline .env
mkdir -p data
# Place PDFs in data/ directory
python -m ingestor.cli
```

---

### Scenario 4: Local Development

**Configuration File:** `.env.scenario-development.example`

**Description:**
Fast local development setup optimized for rapid iteration. Uses in-memory ChromaDB and lightweight embeddings for quick testing cycles.

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Local Files    │───▶│  MarkItDown      │───▶│  MiniLM-L6      │
│  (Test Data)    │    │  (Python PDF)    │    │  (Lightweight)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────────────────────────┐
                       │      ChromaDB (In-Memory/Ephemeral)  │
                       └──────────────────────────────────────┘
```

**Use Cases:**
- ✅ Local development and testing
- ✅ CI/CD pipelines
- ✅ Prototyping new features
- ✅ Learning the pipeline
- ✅ Quick experiments

**Pros:**
- Fastest setup and iteration
- In-memory mode (no cleanup needed)
- Lightweight model (~90MB)
- Works on any laptop/desktop
- Perfect for CI/CD

**Cons:**
- Data lost on restart (unless persistent mode enabled)
- Lower quality than production models
- Limited to small test corpus

**Cost Estimate:** $0/month (free!)

**Performance:**
- 10-page PDF: ~10-20 seconds
- 100-page PDF: ~2-3 minutes

**Common Workflows:**
```bash
# Quick test (single file)
AZURE_LOCAL_GLOB=data/test/test.pdf python -m ingestor.cli

# Persistent development
# Uncomment CHROMADB_PERSIST_DIR in .env
python -m ingestor.cli

# CI/CD integration
# In-memory mode, small test corpus
pytest tests/
```

**Setup:**
```bash
pip install chromadb sentence-transformers torch
cp envs/.env.scenario-development.example .env
mkdir -p data/test
# Place test PDFs in data/test/
python -m ingestor.cli
```

---

### Scenario 5: Multilingual (Global)

**Configuration File:** `.env.scenario-multilingual.example`

**Description:**
Optimized for processing documents in 100+ languages with state-of-the-art multilingual embeddings. Supports cross-lingual semantic search (query in one language, find documents in another).

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Local/Blob     │───▶│  MarkItDown      │───▶│  Multilingual   │
│  (Any Language) │    │  (Unicode Safe)  │    │  E5-Large       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────────────────────────┐
                       │      ChromaDB or Azure Search        │
                       └──────────────────────────────────────┘
```

**Supported Languages (100+):**
- **European:** English, Spanish, French, German, Italian, Portuguese, Dutch, Polish, Russian, etc.
- **Asian:** Chinese, Japanese, Korean, Hindi, Bengali, Vietnamese, Thai, Indonesian, etc.
- **Middle Eastern:** Arabic, Hebrew, Persian, Turkish
- **African:** Swahili, Yoruba, Zulu
- **And many more...**

**Use Cases:**
- ✅ International organizations with multilingual content
- ✅ Cross-language search and retrieval
- ✅ Global knowledge bases
- ✅ Multilingual customer support
- ✅ Academic research with international documents

**Pros:**
- 100+ language support
- Cross-lingual search (query in one language, find in another)
- State-of-the-art multilingual embeddings
- Works with any Unicode text
- Free (ChromaDB) or low-cost (Azure Search)

**Cons:**
- Larger model size (~2.2GB)
- GPU recommended for good performance
- CJK languages tokenize differently (needs more attention to chunking)

**Cost Estimate:**
- ChromaDB option: $0/month (free)
- Azure Search option: $280-700/month

**Performance:**
- CPU: 8-12 minutes per 100-page multilingual PDF
- GPU: 1-2 minutes per 100-page multilingual PDF

**Cross-Lingual Search Example:**
```python
# Query in English
query = "artificial intelligence applications"

# Finds documents in:
# - Spanish: "aplicaciones de inteligencia artificial"
# - Chinese: "人工智能应用"
# - Arabic: "تطبيقات الذكاء الاصطناعي"
# - French: "applications d'intelligence artificielle"
```

**Setup:**
```bash
pip install chromadb sentence-transformers torch
cp envs/.env.scenario-multilingual.example .env
# Place multilingual documents in data/multilingual/
python -m ingestor.cli
```

---

### Scenario 6: Azure + Cohere API

**Configuration File:** `.env.scenario-azure-cohere.example`

**Description:**
Cloud-optimized configuration using Azure Search and Cohere's v3 API for embeddings. Alternative to Azure OpenAI with excellent multilingual support and competitive pricing.

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Azure Blob     │───▶│  Azure Document  │───▶│  Cohere v3 API  │
│  Storage        │    │  Intelligence    │    │  (Cloud)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────────────────────────┐
                       │     Azure AI Search (Vector DB)      │
                       └──────────────────────────────────────┘
```

**Use Cases:**
- ✅ Need cloud embeddings without Azure OpenAI dependency
- ✅ Multilingual content (100+ languages)
- ✅ Want simple API integration
- ✅ Prefer pay-as-you-go pricing
- ✅ Don't want to manage local embedding infrastructure

**Pros:**
- Better multilingual support than Azure OpenAI
- No Azure OpenAI quota limitations
- Simple API integration
- Competitive pricing (~$0.10 per 1M tokens)
- Free tier available for testing

**Cons:**
- No integrated vectorization with Azure Search
- No vision/multimodal support (need Azure OpenAI for images)
- Data leaves your infrastructure
- Rate limits on API

**Cost Estimate:** $330-800/month
- Azure Search: $250-500
- Cohere embeddings: $50-150 (per 1M tokens)
- Document Intelligence: $10-100
- Blob Storage: $20-50

**Cohere Models:**
| Model | Dimensions | Languages | Speed | Cost |
|-------|-----------|-----------|-------|------|
| embed-multilingual-v3.0 | 1024 | 100+ | Medium | $0.10/1M |
| embed-english-v3.0 | 1024 | English | Medium | $0.10/1M |
| embed-multilingual-light-v3.0 | 384 | 100+ | Fast | $0.02/1M |
| embed-english-light-v3.0 | 384 | English | Fast | $0.02/1M |

**Setup:**
```bash
pip install cohere
# Get API key from https://cohere.com/
cp envs/.env.scenario-azure-cohere.example .env
# Fill in Azure and Cohere credentials
python -m ingestor.cli --setup-index
python -m ingestor.cli
```

---

## 🔀 Comparison Matrix

### Feature Comparison

| Feature | Azure Full | Cost-Opt | Offline | Dev | Multilingual | Cohere |
|---------|-----------|----------|---------|-----|-------------|---------|
| **Integrated Vectorization** | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No |
| **Hybrid Search** | ✅ Yes | ✅ Yes | ❌ No | ❌ No | Optional | ✅ Yes |
| **Offline Capable** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **GPU Required** | ❌ No | ⚠️ Rec | ❌ No | ❌ No | ⚠️ Rec | ❌ No |
| **Azure Subscription** | ✅ Req | ✅ Req | ❌ No | ❌ No | Optional | ✅ Req |
| **Enterprise SLA** | ✅ Yes | ✅ Yes | ❌ No | ❌ No | Optional | ✅ Yes |

### Cost Comparison (Monthly)

| Component | Azure Full | Cost-Opt | Offline | Dev | Multilingual | Cohere |
|-----------|-----------|----------|---------|-----|-------------|---------|
| **Vector Store** | $250-500 | $250-500 | $0 | $0 | $0-500 | $250-500 |
| **Embeddings** | $100-300 | $0 | $0 | $0 | $0 | $50-150 |
| **Document Intelligence** | $10-100 | $10-100 | $0 | $0 | $0-100 | $10-100 |
| **Storage** | $20-50 | $20-50 | $0 | $0 | $0-50 | $20-50 |
| **TOTAL** | **$380-950** | **$280-700** | **$0** | **$0** | **$0-700** | **$330-800** |

### Performance Comparison (100-page PDF)

| Scenario | CPU Time | GPU Time | Quality | Setup Complexity |
|----------|----------|----------|---------|------------------|
| **Azure Full** | N/A | N/A | Excellent | Low |
| **Cost-Optimized** | 8-12 min | 1-2 min | Excellent | Medium |
| **Offline** | 2-3 min | 1-2 min | Good | Low |
| **Development** | 2-3 min | N/A | Good | Very Low |
| **Multilingual** | 8-12 min | 1-2 min | Excellent | Low-Medium |
| **Cohere** | N/A | N/A | Excellent | Low |

---

## 🎨 Mixing & Matching Components

The pluggable architecture allows you to mix and match components:

### Vector Store Options
- **Azure AI Search:** Enterprise features, hybrid search, managed service
- **ChromaDB:** Local/self-hosted, free, offline capable

### Embedding Options
- **Azure OpenAI:** Best Azure integration, integrated vectorization
- **Hugging Face:** Free, offline, GPU-accelerated, 100+ models
- **Cohere:** Cloud API, excellent multilingual, competitive pricing
- **OpenAI:** Native OpenAI API (non-Azure)

### Valid Combinations

| Vector Store | Embeddings | Use Case |
|-------------|-----------|----------|
| Azure Search | Azure OpenAI | Classic Azure (Scenario 1) |
| Azure Search | Hugging Face | Cost-optimized (Scenario 2) |
| Azure Search | Cohere | Cloud multilingual (Scenario 6) |
| ChromaDB | Hugging Face | Offline/dev (Scenarios 3, 4, 5) |
| ChromaDB | Cohere | Hybrid local/cloud |

---

## 📚 Additional Scenario Files

### Office Document Processing Scenarios

See `envs/.env.scenarios.example` for Office document processing scenarios:
- **Scenario 1:** Azure DI Only (no fallback)
- **Scenario 2:** MarkItDown Only (fully offline)
- **Scenario 3:** Hybrid with Fallback (recommended for production)

### Input/Output Mode Scenarios

Additional files in `envs/`:
- `env.scenario1-local-dev.example`: Local input + local artifacts
- `env.scenario2-blob-prod.example`: Blob input + blob artifacts
- `env.scenario3-local-to-blob.example`: Local input + blob artifacts
- `env.scenario4-blob-to-local.example`: Blob input + local artifacts

---

## 🚀 Getting Started

### 1. Choose Your Scenario

Use the [Quick Scenario Selector](#-quick-scenario-selector) table above to identify which scenario matches your requirements.

### 2. Copy Configuration

```bash
# Example: Using Cost-Optimized scenario
cp envs/.env.scenario-cost-optimized.example .env
```

### 3. Install Dependencies

```bash
# All scenarios need base dependencies
pip install -r requirements.txt

# Offline/local embeddings scenarios
pip install -r requirements-embeddings.txt

# ChromaDB scenarios
pip install -r requirements-chromadb.txt

# Cohere scenario
pip install cohere
```

### 4. Configure Credentials

Edit `.env` and fill in your credentials:
- Azure credentials (if using Azure services)
- API keys (Cohere, OpenAI)
- Storage paths
- Model selections

### 5. Run Pipeline

```bash
# For Azure Search: Create index first
python -m ingestor.cli --setup-index

# Process documents
python -m ingestor.cli

# Or specify custom env file
python -m ingestor.cli --env-file envs/.env.scenario-multilingual.example
```

---

## 🔧 Customization Tips

### Adjusting for Your Workload

**Low Volume (<1K pages/month):**
- Use Azure Full Stack or Development scenario
- Simplicity over cost optimization

**Medium Volume (1K-100K pages/month):**
- Use Cost-Optimized or Cohere scenario
- Balance cost and convenience

**High Volume (>100K pages/month):**
- Use Cost-Optimized with GPU
- Maximum savings on embedding costs

### Performance Tuning

**CPU-Constrained:**
- Use lightweight models (all-MiniLM-L6-v2)
- Reduce batch sizes
- Lower concurrency

**GPU-Enabled:**
- Use large models (multilingual-e5-large, bge-large)
- Increase batch sizes (64-128)
- Higher concurrency

**Memory-Constrained:**
- Use lighter models
- Reduce CHUNKING_MAX_TOKENS
- Lower batch sizes

### Cost Optimization

**Minimize Costs:**
1. Disable image descriptions: `AZURE_MEDIA_DESCRIBER=disabled`
2. Use local embeddings (Hugging Face)
3. Use ChromaDB instead of Azure Search
4. Reduce chunking limits to save tokens
5. Use light embedding models

**Maximize Quality:**
1. Use Azure Document Intelligence
2. Enable image descriptions (GPT-4)
3. Use large embedding models
4. Enable table summaries
5. Use higher chunking limits

---

## 📖 Related Documentation

- **[Configuration Guide](CONFIGURATION_FLAGS_GUIDE.md)** - All configuration parameters
- **[Environment Variables Reference](../docs/reference/12_ENVIRONMENT_VARIABLES.md)** - Complete variable reference
- **[Vector Stores Guide](../docs/guides/VECTOR_STORES_GUIDE.md)** - Vector store details
- **[Embeddings Providers Guide](../docs/guides/EMBEDDINGS_PROVIDERS_GUIDE.md)** - Embedding provider details
- **[Configuration Examples](../docs/guides/CONFIGURATION_EXAMPLES.md)** - More examples

---

## 💡 Need Help?

Can't decide which scenario? Answer these questions:

1. **Do you need offline/air-gapped?** → Use Scenario 3 (Offline)
2. **Processing 100K+ pages/month?** → Use Scenario 2 (Cost-Optimized)
3. **Multiple languages (100+)?** → Use Scenario 5 (Multilingual) or 6 (Cohere)
4. **Just testing/development?** → Use Scenario 4 (Development)
5. **Want simplest Azure setup?** → Use Scenario 1 (Azure Full)
6. **Need cloud but not Azure OpenAI?** → Use Scenario 6 (Cohere)

Still unsure? Start with **Scenario 4 (Development)** for local testing, then upgrade to your production scenario.

---

## 🔄 Migration Paths

### From Development to Production

```bash
# Start with development
cp envs/.env.scenario-development.example .env
# ... test and develop ...

# Upgrade to production (choose one):
cp envs/.env.scenario-azure-openai-default.example .env  # Full Azure
cp envs/.env.scenario-cost-optimized.example .env        # Hybrid
```

### From Offline to Cloud

```bash
# Start offline
cp .env.offline .env
# ... verify quality and functionality ...

# Move to cloud (choose one):
cp envs/.env.scenario-cost-optimized.example .env  # Keep local embeddings
cp envs/.env.scenario-azure-openai-default.example .env  # Full cloud
```

---

**Last Updated:** 2024-02-11
**Version:** 1.0
