# Using the New --env-file Workflow

**NEW in v2.0:** You can now use `--env-file` parameter to validate and run pipelines without copying .env files!

---

## The Problem (OLD Way)

```bash
# Tedious workflow - copy, edit, test, repeat...
cp .env.basic-pdf.example ../../.env
notepad ../../.env
python -m ingestor.cli --pdf test.pdf

cp .env.production.example ../../.env
notepad ../../.env
python -m ingestor.cli --pdf test.pdf

# Risk: Accidentally commit .env with secrets!
# Annoying: Can't easily switch scenarios
```

---

## The Solution (NEW Way)

```bash
# Edit your credentials ONCE in the template files
notepad .env.basic-pdf.example
notepad .env.production.example

# Use directly - NO COPYING!
python -m ingestor.scenario_validator --env-file .env.basic-pdf.example
python -m ingestor.cli --pdf test.pdf --env-file .env.basic-pdf.example

# Switch scenarios with just one parameter!
python -m ingestor.cli --pdf test.pdf --env-file .env.production.example
```

---

## Complete Workflow Examples

### Example 1: Basic PDF Processing

```bash
# 1. Edit env file with your credentials (ONE TIME)
notepad .env.basic-pdf.example
# Add:
# - AZURE_DI_ENDPOINT=https://your-di.cognitiveservices.azure.com/
# - AZURE_DI_KEY=your_key
# - AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
# - AZURE_OPENAI_API_KEY=your_key
# - AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
# - AZURE_SEARCH_KEY=your_key

# 2. Validate configuration
python -m ingestor.scenario_validator azure_full --env-file .env.basic-pdf.example

# 3. Setup index (first time only)
python -m ingestor.cli --setup-index --env-file .env.basic-pdf.example

# 4. Process PDFs
python -m ingestor.cli --pdf ../documents/sample.pdf --env-file .env.basic-pdf.example

# 5. Process multiple files
python -m ingestor.cli --glob "../documents/*.pdf" --env-file .env.basic-pdf.example

# 6. Query your documents
python -m ingestor.cli --query "What is the main topic?" --env-file .env.basic-pdf.example

# 7. Check index status
python -m ingestor.cli --check-index --env-file .env.basic-pdf.example
```

### Example 2: Production Deployment

```bash
# 1. Edit production env file (ONE TIME)
notepad .env.production.example
# Configure production Azure resources

# 2. Validate production config
python -m ingestor.scenario_validator azure_full --env-file .env.production.example

# 3. Setup production index
python -m ingestor.cli --setup-index --env-file .env.production.example

# 4. Process production documents
python -m ingestor.cli --glob "s:/production-docs/**/*.pdf" --env-file .env.production.example

# 5. Monitor with verbose output
python -m ingestor.cli --glob "s:/production-docs/**/*.pdf" --env-file .env.production.example --verbose
```

### Example 3: Offline Processing (FREE)

```bash
# 1. Edit offline env file
notepad ../../envs/.env.offline-with-vision.example
# Set:
# - EXTRACTION_MODE=markitdown
# - EMBEDDINGS_MODE=huggingface
# - VECTOR_STORE=chromadb
# - ENABLE_MEDIA_DESCRIPTION=false  # For 100% offline

# 2. Download models (ONE TIME, requires internet)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# 3. Validate offline config
python -m ingestor.scenario_validator offline --env-file ../../envs/.env.offline-with-vision.example

# 4. Process offline (works WITHOUT internet!)
python -m ingestor.cli --pdf ../documents/sample.pdf --env-file ../../envs/.env.offline-with-vision.example

# 5. Query offline
python -m ingestor.cli --query "What is this about?" --env-file ../../envs/.env.offline-with-vision.example
```

### Example 4: Switching Between Scenarios

```bash
# No copying needed - just change --env-file parameter!

# Test with Azure
python -m ingestor.cli --pdf test.pdf --env-file .env.basic-pdf.example

# Test with production config
python -m ingestor.cli --pdf test.pdf --env-file .env.production.example

# Test offline
python -m ingestor.cli --pdf test.pdf --env-file ../../envs/.env.offline-with-vision.example

# Compare performance
time python -m ingestor.cli --pdf large.pdf --env-file .env.basic-pdf.example
time python -m ingestor.cli --pdf large.pdf --env-file ../../envs/.env.offline-with-vision.example
```

---

## All Available Commands

### Validation

```bash
# Auto-detect scenario and validate
python -m ingestor.scenario_validator --env-file .env.basic-pdf.example

# Validate specific scenario
python -m ingestor.scenario_validator azure_full --env-file .env.basic-pdf.example
python -m ingestor.scenario_validator offline --env-file ../../envs/.env.offline-with-vision.example

# Verbose validation
python -m ingestor.scenario_validator --env-file .env.basic-pdf.example --verbose

# Show help
python -m ingestor.scenario_validator --help
```

### Processing

```bash
# Single PDF
python -m ingestor.cli --pdf document.pdf --env-file .env.basic-pdf.example

# Multiple PDFs with glob
python -m ingestor.cli --glob "documents/*.pdf" --env-file .env.basic-pdf.example
python -m ingestor.cli --glob "docs/**/*.{pdf,docx,pptx}" --env-file .env.basic-pdf.example

# With verbose output
python -m ingestor.cli --pdf document.pdf --env-file .env.basic-pdf.example --verbose

# Different file types
python -m ingestor.cli --pdf report.docx --env-file .env.basic-pdf.example
python -m ingestor.cli --pdf presentation.pptx --env-file .env.basic-pdf.example
```

### Querying

```bash
# Simple query
python -m ingestor.cli --query "What is the main topic?" --env-file .env.basic-pdf.example

# With verbose output
python -m ingestor.cli --query "Summarize the key findings" --env-file .env.basic-pdf.example --verbose
```

### Index Management (Azure Search only)

```bash
# Check index
python -m ingestor.cli --check-index --env-file .env.basic-pdf.example

# Setup/create index
python -m ingestor.cli --setup-index --env-file .env.basic-pdf.example

# Delete index (careful!)
python -m ingestor.cli --delete-index --env-file .env.basic-pdf.example
```

### Document Management

```bash
# Add document (default)
python -m ingestor.cli --pdf document.pdf --env-file .env.basic-pdf.example --action add

# Remove specific document
python -m ingestor.cli --pdf document.pdf --env-file .env.basic-pdf.example --action remove

# Remove all documents
python -m ingestor.cli --action removeall --env-file .env.basic-pdf.example
```

### Artifacts

```bash
# Clean artifacts
python -m ingestor.cli --clean-artifacts --env-file .env.basic-pdf.example
```

---

## Running Playbook Scripts

The playbook Python scripts still use `PipelineConfig.from_env()` which reads from `.env` in the current directory or environment variables.

### Option 1: Copy .env (Traditional)

```bash
cp .env.basic-pdf.example ../../.env
python 01_basic_pdf_ingestion.py
```

### Option 2: Export Environment Variables (Bash/Linux/Mac)

```bash
export $(cat .env.basic-pdf.example | grep -v '^#' | xargs)
python 01_basic_pdf_ingestion.py
```

### Option 3: PowerShell (Windows)

```powershell
# Load .env into environment
Get-Content .env.basic-pdf.example | ForEach-Object {
    if ($_ -match '^([^#][^=]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

# Run playbook
python 01_basic_pdf_ingestion.py
```

### Option 4: Use CLI Instead (Simplest!)

```bash
# Most playbooks can be replaced with CLI commands
python -m ingestor.cli --pdf documents/sample.pdf --env-file .env.basic-pdf.example
```

---

## Benefits of New Workflow

### ✅ No More Copying
- Keep credentials in template files
- Edit once, use forever
- No risk of accidentally committing secrets

### ✅ Easy Scenario Switching
- Change scenarios with just `--env-file` parameter
- Test multiple configs easily
- Compare performance across scenarios

### ✅ Better Organization
- All configs in `examples/playbooks/` or `envs/` directory
- Clear naming conventions
- Version control friendly

### ✅ Safer
- Templates stay as templates
- Less chance of overwriting configurations
- Can test without affecting current setup

### ✅ Flexible
- Works from any directory
- Auto-finds parent .env
- Supports relative and absolute paths

---

## Comparison

| Task | OLD Way | NEW Way |
|------|---------|---------|
| **Setup** | Copy .env, edit, test | Edit template once |
| **Switch Scenarios** | Copy, edit, test again | Just change `--env-file` |
| **Risk** | High (may commit .env) | Low (templates only) |
| **Steps** | 3-4 commands | 1 command |
| **Testing** | Hard to test multiple | Easy parallel testing |

---

## Migration Guide

### If You Currently Use Playbook Scripts

**Before:**
```bash
cp .env.basic-pdf.example ../../.env
python 01_basic_pdf_ingestion.py
```

**After (Option A - Use CLI):**
```bash
# Use CLI directly - simpler and no copying!
python -m ingestor.cli --pdf documents/sample.pdf --env-file .env.basic-pdf.example
```

**After (Option B - Keep Using Playbook):**
```bash
# Still works, just copy .env as before
cp .env.basic-pdf.example ../../.env
python 01_basic_pdf_ingestion.py
```

### If You Use Multiple Scenarios

**Before:**
```bash
# Tedious switching
cp .env.basic-pdf.example ../../.env
python -m ingestor.cli --pdf test.pdf

cp .env.production.example ../../.env
python -m ingestor.cli --pdf test.pdf
```

**After:**
```bash
# Easy switching - just change parameter!
python -m ingestor.cli --pdf test.pdf --env-file .env.basic-pdf.example
python -m ingestor.cli --pdf test.pdf --env-file .env.production.example
```

---

## Troubleshooting

### Issue: "Environment file not found"

```bash
# Check path (use ls or dir)
ls .env.basic-pdf.example

# Try absolute path
python -m ingestor.cli --pdf test.pdf --env-file C:\Work\ingest-o-bot\examples\playbooks\.env.basic-pdf.example

# Try from root directory
cd ../..
python -m ingestor.cli --pdf test.pdf --env-file examples/playbooks/.env.basic-pdf.example
```

### Issue: "Validation failed"

```bash
# Check what's wrong
python -m ingestor.scenario_validator --env-file .env.basic-pdf.example --verbose

# Verify credentials are filled in
notepad .env.basic-pdf.example
# Make sure no placeholders like "your_key_here" remain
```

### Issue: Playbook script can't find config

```bash
# Playbook scripts need .env in root or environment variables
# Option 1: Copy .env
cp .env.basic-pdf.example ../../.env

# Option 2: Use CLI instead
python -m ingestor.cli --pdf test.pdf --env-file .env.basic-pdf.example
```

---

## Best Practices

### 1. Keep Credentials in Templates
```bash
# Edit templates directly, don't create separate .env
notepad .env.basic-pdf.example  # Add real credentials here
notepad .env.production.example  # Add production credentials here

# Use with --env-file
python -m ingestor.cli --pdf test.pdf --env-file .env.basic-pdf.example
```

### 2. Use Aliases for Common Tasks

**PowerShell:**
```powershell
# Add to $PROFILE
function ingest-basic { python -m ingestor.cli $args --env-file examples\playbooks\.env.basic-pdf.example }
function ingest-prod { python -m ingestor.cli $args --env-file examples\playbooks\.env.production.example }

# Use
ingest-basic --pdf test.pdf
ingest-prod --glob "docs\*.pdf"
```

**Bash:**
```bash
# Add to ~/.bashrc
alias ingest-basic='python -m ingestor.cli --env-file examples/playbooks/.env.basic-pdf.example'
alias ingest-prod='python -m ingestor.cli --env-file examples/playbooks/.env.production.example'

# Use
ingest-basic --pdf test.pdf
ingest-prod --glob "docs/*.pdf"
```

### 3. Validate Before Processing

```bash
# Always validate first
python -m ingestor.scenario_validator --env-file .env.basic-pdf.example

# Then process
python -m ingestor.cli --pdf test.pdf --env-file .env.basic-pdf.example
```

---

## Summary

The new `--env-file` workflow is:
- ✅ **Simpler** - No more copying files
- ✅ **Safer** - Less risk of committing secrets
- ✅ **Flexible** - Easy scenario switching
- ✅ **Faster** - One command instead of three
- ✅ **Better** - Professional workflow

**Use it for all new work!** The old copy-paste method still works but is not recommended.
