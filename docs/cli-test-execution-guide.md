# CLI Test Execution Guide

This guide provides step-by-step instructions for manually executing all CLI test scenarios documented in `cli-test-results.md`.

## Prerequisites

1. **Python Environment**: Ensure Python 3.10+ is installed and activated
2. **Dependencies**: Install required packages: `pip install -e .`
3. **Environment File**: Copy `.env.example` to `.env` and configure
4. **Test Data**: Create test documents in `documents/` folder

## Quick Setup

```bash
# 1. Create test environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Create test documents folder
mkdir -p documents
# Place some test PDF files in documents/

# 4. Configure environment
cp envs/.env.example .env
# Edit .env with your Azure credentials
```

## Test Execution Commands

### Category 1: Validation Operations

```bash
# V01: Basic validation
python -m ingestor.cli --validate

# V02: Validation with verbose logging
python -m ingestor.cli --validate --verbose

# V03: Validation with missing env file
python -m ingestor.cli --validate --env missing.env

# V04: Pre-check alias
python -m ingestor.cli --pre-check
```

### Category 2: Index Management

```bash
# I01: Check if index exists
python -m ingestor.cli --check-index

# I02: Setup index (without ingestion)
python -m ingestor.cli --setup-index

# I03: Index-only mode
python -m ingestor.cli --index-only

# I04: Delete index (DESTRUCTIVE!)
python -m ingestor.cli --delete-index

# I05: Force recreate index (DESTRUCTIVE!)
python -m ingestor.cli --force-index

# I06: Setup index then ingest
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# I07: Setup index, skip ingestion
python -m ingestor.cli --setup-index --skip-ingestion
```

### Category 3: Input Sources

```bash
# IN01: Single file with --pdf
python -m ingestor.cli --pdf "documents/test.pdf"

# IN02: Single file with --file (alias)
python -m ingestor.cli --file "documents/test.pdf"

# IN03: Glob pattern for PDFs
python -m ingestor.cli --glob "documents/*.pdf"

# IN04: Recursive glob
python -m ingestor.cli --glob "documents/**/*"

# IN05: Use .env configuration (no CLI args)
python -m ingestor.cli

# IN06: Non-existent file
python -m ingestor.cli --pdf "nonexistent.pdf"

# IN07: No matching files
python -m ingestor.cli --glob "nomatch/*.pdf"
```

### Category 4: Document Actions

```bash
# A01: Add documents (explicit)
python -m ingestor.cli --action add --glob "documents/*.pdf"

# A02: Remove documents
python -m ingestor.cli --action remove --glob "documents/old_document.pdf"

# A03: Remove all documents (DESTRUCTIVE!)
python -m ingestor.cli --action removeall

# A04: Default action (add)
python -m ingestor.cli --glob "documents/*.pdf"
```

### Category 5: Artifact Management

```bash
# AR01: Clean artifacts for specific files
python -m ingestor.cli --clean-artifacts --glob "documents/*.pdf"

# AR02: Clean ALL artifacts (DESTRUCTIVE!)
python -m ingestor.cli --clean-all-artifacts

# AR03: Clean artifacts without glob (should error)
python -m ingestor.cli --clean-artifacts

# AR04: Clean artifacts combined with remove action
python -m ingestor.cli --clean-artifacts --action remove --glob "documents/*.pdf"
```

### Category 6: Environment Files

```bash
# E01: Default .env
python -m ingestor.cli --env .env --validate

# E02: ChromaDB configuration
python -m ingestor.cli --env envs/.env.chromadb.example --validate

# E03: Cohere configuration
python -m ingestor.cli --env envs/.env.cohere.example --validate

# E04: Missing env file
python -m ingestor.cli --env missing.env --validate
```

### Category 7: Logging & Output

```bash
# L01: Verbose logging
python -m ingestor.cli --verbose --check-index

# L02: No colors
python -m ingestor.cli --no-colors --check-index

# L03: Verbose without colors
python -m ingestor.cli --verbose --no-colors --check-index
```

### Category 8: Error Handling

```bash
# ERR01: No .env and no system env vars
mv .env .env.backup
python -m ingestor.cli --validate
mv .env.backup .env

# ERR02: Invalid action value
python -m ingestor.cli --action invalid_action --glob "*.pdf"

# ERR03: Both --pdf and --glob (last wins)
python -m ingestor.cli --pdf "file1.pdf" --glob "documents/*.pdf" --validate

# ERR04: Ctrl+C during execution (manual test)
python -m ingestor.cli --glob "documents/*.pdf"
# Press Ctrl+C during execution

# ERR05: Invalid env file format
# Create test file with invalid syntax
echo "INVALID=LINE WITHOUT EQUALS" > test_invalid.env
python -m ingestor.cli --env test_invalid.env --validate
rm test_invalid.env
```

### Category 9: Complex Combinations

```bash
# C01: Force recreate with ingestion
python -m ingestor.cli --force-index --setup-index --glob "documents/*.pdf"

# C02: Delete index and skip ingestion
python -m ingestor.cli --delete-index --skip-ingestion

# C03: Validate with custom env and verbose
python -m ingestor.cli --validate --verbose --env envs/.env.chromadb.example

# C04: Index-only with verbose and no colors
python -m ingestor.cli --index-only --verbose --no-colors
```

## Recording Test Results

For each test, record:

1. **Command**: Exact command executed
2. **Exit Code**: Return code (0=success, non-zero=error)
3. **Output**: First 50 lines of stdout/stderr
4. **Duration**: Time taken to complete
5. **Status**: PASS/FAIL/ERROR
6. **Notes**: Any observations or issues

### Example Test Result Format

```markdown
#### Test V01: Basic Validation
**Command**: `python -m ingestor.cli --validate`
**Executed**: 2026-02-11 21:45:00
**Exit Code**: 0
**Duration**: 2.3 seconds
**Status**: ✅ PASS

**Output**:
```
✓ Loaded environment from: .env
==========================================
ingestor - Document Ingestion Pipeline
==========================================
Running Pre-Check Validation
...
✅ Validation Complete - Pipeline is Ready!
```

**Notes**:
- All environment variables validated successfully
- Azure connectivity confirmed
```

## Automated Test Script

Create a test runner script:

```python
#!/usr/bin/env python3
"""Automated CLI test runner."""

import subprocess
import sys
import time
from pathlib import Path

TESTS = {
    "V01": ["--validate"],
    "V02": ["--validate", "--verbose"],
    "I01": ["--check-index"],
    # Add more tests...
}

def run_test(test_id, args):
    """Run a single test and capture results."""
    cmd = [sys.executable, "-m", "ingestor.cli"] + args
    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = time.time() - start

        return {
            "test_id": test_id,
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": duration,
            "status": "PASS" if result.returncode == 0 else "FAIL"
        }
    except subprocess.TimeoutExpired:
        return {
            "test_id": test_id,
            "status": "TIMEOUT",
            "duration": 30
        }
    except Exception as e:
        return {
            "test_id": test_id,
            "status": "ERROR",
            "error": str(e)
        }

def main():
    """Run all tests and generate report."""
    results = []

    for test_id, args in TESTS.items():
        print(f"Running {test_id}...", end=" ")
        result = run_test(test_id, args)
        results.append(result)
        print(result["status"])

    # Generate markdown report
    # ... (implementation)

if __name__ == "__main__":
    main()
```

## Safety Notes

### Destructive Operations
These commands will DELETE data - use with caution:
- `--delete-index`
- `--force-index`
- `--action removeall`
- `--clean-all-artifacts`

### Test Environment
Always test on a non-production environment:
- Use separate Azure resources for testing
- Use test index names (e.g., `documents-test`)
- Create backups before destructive operations

## Troubleshooting

### Common Issues

**Issue**: `No pyvenv.cfg file`
**Solution**: Ensure Python virtual environment is activated

**Issue**: `ImportError: No module named 'ingestor'`
**Solution**: Run `pip install -e .` from project root

**Issue**: `ValueError: AZURE_SEARCH_ENDPOINT is required`
**Solution**: Configure .env file with required credentials

**Issue**: Exit code 106
**Solution**: This is a venv/Python environment issue, not a CLI issue

## Next Steps

1. Execute all tests systematically
2. Record results in `cli-test-results.md`
3. Identify any bugs or issues
4. Document edge cases and unexpected behaviors
5. Create automated regression test suite
