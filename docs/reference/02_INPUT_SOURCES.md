# INPUT Container Lifecycle Guide

This guide explains when and how INPUT containers are created, and how file validation works.

---

## Key Principle: INPUT vs OUTPUT Containers

The pipeline treats INPUT and OUTPUT containers very differently:

| Container Type | Purpose | Created By | Must Pre-Exist? |
|---|---|---|---|
| **INPUT** | Read source files | **YOU** (manually) | **YES** |
| **OUTPUT** | Write artifacts | **Pipeline** (auto) | NO |

---

## INPUT Container (`AZURE_BLOB_CONTAINER_IN`)

### The INPUT container is NEVER created by the pipeline

When you configure:
```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-improvement-index
```

The pipeline **expects this container to already exist** in your Azure Storage account with files uploaded.

### How to create the INPUT container

**Option 1: Azure Portal**
1. Navigate to your Storage Account
2. Go to "Containers" section
3. Click "+ Container"
4. Create container named `my-improvement-index`
5. Upload your PDF/document files

**Option 2: Azure CLI**
```bash
# Create container
az storage container create \
  --name my-improvement-index \
  --account-name mystorageaccount

# Upload files
az storage blob upload-batch \
  --destination my-improvement-index \
  --source ./local-docs/ \
  --account-name mystorageaccount
```

**Option 3: Azure Storage Explorer**
1. Open Azure Storage Explorer
2. Connect to your storage account
3. Right-click "Blob Containers"
4. Create new container
5. Drag and drop files

---

## OUTPUT Containers (Auto-Created)

When you configure:
```bash
AZURE_BLOB_CONTAINER_PREFIX=myproject
AZURE_BLOB_CONTAINER_OUT_PAGES=pages
AZURE_BLOB_CONTAINER_OUT_CHUNKS=chunks
AZURE_BLOB_CONTAINER_OUT_IMAGES=images
```

The pipeline **automatically creates** these containers:
- `myproject-pages`
- `myproject-chunks`
- `myproject-images`

You do NOT need to create these manually.

---

## File Validation (NEW)

As of the latest version, the pipeline validates that files exist before processing.

### What happens when no files are found?

**Before (old behavior)**:
```
INFO: Starting document ingestion pipeline
INFO: Downloaded 0 files from blob storage
INFO: Pipeline completed successfully
# ^ Confusing - nothing was processed!
```

**After (new behavior)**:
```
INFO: Starting document ingestion pipeline
ERROR: No files found in input source. Check your configuration:
ERROR:   - AZURE_INPUT_MODE=blob
ERROR:   - AZURE_BLOB_CONTAINER_IN=my-improvement-index
ERROR:   - AZURE_BLOB_PREFIX=(none)
ERROR:   Ensure the container exists and contains files
ValueError: No files found to process
# ^ Clear error prevents wasted processing
```

### When validation occurs

File validation happens at the start of:
1. **ADD action** (`python -m cli` or `python -m cli --action add`)
2. **REMOVE action** (`python -m cli --action remove`)

The pipeline will immediately exit with an error if no files are found.

---

## Common Scenarios

### Scenario 1: Container doesn't exist

```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-docs
```

**What happens**: Pipeline crashes with Azure SDK error
```
azure.core.exceptions.ResourceNotFoundError: The specified container does not exist.
```

**Solution**: Create the container first (see above)

---

### Scenario 2: Container exists but is empty

```bash
AZURE_INPUT_MODE=blob
AZURE_BLOB_CONTAINER_IN=my-docs  # Container exists but empty
```

**What happens**: Pipeline exits with validation error
```
ERROR: No files found in input source. Check your configuration:
ERROR:   - AZURE_BLOB_CONTAINER_IN=my-docs
ValueError: No files found to process
```

**Solution**: Upload files to the container

---

### Scenario 3: Container has files but wrong prefix

```bash
AZURE_BLOB_CONTAINER_IN=my-docs     # Has files: reports/doc1.pdf, reports/doc2.pdf
AZURE_BLOB_PREFIX=documents/        # But you're looking in wrong folder!
```

**What happens**: Pipeline exits with validation error
```
ERROR: No files found in input source. Check your configuration:
ERROR:   - AZURE_BLOB_CONTAINER_IN=my-docs
ERROR:   - AZURE_BLOB_PREFIX=documents/
ValueError: No files found to process
```

**Solution**: Fix the prefix or remove it to search entire container

---

### Scenario 4: Local mode with wrong glob pattern

```bash
AZURE_INPUT_MODE=local
AZURE_LOCAL_GLOB=./data/*.pdf  # But files are in ./documents/
```

**What happens**: Pipeline exits with validation error
```
ERROR: No files found in input source. Check your configuration:
ERROR:   - AZURE_INPUT_MODE=local
ERROR:   - AZURE_LOCAL_GLOB=./data/*.pdf
ERROR:   Ensure files exist matching the glob pattern
ValueError: No files found to process
```

**Solution**: Fix the glob pattern to match your files

---

## Understanding the Sample Test PDF

If you see the pipeline processing `samples/sample_pages_test.pdf` by default, it's because:

1. You're using the test environment configuration
2. The file `envs/env.test` contains:
   ```bash
   AZURE_INPUT_MODE=local
   AZURE_LOCAL_GLOB=samples/sample_pages_test.pdf
   ```

This is intentional for testing purposes. To use your own files:

**Option 1: Create your own .env**
```bash
cp .env .env.backup
# Edit .env with your own configuration
```

**Option 2: Use different env file**
```bash
cp envs/env.production .env
# Edit .env with your settings
```

**Option 3: Override with environment variables**
```bash
AZURE_INPUT_MODE=blob \
AZURE_BLOB_CONTAINER_IN=my-docs \
python -m cli
```

---

## Checklist: Before Running the Pipeline

- [ ] **INPUT container exists** in Azure Storage (if using blob mode)
- [ ] **Files are uploaded** to the INPUT container
- [ ] **Glob pattern is correct** (if using local mode)
- [ ] **Files are in the right location** matching your configuration
- [ ] **Prefix is correct** (if filtering blob container by path)

If all checks pass, you'll see:
```
INFO: Found 5 file(s) to process
INFO: Processing document: doc1.pdf
...
```

---

## Related Documentation

- [Configuration Guide](../guides/CONFIGURATION.md)
- [Blob Storage](03_BLOB_STORAGE.md)
- [Environment Variables](12_ENVIRONMENT_VARIABLES.md)
