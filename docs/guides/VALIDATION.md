# Pipeline Configuration Validation

The ingestor pipeline now includes a comprehensive pre-check validation system that verifies your configuration and dependencies before running the pipeline.

## Usage

### Command Line

Run validation using the `--validate` or `--pre-check` flag:

```bash
python -m ingestor.cli --validate
```

This will:
1. Check all configuration settings based on your environment
2. Test connectivity to Azure services (if configured)
3. Verify all required dependencies are installed
4. Provide helpful error messages with fixes if validation fails
5. Exit without processing any documents

### Programmatic Usage

You can also run validation programmatically:

```python
from ingestor.config import PipelineConfig
from ingestor.pipeline import Pipeline

# Load configuration
config = PipelineConfig.from_env()

# Create pipeline with validate_only flag
pipeline = Pipeline(config, validate_only=True)

# Run validation
try:
    await pipeline.run()
    print("✅ Validation passed!")
except RuntimeError as e:
    print(f"❌ Validation failed: {e}")
```

Or use the validator directly:

```python
from ingestor.config import PipelineConfig
from ingestor.validator import PipelineValidator

# Load configuration
config = PipelineConfig.from_env()

# Create and run validator
validator = PipelineValidator(config)
success = await validator.validate_all()

if success:
    print("✅ All checks passed!")
else:
    print("❌ Some checks failed")
```

## What Gets Validated

The validation system checks different components based on your configuration:

### 1. Input Source
- **Local mode**: Verifies files exist matching the glob pattern
- **Blob mode**: Tests connection to Azure Blob Storage and verifies container exists and contains files

### 2. Artifacts Storage
- **Local mode**: Checks directory is writable
- **Blob mode**: Tests connection and verifies/creates required containers (pages, chunks, images, citations)

### 3. Document Intelligence
- **Azure DI mode**: Validates endpoint and credentials
- **MarkItDown mode**: Skips (not required)
- **Hybrid mode**: Validates Azure DI with fallback to MarkItDown

### 4. Office Extractor
- Verifies MarkItDown library is installed (if using markitdown or hybrid mode)
- Checks Azure Document Intelligence configuration (if using azure_di or hybrid mode)

### 5. Azure OpenAI
- **Client-side embeddings**: Validates endpoint, API key, and deployment
- **Integrated vectorization**: Skips embedding validation
- **Media description (GPT-4o)**: Validates chat deployment configuration

### 6. Azure AI Search
- Tests connection to search service
- Verifies index exists (or provides guidance to create it)
- Checks index accessibility and document count

### 7. Media Describer
- **GPT-4o mode**: Validates Azure OpenAI chat deployment
- **Content Understanding mode**: Validates Content Understanding endpoint
- **Disabled mode**: Skips validation

### 8. Python Dependencies
- Checks required libraries (tiktoken, etc.)
- Validates optional dependencies based on configuration (pypdf for page splitting)

## Validation Scenarios by Environment

### Local Development (Offline Mode)
When using `EXTRACTION_MODE=markitdown`:
- ✅ Local files validation
- ✅ Local artifacts directory validation
- ✅ MarkItDown library check
- ⏭️ Skips Azure DI validation
- ⏭️ May skip Azure OpenAI if using integrated vectorization

### Cloud Mode (Full Azure)
When using `EXTRACTION_MODE=azure_di`:
- ✅ Blob storage validation (if configured)
- ✅ Azure Document Intelligence validation
- ✅ Azure OpenAI validation (if client-side embeddings)
- ✅ Azure AI Search validation
- ✅ Media describer validation (if enabled)

### Hybrid Mode (Recommended)
When using `EXTRACTION_MODE=hybrid`:
- ✅ All Azure services validation
- ✅ MarkItDown fallback validation
- ✅ Comprehensive dependency check

## Example Output

### Successful Validation
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

### Failed Validation
```
================================================================================
🔍 PIPELINE PRE-CHECK VALIDATION
================================================================================

🔍 Validating Input Source...
🔍 Validating Artifacts Storage...
🔍 Validating Azure Document Intelligence...
🔍 Validating Azure OpenAI...
🔍 Validating Azure AI Search...

================================================================================
VALIDATION RESULTS
================================================================================

❌ [Input Source (Local)] No files found matching pattern: ./data/**/*.pdf
   💡 Fix: Ensure files exist at the specified path or adjust LOCAL_INPUT_GLOB

❌ [Azure OpenAI (Embeddings)] API key not configured
   💡 Fix: Set AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY environment variable

❌ [Azure AI Search] Index does not exist: my-search-index
   💡 Fix: Create the index first or check AZURE_SEARCH_INDEX

✅ [Document Intelligence] Client configured: https://your-di.cognitiveservices.azure.com/
✅ [Artifacts Storage (Local)] Directory writable: ./artifacts

================================================================================
Summary: 2 passed, 3 failed
================================================================================

ERROR: Validation failed with 3 error(s). Please fix the issues above and try again.
```

## Integration with CI/CD

You can use validation in your CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Validate Pipeline Configuration
  run: |
    python -m ingestor.cli --validate
  env:
    AZURE_SEARCH_ENDPOINT: ${{ secrets.AZURE_SEARCH_ENDPOINT }}
    AZURE_SEARCH_INDEX: ${{ secrets.AZURE_SEARCH_INDEX }}
    AZURE_SEARCH_KEY: ${{ secrets.AZURE_SEARCH_KEY }}
    # ... other environment variables
```

## Environment Variables Checked

The validator checks different environment variables based on your configuration:

### Always Required
- `AZURE_SEARCH_ENDPOINT` or `AZURE_SEARCH_SERVICE`
- `AZURE_SEARCH_INDEX`

### Required for Client-Side Embeddings (when not using integrated vectorization)
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY` or `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

### Required for Azure DI Mode
- `AZURE_DOC_INT_ENDPOINT`
- `AZURE_DOC_INT_KEY` (optional, can use DefaultAzureCredential)

### Required for Local Input
- `LOCAL_INPUT_GLOB`

### Required for Blob Input
- `AZURE_STORAGE_ACCOUNT` or `AZURE_CONNECTION_STRING`
- `AZURE_BLOB_CONTAINER_IN` or `AZURE_STORAGE_CONTAINER`

### Required for Blob Artifacts
- `AZURE_STORAGE_ACCOUNT` or `AZURE_CONNECTION_STRING`
- `AZURE_BLOB_CONTAINER_OUT_PAGES` or `AZURE_STORAGE_CONTAINER`
- `AZURE_BLOB_CONTAINER_OUT_CHUNKS` or `AZURE_STORAGE_CONTAINER`

### Optional (Validated if Configured)
- `AZURE_OPENAI_CHAT_DEPLOYMENT` (for GPT-4o media description)
- `AZURE_CONTENT_UNDERSTANDING_ENDPOINT` (for Content Understanding)
- `AZURE_BLOB_CONTAINER_OUT_IMAGES`
- `AZURE_BLOB_CONTAINER_CITATIONS`

## Tips

1. **Run validation before deploying** to catch configuration issues early
2. **Use validation in development** to verify your .env file is correct
3. **Check validation output** for hints on how to fix issues
4. **Combine with verbose logging** (`--validate --verbose`) for more details
5. **Test different scenarios** by changing environment variables and re-running validation
