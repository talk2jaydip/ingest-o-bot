# Pipeline Validation Feature - Summary

## Overview

I've added a comprehensive validation system to the ingestor pipeline that checks your configuration and environment before running the pipeline. This helps catch configuration issues early and provides helpful guidance on how to fix them.

## What Was Added

### 1. New Validator Module ([src/ingestor/validator.py](src/ingestor/validator.py))

A dedicated validation module that checks:
- ✅ **Input Source**: Files exist and are accessible (local or blob)
- ✅ **Artifacts Storage**: Storage is writable/accessible (local or blob)
- ✅ **Azure Document Intelligence**: Endpoint and credentials are valid (if using Azure DI)
- ✅ **Office Extractor**: Required libraries are installed (MarkItDown, etc.)
- ✅ **Azure OpenAI**: Endpoint, credentials, and deployments are configured (if needed)
- ✅ **Azure AI Search**: Search service and index are accessible
- ✅ **Media Describer**: Configuration is valid based on mode (GPT-4o, Content Understanding, or disabled)
- ✅ **Python Dependencies**: Required and optional libraries are installed

### 2. Pipeline Integration ([src/ingestor/pipeline.py](src/ingestor/pipeline.py))

Updated the Pipeline class to support validation:
- Added `validate_only` parameter to `__init__`
- Added `validate()` method that runs comprehensive validation
- Updated `run()` method to check `validate_only` flag and exit after validation

### 3. CLI Support ([src/ingestor/cli.py](src/ingestor/cli.py))

Added `--validate` (or `--pre-check`) command-line flag:
```bash
python -m ingestor.cli --validate
```

### 4. Documentation

- **[VALIDATION.md](VALIDATION.md)**: Comprehensive guide on using the validation feature
- **[examples/validate_config.py](examples/validate_config.py)**: Example script showing programmatic usage

## How It Works

### Validation Based on Environment

The validator intelligently checks only what's needed based on your configuration:

#### Scenario 1: Local Development (Offline Mode)
```bash
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
AZURE_INPUT_MODE=local
AZURE_ARTIFACTS_MODE=local
```

**Validates:**
- Local files exist
- Local artifacts directory is writable
- MarkItDown library is installed
- Azure AI Search (still required for indexing)

**Skips:**
- Azure Document Intelligence (not needed in markitdown mode)
- Blob storage (using local mode)

#### Scenario 2: Full Azure Cloud Mode
```bash
AZURE_OFFICE_EXTRACTOR_MODE=azure_di
AZURE_INPUT_MODE=blob
AZURE_ARTIFACTS_MODE=blob
```

**Validates:**
- Azure Blob Storage (input and artifacts)
- Azure Document Intelligence
- Azure OpenAI (if client-side embeddings)
- Azure AI Search
- All containers exist or can be created

#### Scenario 3: Hybrid Mode (Recommended)
```bash
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true
```

**Validates:**
- Both Azure DI and MarkItDown
- Falls back gracefully if Azure services unavailable
- Comprehensive dependency check

## Usage Examples

### Command Line Validation
```bash
# Basic validation
python -m ingestor.cli --validate

# Validation with verbose output
python -m ingestor.cli --validate --verbose
```

### Programmatic Validation
```python
from ingestor.config import PipelineConfig
from ingestor.pipeline import Pipeline

config = PipelineConfig.from_env()
pipeline = Pipeline(config, validate_only=True)

try:
    await pipeline.run()
    print("✅ Validation passed!")
except RuntimeError as e:
    print(f"❌ Validation failed: {e}")
```

### Using Validator Directly
```python
from ingestor.config import PipelineConfig
from ingestor.validator import PipelineValidator

config = PipelineConfig.from_env()
validator = PipelineValidator(config)
success = await validator.validate_all()
```

## Example Output

### Success Case
```
================================================================================
🔍 PIPELINE PRE-CHECK VALIDATION
================================================================================

🔍 Validating Input Source...
🔍 Validating Artifacts Storage...
🔍 Validating Azure Document Intelligence...
🔍 Validating Office Extractor...
🔍 Validating Azure OpenAI...
🔍 Validating Azure AI Search...
🔍 Validating Media Describer...
🔍 Validating Python Dependencies...

================================================================================
VALIDATION RESULTS
================================================================================

✅ [Input Source (Local)] Found 5 file(s) matching pattern: ./data/**/*.pdf
✅ [Artifacts Storage (Local)] Directory writable: ./artifacts
✅ [Document Intelligence] Client configured: https://your-di.cognitiveservices.azure.com/
✅ [Office Extractor (MarkItDown)] MarkItDown library available (mode: hybrid)
✅ [Azure OpenAI (Embeddings)] Client configured: text-embedding-3-large
✅ [Azure OpenAI (Chat/GPT-4o)] Chat deployment configured: gpt-4o
✅ [Azure AI Search] Index accessible: my-search-index (1234 documents)
✅ [Media Describer] Using GPT-4o (validated in Azure OpenAI section)
✅ [Dependency (tiktoken)] tiktoken available - Token counting for chunking

================================================================================
Summary: 9 passed, 0 failed
================================================================================

✅ All validation checks passed! Pipeline is ready to run.
```

### Failure Case with Helpful Hints
```
================================================================================
VALIDATION RESULTS
================================================================================

❌ [Input Source (Local)] No files found matching pattern: ./data/**/*.pdf
   💡 Fix: Ensure files exist at the specified path or adjust AZURE_LOCAL_GLOB

❌ [Azure OpenAI (Embeddings)] API key not configured
   💡 Fix: Set AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY environment variable

❌ [Azure AI Search] Index does not exist: my-search-index
   💡 Fix: Create the index first or check AZURE_SEARCH_INDEX

================================================================================
Summary: 6 passed, 3 failed
================================================================================
```

## Benefits

1. **Early Error Detection**: Catch configuration issues before processing documents
2. **Environment-Aware**: Only validates what's needed for your specific setup
3. **Helpful Error Messages**: Each error includes a "Fix" hint explaining how to resolve it
4. **Different Scenarios**: Validates correctly for offline, cloud, and hybrid modes
5. **CI/CD Integration**: Can be used in pipelines to verify configuration
6. **Development Friendly**: Quick way to verify .env file is correct

## Key Features

### Smart Validation
- Only checks services you're actually using
- Skips Azure DI validation if using markitdown mode
- Skips embedding validation if using integrated vectorization
- Adapts to local vs blob storage modes

### Connectivity Testing
- Tests actual connections to Azure services
- Verifies containers exist (or can be created)
- Checks index accessibility and document count
- Validates file system permissions

### Helpful Guidance
- Each failed check includes a fix hint
- Suggests environment variables to set
- Provides configuration examples
- Links related settings

## Integration Points

### In Pipeline Class
```python
class Pipeline:
    def __init__(self, ..., validate_only: bool = False):
        self.validate_only = validate_only
        ...

    async def validate(self) -> bool:
        """Run pre-check validation."""
        validator = PipelineValidator(self.config)
        return await validator.validate_all()

    async def run(self) -> Optional[PipelineStatus]:
        """Run pipeline with optional validation."""
        if self.validate_only:
            await self.validate()
            return None
        ...
```

### In CLI
```python
parser.add_argument(
    "--validate",
    "--pre-check",
    dest="validate_only",
    action="store_true",
    help="Run pre-check validation, then exit"
)
```

## Testing the Feature

### Test 1: Validate with Everything Configured
```bash
# Set up your .env with all required variables
python -m ingestor.cli --validate
```

### Test 2: Validate with Missing Configuration
```bash
# Temporarily remove AZURE_OPENAI_KEY from .env
python -m ingestor.cli --validate
# Should show helpful error about missing API key
```

### Test 3: Validate Before Processing
```bash
# Validate first
python -m ingestor.cli --validate

# If validation passes, run the pipeline
python -m ingestor.cli --glob "documents/*.pdf"
```

### Test 4: Use Validation in Development
```bash
# Create a test script
python examples/validate_config.py
```

## Next Steps

1. **Try It Out**: Run `python -m ingestor.cli --validate` to test your current setup
2. **Review Output**: Check which validations pass/fail
3. **Fix Issues**: Follow the fix hints for any failed validations
4. **Integrate**: Add `--validate` to your CI/CD pipeline
5. **Customize**: Extend the validator for your specific needs

## Files Modified/Created

### New Files
- `src/ingestor/validator.py` - Main validation logic
- `VALIDATION.md` - User documentation
- `examples/validate_config.py` - Example usage
- `VALIDATION_SUMMARY.md` - This file

### Modified Files
- `src/ingestor/pipeline.py` - Added validation support
- `src/ingestor/cli.py` - Added `--validate` flag

## Future Enhancements

Potential improvements:
- [ ] Add performance benchmarking (test query speed, embedding speed)
- [ ] Validate embedding dimensions match search index
- [ ] Test actual document processing with a sample file
- [ ] Validate rate limits and quotas
- [ ] Add JSON output format for CI/CD integration
- [ ] Cache validation results for faster re-runs
- [ ] Add fix automation (e.g., auto-create missing containers)
