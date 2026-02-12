# Quick Test Commands - Windows

Fast reference for testing ingest-o-bot on Windows with all environment scenarios.

---

## Automated Testing (Easiest)

### Option 1: PowerShell Script (Recommended)
```powershell
# Run automated tests for all scenarios
.\test-scenarios.ps1
```

### Option 2: Batch Script
```cmd
# Run automated tests for all scenarios
test-scenarios.bat
```

---

## Manual Testing by Scenario

### Scenario 1: Azure Local Input (Full Azure, No Blob Storage)

```cmd
REM Setup
copy envs\.env.azure-local-input.example .env
notepad .env  REM Edit your Azure credentials

REM Validate
python -m ingestor.scenario_validator azure_full
python -m ingestor.cli --validate

REM Setup index (first time only)
python -m ingestor.cli --setup-index

REM Test single file
python -m ingestor.cli --pdf test-documents\sample.pdf

REM Test multiple files
python -m ingestor.cli --glob "documents\*.pdf"
python -m ingestor.cli --glob "docs\**\*.{pdf,docx,pptx}"

REM Query
python -m ingestor.cli --query "What is the main topic?"

REM Test with vision (GPT-4o)
REM Ensure ENABLE_MEDIA_DESCRIPTION=true in .env
python -m ingestor.cli --pdf document-with-charts.pdf --verbose
```

---

### Scenario 2: Azure + ChromaDB (Best Cost Savings)

```cmd
REM Install ChromaDB if needed
pip install chromadb

REM Setup
copy envs\.env.azure-chromadb-hybrid.example .env
notepad .env  REM Edit Azure DI and OpenAI credentials (no Search needed!)

REM Validate
python -m ingestor.scenario_validator hybrid
python -m ingestor.cli --validate

REM Test
python -m ingestor.cli --pdf test-documents\sample.pdf
python -m ingestor.cli --glob "documents\*.pdf"

REM Query ChromaDB
python -m ingestor.cli --query "What are the findings?"

REM Check ChromaDB stats
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); print(f'Collections: {client.list_collections()}')"

REM Backup ChromaDB
xcopy /E /I chroma_db chroma_db_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%
```

---

### Scenario 3: Fully Offline (100% FREE)

```cmd
REM Install dependencies
pip install chromadb sentence-transformers torch markitdown

REM Download models (ONE TIME, requires internet)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

REM Setup
copy envs\.env.offline-with-vision.example .env
notepad .env  REM Set ENABLE_MEDIA_DESCRIPTION=false for 100% offline

REM Validate
python -m ingestor.scenario_validator offline
python -m ingestor.cli --validate

REM Test (works WITHOUT internet!)
python -m ingestor.cli --pdf test-documents\sample.pdf
python -m ingestor.cli --glob "documents\*.{pdf,docx,pptx,txt,md}"

REM Query
python -m ingestor.cli --query "What is discussed?"

REM Check model
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-mpnet-base-v2'); print(f'Dims: {model.get_sentence_embedding_dimension()}')"
```

---

### Scenario 4: Hybrid Mix & Match

```cmd
REM Copy template
copy envs\.env.hybrid-scenarios.example .env

REM Edit .env and uncomment ONE scenario section:
REM - Scenario 1: Markitdown + HF + Azure Search (cost-optimized)
REM - Scenario 2: Azure DI + HF + ChromaDB (quality + savings)
REM - Scenario 3: Markitdown + Cohere + ChromaDB (multilingual)
REM - Scenario 4: Markitdown + OpenAI + ChromaDB (OpenAI alternative)
REM - Scenario 5: Full Azure (maximum quality)
REM - Scenario 6: All local (development)
notepad .env

REM Install dependencies for your chosen scenario
pip install chromadb sentence-transformers  REM For HF embeddings
pip install cohere  REM For Cohere embeddings
pip install openai  REM For OpenAI embeddings

REM Validate
python -m ingestor.scenario_validator
python -m ingestor.cli --validate

REM Test
python -m ingestor.cli --pdf test-documents\sample.pdf
```

---

## Common Commands (All Scenarios)

### Validation
```cmd
REM Auto-detect and validate current .env
python -m ingestor.scenario_validator

REM Validate specific scenario
python -m ingestor.scenario_validator azure_full
python -m ingestor.scenario_validator hybrid
python -m ingestor.scenario_validator offline

REM Full pre-flight check
python -m ingestor.cli --validate
python -m ingestor.cli --pre-check
```

### Processing
```cmd
REM Single file
python -m ingestor.cli --pdf my-document.pdf

REM Multiple files
python -m ingestor.cli --glob "documents\*.pdf"
python -m ingestor.cli --glob "docs\**\*.{pdf,docx,pptx}"

REM With verbose output
python -m ingestor.cli --pdf my-document.pdf --verbose

REM Different formats
python -m ingestor.cli --pdf report.docx
python -m ingestor.cli --pdf presentation.pptx
python -m ingestor.cli --pdf notes.txt
```

### Querying
```cmd
REM Basic query
python -m ingestor.cli --query "What is the main topic?"

REM With verbose output
python -m ingestor.cli --query "Summarize the key findings" --verbose
```

### Index Management (Azure Search only)
```cmd
REM Check if index exists
python -m ingestor.cli --check-index

REM Create index
python -m ingestor.cli --setup-index

REM Delete index (careful!)
python -m ingestor.cli --delete-index
```

### Document Management
```cmd
REM Add document (default action)
python -m ingestor.cli --pdf document.pdf --action add

REM Remove specific document
python -m ingestor.cli --pdf document.pdf --action remove

REM Remove all documents
python -m ingestor.cli --action removeall
```

### Artifacts
```cmd
REM Clean artifacts
python -m ingestor.cli --clean-artifacts

REM View artifacts
dir artifacts
dir artifacts\extracted
dir artifacts\chunks

REM Clean manually
rmdir /S /Q artifacts
mkdir artifacts
```

---

## Quick Scenario Switching

```cmd
REM Save current working config
copy .env .env.working

REM Try Azure Local Input
copy envs\.env.azure-local-input.example .env
REM Edit credentials, then test...
python -m ingestor.cli --pdf test.pdf

REM Try Azure + ChromaDB
copy envs\.env.azure-chromadb-hybrid.example .env
REM Edit credentials, then test...
python -m ingestor.cli --pdf test.pdf

REM Try Fully Offline
copy envs\.env.offline-with-vision.example .env
python -m ingestor.cli --pdf test.pdf

REM Restore working config
copy .env.working .env
```

---

## Troubleshooting Commands

### Check Installation
```cmd
REM Python version
python --version

REM Installed packages
pip list | findstr /I "azure chromadb sentence torch cohere openai"

REM Check .env file
type .env | findstr /I "MODE ENDPOINT KEY"
```

### View Logs
```cmd
REM View recent logs
type logs\ingestor.log | more

REM Tail logs (PowerShell)
Get-Content -Path logs\ingestor.log -Wait -Tail 50

REM Clear logs
del logs\*.log
```

### Azure Connectivity Tests
```cmd
REM Test Azure DI
python -c "from azure.ai.documentintelligence import DocumentIntelligenceClient; from azure.core.credentials import AzureKeyCredential; import os; client = DocumentIntelligenceClient(endpoint=os.getenv('AZURE_DI_ENDPOINT'), credential=AzureKeyCredential(os.getenv('AZURE_DI_KEY'))); print('Azure DI: Connected')"

REM Test Azure OpenAI
python -c "import openai, os; openai.api_type='azure'; openai.api_key=os.getenv('AZURE_OPENAI_API_KEY'); openai.api_base=os.getenv('AZURE_OPENAI_ENDPOINT'); print('Azure OpenAI: Connected')"

REM Check Azure Search index
python -m ingestor.cli --check-index
```

### ChromaDB Commands
```cmd
REM List collections
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); print([c.name for c in client.list_collections()])"

REM Get collection count
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); collection = client.get_collection('ingestor-docs-offline'); print(f'Documents: {collection.count()}')"

REM Delete collection
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); client.delete_collection('ingestor-docs-offline'); print('Deleted')"

REM Check disk usage
dir chroma_db /s
```

### Offline Mode Tests
```cmd
REM Check if model is downloaded
dir %USERPROFILE%\.cache\torch\sentence_transformers

REM Test model loading
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-mpnet-base-v2'); print('Model loaded')"

REM Test offline (disconnect internet, then run)
python -m ingestor.cli --pdf test.pdf --verbose
```

---

## Performance Testing

```cmd
REM Time single document processing
powershell "Measure-Command {python -m ingestor.cli --pdf test.pdf}"

REM Process large batch with timing
powershell "$start = Get-Date; python -m ingestor.cli --glob 'large-batch\*.pdf'; $end = Get-Date; Write-Host \"Duration: $($end - $start)\""

REM Monitor resource usage
REM Open Task Manager (Ctrl+Shift+Esc) and watch Python process while running:
python -m ingestor.cli --glob "large-docs\*.pdf" --verbose
```

---

## Automated Test Suites

### Run Comprehensive CLI Tests
```cmd
REM Run all CLI tests
python tests\test_cli_comprehensive.py

REM Run with verbose output
python tests\test_cli_comprehensive.py --verbose

REM Run including destructive tests (careful!)
python tests\test_cli_comprehensive.py --include-destructive
```

### Run Scenario-Specific Tests
```cmd
REM Test current scenario
python -m pytest tests\ -v

REM Test with coverage
python -m pytest tests\ --cov=src\ingestor --cov-report=html
```

---

## One-Liner Quick Tests

```cmd
REM Quick offline test
copy envs\.env.offline-with-vision.example .env && python -m ingestor.cli --pdf test.pdf

REM Quick Azure test (edit .env first!)
copy envs\.env.azure-local-input.example .env && python -m ingestor.cli --validate && python -m ingestor.cli --pdf test.pdf

REM Quick validation
python -m ingestor.scenario_validator && python -m ingestor.cli --validate

REM Quick query test
python -m ingestor.cli --query "test" --verbose
```

---

## Environment Variables Quick Check

```cmd
REM Show key configuration
python -c "import os; print(f'EXTRACTION_MODE: {os.getenv(\"EXTRACTION_MODE\")}'); print(f'EMBEDDINGS_MODE: {os.getenv(\"EMBEDDINGS_MODE\")}'); print(f'VECTOR_STORE: {os.getenv(\"VECTOR_STORE\")}')"

REM Show all env vars (PowerShell)
Get-Content .env | Where-Object {$_ -notmatch '^#' -and $_ -match '='}

REM Check specific value
python -c "import os; print(os.getenv('AZURE_DI_ENDPOINT', 'Not set'))"
```

---

## Creating Test Documents

```cmd
REM Create test documents folder
if not exist test-documents mkdir test-documents

REM Create a simple test text file
echo This is a test document for ingestion. > test-documents\test.txt

REM Copy some sample PDFs
copy *.pdf test-documents\

REM List test documents
dir test-documents
```

---

## Comparison: Cost per 1000 Pages

| Scenario | Command | Cost |
|----------|---------|------|
| **Azure Local** | `copy envs\.env.azure-local-input.example .env` | ~$10-15 |
| **Azure + ChromaDB** | `copy envs\.env.azure-chromadb-hybrid.example .env` | ~$2-3 |
| **Fully Offline** | `copy envs\.env.offline-with-vision.example .env` | $0 |
| **Hybrid Mix** | `copy envs\.env.hybrid-scenarios.example .env` | Varies |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ SETUP                                                       │
├─────────────────────────────────────────────────────────────┤
│ copy envs\.env.[scenario].example .env                     │
│ notepad .env                                                │
│ python -m ingestor.scenario_validator                      │
├─────────────────────────────────────────────────────────────┤
│ PROCESS                                                     │
├─────────────────────────────────────────────────────────────┤
│ python -m ingestor.cli --pdf document.pdf                  │
│ python -m ingestor.cli --glob "docs\*.pdf"                 │
├─────────────────────────────────────────────────────────────┤
│ QUERY                                                       │
├─────────────────────────────────────────────────────────────┤
│ python -m ingestor.cli --query "What is this about?"       │
├─────────────────────────────────────────────────────────────┤
│ TROUBLESHOOT                                                │
├─────────────────────────────────────────────────────────────┤
│ python -m ingestor.cli --validate                          │
│ python -m ingestor.cli --verbose                           │
│ type logs\ingestor.log                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Help Commands

```cmd
REM General help
python -m ingestor.cli --help

REM Scenario validator help
python -m ingestor.scenario_validator --help

REM Check version
python -m ingestor.cli --version

REM List all options
python -m ingestor.cli --help | more
```

---

## For More Information

- **Full Guide**: [CLI_TESTING_COMMANDS.md](CLI_TESTING_COMMANDS.md)
- **Configuration**: [ENVIRONMENT_CONFIGURATION_GUIDE.md](ENVIRONMENT_CONFIGURATION_GUIDE.md)
- **Quick Reference**: [ENVIRONMENT_QUICK_REFERENCE.md](ENVIRONMENT_QUICK_REFERENCE.md)
- **CLI Tests**: [tests/README-CLI-TESTS.md](tests/README-CLI-TESTS.md)
- **Playbooks**: [examples/playbooks/README.md](examples/playbooks/README.md)

---

**Ready to start?** Run: `.\test-scenarios.ps1`
