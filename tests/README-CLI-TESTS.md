# CLI Comprehensive Test Suite

This directory contains a comprehensive test suite for the ingest-o-bot CLI, designed to validate all command-line options, combinations, and edge cases.

## Overview

The test suite consists of:

1. **Test Documentation**: `cli-test-results.md` - Detailed test scenarios and results template
2. **Execution Guide**: `cli-test-execution-guide.md` - Manual testing procedures
3. **Automated Runner**: `test_cli_comprehensive.py` - Python script for automated testing
4. **Results Schema**: `cli-test-schema.json` - JSON schema for test results
5. **Results Output**: `test-results/cli-test-results.json` - Actual test execution results

## Quick Start

### Running All Tests

```bash
# Run non-destructive tests only (default)
python tests/test_cli_comprehensive.py

# Run all tests including destructive operations (CAREFUL!)
python tests/test_cli_comprehensive.py --include-destructive

# Use specific environment file
python tests/test_cli_comprehensive.py --env envs/.env.test

# Custom output location
python tests/test_cli_comprehensive.py --output my-results.json
```

### Running Manual Tests

Follow the step-by-step instructions in `cli-test-execution-guide.md`:

```bash
# Example: Test validation
python -m ingestor.cli --validate

# Example: Check index
python -m ingestor.cli --check-index
```

## Test Categories

### 1. Validation Operations (V01-V04)
- Basic validation (`--validate`)
- Verbose validation (`--validate --verbose`)
- Missing environment file handling
- Pre-check alias (`--pre-check`)

### 2. Index Management (I01-I07)
- Check index exists (`--check-index`)
- Setup index (`--setup-index`)
- Index-only mode (`--index-only`)
- Delete index (`--delete-index`) **DESTRUCTIVE**
- Force recreate (`--force-index`) **DESTRUCTIVE**
- Combined operations

### 3. Input Sources (IN01-IN07)
- Single file processing (`--pdf`, `--file`)
- Glob patterns (`--glob`)
- Recursive patterns (`--glob "**/*"`)
- Environment-based input
- Error handling (missing files, no matches)

### 4. Document Actions (A01-A04)
- Add documents (`--action add`)
- Remove documents (`--action remove`)
- Remove all (`--action removeall`) **DESTRUCTIVE**
- Default behavior

### 5. Artifact Management (AR01-AR04)
- Clean specific artifacts (`--clean-artifacts`)
- Clean all artifacts (`--clean-all-artifacts`) **DESTRUCTIVE**
- Error cases

### 6. Environment Files (E01-E04)
- Default `.env`
- ChromaDB configuration
- Cohere configuration
- Missing file handling

### 7. Logging & Output (L01-L03)
- Verbose logging (`--verbose`)
- No colors (`--no-colors`)
- Combined options

### 8. Error Handling (ERR01-ERR05)
- Missing configuration
- Invalid arguments
- Argument conflicts
- Keyboard interrupt
- Invalid file formats

### 9. Complex Combinations (C01-C04)
- Multiple flags
- Conflicting options
- Edge cases

## Test Result Formats

### JSON Output

Results are saved in structured JSON format:

```json
{
  "summary": {
    "total_tests": 20,
    "passed": 18,
    "failed": 2,
    "pass_rate": 90.0,
    "total_duration_seconds": 45.3,
    "timestamp": "2026-02-11T21:00:00Z"
  },
  "test_results": [
    {
      "test_id": "V01",
      "category": "validation",
      "description": "Basic validation",
      "command": "python -m ingestor.cli --validate",
      "exit_code": 0,
      "expected_exit": 0,
      "status": "PASS",
      "duration_seconds": 2.3,
      "timestamp": "2026-02-11T21:00:00Z",
      "stdout_lines": 25,
      "stderr_lines": 0,
      "stdout_preview": "✓ Loaded environment from: .env\n...",
      "stderr_preview": ""
    }
  ],
  "environment": {
    "env_file": null,
    "skip_destructive": true,
    "project_root": "/path/to/ingest-o-bot"
  }
}
```

### Markdown Output

Human-readable results in `cli-test-results.md`:

```markdown
#### Test V01: Basic Validation
**Command**: `python -m ingestor.cli --validate`
**Status**: ✅ PASS
**Exit Code**: 0 (expected: 0)
**Duration**: 2.3 seconds
**Output**: (truncated)
```

## Interpreting Results

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Argument parsing error |
| 130 | Interrupted by user (Ctrl+C) |
| -1 | Timeout or exception |

### Test Status

- ✅ **PASS**: Test completed with expected exit code
- ❌ **FAIL**: Test completed with unexpected exit code
- ⏱️ **TIMEOUT**: Test exceeded 60-second timeout
- 💥 **ERROR**: Exception during test execution
- ⏭️ **SKIPPED**: Test skipped (usually destructive tests)

## Safety Features

### Destructive Test Protection

By default, destructive tests are **SKIPPED** unless explicitly enabled:

```python
# These are skipped by default:
- --delete-index
- --force-index
- --action removeall
- --clean-all-artifacts
```

To run destructive tests:

```bash
python tests/test_cli_comprehensive.py --include-destructive
```

### Test Environment Isolation

Always use a separate test environment:

1. Create test `.env` file:
   ```bash
   cp .env .env.test
   # Edit .env.test with test credentials
   ```

2. Use test-specific resources:
   - Test search index: `documents-test`
   - Test storage account
   - Test Document Intelligence resource

3. Run tests with test environment:
   ```bash
   python tests/test_cli_comprehensive.py --env .env.test
   ```

## Continuous Integration

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
      - name: Run CLI tests
        run: python tests/test_cli_comprehensive.py
        env:
          AZURE_SEARCH_SERVICE: ${{ secrets.TEST_SEARCH_SERVICE }}
          AZURE_SEARCH_INDEX: cli-tests
          # ... other secrets
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

## Regression Testing

### Comparing Results

Compare test results across versions:

```python
import json

def compare_results(old_file, new_file):
    with open(old_file) as f:
        old = json.load(f)
    with open(new_file) as f:
        new = json.load(f)

    # Compare pass rates
    old_rate = old['summary']['pass_rate']
    new_rate = new['summary']['pass_rate']

    print(f"Pass rate change: {old_rate}% → {new_rate}%")

    # Identify new failures
    old_passed = {r['test_id'] for r in old['test_results'] if r['status'] == 'PASS'}
    new_failed = {r['test_id'] for r in new['test_results'] if r['status'] == 'FAIL'}

    regressions = old_passed & new_failed
    if regressions:
        print(f"Regressions: {regressions}")

# Usage
compare_results('baseline-results.json', 'current-results.json')
```

### Baseline Results

Establish a baseline:

```bash
# Run tests on known-good version
python tests/test_cli_comprehensive.py --output baseline-results.json

# Compare future runs against baseline
python tests/test_cli_comprehensive.py --output current-results.json
python scripts/compare_test_results.py baseline-results.json current-results.json
```

## Extending Tests

### Adding New Test Scenarios

Edit `test_cli_comprehensive.py`:

```python
TEST_SCENARIOS = {
    "your_category": {
        "NEW01": {
            "args": ["--your-new-flag"],
            "desc": "Test description",
            "expected_exit": 0,
            "destructive": False
        },
    },
}
```

### Adding Test Categories

1. Add category to `TEST_SCENARIOS` dict
2. Update schema in `cli-test-schema.json`
3. Document in `cli-test-results.md`

## Troubleshooting

### Common Issues

**Issue**: All tests fail with "No pyvenv.cfg file"
```bash
# Solution: Activate virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -e .
```

**Issue**: Tests timeout
```bash
# Increase timeout in test_cli_comprehensive.py:
result = subprocess.run(..., timeout=120)  # Increase from 60 to 120
```

**Issue**: Azure connection errors
```bash
# Verify .env configuration
python -m ingestor.cli --validate --verbose
```

## Performance Benchmarking

Track CLI performance over time:

```python
# Extract duration metrics
import json

with open('test-results/cli-test-results.json') as f:
    data = json.load(f)

for result in data['test_results']:
    print(f"{result['test_id']}: {result['duration_seconds']}s")
```

## Contributing

When adding new CLI options:

1. Add test scenarios for the new option
2. Test all combinations with existing options
3. Update documentation
4. Run full test suite
5. Update baseline results

## Resources

- **CLI Source Code**: `src/ingestor/cli.py`
- **Configuration**: `src/ingestor/config.py`
- **Pipeline**: `src/ingestor/pipeline.py`
- **Documentation**: `docs/`

## Support

For issues or questions:

1. Check test output in `test-results/`
2. Review `cli-test-execution-guide.md`
3. Run individual tests with `--verbose`
4. Check logs in `logs/` directory

---

**Last Updated**: 2026-02-11
**Test Suite Version**: 1.0.0
