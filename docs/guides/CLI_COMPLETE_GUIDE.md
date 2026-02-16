# Complete CLI Usage Guide

**Version:** 4.0
**Last Updated:** 2026-02-13

Complete reference for all CLI commands, flags, and combinations with practical examples.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [All CLI Flags Reference](#all-cli-flags-reference)
3. [Environment & Configuration](#environment--configuration)
4. [Input Sources](#input-sources)
5. [Index Management](#index-management)
6. [Document Actions](#document-actions)
7. [Validation & Diagnostics](#validation--diagnostics)
8. [Artifact Management](#artifact-management)
9. [Logging & Output](#logging--output)
10. [Common Use Cases](#common-use-cases)
11. [Advanced Combinations](#advanced-combinations)
12. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install
pip install -e .

# Validate configuration
python -m ingestor.cli --validate

# Process a PDF
python -m ingestor.cli --pdf document.pdf

# Process multiple files
python -m ingestor.cli --glob "documents/*.pdf"

# Use different env file
python -m ingestor.cli --env-file envs/.env.chromadb.example --validate
```

---

## All CLI Flags Reference

### Complete Flag List

| Flag | Aliases | Type | Default | Description |
|------|---------|------|---------|-------------|
| `--env-file` | `--env` | string | `.env` | Path to environment file |
| `--pdf` | `--file` | string | - | Path to single file to process |
| `--glob` | - | string | - | Glob pattern for multiple files |
| `--action` | - | choice | `add` | Document action: add, remove, removeall |
| `--setup-index` | - | flag | false | Deploy/update index before ingestion |
| `--force-index` | - | flag | false | **DESTRUCTIVE**: Delete and recreate index |
| `--index-only` | - | flag | false | Deploy index, skip ingestion |
| `--delete-index` | - | flag | false | **DESTRUCTIVE**: Delete index |
| `--skip-ingestion` | - | flag | false | Skip document processing |
| `--check-index` | - | flag | false | Check if index exists |
| `--clean-artifacts` | - | flag | false | Clean artifacts for specific files |
| `--clean-all-artifacts` | - | flag | false | **DESTRUCTIVE**: Clean ALL artifacts |
| `--validate` | `--pre-check` | flag | false | Validation only, no processing |
| `--verbose` | - | flag | false | Enable DEBUG logging |
| `--no-colors` | - | flag | false | Disable colored output |

---

## Environment & Configuration

### Using Different Environment Files

```bash
# Default .env file
python -m ingestor.cli --validate

# Azure full stack with local input
python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate

# ChromaDB offline mode
python -m ingestor.cli --env-file envs/.env.scenario-03-azure-di-chromadb.example --validate

# Multilingual setup
python -m ingestor.cli --env-file envs/.env.scenario-06-azure-multilingual.example --validate

# Custom env file (relative path)
python -m ingestor.cli --env-file ../configs/.env.production --validate

# Custom env file (absolute path)
python -m ingestor.cli --env-file C:\configs\.env.staging --validate
```

### Testing Different Configurations

```bash
# Test configuration without processing
python -m ingestor.cli --env-file .env.test --validate

# Process with test configuration
python -m ingestor.cli --env-file .env.test --glob "test_data/*.pdf"

# Switch between dev/staging/prod
python -m ingestor.cli --env-file .env.dev --validate
python -m ingestor.cli --env-file .env.staging --validate
python -m ingestor.cli --env-file .env.prod --validate
```

---

## Input Sources

### Single File Processing

```bash
# Process one PDF
python -m ingestor.cli --pdf document.pdf

# Process using --file alias
python -m ingestor.cli --file report.pdf

# Process with specific env
python -m ingestor.cli --env-file .env.prod --pdf important_document.pdf

# Process with verbose logging
python -m ingestor.cli --pdf document.pdf --verbose

# Process with custom action
python -m ingestor.cli --pdf document.pdf --action add
```

### Multiple Files with Glob Patterns

```bash
# All PDFs in directory
python -m ingestor.cli --glob "documents/*.pdf"

# Recursive search
python -m ingestor.cli --glob "documents/**/*.pdf"

# Multiple file types
python -m ingestor.cli --glob "documents/**/*"

# Specific subdirectory
python -m ingestor.cli --glob "data/reports/*.pdf"

# Complex patterns
python -m ingestor.cli --glob "data/**/202[3-4]/*.pdf"

# Quoted patterns (Windows)
python -m ingestor.cli --glob "C:\Documents\*.pdf"

# Quoted patterns (Linux/Mac)
python -m ingestor.cli --glob "/home/user/documents/**/*.pdf"
```

### Environment-Based Input

```bash
# Use LOCAL_INPUT_GLOB from .env
python -m ingestor.cli

# Override env glob with CLI
python -m ingestor.cli --glob "override/*.pdf"
```

---

## Index Management

### Check Index Status

```bash
# Check if index exists
python -m ingestor.cli --check-index

# Check with different env
python -m ingestor.cli --env-file .env.prod --check-index
```

### Create/Update Index

```bash
# Setup index (create if missing, update if exists)
python -m ingestor.cli --setup-index

# Setup then process documents
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# Setup index only, skip ingestion
python -m ingestor.cli --setup-index --skip-ingestion

# Setup with index-only flag
python -m ingestor.cli --index-only
```

### Delete Index (DESTRUCTIVE)

```bash
# ⚠️ WARNING: Deletes all data in index!

# Delete index only
python -m ingestor.cli --delete-index

# Delete and skip ingestion
python -m ingestor.cli --delete-index --skip-ingestion
```

### Force Recreate Index (DESTRUCTIVE)

```bash
# ⚠️ WARNING: Destroys all data and recreates index!

# Delete + recreate index, then EXIT
python -m ingestor.cli --force-index

# Cannot combine with ingestion (exits after recreate)
```

---

## Document Actions

### Add Documents (Default)

```bash
# Add/update documents (default behavior)
python -m ingestor.cli --glob "documents/*.pdf"

# Explicitly specify add action
python -m ingestor.cli --action add --glob "documents/*.pdf"

# Setup index and add
python -m ingestor.cli --setup-index --action add --glob "documents/*.pdf"
```

### Remove Specific Documents

```bash
# Remove documents by filename
python -m ingestor.cli --action remove --glob "old_document.pdf"

# Remove multiple documents
python -m ingestor.cli --action remove --glob "archive/*.pdf"

# Remove and clean artifacts
python -m ingestor.cli --action remove --glob "document.pdf" --clean-artifacts
```

### Remove All Documents (DESTRUCTIVE)

```bash
# ⚠️ WARNING: Removes ALL documents from index!

# Remove all documents
python -m ingestor.cli --action removeall

# Remove all and clean all artifacts
python -m ingestor.cli --action removeall --clean-all-artifacts
```

---

## Validation & Diagnostics

### Pre-Check Validation

```bash
# Basic validation
python -m ingestor.cli --validate

# Validation with verbose output
python -m ingestor.cli --validate --verbose

# Validate specific env file
python -m ingestor.cli --env-file .env.test --validate

# Use --pre-check alias
python -m ingestor.cli --pre-check

# Validate all scenarios
python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate
python -m ingestor.cli --env-file envs/.env.scenario-02-azure-full-blob.example --validate
python -m ingestor.cli --env-file envs/.env.scenario-03-azure-di-chromadb.example --validate
```

### Scenario Validator

```bash
# Auto-detect scenario and validate
python -m ingestor.scenario_validator

# Validate specific scenario
python -m ingestor.scenario_validator azure_full
python -m ingestor.scenario_validator local_dev
python -m ingestor.scenario_validator offline

# Validate with env file
python -m ingestor.scenario_validator --env-file .env.test

# Verbose validation
python -m ingestor.scenario_validator --verbose

# Available scenarios:
# - local_dev
# - azure_full
# - offline
# - hybrid
# - azure_cohere
```

---

## Artifact Management

### Clean Specific Artifacts

```bash
# Clean artifacts for removed documents
python -m ingestor.cli --action remove --glob "document.pdf" --clean-artifacts

# Clean artifacts for specific pattern
python -m ingestor.cli --clean-artifacts --glob "old_docs/*.pdf"
```

### Clean All Artifacts (DESTRUCTIVE)

```bash
# ⚠️ WARNING: Deletes ALL blob artifacts!

# Clean all artifacts
python -m ingestor.cli --clean-all-artifacts

# Remove all docs and clean all artifacts
python -m ingestor.cli --action removeall --clean-all-artifacts
```

---

## Logging & Output

### Verbose Logging

```bash
# Enable DEBUG logging
python -m ingestor.cli --verbose --glob "documents/*.pdf"

# Validation with verbose
python -m ingestor.cli --validate --verbose

# Combine with other flags
python -m ingestor.cli --verbose --setup-index --glob "documents/*.pdf"
```

### Disable Colors

```bash
# Disable colored output (for CI/CD or log files)
python -m ingestor.cli --no-colors --glob "documents/*.pdf"

# Combine with verbose
python -m ingestor.cli --verbose --no-colors --validate

# Useful for logging to file
python -m ingestor.cli --no-colors --glob "documents/*.pdf" > processing.log 2>&1
```

---

## Common Use Cases

### 1. First-Time Setup

```bash
# Step 1: Validate configuration
python -m ingestor.cli --validate

# Step 2: Create index
python -m ingestor.cli --setup-index

# Step 3: Process documents
python -m ingestor.cli --glob "documents/*.pdf"
```

### 2. Add New Documents

```bash
# Simple add
python -m ingestor.cli --glob "new_documents/*.pdf"

# Add with verbose logging
python -m ingestor.cli --verbose --glob "new_documents/*.pdf"
```

### 3. Update Existing Documents

```bash
# Reprocess (updates existing docs)
python -m ingestor.cli --glob "documents/updated_report.pdf"

# Batch update
python -m ingestor.cli --glob "documents/*.pdf"
```

### 4. Remove Old Documents

```bash
# Remove specific document
python -m ingestor.cli --action remove --glob "old_document.pdf"

# Remove and clean artifacts
python -m ingestor.cli --action remove --glob "old_document.pdf" --clean-artifacts
```

### 5. Switch Environments

```bash
# Development
python -m ingestor.cli --env-file .env.dev --validate
python -m ingestor.cli --env-file .env.dev --glob "test_data/*.pdf"

# Staging
python -m ingestor.cli --env-file .env.staging --validate
python -m ingestor.cli --env-file .env.staging --glob "documents/*.pdf"

# Production
python -m ingestor.cli --env-file .env.prod --validate
python -m ingestor.cli --env-file .env.prod --glob "production_docs/*.pdf"
```

### 6. Testing Different Configurations

```bash
# Test ChromaDB setup
python -m ingestor.cli --env-file envs/.env.chromadb.example --validate

# Test Cohere embeddings
python -m ingestor.cli --env-file envs/.env.cohere.example --validate

# Test with vision processing
python -m ingestor.cli --env-file envs/.env.scenario-05-azure-vision-heavy.example --validate
```

### 7. Index Maintenance

```bash
# Check index exists
python -m ingestor.cli --check-index

# Update index schema
python -m ingestor.cli --setup-index --skip-ingestion

# Recreate index from scratch
python -m ingestor.cli --force-index
python -m ingestor.cli --glob "documents/*.pdf"
```

### 8. Batch Processing

```bash
# Process all documents in stages
python -m ingestor.cli --glob "documents/batch1/*.pdf"
python -m ingestor.cli --glob "documents/batch2/*.pdf"
python -m ingestor.cli --glob "documents/batch3/*.pdf"

# Process with logging
python -m ingestor.cli --verbose --glob "documents/*.pdf" > processing.log 2>&1
```

---

## Advanced Combinations

### Setup + Process Pipeline

```bash
# Full pipeline: validate, setup index, process
python -m ingestor.cli --validate
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# One command (setup + process)
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# With verbose logging
python -m ingestor.cli --verbose --setup-index --glob "documents/*.pdf"
```

### Environment-Specific Processing

```bash
# Production pipeline
python -m ingestor.cli --env-file .env.prod --check-index
python -m ingestor.cli --env-file .env.prod --glob "production/**/*.pdf" --no-colors > prod.log 2>&1

# Staging test
python -m ingestor.cli --env-file .env.staging --validate --verbose
python -m ingestor.cli --env-file .env.staging --setup-index
python -m ingestor.cli --env-file .env.staging --glob "test_docs/*.pdf"
```

### Complete Document Lifecycle

```bash
# 1. Add documents
python -m ingestor.cli --glob "documents/*.pdf"

# 2. Update specific document
python -m ingestor.cli --glob "documents/updated.pdf"

# 3. Remove outdated documents
python -m ingestor.cli --action remove --glob "documents/old/*.pdf" --clean-artifacts

# 4. Verify index
python -m ingestor.cli --check-index
```

### Maintenance Operations

```bash
# Clean up and rebuild
python -m ingestor.cli --action removeall --clean-all-artifacts
python -m ingestor.cli --force-index
python -m ingestor.cli --glob "documents/*.pdf"

# Incremental maintenance
python -m ingestor.cli --action remove --glob "archive/*.pdf" --clean-artifacts
python -m ingestor.cli --glob "new_documents/*.pdf"
```

---

## Troubleshooting

### Validation Issues

```bash
# Check configuration
python -m ingestor.cli --validate --verbose

# Test with example env
python -m ingestor.cli --env-file envs/.env.example --validate

# Check scenario detection
python -m ingestor.scenario_validator --verbose
```

### Connection Issues

```bash
# Check index connectivity
python -m ingestor.cli --check-index

# Test with verbose logging
python -m ingestor.cli --verbose --check-index

# Validate Azure credentials
python -m ingestor.cli --validate
```

### Processing Errors

```bash
# Enable DEBUG logging
python -m ingestor.cli --verbose --glob "problematic_document.pdf"

# Process with logging to file
python -m ingestor.cli --verbose --no-colors --glob "documents/*.pdf" > debug.log 2>&1

# Test single file first
python -m ingestor.cli --verbose --pdf "test.pdf"
```

### Index Issues

```bash
# Check index exists
python -m ingestor.cli --check-index

# Recreate index
python -m ingestor.cli --force-index

# Update index schema
python -m ingestor.cli --setup-index --skip-ingestion
```

### Environment File Issues

```bash
# Test with absolute path
python -m ingestor.cli --env-file C:\full\path\to\.env --validate

# Test with different env files
python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate
python -m ingestor.cli --env-file envs/.env.scenario-03-azure-di-chromadb.example --validate

# Check path resolution
python -m ingestor.cli --env-file ./envs/.env.example --validate
python -m ingestor.cli --env-file ../configs/.env --validate
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 1 | General error | Check error messages |
| 2 | Argument error | Fix command syntax |
| 130 | User interrupt (Ctrl+C) | Normal |

---

## Best Practices

### 1. Always Validate First

```bash
# Before processing
python -m ingestor.cli --validate

# Before production deployment
python -m ingestor.cli --env-file .env.prod --validate
```

### 2. Use Verbose for Debugging

```bash
# Development
python -m ingestor.cli --verbose --glob "test/*.pdf"

# Production logging
python -m ingestor.cli --no-colors --glob "docs/*.pdf" > prod.log 2>&1
```

### 3. Test with Small Batches

```bash
# Test with one file first
python -m ingestor.cli --pdf "test.pdf"

# Then small batch
python -m ingestor.cli --glob "test_batch/*.pdf"

# Finally full batch
python -m ingestor.cli --glob "documents/**/*.pdf"
```

### 4. Separate Test/Prod Environments

```bash
# Test environment
python -m ingestor.cli --env-file .env.test --validate
python -m ingestor.cli --env-file .env.test --glob "test_docs/*.pdf"

# Production environment
python -m ingestor.cli --env-file .env.prod --validate
python -m ingestor.cli --env-file .env.prod --glob "production_docs/*.pdf"
```

### 5. Regular Index Maintenance

```bash
# Weekly: Check index status
python -m ingestor.cli --check-index

# Monthly: Update index schema if needed
python -m ingestor.cli --setup-index --skip-ingestion

# Quarterly: Clean up artifacts
python -m ingestor.cli --action remove --glob "archive/*.pdf" --clean-artifacts
```

---

## Quick Reference Card

```bash
# Most Common Commands

# Validate
python -m ingestor.cli --validate

# Process one file
python -m ingestor.cli --pdf document.pdf

# Process multiple files
python -m ingestor.cli --glob "documents/*.pdf"

# Setup + process
python -m ingestor.cli --setup-index --glob "documents/*.pdf"

# Different env
python -m ingestor.cli --env-file .env.prod --validate

# Verbose mode
python -m ingestor.cli --verbose --glob "documents/*.pdf"

# Remove documents
python -m ingestor.cli --action remove --glob "old.pdf"

# Check index
python -m ingestor.cli --check-index
```

---

---

## Automated Testing

### Test Runner Script

Create `test_cli_runner.py` for automated testing:

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
    "I02": ["--setup-index"],
    "IN01": ["--pdf", "test_document.pdf"],
    "IN03": ["--glob", "documents/*.pdf"],
    "A01": ["--action", "add", "--glob", "documents/*.pdf"],
    "L01": ["--verbose", "--check-index"],
    # Add more tests as needed
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
            timeout=60
        )
        duration = time.time() - start

        return {
            "test_id": test_id,
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "stdout": result.stdout[:500],  # First 500 chars
            "stderr": result.stderr[:500],
            "duration": duration,
            "status": "PASS" if result.returncode == 0 else "FAIL"
        }
    except subprocess.TimeoutExpired:
        return {
            "test_id": test_id,
            "status": "TIMEOUT",
            "duration": 60
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

    # Print summary
    passed = len([r for r in results if r["status"] == "PASS"])
    total = len(results)
    print(f"\n\nSummary: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Run all tests
python test_cli_runner.py

# Add custom tests to TESTS dict and run
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CLI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -e .

      - name: Run validation tests
        run: python -m ingestor.cli --validate
        env:
          AZURE_SEARCH_SERVICE: ${{ secrets.TEST_SEARCH_SERVICE }}
          AZURE_SEARCH_KEY: ${{ secrets.TEST_SEARCH_KEY }}
          DOCUMENTINTELLIGENCE_ENDPOINT: ${{ secrets.TEST_DI_ENDPOINT }}
          DOCUMENTINTELLIGENCE_KEY: ${{ secrets.TEST_DI_KEY }}

      - name: Check index status
        run: python -m ingestor.cli --check-index

      - name: Run test processing
        run: python -m ingestor.cli --glob "test_data/*.pdf"
```

---

## Regression Testing

### Establishing Baseline

```bash
# On stable version
git checkout v1.0.0
python test_cli_runner.py > baseline-v1.0.0.txt

# On new version
git checkout main
python test_cli_runner.py > current.txt

# Compare
diff baseline-v1.0.0.txt current.txt
```

### Performance Tracking

```python
import json
import time

# Track execution time over versions
results = {
    "v1.0": 45.3,
    "v1.1": 48.1,
    "v1.2": 42.7
}

for version, duration in sorted(results.items()):
    status = "✓ Faster" if duration < 45.0 else "⚠ Slower"
    print(f"{version}: {duration}s {status}")
```

---

## Related Documentation

- [Scenario Validator Guide](../VALIDATION.md)
- [Environment Variables Reference](../reference/12_ENVIRONMENT_VARIABLES.md)
- [Quick Start Guide](QUICKSTART.md)
- [Configuration Guide](CONFIGURATION.md)

---

**Last Updated:** 2026-02-13
**CLI Version:** 4.0
**Status:** ✅ Complete
