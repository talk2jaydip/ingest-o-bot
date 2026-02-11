# Environment Configuration Examples

This directory contains pre-configured environment templates demonstrating the pluggable architecture with different vector stores and embeddings providers.

## 🎯 NEW: Complete Scenario Guide

**See [SCENARIOS_GUIDE.md](SCENARIOS_GUIDE.md) for comprehensive scenario examples with:**
- Complete end-to-end configurations (Azure Full Stack, Cost-Optimized, Offline, etc.)
- Cost estimates and performance benchmarks
- Use case recommendations
- Setup instructions
- Feature comparison matrices

## 🔌 Pluggable Architecture

Ingestor supports mixing and matching different vector stores and embeddings providers:

**Vector Stores:** Azure AI Search | ChromaDB
**Embeddings:** Azure OpenAI | Hugging Face | Cohere | OpenAI

## Quick Start

### Option 1: Use Complete Scenarios (Recommended)
```bash
# Choose a complete scenario configuration
cp envs/.env.scenario-azure-openai-default.example .env     # Azure full stack
cp envs/.env.scenario-cost-optimized.example .env           # Cost-optimized hybrid
cp .env.offline .env                                         # Fully offline
cp envs/.env.scenario-development.example .env              # Local development
cp envs/.env.scenario-multilingual.example .env             # Multilingual (100+ languages)
cp envs/.env.scenario-azure-cohere.example .env             # Azure + Cohere API

# Install dependencies and run
python -m ingestor.cli --setup-index  # If using Azure Search
python -m ingestor.cli
```

### Option 2: Mix & Match Components
```bash
# Choose base configuration
cp envs/.env.chromadb.example .env

# For offline setup (no Azure needed):
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt

# Run the pipeline
python -m ingestor.cli
```

## Configuration Types

This directory contains **three types** of configuration files:

1. **Complete Scenarios** (`.env.scenario-*.example`): End-to-end configurations ready to use
2. **Component Examples** (`.env.*.example`): Focus on specific vector store/embedding combinations
3. **Input/Output Scenarios** (`env.scenario*.example`): Focus on data flow patterns
4. **Office Processing Scenarios** (`env.office-scenario*.example`): Focus on document extraction

### Complete Scenarios (NEW - Recommended)

| File | Vector Store | Embeddings | Cost | Best For |
|------|--------------|------------|------|----------|
| `.env.scenario-azure-openai-default.example` | Azure Search | Azure OpenAI | $$$ | Enterprise production |
| `.env.scenario-cost-optimized.example` | Azure Search | Hugging Face | $$ | High-volume cost optimization |
| `.env.scenario-development.example` | ChromaDB | Hugging Face | Free | Local development |
| `.env.scenario-multilingual.example` | ChromaDB/Azure | Hugging Face | Free-$$ | 100+ languages |
| `.env.scenario-azure-cohere.example` | Azure Search | Cohere API | $$-$$$ | Cloud multilingual |
| `../.env.offline` | ChromaDB | Hugging Face | Free | Air-gapped/offline |

**See [SCENARIOS_GUIDE.md](SCENARIOS_GUIDE.md) for detailed information.**

### Component Examples

| File | Vector Store | Embeddings | Description |
|------|--------------|------------|-------------|
| `.env.example` | Azure Search | Azure OpenAI | Classic Azure setup |
| `.env.chromadb.example` | ChromaDB | Hugging Face | Fully offline |
| `.env.hybrid.example` | Azure Search | Hugging Face | Cost-optimized |
| `.env.cohere.example` | Azure Search | Cohere | Cloud API alternative |

## Legacy Scenario Categories

There are also **granular scenarios** for specific aspects:

1. **Input/Output Scenarios** (1-5): Define where documents come from and where artifacts go
2. **Office Processing Scenarios** (Office 1-3): Define how Office documents (DOCX, PPTX, DOC) are processed

You can **mix and match**: Choose one input/output scenario + one office processing scenario.

---

## Input/Output Scenarios (1-5)

### Scenario 1: Local Development
**File**: `env.scenario1-local-dev.example`

**Pattern**: Local Input → Local Artifacts

**Use Cases**:
- Local development and debugging
- Testing without cloud costs
- Rapid iteration
- Inspecting artifacts on disk

**Configuration**:
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=samples/**/*.pdf
AZURE_ARTIFACTS_DIR=./test_artifacts
```

**Best For**: Developers working on features, debugging issues locally

---

### Scenario 2: Production Deployment
**File**: `env.scenario2-blob-prod.example`

**Pattern**: Blob Input → Blob Artifacts

**Use Cases**:
- Production deployment
- Processing large document collections
- Serverless/cloud-native workflows
- Persistent artifact storage

**Configuration**:
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=production-documents-input
# Artifacts go to blob (no AZURE_ARTIFACTS_DIR)
```

**Best For**: Production environments, scheduled processing, scalable deployments

**Requirements**: Pre-create INPUT container in Azure Storage

---

### Scenario 3: Hybrid Testing
**File**: `env.scenario3-local-to-blob.example`

**Pattern**: Local Input → Blob Artifacts

**Use Cases**:
- Testing locally with production-like storage
- Validating blob storage integration
- Sharing artifacts with team
- CI/CD pipelines

**Configuration**:
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=./test_data/**/*.pdf
AZURE_STORE_ARTIFACTS_TO_BLOB=true
```

**Best For**: Integration testing, CI/CD, team collaboration

---

### Scenario 4: Production Debug
**File**: `env.scenario4-blob-to-local.example`

**Pattern**: Blob Input → Local Artifacts

**Use Cases**:
- Debugging production files locally
- Inspecting specific problematic documents
- Quality assurance testing
- Artifact inspection

**Configuration**:
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=production-documents-input
AZURE_ARTIFACTS_DIR=./debug_artifacts  # Override to local
```

**Best For**: Troubleshooting production issues, QA validation

---

### Scenario 5: Fully Offline
**File**: `env.scenario5-offline.example`

**Pattern**: Local Input → Local Artifacts (No Azure Services)

**Use Cases**:
- Air-gapped/secure environments
- Development without Azure access
- Cost optimization
- Demos and prototyping

**Configuration**:
```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=./documents/**/*
AZURE_ARTIFACTS_DIR=./offline_artifacts
AZURE_OFFICE_EXTRACTOR_MODE=markitdown  # No Azure DI
AZURE_MEDIA_DESCRIBER=none  # No Azure OpenAI
```

**Requirements**: LibreOffice installation for Office docs

**Best For**: Secure environments, development, demos

---

## Configuration Matrix

| Scenario | Input Source | Artifacts Storage | Azure Services | Use Case |
|----------|-------------|-------------------|----------------|----------|
| 1 - Local Dev | Local disk | Local disk | Yes (DI, OpenAI) | Development |
| 2 - Production | Blob Storage | Blob Storage | Yes (All) | Production |
| 3 - Hybrid Test | Local disk | Blob Storage | Yes (All) | Testing |
| 4 - Debug | Blob Storage | Local disk | Yes (DI, OpenAI) | Debugging |
| 5 - Offline | Local disk | Local disk | No (MarkItDown only) | Air-gapped |

---

## Office Document Processing Scenarios (Office 1-3)

These scenarios control how Office documents (DOCX, PPTX, DOC) are processed. Choose based on your quality, cost, and offline requirements.

### Office Scenario 1: Azure DI Only (No Fallback)
**File**: `env.office-scenario1-azure-di-only.example`

**Processing**: Azure Document Intelligence Only

**Features**:
- ✅ Highest quality extraction
- ✅ LaTeX equation support (premium tier)
- ✅ Bounding boxes available
- ❌ DOC files NOT supported (will fail)
- ❌ No fallback if Azure DI fails

**Use Cases**:
- Production requiring guaranteed highest quality
- Only DOCX/PPTX files (no legacy DOC)
- Need LaTeX equations
- Need bounding boxes for spatial analysis

**Cost**: Azure DI fees per page

---

### Office Scenario 2: MarkItDown Only (Fully Offline)
**File**: `env.office-scenario2-markitdown-only.example`

**Processing**: MarkItDown with LibreOffice

**Features**:
- ✅ Works completely offline
- ✅ Supports DOC legacy files
- ✅ No Azure costs
- ❌ Lower quality extraction (70-80% of DI)
- ❌ No LaTeX equations
- ❌ No bounding boxes

**Requirements**: LibreOffice installation

**Use Cases**:
- Air-gapped/secure environments
- Development without Azure access
- Cost optimization (no Azure fees)
- Processing DOC legacy files
- Offline demos

**Cost**: FREE (LibreOffice is open source)

---

### Office Scenario 3: Hybrid Mode with Fallback (RECOMMENDED)
**File**: `env.office-scenario3-hybrid-fallback.example`

**Processing**: Azure DI first, MarkItDown fallback

**Features**:
- ✅ Best quality when Azure DI available
- ✅ Automatic fallback on failure
- ✅ Supports all formats (DOC, DOCX, PPTX)
- ✅ Maximum reliability
- ✅ Graceful degradation

**How it works**:
- DOCX/PPTX: Try Azure DI → Fallback to MarkItDown if needed
- DOC: Use MarkItDown directly (DI doesn't support DOC)
- Continues processing even if Azure DI is unavailable

**Use Cases**:
- Production requiring maximum uptime (RECOMMENDED)
- Mixed document types (DOCX + DOC)
- Unpredictable Azure availability
- Need reliability + quality

**Cost**: Azure DI fees when available, FREE fallback

---

### Office Scenarios Comparison

| Feature | Office 1 (DI Only) | Office 2 (MarkItDown) | Office 3 (Hybrid) |
|---------|-------------------|----------------------|-------------------|
| **DOCX Quality** | Excellent | Good | Excellent → Good |
| **PPTX Quality** | Excellent | Good | Excellent → Good |
| **DOC Support** | ❌ Fails | ✅ Yes | ✅ Yes |
| **LaTeX Equations** | ✅ Yes | ❌ No | ✅ When DI works |
| **Bounding Boxes** | ✅ Yes | ❌ No | ✅ When DI works |
| **Offline** | ❌ No | ✅ Yes | ⚠️ Fallback |
| **Reliability** | Low | Medium | High |
| **Cost** | DI fees | FREE | DI fees + FREE fallback |
| **Best For** | Guaranteed quality | Offline/Cost | Production |

---

## Mixing Input/Output + Office Processing Scenarios

You can combine any input/output scenario with any office processing scenario by copying one as base and merging the office settings from another.

### Example: Local Dev + Hybrid Office Processing

```bash
# 1. Start with input/output scenario
cp envs/env.scenario1-local-dev.example .env

# 2. Update office processing settings in .env
nano .env

# 3. Find the "Office Document Processing" section and set:
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true
AZURE_OFFICE_LIBREOFFICE_PATH=/usr/bin/soffice

# Done! You now have Local Dev + Hybrid Office
```

### Common Combinations

**Production Deployment (Best Quality)**:
```bash
# Input/Output: Scenario 2 (Blob → Blob)
# Office: Scenario 1 (Azure DI Only)
cp envs/env.scenario2-blob-prod.example .env
# Then set: AZURE_OFFICE_EXTRACTOR_MODE=azure_di
```

**Production Deployment (Maximum Reliability)**:
```bash
# Input/Output: Scenario 2 (Blob → Blob)
# Office: Scenario 3 (Hybrid)
cp envs/env.scenario2-blob-prod.example .env
# Then set: AZURE_OFFICE_EXTRACTOR_MODE=hybrid
#           AZURE_OFFICE_OFFLINE_FALLBACK=true
```

**Development (Cost-Optimized)**:
```bash
# Input/Output: Scenario 1 (Local → Local)
# Office: Scenario 2 (MarkItDown Only)
cp envs/env.scenario1-local-dev.example .env
# Then set: AZURE_OFFICE_EXTRACTOR_MODE=markitdown
#           AZURE_OFFICE_LIBREOFFICE_PATH=/usr/bin/soffice
```

**Air-Gapped Deployment**:
```bash
# Input/Output: Scenario 5 (Offline)
# Office: Scenario 2 (MarkItDown Only)
cp envs/env.scenario5-offline.example .env
# Already configured for fully offline!
```

---

## How to Switch Scenarios

### Method 1: Manual Copy (Recommended)

```bash
# 1. Choose your INPUT/OUTPUT scenario
cp envs/env.scenario1-local-dev.example .env

# 2. (Optional) Choose your OFFICE processing scenario
# Open the office scenario file to see the settings
cat envs/env.office-scenario3-hybrid-fallback.example

# 3. Edit .env with your credentials and office settings
nano .env
# - Replace all "your-*-here" placeholders
# - Update AZURE_OFFICE_EXTRACTOR_MODE if needed
# - Update AZURE_OFFICE_LIBREOFFICE_PATH if needed

# 4. Test the configuration
prepdocs --help

# 5. Run the pipeline
prepdocs --setup-index --glob "documents/**/*.{pdf,docx,pptx}"
```

### Method 2: Using the Switcher Script

```bash
# Interactive switcher
python scripts/switch_env.py

# Or specify scenario directly
python scripts/switch_env.py --scenario 2

# List available scenarios
python scripts/switch_env.py --list
```

### Method 3: Environment Variable Override

```bash
# Override specific settings without changing .env
INPUT_MODE=blob INPUT_CONTAINER=test-docs prepdocs --glob
```

## Credential Management

### Security Best Practices

1. **Never commit .env to git** (.env is in .gitignore)
2. **Use Azure Key Vault for production**
   ```bash
   KEY_VAULT_URI=https://your-keyvault.vault.azure.net/
   ```
3. **Use service principals**, not personal accounts
4. **Rotate credentials regularly**
5. **Use managed identities** when running in Azure

### Placeholder Replacement

All scenario files use placeholders that must be replaced:

```bash
# Find all placeholders
grep -r "your-.*-here" .env

# Example replacements:
your-tenant-id-here          → b5b8b483-5597-4ae7-8e27-fcc464a3b584
your-client-id-here          → d0e06358-47d7-480a-b576-cdb4c30593a8
your-client-secret-here      → <your-actual-secret>
your-search-service          → ais-dev-eus-yourname-01
your-search-key-here         → <your-actual-search-key>
```

## Scenario-Specific Configuration

### For Scenario 1 (Local Dev):
```bash
# Adjust local paths
AZURE_LOCAL_GLOB=./my_documents/**/*.pdf  # Your documents
AZURE_ARTIFACTS_DIR=./my_artifacts        # Your artifacts location
```

### For Scenario 2 (Production):
```bash
# Create INPUT container first in Azure Portal or CLI:
az storage container create \
  --name production-documents-input \
  --account-name your-storage-account

# Upload documents to INPUT container
az storage blob upload-batch \
  --destination production-documents-input \
  --source ./documents \
  --account-name your-storage-account
```

### For Scenario 3 (Hybrid):
```bash
# Test with local files but blob storage
AZURE_LOCAL_GLOB=./test_cases/**/*.pdf
AZURE_STORE_ARTIFACTS_TO_BLOB=true
AZURE_BLOB_CONTAINER_PREFIX=test-run-$(date +%Y%m%d)
```

### For Scenario 4 (Debug):
```bash
# Focus on specific problematic files
AZURE_BLOB_CONTAINER_IN=production-documents-input
AZURE_BLOB_PREFIX=documents/problematic/  # Specific subfolder
AZURE_ARTIFACTS_DIR=./debug_$(date +%Y%m%d)
```

### For Scenario 5 (Offline):
```bash
# Install LibreOffice first!
# Linux: sudo apt-get install libreoffice
# Mac: brew install --cask libreoffice
# Windows: Download from libreoffice.org

# Then set path
AZURE_OFFICE_LIBREOFFICE_PATH=/usr/bin/soffice  # Linux/Mac
# or
AZURE_OFFICE_LIBREOFFICE_PATH=C:\\Program Files\\LibreOffice\\program\\soffice.exe  # Windows
```

## Office Document Processing Modes

All scenarios support three office processing modes:

### 1. Azure DI Only (Best Quality)
```bash
AZURE_OFFICE_EXTRACTOR_MODE=azure_di
# + Highest quality
# + LaTeX equations
# + Bounding boxes
# - Requires Azure DI
# - DOC files not supported
```

### 2. MarkItDown Only (Fully Offline)
```bash
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
# + Works offline
# + No Azure costs
# + Supports DOC files
# - Lower quality
# - Requires LibreOffice
```

### 3. Hybrid Mode (Recommended)
```bash
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true
# + Best of both worlds
# + Automatic fallback
# + Handles all formats
# - Requires both Azure DI + LibreOffice for full features
```

## Performance Tuning

### Development (Fast Iteration)
```bash
AZURE_MAX_WORKERS=2
AZURE_DI_MAX_CONCURRENCY=2
AZURE_OPENAI_MAX_CONCURRENCY=3
AZURE_EMBED_BATCH_SIZE=64
```

### Production (Maximum Throughput)
```bash
AZURE_MAX_WORKERS=8
AZURE_DI_MAX_CONCURRENCY=10
AZURE_OPENAI_MAX_CONCURRENCY=15
AZURE_EMBED_BATCH_SIZE=256
AZURE_UPLOAD_BATCH_SIZE=1000
```

### Debugging (Slow and Careful)
```bash
AZURE_MAX_WORKERS=1
AZURE_DI_MAX_CONCURRENCY=1
AZURE_OPENAI_MAX_CONCURRENCY=1
AZURE_OFFICE_VERBOSE=true
```

## Testing Your Configuration

```bash
# 1. Validate environment
python -c "from ingestor.config import PipelineConfig; print('Config OK')"

# 2. Test with single file
ingestor --pdf "samples/test.pdf"

# 3. Test index operations
prepdocs --setup-index --index-only

# 4. Full pipeline test
prepdocs --setup-index --glob "samples/**/*.pdf"
```

## Troubleshooting

### .env Not Found
```bash
# Make sure you copied from envs/ to root
ls -la .env  # Should exist in project root
pwd          # Should be in ingest-o-bot/ (or your project directory)
```

### Credentials Not Working
```bash
# Test Azure connection
az login
az account show

# Test specific services
az cognitiveservices account show --name your-di --resource-group your-rg
az search service show --name your-search --resource-group your-rg
```

### Blob Container Not Found
```bash
# List containers
az storage container list --account-name your-storage-account

# Create INPUT container
az storage container create \
  --name your-input-container \
  --account-name your-storage-account
```

### LibreOffice Not Found (Offline Mode)
```bash
# Check installation
which soffice  # Linux/Mac
where soffice  # Windows

# Install if missing
# Linux: sudo apt-get install libreoffice
# Mac: brew install --cask libreoffice
# Windows: Download from https://www.libreoffice.org/
```

## Additional Resources

- **[Configuration Matrix](../docs/reference/01_CONFIGURATION_MATRIX.md)**: Detailed configuration reference
- **[Quick Start Guide](../docs/guides/QUICKSTART.md)**: Getting started tutorial
- **[Configuration Guide](../docs/guides/CONFIGURATION.md)**: Complete configuration documentation
- **[Main README](../README.md)**: Project overview and usage

## Support

For issues or questions:
1. Check [Troubleshooting Guide](../README.md#troubleshooting)
2. Review [docs/INDEX.md](../docs/INDEX.md) for all documentation
3. Open an issue on GitHub

---

**Quick Reference**:
- Development: Use Scenario 1
- Production: Use Scenario 2
- Testing: Use Scenario 3
- Debugging: Use Scenario 4
- Offline: Use Scenario 5
