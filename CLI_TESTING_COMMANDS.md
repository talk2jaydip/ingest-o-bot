# CLI Testing Commands for All Environment Scenarios

Quick reference guide for testing ingest-o-bot with all created environment configurations.

---

## Quick Setup Pattern

```bash
# 1. Copy the scenario template
cp envs/.env.[scenario].example .env

# 2. Edit and add your credentials
nano .env  # or code .env

# 3. Validate configuration
python -m ingestor.scenario_validator

# 4. Pre-flight check
python -m ingestor.cli --validate

# 5. Test with sample document
python -m ingestor.cli --pdf ./test.pdf

# 6. Process multiple documents
python -m ingestor.cli --glob "docs/**/*.pdf"
```

---

## Scenario 1: Azure Local Input (Full Azure Stack, Local Files)

### Setup
```bash
# Copy template
cp envs/.env.azure-local-input.example .env

# Edit these required values:
# - AZURE_DI_ENDPOINT
# - AZURE_DI_KEY
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
# - AZURE_SEARCH_ENDPOINT
# - AZURE_SEARCH_KEY
# - AZURE_SEARCH_INDEX_NAME
```

### Validation
```bash
# Validate all Azure credentials
python -m ingestor.scenario_validator azure_full

# Check Azure connections
python -m ingestor.cli --validate

# Verify index exists (create if not)
python -m ingestor.cli --check-index
python -m ingestor.cli --setup-index  # If needed
```

### Testing Commands
```bash
# Test single PDF (local file)
python -m ingestor.cli --pdf ./documents/sample.pdf

# Test with verbose output
python -m ingestor.cli --pdf ./documents/sample.pdf --verbose

# Process multiple PDFs
python -m ingestor.cli --glob "documents/*.pdf"

# Process with patterns
python -m ingestor.cli --glob "docs/**/*.{pdf,docx,pptx}"

# Test with media description (GPT-4o vision)
# Ensure ENABLE_MEDIA_DESCRIPTION=true in .env
python -m ingestor.cli --pdf ./document-with-charts.pdf --verbose

# Test document removal
python -m ingestor.cli --pdf ./test.pdf --action remove

# Test query
python -m ingestor.cli --query "What is the main topic discussed?"

# Clean artifacts
python -m ingestor.cli --clean-artifacts
```

### Advanced Testing
```bash
# Dry run (validate without processing)
python -m ingestor.cli --pdf ./test.pdf --pre-check

# Process with custom chunk size (if supported)
# Edit .env: CHUNK_SIZE=1500
python -m ingestor.cli --pdf ./test.pdf

# Test table extraction
# Ensure AZURE_DI_EXTRACT_TABLES=true
python -m ingestor.cli --pdf ./document-with-tables.pdf --verbose

# Monitor processing
python -m ingestor.cli --glob "large_docs/*.pdf" --verbose --show-progress
```

---

## Scenario 2: Azure + ChromaDB Hybrid (Cost Optimized)

### Setup
```bash
# Copy template
cp envs/.env.azure-chromadb-hybrid.example .env

# Edit these required values:
# - AZURE_DI_ENDPOINT
# - AZURE_DI_KEY
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_EMBEDDING_DEPLOYMENT
# - CHROMADB_PATH (default: ./chroma_db)
# - CHROMADB_COLLECTION_NAME

# Install ChromaDB if not already installed
pip install chromadb
```

### Validation
```bash
# Validate hybrid configuration
python -m ingestor.scenario_validator

# Verify Azure services (DI + OpenAI only, no Search)
python -m ingestor.cli --validate

# Check ChromaDB collection (auto-created on first run)
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); print(client.list_collections())"
```

### Testing Commands
```bash
# Test single document
python -m ingestor.cli --pdf ./documents/sample.pdf

# Process batch
python -m ingestor.cli --glob "documents/*.pdf"

# Query ChromaDB
python -m ingestor.cli --query "What are the key findings?"

# Check ChromaDB statistics
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('ingestor-docs-hybrid')
print(f'Total documents: {collection.count()}')
"

# Test removal from ChromaDB
python -m ingestor.cli --pdf ./test.pdf --action remove

# Delete and recreate collection
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
try:
    client.delete_collection('ingestor-docs-hybrid')
    print('Collection deleted')
except:
    print('Collection does not exist')
"

# Backup ChromaDB data
cp -r ./chroma_db ./chroma_db_backup_$(date +%Y%m%d)
```

### Performance Testing
```bash
# Test with large batch
python -m ingestor.cli --glob "large_docs/**/*.pdf" --verbose

# Monitor disk usage
du -sh ./chroma_db
du -h ./chroma_db/* | sort -h

# Test concurrent access (multiple terminals)
# Terminal 1:
python -m ingestor.cli --glob "batch1/*.pdf"
# Terminal 2:
python -m ingestor.cli --query "test query"
```

---

## Scenario 3: Fully Offline (100% Free)

### Setup
```bash
# Copy template
cp envs/.env.offline-with-vision.example .env

# Install required packages
pip install chromadb sentence-transformers torch markitdown

# Download models (ONE TIME, requires internet)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# For GPU support (optional)
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Edit these values:
# - ENABLE_MEDIA_DESCRIPTION=false  (for 100% offline)
# - MARKITDOWN_IMAGE_MODE=skip  (for 100% offline)
# - CHROMADB_PATH=./chroma_db_offline
```

### Validation
```bash
# Validate offline setup
python -m ingestor.scenario_validator offline

# Verify no network calls (should work without internet)
python -m ingestor.cli --validate

# Check model availability
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
print(f'Model loaded: {model}')
print(f'Dimensions: {model.get_sentence_embedding_dimension()}')
"
```

### Testing Commands (100% Offline)
```bash
# Disconnect internet to verify offline capability (optional)
# Then test:

# Process single PDF
python -m ingestor.cli --pdf ./documents/sample.pdf

# Process multiple formats
python -m ingestor.cli --glob "docs/**/*.{pdf,docx,pptx,txt,md}"

# Query offline
python -m ingestor.cli --query "What is discussed?"

# Test with verbose logging
python -m ingestor.cli --pdf ./test.pdf --verbose

# Verify no network calls
# Watch for any errors about network connectivity
python -m ingestor.cli --pdf ./test.pdf --verbose 2>&1 | grep -i "network\|connection\|timeout"
```

### Testing with Optional Vision (Hybrid Mode)
```bash
# Edit .env:
# ENABLE_MEDIA_DESCRIPTION=true
# MARKITDOWN_IMAGE_MODE=describe
# Add Azure OpenAI GPT-4o credentials

# Reconnect internet
# Test with images
python -m ingestor.cli --pdf ./document-with-charts.pdf --verbose

# Only images are sent to cloud, everything else offline
# Check logs for vision API calls
python -m ingestor.cli --pdf ./test.pdf --verbose 2>&1 | grep -i "vision\|gpt-4o\|image"
```

### Performance Testing (Offline)
```bash
# Test CPU performance
time python -m ingestor.cli --pdf ./large-document.pdf

# Test with different batch sizes
# Edit .env: HUGGINGFACE_BATCH_SIZE=16
python -m ingestor.cli --pdf ./test.pdf
# Edit .env: HUGGINGFACE_BATCH_SIZE=64
python -m ingestor.cli --pdf ./test.pdf

# Monitor resource usage
# Linux/Mac:
top -p $(pgrep -f "ingestor.cli")
# Windows:
# Use Task Manager or:
# Get-Process python | Select-Object CPU,Memory
```

---

## Scenario 4: Hybrid Scenarios (Mix & Match)

### Setup for Different Hybrid Combinations

#### Hybrid 1: Markitdown + Hugging Face + Azure Search
```bash
cp envs/.env.hybrid-scenarios.example .env

# Uncomment and configure SCENARIO 1 section in .env
# Required:
# - AZURE_SEARCH_ENDPOINT
# - AZURE_SEARCH_KEY
# - EXTRACTION_MODE=markitdown
# - EMBEDDINGS_MODE=huggingface
# - VECTOR_STORE=azure_search

pip install sentence-transformers torch

# Test
python -m ingestor.cli --validate
python -m ingestor.cli --pdf ./test.pdf
```

#### Hybrid 2: Azure DI + Hugging Face + ChromaDB
```bash
cp envs/.env.hybrid-scenarios.example .env

# Uncomment and configure SCENARIO 2 section in .env
# Required:
# - AZURE_DI_ENDPOINT, AZURE_DI_KEY
# - EXTRACTION_MODE=azure_di
# - EMBEDDINGS_MODE=huggingface
# - VECTOR_STORE=chromadb

pip install chromadb sentence-transformers torch

# Test
python -m ingestor.cli --validate
python -m ingestor.cli --pdf ./test.pdf
```

#### Hybrid 3: Markitdown + Cohere + ChromaDB
```bash
cp envs/.env.hybrid-scenarios.example .env

# Uncomment and configure SCENARIO 3 section in .env
# Required:
# - COHERE_API_KEY
# - EXTRACTION_MODE=markitdown
# - EMBEDDINGS_MODE=cohere
# - VECTOR_STORE=chromadb

pip install chromadb cohere

# Test multilingual document
python -m ingestor.cli --pdf ./spanish-document.pdf
python -m ingestor.cli --pdf ./chinese-document.pdf
```

#### Hybrid 4: Markitdown + OpenAI + ChromaDB
```bash
cp envs/.env.hybrid-scenarios.example .env

# Uncomment and configure SCENARIO 4 section in .env
# Required:
# - OPENAI_API_KEY
# - EXTRACTION_MODE=markitdown
# - EMBEDDINGS_MODE=openai
# - VECTOR_STORE=chromadb

pip install chromadb openai

# Test
python -m ingestor.cli --validate
python -m ingestor.cli --pdf ./test.pdf
```

---

## Testing Checklist for Each Scenario

### Basic Functionality Tests
```bash
# 1. Validation
python -m ingestor.scenario_validator
python -m ingestor.cli --validate

# 2. Single document
python -m ingestor.cli --pdf ./test-documents/sample.pdf

# 3. Multiple documents
python -m ingestor.cli --glob "test-documents/*.pdf"

# 4. Different formats
python -m ingestor.cli --pdf ./test.docx
python -m ingestor.cli --pdf ./test.pptx

# 5. Query test
python -m ingestor.cli --query "test query"

# 6. Removal test
python -m ingestor.cli --pdf ./test.pdf --action remove

# 7. Clean artifacts
python -m ingestor.cli --clean-artifacts
```

### Advanced Tests
```bash
# 8. Pre-check (dry run)
python -m ingestor.cli --pdf ./test.pdf --pre-check

# 9. Verbose output
python -m ingestor.cli --pdf ./test.pdf --verbose

# 10. Index operations (Azure Search scenarios only)
python -m ingestor.cli --check-index
python -m ingestor.cli --setup-index

# 11. Glob patterns
python -m ingestor.cli --glob "**/*.pdf"
python -m ingestor.cli --glob "docs/**/*.{pdf,docx}"

# 12. Error handling
python -m ingestor.cli --pdf ./nonexistent.pdf  # Should handle gracefully

# 13. Large file test
python -m ingestor.cli --pdf ./large-document.pdf --verbose

# 14. Batch processing with progress
python -m ingestor.cli --glob "large-batch/*.pdf" --verbose
```

---

## Automated Testing Script

Create `test-all-scenarios.sh`:

```bash
#!/bin/bash

# Test all environment scenarios
# Usage: ./test-all-scenarios.sh

set -e  # Exit on error

TEST_PDF="test-documents/sample.pdf"
BACKUP_ENV=".env.backup"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "Testing All Environment Scenarios"
echo "=================================="

# Backup current .env if exists
if [ -f .env ]; then
    echo "Backing up current .env to $BACKUP_ENV"
    cp .env "$BACKUP_ENV"
fi

# Test function
test_scenario() {
    local scenario_name=$1
    local env_file=$2
    local scenario_type=$3

    echo ""
    echo -e "${YELLOW}Testing: $scenario_name${NC}"
    echo "=================================="

    # Copy template
    cp "$env_file" .env
    echo "✓ Copied $env_file"

    # Validate
    echo "Running validation..."
    if python -m ingestor.scenario_validator $scenario_type 2>&1 | grep -q "✓"; then
        echo -e "${GREEN}✓ Validation passed${NC}"
    else
        echo -e "${RED}✗ Validation failed${NC}"
        return 1
    fi

    # Pre-check
    echo "Running pre-check..."
    if python -m ingestor.cli --validate; then
        echo -e "${GREEN}✓ Pre-check passed${NC}"
    else
        echo -e "${RED}✗ Pre-check failed${NC}"
        return 1
    fi

    # Test processing (if test PDF exists)
    if [ -f "$TEST_PDF" ]; then
        echo "Testing document processing..."
        if python -m ingestor.cli --pdf "$TEST_PDF"; then
            echo -e "${GREEN}✓ Processing test passed${NC}"
        else
            echo -e "${RED}✗ Processing test failed${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ Skipping processing test (no test PDF)${NC}"
    fi

    echo -e "${GREEN}✓ $scenario_name: ALL TESTS PASSED${NC}"
}

# Test each scenario
test_scenario "Azure Local Input" "envs/.env.azure-local-input.example" "azure_full"
test_scenario "Azure + ChromaDB" "envs/.env.azure-chromadb-hybrid.example" "hybrid"
test_scenario "Fully Offline" "envs/.env.offline-with-vision.example" "offline"

# Restore original .env
if [ -f "$BACKUP_ENV" ]; then
    echo ""
    echo "Restoring original .env from backup"
    mv "$BACKUP_ENV" .env
fi

echo ""
echo -e "${GREEN}=================================="
echo "All Scenario Tests Completed!"
echo "==================================${NC}"
```

Make it executable:
```bash
chmod +x test-all-scenarios.sh
./test-all-scenarios.sh
```

---

## Quick Reference: Switching Between Scenarios

```bash
# Save your current working .env
cp .env .env.working

# Try Azure Local Input
cp envs/.env.azure-local-input.example .env
# Edit credentials...
python -m ingestor.cli --pdf ./test.pdf

# Try Azure + ChromaDB
cp envs/.env.azure-chromadb-hybrid.example .env
# Edit credentials...
python -m ingestor.cli --pdf ./test.pdf

# Try Fully Offline
cp envs/.env.offline-with-vision.example .env
python -m ingestor.cli --pdf ./test.pdf

# Restore your working config
cp .env.working .env
```

---

## Troubleshooting Commands

### General Diagnostics
```bash
# Check Python environment
python --version
pip list | grep -E "(azure|chromadb|sentence|torch|cohere|openai)"

# Verify configuration
python -m ingestor.scenario_validator --verbose

# Check file permissions
ls -la .env
ls -la envs/*.example

# View logs
tail -f ./logs/ingestor.log

# Clear cache and artifacts
python -m ingestor.cli --clean-artifacts
rm -rf ./artifacts/*
rm -rf ./cache/*
```

### Azure-Specific Diagnostics
```bash
# Test Azure DI connectivity
python -c "
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import os
client = DocumentIntelligenceClient(
    endpoint=os.getenv('AZURE_DI_ENDPOINT'),
    credential=AzureKeyCredential(os.getenv('AZURE_DI_KEY'))
)
print('Azure DI: Connected')
"

# Test Azure OpenAI connectivity
python -c "
import openai
import os
openai.api_type = 'azure'
openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')
openai.api_base = os.getenv('AZURE_OPENAI_ENDPOINT')
openai.api_version = '2024-02-15-preview'
print('Azure OpenAI: Connected')
"

# Check Azure Search index
python -m ingestor.cli --check-index
```

### ChromaDB Diagnostics
```bash
# List collections
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
print('Collections:', client.list_collections())
"

# Get collection info
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('ingestor-docs-offline')
print(f'Count: {collection.count()}')
print(f'Metadata: {collection.metadata}')
"

# Reset ChromaDB
rm -rf ./chroma_db
python -m ingestor.cli --pdf ./test.pdf  # Recreates collection
```

### Offline Mode Diagnostics
```bash
# Check model availability
python -c "
from sentence_transformers import SentenceTransformer
import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'
model = SentenceTransformer('all-mpnet-base-v2')
print('Model available offline')
"

# List cached models
ls -lh ~/.cache/torch/sentence_transformers/
ls -lh ./models/huggingface/  # If custom cache
```

---

## Performance Benchmarking

```bash
# Create benchmark script
cat > benchmark.sh << 'EOF'
#!/bin/bash
SCENARIO=$1
TEST_FILES="test-documents/*.pdf"

echo "Benchmarking: $SCENARIO"
echo "Start: $(date)"

time python -m ingestor.cli --glob "$TEST_FILES" --verbose

echo "End: $(date)"
EOF

chmod +x benchmark.sh

# Run benchmarks
./benchmark.sh "Azure Local Input"
./benchmark.sh "Azure ChromaDB"
./benchmark.sh "Offline"
```

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
# .github/workflows/test-scenarios.yml
name: Test All Scenarios

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        scenario:
          - offline
          - azure-chromadb

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install chromadb sentence-transformers torch

      - name: Download models (offline scenario)
        if: matrix.scenario == 'offline'
        run: |
          python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

      - name: Setup environment
        run: |
          cp envs/.env.${{ matrix.scenario }}.example .env

      - name: Validate configuration
        run: |
          python -m ingestor.scenario_validator

      - name: Run tests
        run: |
          python -m pytest tests/test_cli_comprehensive.py
```

---

## Summary Commands by Scenario

| Scenario | Setup | Test | Query |
|----------|-------|------|-------|
| **Azure Local** | `cp envs/.env.azure-local-input.example .env` | `python -m ingestor.cli --pdf ./test.pdf` | `python -m ingestor.cli --query "test"` |
| **Azure + ChromaDB** | `cp envs/.env.azure-chromadb-hybrid.example .env` | `python -m ingestor.cli --pdf ./test.pdf` | `python -m ingestor.cli --query "test"` |
| **Offline** | `cp envs/.env.offline-with-vision.example .env` | `python -m ingestor.cli --pdf ./test.pdf` | `python -m ingestor.cli --query "test"` |
| **Hybrid** | `cp envs/.env.hybrid-scenarios.example .env` | `python -m ingestor.cli --pdf ./test.pdf` | `python -m ingestor.cli --query "test"` |

---

For more help:
- Run: `python -m ingestor.cli --help`
- Check: `python -m ingestor.scenario_validator --help`
- See: `docs/CLI-TESTING-SUMMARY.md`
- Read: `ENVIRONMENT_CONFIGURATION_GUIDE.md`
