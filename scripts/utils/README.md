# Utility Scripts

This folder contains utility scripts for pipeline operations and testing.

## Available Scripts

### validate_config.py

Programmatic validation of pipeline configuration and environment setup.

**Usage:**
```bash
# From project root
python scripts/utils/validate_config.py
```

**What it does:**
- Loads configuration from environment variables
- Validates all required services and dependencies
- Provides detailed error messages with fix hints
- Returns exit code 0 on success, 1 on failure

**When to use:**
- Before running the pipeline for the first time
- After changing environment configuration
- In CI/CD pipelines to verify setup
- To troubleshoot configuration issues

**See also:**
- [docs/guides/VALIDATION.md](../../docs/guides/VALIDATION.md) - Validation guide
- [docs/reference/validation-reference.md](../../docs/reference/validation-reference.md) - Technical reference

## Adding New Utilities

When adding new utility scripts to this folder:
1. Add a clear docstring explaining the purpose
2. Update this README with usage instructions
3. Make the script runnable from the project root
4. Add error handling and helpful messages
