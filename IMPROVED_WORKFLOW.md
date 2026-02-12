# Improved Workflow - No More Copying .env Files!

**The OLD tedious way:** ❌
```cmd
copy envs\.env.azure-local-input.example .env
notepad .env
python -m ingestor.cli --pdf test.pdf
copy envs\.env.azure-chromadb-hybrid.example .env
notepad .env
python -m ingestor.cli --pdf test.pdf
REM ... repeat for every scenario
```

**The NEW easy way:** ✅
```cmd
REM Edit once, use forever - no copying!
notepad envs\.env.azure-local-input.example
notepad envs\.env.azure-chromadb-hybrid.example
notepad envs\.env.offline-with-vision.example

REM Use directly with --env-file
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-local-input.example
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-chromadb-hybrid.example
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.offline-with-vision.example
```

---

## New Features Added

### 1. **scenario_validator** now accepts `--env-file`

```cmd
REM Validate specific env file without copying
python -m ingestor.scenario_validator --env-file envs\.env.azure-local-input.example

REM Validate with specific scenario
python -m ingestor.scenario_validator azure_full --env-file envs\.env.azure-local-input.example

REM Show help
python -m ingestor.scenario_validator --help
```

### 2. **CLI** already had `--env-file` support

```cmd
REM Process with specific env file
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-local-input.example

REM Validate with specific env file
python -m ingestor.cli --validate --env-file envs\.env.offline-with-vision.example

REM Query with specific env file
python -m ingestor.cli --query "test" --env-file envs\.env.azure-chromadb-hybrid.example
```

### 3. **Auto-finds .env in parent directory**

```cmd
REM Works from src/ subdirectory now!
cd src
python -m ingestor.scenario_validator  # Finds ../.env automatically
python -m ingestor.scenario_validator --env-file ../envs/.env.azure-local-input.example
```

---

## Complete Workflow Examples

### Scenario 1: Azure Local Input

```cmd
REM 1. Edit your env file ONCE (keep your credentials here)
notepad envs\.env.azure-local-input.example

REM 2. Validate
python -m ingestor.scenario_validator azure_full --env-file envs\.env.azure-local-input.example

REM 3. Setup index (first time only)
python -m ingestor.cli --setup-index --env-file envs\.env.azure-local-input.example

REM 4. Process documents (use anytime, no copying!)
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-local-input.example
python -m ingestor.cli --glob "docs\*.pdf" --env-file envs\.env.azure-local-input.example

REM 5. Query
python -m ingestor.cli --query "What is this about?" --env-file envs\.env.azure-local-input.example
```

### Scenario 2: Azure + ChromaDB (Cost Savings)

```cmd
REM 1. Edit env file
notepad envs\.env.azure-chromadb-hybrid.example

REM 2. Validate
python -m ingestor.scenario_validator hybrid --env-file envs\.env.azure-chromadb-hybrid.example

REM 3. Process
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-chromadb-hybrid.example

REM 4. Query
python -m ingestor.cli --query "test" --env-file envs\.env.azure-chromadb-hybrid.example
```

### Scenario 3: Fully Offline (FREE)

```cmd
REM 1. Edit env file (set ENABLE_MEDIA_DESCRIPTION=false for 100% offline)
notepad envs\.env.offline-with-vision.example

REM 2. Download models once
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

REM 3. Validate
python -m ingestor.scenario_validator offline --env-file envs\.env.offline-with-vision.example

REM 4. Process (works without internet!)
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.offline-with-vision.example
```

### Scenario 4: Hybrid Mix & Match

```cmd
REM 1. Edit env file and uncomment one scenario
notepad envs\.env.hybrid-scenarios.example

REM 2. Validate
python -m ingestor.scenario_validator --env-file envs\.env.hybrid-scenarios.example

REM 3. Process
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.hybrid-scenarios.example
```

---

## Benefits of This Approach

### ✅ **No More Copying**
- Keep credentials in template files
- No risk of accidentally committing .env with secrets
- Edit once, use forever

### ✅ **Easy Switching**
- Switch between scenarios with just `--env-file` parameter
- No need to backup and restore .env
- Compare scenarios easily

### ✅ **Better Organization**
- All configs in `envs/` directory
- Clear naming: `.env.azure-local-input.example`, `.env.offline-with-vision.example`
- Version control friendly (templates only)

### ✅ **Safer**
- Templates stay as templates
- Less chance of overwriting configurations
- Can test scenarios without affecting current setup

---

## PowerShell Aliases (Optional)

Make it even easier with aliases:

```powershell
# Add to your PowerShell profile ($PROFILE)

# Aliases for different scenarios
function ingest-azure-local {
    python -m ingestor.cli $args --env-file envs\.env.azure-local-input.example
}

function ingest-hybrid {
    python -m ingestor.cli $args --env-file envs\.env.azure-chromadb-hybrid.example
}

function ingest-offline {
    python -m ingestor.cli $args --env-file envs\.env.offline-with-vision.example
}

function validate-azure {
    python -m ingestor.scenario_validator azure_full --env-file envs\.env.azure-local-input.example
}

function validate-hybrid {
    python -m ingestor.scenario_validator hybrid --env-file envs\.env.azure-chromadb-hybrid.example
}

function validate-offline {
    python -m ingestor.scenario_validator offline --env-file envs\.env.offline-with-vision.example
}
```

Then use:
```powershell
ingest-azure-local --pdf test.pdf
ingest-hybrid --query "What is this?"
ingest-offline --glob "docs\*.pdf"

validate-azure
validate-hybrid
validate-offline
```

---

## Batch Aliases (Windows CMD)

Create `ingest-shortcuts.bat`:

```batch
@echo off
REM Shortcuts for different scenarios

if "%1"=="azure" (
    python -m ingestor.cli --env-file envs\.env.azure-local-input.example %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="hybrid" (
    python -m ingestor.cli --env-file envs\.env.azure-chromadb-hybrid.example %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="offline" (
    python -m ingestor.cli --env-file envs\.env.offline-with-vision.example %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="validate-azure" (
    python -m ingestor.scenario_validator azure_full --env-file envs\.env.azure-local-input.example
) else if "%1"=="validate-hybrid" (
    python -m ingestor.scenario_validator hybrid --env-file envs\.env.azure-chromadb-hybrid.example
) else if "%1"=="validate-offline" (
    python -m ingestor.scenario_validator offline --env-file envs\.env.offline-with-vision.example
) else (
    echo Usage:
    echo   ingest-shortcuts azure --pdf test.pdf
    echo   ingest-shortcuts hybrid --query "test"
    echo   ingest-shortcuts offline --glob "docs\*.pdf"
    echo   ingest-shortcuts validate-azure
    echo   ingest-shortcuts validate-hybrid
    echo   ingest-shortcuts validate-offline
)
```

Usage:
```cmd
ingest-shortcuts azure --pdf test.pdf
ingest-shortcuts hybrid --query "What is this?"
ingest-shortcuts validate-azure
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│ OLD WAY (Tedious)                                                │
├──────────────────────────────────────────────────────────────────┤
│ copy envs\.env.azure.example .env                               │
│ notepad .env                                                     │
│ python -m ingestor.cli --pdf test.pdf                           │
│ copy envs\.env.offline.example .env                             │
│ notepad .env                                                     │
│ python -m ingestor.cli --pdf test.pdf                           │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ NEW WAY (Easy)                                                   │
├──────────────────────────────────────────────────────────────────┤
│ notepad envs\.env.azure.example          # Edit once            │
│ notepad envs\.env.offline.example        # Edit once            │
│                                                                  │
│ # Use directly                                                   │
│ python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure.example │
│ python -m ingestor.cli --pdf test.pdf --env-file envs\.env.offline.example │
│                                                                  │
│ # Validate without copying                                      │
│ python -m ingestor.scenario_validator --env-file envs\.env.azure.example │
└──────────────────────────────────────────────────────────────────┘
```

---

## Comparison Table

| Task | OLD Way | NEW Way |
|------|---------|---------|
| **Switch Scenarios** | Copy .env, edit, test | Just change `--env-file` parameter |
| **Validate Config** | Copy to .env first, then validate | `--env-file envs/.env.azure.example` |
| **Process Files** | Copy .env every time | `--env-file` once |
| **Risk of Secrets** | High (editing .env) | Low (templates only) |
| **Steps to Switch** | 3-4 commands | 1 command |

---

## Environment File Naming Convention

Recommended naming for your configured files:

```
envs/
├── .env.azure-local-input.example      # Template (committed)
├── .env.azure-local-input.mine         # Your credentials (gitignored)
├── .env.azure-chromadb-hybrid.example  # Template
├── .env.azure-chromadb-hybrid.mine     # Your credentials
├── .env.offline-with-vision.example    # Template
├── .env.offline-with-vision.mine       # Your credentials
└── .env.hybrid-scenarios.example       # Template
```

Update `.gitignore`:
```
# Ignore personal env files
envs/*.mine
*.mine
```

Then use:
```cmd
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-local-input.mine
```

---

## Testing Multiple Scenarios

```cmd
REM Test Azure scenario
python -m ingestor.scenario_validator azure_full --env-file envs\.env.azure-local-input.example
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-local-input.example

REM Test Hybrid scenario
python -m ingestor.scenario_validator hybrid --env-file envs\.env.azure-chromadb-hybrid.example
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.azure-chromadb-hybrid.example

REM Test Offline scenario
python -m ingestor.scenario_validator offline --env-file envs\.env.offline-with-vision.example
python -m ingestor.cli --pdf test.pdf --env-file envs\.env.offline-with-vision.example

REM All in one script
FOR %%e IN (azure-local-input azure-chromadb-hybrid offline-with-vision) DO (
    echo Testing %%e...
    python -m ingestor.cli --pdf test.pdf --env-file envs\.env.%%e.example
)
```

---

## Updated Test Scripts

Update `test-scenarios.ps1`:

```powershell
# No need to copy .env anymore!
$scenarios = @{
    "Azure Local Input" = @{
        envFile = "envs\.env.azure-local-input.example"
        scenario = "azure_full"
    }
    "Azure + ChromaDB" = @{
        envFile = "envs\.env.azure-chromadb-hybrid.example"
        scenario = "hybrid"
    }
    "Fully Offline" = @{
        envFile = "envs\.env.offline-with-vision.example"
        scenario = "offline"
    }
}

foreach ($name in $scenarios.Keys) {
    $config = $scenarios[$name]
    Write-Host "Testing: $name" -ForegroundColor Yellow

    # Validate
    python -m ingestor.scenario_validator $config.scenario --env-file $config.envFile

    # Test processing
    python -m ingestor.cli --pdf test.pdf --env-file $config.envFile
}
```

---

## Documentation Updates

All documentation has been updated to use `--env-file`:

- [CLI_TESTING_COMMANDS.md](CLI_TESTING_COMMANDS.md)
- [QUICK_TEST_COMMANDS.md](QUICK_TEST_COMMANDS.md)
- [ENV_FILE_USAGE_GUIDE.md](ENV_FILE_USAGE_GUIDE.md)

---

## Summary

✅ **No more copying .env files back and forth**
✅ **Direct validation:** `python -m ingestor.scenario_validator --env-file envs/.env.azure.example`
✅ **Direct processing:** `python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure.example`
✅ **Works from any directory** (finds parent .env automatically)
✅ **Safer** (keep credentials in templates, not in root .env)
✅ **Easier** (one command to switch scenarios)

**This is the workflow you wanted!** 🎉
