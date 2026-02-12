# Document Processing Playbooks

Comprehensive, production-ready playbooks demonstrating end-to-end document processing workflows with the Ingestor library.

## What Are Playbooks?

Playbooks are complete, runnable examples that demonstrate real-world document processing scenarios. Unlike basic examples, playbooks include:

- **Complete workflows** from start to finish
- **Proper error handling** and recovery strategies
- **Environment configurations** with detailed comments
- **Production best practices** and patterns
- **Testing and validation** steps
- **Monitoring and observability** guidance

## Quick Start

```bash
# 1. Choose a playbook
cd examples/playbooks

# 2. Copy the companion .env file
cp .env.basic-pdf.example ../../.env

# 3. Configure credentials in .env

# 4. Run the playbook
python 01_basic_pdf_ingestion.py
```

---

## Available Playbooks

### 1. Basic PDF Ingestion
**File:** `01_basic_pdf_ingestion.py`
**Environment:** `.env.basic-pdf.example`
**Level:** Beginner
**Time:** 10-30 seconds per PDF

**What it demonstrates:**
- Simple end-to-end PDF processing
- Configuration from environment
- Validation and error checking
- Result analysis and reporting

**Use when:**
- Getting started with the library
- Processing simple PDF collections
- Learning the basic workflow
- Testing your setup

**Key features:**
- Step-by-step execution
- Detailed logging
- Clear error messages
- Next steps guidance

```bash
python 01_basic_pdf_ingestion.py
```

---

### 2. Multi-Stage Pipeline
**File:** `02_multi_stage_pipeline.py`
**Level:** Intermediate
**Time:** Varies by document count

**What it demonstrates:**
- Processing multiple document types with different settings
- Optimized chunking per content type
- Stage-by-stage execution
- Aggregate reporting

**Use when:**
- Processing diverse document types
- Applying different strategies per type
- Need granular control over processing
- Want comprehensive reports

**Document types supported:**
- **Technical:** Large chunks for code context (3000 chars, 800 tokens, 15% overlap)
- **Legal:** Small chunks for precision (1200 chars, 300 tokens, 20% overlap)
- **Research:** Medium chunks for academic content (2000 chars, 500 tokens, 12% overlap)
- **General:** Balanced settings (2000 chars, 500 tokens, 10% overlap)

**Directory structure:**
```
documents/
├── technical/    # Technical manuals, code docs
├── legal/        # Contracts, legal documents
├── research/     # Academic papers
└── general/      # Mixed content
```

```bash
python 02_multi_stage_pipeline.py
```

---

### 3. Error Handling & Recovery
**File:** `03_error_handling_recovery.py`
**Level:** Advanced
**Time:** Varies (includes retry delays)

**What it demonstrates:**
- Robust error handling
- Automatic retry with exponential backoff
- Checkpoint/resume capability
- Detailed error reporting
- Recovery from failures

**Use when:**
- Processing large document collections
- Need reliability in production
- Have problematic documents
- Want resumable processing
- Need detailed failure analysis

**Key features:**
- **Exponential backoff:** 2^n second delays between retries
- **Smart retry logic:** Only retries transient errors (timeouts, rate limits)
- **Checkpointing:** Save progress every 10 documents
- **Resume from failure:** Automatically skips processed documents
- **Error classification:** Groups failures by error type
- **Detailed reports:** JSON reports with full error context

**Retryable errors:**
- Timeouts
- Connection issues
- Rate limiting (429, 503)
- Throttling

```bash
# First run
python 03_error_handling_recovery.py

# If interrupted or failed, resume with:
python 03_error_handling_recovery.py
# (Automatically resumes from checkpoint)

# To start fresh:
rm processing_checkpoint.json
python 03_error_handling_recovery.py
```

---

### 4. Local Development
**File:** `04_local_development.py`
**Level:** Beginner
**Time:** ~5-15 seconds per PDF
**Cost:** FREE

**What it demonstrates:**
- Complete offline development setup
- ChromaDB for local vector storage
- Hugging Face for free embeddings
- Local artifact inspection
- Development debugging

**Use when:**
- Developing new features
- Testing without cloud costs
- Need fast iteration
- Working offline
- Want to inspect artifacts

**Technology stack:**
- **Vector Store:** ChromaDB (local, persistent)
- **Embeddings:** Hugging Face sentence-transformers (free, offline)
- **Model:** all-MiniLM-L6-v2 (fast, 384 dims)
- **Processing:** MarkItDown (offline, requires LibreOffice)

**Requirements:**
```bash
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt
```

**First run note:**
- Downloads embedding model (~80-400MB depending on model)
- Subsequent runs use cached model
- No internet required after first run

**Artifacts inspection:**
The playbook automatically inspects:
- ChromaDB contents
- Generated chunks
- Processing statistics
- Sample embeddings

```bash
python 04_local_development.py
```

---

### 5. Production Deployment
**File:** `05_production_deployment.py`
**Level:** Advanced
**Time:** ~10-30 seconds per PDF
**Cost:** Pay-per-use (Azure)

**What it demonstrates:**
- Enterprise production deployment
- Azure cloud-native architecture
- Production readiness checks
- Comprehensive monitoring
- Metrics and reporting

**Use when:**
- Deploying to production
- Need enterprise features
- Require scalability
- Want cloud-native solution
- Need monitoring and metrics

**Technology stack:**
- **Vector Store:** Azure AI Search (enterprise SLA)
- **Embeddings:** Azure OpenAI (high quality)
- **Processing:** Azure Document Intelligence (best extraction)
- **Storage:** Azure Blob Storage (scalable)

**Production readiness checks:**
1. Environment variable validation
2. Dependency verification
3. Configuration validation
4. Connectivity tests
5. Resource accessibility

**Outputs:**
- Processing metrics (JSON)
- Error reports (if failures)
- Production logs
- Performance statistics

**Cost optimization:**
- Consider `AZURE_OFFICE_EXTRACTOR_MODE=hybrid` for fallback
- Use `AZURE_MEDIA_DESCRIBER=disabled` if not needed
- Adjust `AZURE_CHUNKING_MAX_WORKERS` to balance speed vs cost
- Process during off-peak hours for lower costs

```bash
python 05_production_deployment.py
```

---

## Playbook Comparison Matrix

| Feature | Basic PDF | Multi-Stage | Error Handling | Local Dev | Production |
|---------|-----------|-------------|----------------|-----------|------------|
| **Level** | Beginner | Intermediate | Advanced | Beginner | Advanced |
| **Use Case** | Learning | Multiple types | Reliability | Development | Production |
| **Error Handling** | Basic | Per-stage | Advanced | Basic | Production-grade |
| **Retry Logic** | No | No | Yes | No | Recommended |
| **Checkpointing** | No | No | Yes | No | Recommended |
| **Metrics** | Basic | Detailed | Comprehensive | Detailed | Production |
| **Cloud Required** | Optional | Optional | Optional | No | Yes |
| **Cost** | $ or Free | $ or Free | $ or Free | Free | $$ |

---

## Environment Configuration

Each playbook has a companion `.env.example` file with detailed configuration:

### Basic PDF Ingestion
```bash
cp .env.basic-pdf.example ../../.env
```
- Supports both cloud (Azure) and offline (ChromaDB + Hugging Face)
- Comprehensive comments explaining each setting
- Troubleshooting guide included

### Production Deployment
```bash
# See 05_production_deployment.py for production-specific settings
```
- Enterprise Azure stack
- Production-optimized performance settings
- Security best practices
- Monitoring configuration

---

## Common Workflows

### Getting Started
```bash
# 1. Start with basic playbook
python 01_basic_pdf_ingestion.py

# 2. Try local development for fast iteration
python 04_local_development.py

# 3. Add error handling for production
python 03_error_handling_recovery.py
```

### Development to Production
```bash
# Development phase
python 04_local_development.py

# Testing phase
python 01_basic_pdf_ingestion.py  # With Azure test environment

# Production deployment
python 05_production_deployment.py
```

### Processing Different Document Types
```bash
# Organize documents by type
mkdir -p documents/{technical,legal,research,general}

# Run multi-stage pipeline
python 02_multi_stage_pipeline.py
```

### Handling Problematic Documents
```bash
# Use error handling playbook
python 03_error_handling_recovery.py

# Review error_report_*.json
# Fix issues
# Re-run (automatically resumes)
python 03_error_handling_recovery.py
```

---

## Directory Structure

```
examples/playbooks/
├── README.md                           # This file
├── 01_basic_pdf_ingestion.py          # Basic workflow
├── .env.basic-pdf.example              # Basic configuration
├── 02_multi_stage_pipeline.py         # Multi-stage processing
├── 03_error_handling_recovery.py      # Error handling
├── 04_local_development.py            # Local dev setup
└── 05_production_deployment.py        # Production deployment
```

---

## Configuration Quick Reference

### Cloud Setup (Azure)
```bash
VECTOR_STORE_MODE=azure_search
EMBEDDINGS_MODE=azure_openai
AZURE_SEARCH_SERVICE=your-service
AZURE_SEARCH_KEY=your-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_KEY=your-key
```

### Offline Setup (Free)
```bash
VECTOR_STORE_MODE=chromadb
EMBEDDINGS_MODE=huggingface
CHROMADB_PERSIST_DIR=./chroma_db
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
```

### Hybrid Setup (Cost-Optimized)
```bash
VECTOR_STORE_MODE=azure_search       # Cloud search
EMBEDDINGS_MODE=huggingface          # Free embeddings
AZURE_USE_INTEGRATED_VECTORIZATION=false
```

---

## Performance Tuning

### Development (Fast Iteration)
```bash
AZURE_CHUNKING_MAX_WORKERS=2
AZURE_DI_MAX_CONCURRENCY=2
CHUNKING_MAX_CHARS=1500
HUGGINGFACE_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

### Production (Maximum Throughput)
```bash
AZURE_CHUNKING_MAX_WORKERS=8
AZURE_DI_MAX_CONCURRENCY=10
AZURE_OPENAI_MAX_CONCURRENCY=15
AZURE_EMBED_BATCH_SIZE=256
```

### Cost-Optimized
```bash
EMBEDDINGS_MODE=huggingface          # Free embeddings
AZURE_OFFICE_EXTRACTOR_MODE=hybrid   # Fallback to free
AZURE_MEDIA_DESCRIBER=disabled       # Skip expensive descriptions
AZURE_TABLE_SUMMARIES=false          # Skip extra API calls
```

---

## Troubleshooting

### "No documents found"
```bash
# Check your input glob pattern
LOCAL_INPUT_GLOB=documents/**/*.pdf

# Verify documents exist
ls -la documents/

# Try absolute path
LOCAL_INPUT_GLOB=/absolute/path/to/documents/**/*.pdf
```

### "Authentication failed"
```bash
# Verify credentials in .env
cat .env | grep KEY

# Check for trailing spaces
# Ensure no quotes around values
# Verify endpoints are correctly formatted
```

### "Validation failed"
```bash
# Check dependencies
pip install -r requirements.txt
pip install -r requirements-chromadb.txt
pip install -r requirements-embeddings.txt

# For Azure: Check index exists
# For ChromaDB: Check directory writable
```

### "Out of memory"
```bash
# Reduce concurrency
AZURE_CHUNKING_MAX_WORKERS=2
HUGGINGFACE_BATCH_SIZE=16

# Process fewer documents at once
# Use smaller embedding model
```

### "Rate limit exceeded"
```bash
# Reduce concurrency
AZURE_DI_MAX_CONCURRENCY=3
AZURE_OPENAI_MAX_CONCURRENCY=5

# Add delays between batches
# Consider exponential backoff (playbook 03)
```

---

## Best Practices

### Security
- Never commit `.env` files to git
- Use Azure Key Vault for production secrets
- Rotate credentials regularly
- Use service principals, not personal accounts
- Implement least-privilege access

### Performance
- Start with low concurrency, increase gradually
- Monitor rate limits and adjust accordingly
- Use appropriate chunk sizes for your use case
- Consider batch processing during off-peak hours
- Cache embedding models locally

### Reliability
- Always implement retry logic for production
- Use checkpointing for long-running jobs
- Monitor and alert on failures
- Keep backups of processed documents
- Test with small batches first

### Cost Optimization
- Use hybrid configurations (Azure Search + Hugging Face)
- Disable expensive features if not needed
- Process documents in batches
- Monitor usage and set budgets
- Consider reserved capacity for predictable workloads

---

## Testing Your Playbook

### Pre-flight Checklist
- [ ] `.env` file configured
- [ ] Dependencies installed
- [ ] Test documents in input directory
- [ ] Azure resources created (if using Azure)
- [ ] Credentials validated
- [ ] Index created (if required)

### Test Process
```bash
# 1. Validate configuration
python -c "from ingestor.config import PipelineConfig; PipelineConfig.from_env()"

# 2. Test with single document
# (Place one test PDF in documents/)

# 3. Run playbook
python 01_basic_pdf_ingestion.py

# 4. Verify results
# - Check logs for errors
# - Inspect artifacts directory
# - Query vector store
```

---

## Next Steps

After running playbooks:

1. **Customize for your use case**
   - Adjust chunking parameters
   - Modify processing strategies
   - Add custom validation

2. **Integrate into your application**
   - Import playbook patterns
   - Build REST API wrapper
   - Add to CI/CD pipeline

3. **Scale to production**
   - Implement monitoring
   - Add alerting
   - Set up scheduled processing
   - Optimize for cost and performance

4. **Extend functionality**
   - Add custom processors
   - Implement document classification
   - Add metadata enrichment
   - Build custom pipelines

---

## Additional Resources

### Documentation
- [Main README](../../README.md)
- [Configuration Guide](../../docs/guides/CONFIGURATION.md)
- [Examples Overview](../README.md)
- [Environment Scenarios](../../envs/README.md)

### Related Examples
- [Basic Scripts](../scripts/) - Simple script examples
- [Notebooks](../notebooks/) - Interactive Jupyter notebooks
- [Quick Examples](../) - Minimal code examples

### Support
- GitHub Issues: Report bugs and request features
- Documentation: Comprehensive guides and references
- Examples: More examples in `examples/` directory

---

## Contributing

Have a useful playbook to share? Contributions welcome!

1. Create your playbook following the existing structure
2. Include comprehensive comments
3. Add companion `.env.example` file
4. Update this README
5. Submit a pull request

---

## License

These playbooks are part of the Ingestor project and are licensed under the MIT License.

---

**Happy Document Processing!** 🚀
