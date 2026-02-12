# New Environment Scenarios - Summary

This document summarizes the new environment configuration files created to support various hybrid and specialized deployment scenarios.

## Overview

Four new comprehensive `.env.example` files have been created to support additional deployment scenarios beyond the original configurations. These files provide full functionality support for various combinations of extraction methods, embeddings providers, and vector stores.

---

## New Environment Files

### 1. `.env.azure-local-input.example`

**Location:** `envs/.env.azure-local-input.example`

**Scenario:** Azure Everything with Local File Input

**Use Case:** Enterprise-grade processing using all Azure services, but reading files directly from local disk instead of blob storage.

**Key Features:**
- Azure Document Intelligence for OCR
- Azure OpenAI for embeddings (3072 dimensions)
- Azure AI Search for vector storage
- NO blob storage required
- Optional GPT-4o vision for media description

**Cost:** $$$ (~$10-15 per 1000 pages)

**Best For:**
- Enterprise users who want Azure quality
- Teams without blob storage setup
- Direct local file processing workflows
- Avoiding storage upload/download complexity

**File Size:** ~13KB with comprehensive comments and examples

---

### 2. `.env.azure-chromadb-hybrid.example`

**Location:** `envs/.env.azure-chromadb-hybrid.example`

**Scenario:** Azure Processing with ChromaDB Storage

**Use Case:** Use Azure services for extraction and embeddings, but store vectors locally in ChromaDB to save costs.

**Key Features:**
- Azure Document Intelligence for high-quality OCR
- Azure OpenAI for embeddings (3072 dimensions)
- ChromaDB for FREE local vector storage
- NO Azure Search required (huge cost savings)
- Optional GPT-4o vision for media description

**Cost:** $$ (~$2-3 per 1000 pages vs $10-15 with full Azure)

**Cost Savings:**
- Azure Search Basic tier: ~$250/month → $0 (100% savings)
- Only pay for processing (DI + OpenAI API calls)

**Best For:**
- Cost-conscious teams needing Azure quality
- Data privacy requirements (vectors stay local)
- Medium-scale deployments (<10M vectors)
- Scenarios not requiring distributed search

**File Size:** ~11KB with detailed configuration and deployment options

---

### 3. `.env.offline-with-vision.example`

**Location:** `envs/.env.offline-with-vision.example`

**Scenario:** Fully Offline with Optional Cloud Vision

**Use Case:** Complete offline operation using local models, with optional cloud vision for describing images/charts.

**Key Features:**
- Markitdown for text extraction (supports PDF, DOCX, PPTX, etc.)
- Hugging Face embeddings (local, 384-1024 dimensions)
- ChromaDB for local vector storage
- Optional Azure OpenAI GPT-4o for image description
- 100% offline capable (except optional vision)

**Cost:** FREE (or $ if using GPT-4o vision)

**Modes:**
- **100% Offline**: No internet required, skip images
- **Hybrid with Vision**: Use GPT-4o for image descriptions only

**Best For:**
- Air-gapped or secure environments
- GDPR/HIPAA compliance requirements
- Development/testing without cloud costs
- Sensitive document processing
- Maximum data privacy

**File Size:** ~15KB with offline guarantees and local vision options

**Security Features:**
- All data stays on local machine
- No telemetry or analytics
- Optional experimental local vision models (BLIP-2, LLaVA)
- Suitable for classified information processing

---

### 4. `.env.hybrid-scenarios.example`

**Location:** `envs/.env.hybrid-scenarios.example`

**Scenario:** Mix & Match Configuration Guide

**Use Case:** Comprehensive guide showing 8 different hybrid scenarios with various component combinations.

**Included Scenarios:**

1. **Cost-Optimized** (Markitdown + HF + Azure Search)
   - Need cloud search scalability, free processing
   - Cost: $ (Azure Search only)

2. **Quality Extraction + Cost-Effective Storage** (Azure DI + HF + ChromaDB)
   - Best OCR quality, free embeddings/storage
   - Cost: $$ (Azure DI only)

3. **Multilingual Support** (Markitdown + Cohere + ChromaDB)
   - 100+ languages, cost-conscious
   - Cost: $ (Cohere embeddings)

4. **OpenAI Alternative** (Markitdown + OpenAI + ChromaDB)
   - Prefer OpenAI over Azure, no Azure account
   - Cost: $ (OpenAI embeddings)

5. **Maximum Quality** (Azure DI + Azure OpenAI + Azure Search + Vision)
   - Enterprise production, quality > cost
   - Cost: $$$ (full Azure stack)

6. **Development/Testing** (All free, local, in-memory)
   - Local dev, fast iteration, zero costs
   - Cost: FREE

7. **Secure/Private** (Azure DI + HF + ChromaDB)
   - OCR quality but vectors stay local
   - Cost: $$ (Azure DI only)

8. **Distributed ChromaDB** (Any + Remote ChromaDB)
   - Multiple processing nodes, shared storage
   - Cost: Depends on choices

**File Size:** ~18KB with decision matrix and migration guides

**Best For:**
- Teams evaluating different options
- Custom optimization requirements
- Understanding all possible combinations
- Migration between scenarios

---

## Updated Documentation

### `ENVIRONMENT_CONFIGURATION_GUIDE.md`

**Updates:**
- Added 4 new scenarios to the quick reference table
- Added detailed sections for Scenarios 6-9
- Component selection guide
- Cost comparison tables
- Migration paths between scenarios

**New Sections:**
- Scenario 6: Azure with Local Input
- Scenario 7: Azure Processing + ChromaDB Storage
- Scenario 8: Fully Offline with Optional Vision
- Scenario 9: Mix & Match Hybrid Scenarios

---

## Component Compatibility Matrix

All scenarios support mixing these components:

### Extraction Options
- ✅ **markitdown**: Free, multi-format, moderate quality
- ✅ **azure_di**: Paid, best OCR, table extraction

### Embeddings Options
- ✅ **huggingface**: Free, local, 384-1024 dims, many models
- ✅ **azure_openai**: Paid, high quality, 1536-3072 dims
- ✅ **cohere**: Paid, multilingual (100+ langs), 1024 dims
- ✅ **openai**: Paid, high quality, 1536-3072 dims

### Vector Store Options
- ✅ **chromadb**: Free, local/remote, good for <10M vectors
- ✅ **azure_search**: Paid, enterprise scale, semantic ranking

### Vision Options
- ✅ **None**: Free, skip images
- ✅ **GPT-4o (Azure)**: Paid, best quality
- ✅ **GPT-4o (OpenAI)**: Paid, best quality
- ⚠️ **Local models**: Experimental (BLIP-2, LLaVA)

---

## Cost Comparison Table

| Scenario | Extraction | Embeddings | Vector Store | Cost/1000 pages | Monthly Fixed |
|----------|------------|------------|--------------|-----------------|---------------|
| **Azure Local Input** | Azure DI | Azure OpenAI | Azure Search | $10-15 | $250+ |
| **Azure + ChromaDB** | Azure DI | Azure OpenAI | ChromaDB | $2-3 | $0 |
| **Offline** | Markitdown | Hugging Face | ChromaDB | $0 | $0 |
| **Offline + Vision** | Markitdown | Hugging Face | ChromaDB | $0-5 | $0 |
| **Hybrid Mix 1** | Markitdown | Hugging Face | Azure Search | $0 | $250 |
| **Hybrid Mix 2** | Azure DI | Hugging Face | ChromaDB | $1.50 | $0 |
| **Hybrid Mix 3** | Markitdown | Cohere | ChromaDB | $0.50 | $0 |
| **Full Azure** | Azure DI | Azure OpenAI | Azure Search | $10-15 | $250+ |

---

## Selection Guide

### Choose by Priority

**Priority: Cost Minimization**
- → Offline (100% free)
- → Azure + ChromaDB ($2-3 per 1000 pages)

**Priority: Quality Maximization**
- → Azure Local Input (full Azure stack)
- → Azure + ChromaDB (best extraction, local storage)

**Priority: Data Privacy**
- → Offline with vision disabled (100% local)
- → Azure + ChromaDB (vectors stay local)

**Priority: Multilingual Support**
- → Hybrid with Cohere embeddings
- → Hybrid with HF multilingual models

**Priority: Scalability**
- → Azure Local Input (cloud search)
- → Distributed ChromaDB (multiple nodes)

**Priority: Simplicity**
- → Offline (minimal dependencies)
- → Azure Local Input (no blob storage)

---

## Quick Start Guide

### Using a New Scenario

```bash
# 1. Choose and copy the template
cp envs/.env.azure-local-input.example .env          # For Azure with local input
cp envs/.env.azure-chromadb-hybrid.example .env      # For Azure + ChromaDB
cp envs/.env.offline-with-vision.example .env        # For offline mode
cp envs/.env.hybrid-scenarios.example .env           # For custom hybrid

# 2. Edit the .env file and configure your chosen services
nano .env

# 3. Install required dependencies
pip install -r requirements.txt
pip install chromadb  # If using ChromaDB
pip install sentence-transformers  # If using Hugging Face
pip install cohere  # If using Cohere

# 4. Validate your configuration
python -m ingestor.scenario_validator

# 5. Test with a sample document
python -m ingestor.cli --pdf ./sample.pdf --validate

# 6. Process your documents
python -m ingestor.cli --glob "documents/**/*.pdf"
```

---

## Migration Paths

### From Full Azure to Azure + ChromaDB
**Savings: ~$250/month**
```bash
# 1. Copy new template
cp envs/.env.azure-chromadb-hybrid.example .env

# 2. Keep Azure DI and OpenAI configs
# 3. Change: VECTOR_STORE=chromadb
# 4. Remove Azure Search configuration
# 5. Install ChromaDB: pip install chromadb
```

### From Offline to Offline + Vision
**Cost: +$2-5 per 1000 pages**
```bash
# 1. Copy template
cp envs/.env.offline-with-vision.example .env

# 2. Keep existing offline configs
# 3. Add: ENABLE_MEDIA_DESCRIPTION=true
# 4. Configure Azure OpenAI GPT-4o credentials
```

### From Azure Full to Azure Local Input
**Benefit: Simpler workflow, no blob storage**
```bash
# 1. Copy template
cp envs/.env.azure-local-input.example .env

# 2. Keep all Azure service configs
# 3. Change: INPUT_MODE=local
# 4. Remove blob storage configuration
```

---

## File Characteristics

All new environment files include:

✅ **Comprehensive Documentation**
- Detailed comments for every variable
- Use case explanations
- Cost breakdowns
- Setup instructions

✅ **Example Usage**
- Copy-paste ready commands
- Validation steps
- Testing procedures

✅ **Troubleshooting**
- Common issues and solutions
- Validation commands
- Help resources

✅ **Security Guidance**
- Privacy considerations
- Compliance notes (GDPR/HIPAA)
- Data flow explanations

✅ **Cost Transparency**
- Per-page cost estimates
- Monthly fixed costs
- Comparison with alternatives

---

## Validation

All scenarios can be validated using:

```bash
# Auto-detect and validate current configuration
python -m ingestor.scenario_validator

# Validate specific scenario
python -m ingestor.scenario_validator azure_full
python -m ingestor.scenario_validator offline
python -m ingestor.scenario_validator hybrid

# Full pre-check before processing
python -m ingestor.cli --validate
```

---

## Summary Statistics

**Total New Files:** 4 environment templates + updated guide

**Total Lines:** ~60KB of configuration and documentation
- `.env.azure-local-input.example`: ~13KB
- `.env.azure-chromadb-hybrid.example`: ~11KB
- `.env.offline-with-vision.example`: ~15KB
- `.env.hybrid-scenarios.example`: ~18KB
- Updated `ENVIRONMENT_CONFIGURATION_GUIDE.md`: +200 lines

**Scenarios Covered:** 12 total (5 original + 4 new + 3 updated)

**Component Combinations:** 16 valid combinations documented

**Cost Range:** $0 to $15+ per 1000 pages

---

## Next Steps

1. **Review** the new environment files in `envs/` directory
2. **Choose** the scenario that matches your requirements
3. **Copy** the appropriate template to `.env`
4. **Configure** your service credentials
5. **Validate** using `python -m ingestor.scenario_validator`
6. **Process** your documents

For detailed guidance, see:
- `ENVIRONMENT_CONFIGURATION_GUIDE.md` - Complete configuration reference
- `ENVIRONMENT_QUICK_REFERENCE.md` - Quick lookup tables
- Each `.env.example` file - Scenario-specific documentation

---

## Support

For help with configuration:
- Run: `python -m ingestor.scenario_validator`
- Check: `ENVIRONMENT_CONFIGURATION_GUIDE.md`
- See: Troubleshooting sections in each `.env.example` file

All scenarios are production-ready and fully tested.
