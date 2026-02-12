# Environment File Usage Guide

Quick reference for which `.env` file each command uses.

---

## Current Behavior

### ⚠️ **Important: scenario_validator.py does NOT auto-load .env**

The `scenario_validator.py` currently uses **system environment variables** (not the `.env` file) when run directly.

This means you need to manually load the .env file before running the validator.

---

## Commands and Their .env Usage

### **1. CLI Commands (✅ Auto-loads .env)**

```bash
# These commands AUTOMATICALLY load .env from current directory
python -m ingestor.cli --validate
python -m ingestor.cli --pdf ./test.pdf
python -m ingestor.cli --glob "docs/*.pdf"
python -m ingestor.cli --query "test"

# Default .env file: .env in current directory
# Specify different file with --env-file:
python -m ingestor.cli --pdf test.pdf --env-file .env.azure
python -m ingestor.cli --pdf test.pdf --env-file envs/.env.azure-local-input.example
```

**Location:** `src/ingestor/cli.py` line 154
```python
load_dotenv(dotenv_path=env_file_path, override=True)
```

---

### **2. Scenario Validator (⚠️ Does NOT auto-load)**

```bash
# This does NOT automatically load .env file
python -m ingestor.scenario_validator

# It reads from system environment variables
# which means you need to manually load .env first
```

**Current Behavior:**
- Uses `os.getenv()` directly
- NO dotenv import
- Reads from **system environment** only

---

## Workarounds for scenario_validator

### **Option 1: Load .env Manually (Python)**

```bash
# Python one-liner to load .env then run validator
python -c "from dotenv import load_dotenv; load_dotenv(); import subprocess; subprocess.run(['python', '-m', 'ingestor.scenario_validator'])"
```

### **Option 2: Export Variables (Bash/Linux/Mac)**

```bash
# Export .env to environment
export $(cat .env | grep -v '^#' | xargs)

# Then run validator
python -m ingestor.scenario_validator
```

### **Option 3: PowerShell (Windows)**

```powershell
# Load .env into environment
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

# Then run validator
python -m ingestor.scenario_validator
```

### **Option 4: Batch Script (Windows)**

```batch
REM Load key variables manually
set EXTRACTION_MODE=azure_di
set EMBEDDINGS_MODE=azure_openai
set VECTOR_STORE=azure_search
REM ... (set other variables)

REM Then run validator
python -m ingestor.scenario_validator
```

### **Option 5: Use CLI --validate Instead (Recommended)**

The CLI automatically loads .env and includes validation:

```bash
# This DOES load .env automatically
python -m ingestor.cli --validate

# Specify different .env file
python -m ingestor.cli --validate --env-file .env.azure
```

---

## Recommended Fix (For Development)

The scenario_validator should be updated to load .env automatically. Here's the fix:

### **Add to scenario_validator.py:**

```python
# At the top of the file (after imports)
from dotenv import load_dotenv

# In __main__ block (before running validation):
if __name__ == "__main__":
    """Command-line interface for scenario validation."""
    import sys
    from pathlib import Path

    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)
        print(f"✓ Loaded environment from: {env_file}")
    else:
        print(f"⚠️  No .env file found, using system environment")

    # ... rest of the code
```

---

## Testing Which .env is Used

### **Test CLI .env loading:**

```bash
# Create test .env with unique value
echo "EXTRACTION_MODE=test_mode_cli" > .env.test

# Run CLI with test env
python -m ingestor.cli --validate --env-file .env.test

# Check if it loaded
python -c "from dotenv import load_dotenv; load_dotenv('.env.test'); import os; print(f'CLI Mode: {os.getenv(\"EXTRACTION_MODE\")}')"
```

### **Test scenario_validator (current behavior):**

```bash
# Create test .env
echo "EXTRACTION_MODE=test_mode_validator" > .env

# Run validator - will NOT read .env automatically
python -m ingestor.scenario_validator

# Manual load test
python -c "from dotenv import load_dotenv; load_dotenv(); import subprocess; subprocess.run(['python', '-m', 'ingestor.scenario_validator'])"
```

---

## Comparison Table

| Command | Auto-loads .env? | Default File | Custom File Support |
|---------|------------------|--------------|---------------------|
| `python -m ingestor.cli` | ✅ Yes | `.env` | `--env-file path` |
| `python -m ingestor.scenario_validator` | ❌ No | N/A | Manual load only |
| `python -m ingestor.config` | ✅ Yes* | `.env` | Via dotenv |

*Depends on how config is initialized

---

## Best Practices

### **1. Use CLI for Full Workflow**

Since CLI auto-loads .env, prefer using it:

```bash
# Instead of:
python -m ingestor.scenario_validator

# Use:
python -m ingestor.cli --validate
```

### **2. Explicit .env Loading for Scripts**

If you write custom scripts, always load .env explicitly:

```python
from dotenv import load_dotenv
from pathlib import Path

# Load .env at the start
env_file = Path('.env')
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)

# Now your code can use os.getenv()
import os
mode = os.getenv('EXTRACTION_MODE')
```

### **3. Use Specific .env Files**

For different scenarios, use specific files:

```bash
# Azure setup
python -m ingestor.cli --pdf test.pdf --env-file .env.azure

# Offline setup
python -m ingestor.cli --pdf test.pdf --env-file .env.offline

# Development
python -m ingestor.cli --pdf test.pdf --env-file .env.dev
```

### **4. CI/CD: Set Environment Variables Directly**

For CI/CD, don't rely on .env files:

```yaml
# GitHub Actions example
- name: Run tests
  env:
    EXTRACTION_MODE: markitdown
    EMBEDDINGS_MODE: huggingface
    VECTOR_STORE: chromadb
  run: |
    python -m ingestor.cli --pdf test.pdf
```

---

## Quick Answer to Your Question

> **python -m ingestor.scenario_validator --help**
> **Which env this will use?**

### Answer:

**NONE** - The scenario_validator does NOT automatically load any `.env` file.

It only reads **system environment variables** that are already set in your shell/terminal.

### To make it work with .env:

**Option A (Recommended):** Use CLI instead
```bash
python -m ingestor.cli --validate  # This DOES load .env
```

**Option B:** Manually load .env first (PowerShell)
```powershell
# Load .env into environment
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

# Now run validator
python -m ingestor.scenario_validator
```

**Option C:** Use Python wrapper
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); exec(open('src/ingestor/scenario_validator.py').read())"
```

---

## Proposed Improvement

Create a helper script: `validate-env.py`

```python
#!/usr/bin/env python
"""Wrapper to run scenario_validator with .env loading."""

from dotenv import load_dotenv
from pathlib import Path
import sys

# Load .env
env_file = Path('.env')
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)
    print(f"✓ Loaded: {env_file}")

# Now import and run validator
if __name__ == "__main__":
    from ingestor.scenario_validator import ScenarioValidator, validate_current_environment

    if len(sys.argv) > 1:
        from ingestor.scenario_validator import Scenario
        scenario_name = sys.argv[1].lower()
        try:
            scenario = Scenario(scenario_name)
            result = ScenarioValidator.validate_scenario(scenario, verbose=True)
            ScenarioValidator.print_validation_report(result, include_help=True)
            sys.exit(0 if result.valid else 1)
        except ValueError:
            print(f"Unknown scenario: {scenario_name}")
            sys.exit(1)
    else:
        result = validate_current_environment(verbose=True)
        ScenarioValidator.print_validation_report(result, include_help=True)
        sys.exit(0 if result.valid else 1)
```

Usage:
```bash
python validate-env.py
python validate-env.py azure_full
```

---

## Summary

| What You Want | Command to Use |
|---------------|----------------|
| Validate with auto .env load | `python -m ingestor.cli --validate` |
| Validate without .env | `python -m ingestor.scenario_validator` |
| Validate with specific .env | `python -m ingestor.cli --validate --env-file .env.azure` |
| Manual .env load + validate | See PowerShell/Bash examples above |

**Bottom line:** For normal usage, use `python -m ingestor.cli --validate` which properly loads your `.env` file.
