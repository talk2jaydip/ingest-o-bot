# Gradio UI User Guide

A comprehensive guide to using the ingestor web interface for document processing and index management.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Feature Overview](#feature-overview)
3. [Tab-by-Tab Guide](#tab-by-tab-guide)
4. [Common Workflows](#common-workflows)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

---

## Getting Started

### Launching the UI

**Option 1: Using the installed command**
```bash
ingestor-ui
```

**Option 2: Using launch scripts**
```bash
# Windows
scripts\launch_ui.bat

# Linux/Mac
./scripts/launch_ui.sh
```

The UI will open automatically at http://localhost:7860

### First Time Setup

1. **Configure Environment**: Create a `.env` file or select one from the `envs/` directory
2. **Validate Configuration**: Click "Validate Configuration" to check your setup
3. **Test Connection**: Use "Check Index" to verify Azure Search connectivity
4. **Process Documents**: Start with a small test file

---

## Feature Overview

### All Tabs at a Glance

| Tab | Purpose | Key Features |
|-----|---------|--------------|
| **Run Pipeline** | Main workflow for document processing | Env file selection, validation, pipeline execution |
| **Configuration Status** | View current environment and settings | Real-time env var display, index status, auto-detection |
| **Help & Documentation** | Reference and usage statistics | Env var reference, quick start guide, analytics |
| **Artifact Management** | Clean up blob storage artifacts | Search files, selective cleanup, full cleanup |
| **Review Index** | Search and manage documents in index | Document search, chunk viewer, remove documents |

---

## Tab-by-Tab Guide

### Tab 1: Run Pipeline

The main tab for processing documents and managing the ingestion pipeline.

#### Section 1: Environment Configuration

**Purpose**: Load different environment files to test various scenarios without copying files.

**Features**:
- **Select Environment File**: Dropdown showing all `.env` files in the `envs/` directory
- **Upload Custom .env File**: Upload a custom environment file from anywhere
- **Load Selected Environment**: Apply the selected environment file
- **Reload Current**: Reload the currently active environment file
- **Refresh File List**: Update the dropdown with new files from `envs/` directory

**How to Use**:
1. Select a `.env` file from the dropdown (e.g., `.env.chromadb.example` for offline mode)
2. Click "Load Selected Environment"
3. The active environment is displayed below the buttons
4. All subsequent operations use this environment

**Use Cases**:
- Test different vector stores (Azure Search vs ChromaDB)
- Test different embedding providers (Azure OpenAI vs Hugging Face vs Cohere)
- Compare performance across configurations
- Debug issues with specific configurations

**Example Workflow**:
```
1. Select ".env.chromadb.example" → Load → Test offline ingestion
2. Select ".env.cohere.example" → Load → Test cloud with Cohere embeddings
3. Select ".env.hybrid.example" → Load → Test hybrid configuration
```

#### Section 2: Configuration Validation

**Purpose**: Validate your environment configuration before running the pipeline to catch errors early.

**Features**:
- **Validate Configuration**: Run comprehensive pre-check validation
- **Auto-validate on env file change**: Automatically validate when loading new environment
- **Validation Results**: Expandable accordion showing detailed results

**What Gets Validated**:
- Input source (local files or blob storage)
- Artifact storage configuration
- Document Intelligence credentials
- Azure OpenAI endpoints and deployments
- Azure Search connectivity
- Required Python dependencies

**Validation Scenarios Detected**:
1. **Local Development** - Local input, local artifacts, Azure Search
2. **Azure Full** - Blob input/output, Azure DI, Azure OpenAI, Azure Search
3. **Offline** - Local input/output, MarkItDown, ChromaDB, Hugging Face
4. **Hybrid Cloud/Local** - Azure Search, local embeddings (Hugging Face)
5. **Azure Cohere** - Azure Search with Cohere embeddings

**How to Read Results**:
- **✅ Green badges**: Configuration passed all checks
- **⚠️ Yellow badges**: Warnings (optional features missing)
- **❌ Red badges**: Errors (required configuration missing)
- **Detected Scenario**: Shows which scenario was detected from your config
- **Required Variables**: Lists what's configured vs missing
- **Actionable Fixes**: Specific instructions to fix issues

**Example Output**:
```
🎯 Detected Scenario: local_dev
✅ Configuration Valid

Required Variables:
✅ AZURE_SEARCH_SERVICE: your-search-service
✅ AZURE_SEARCH_KEY: [set]
✅ AZURE_SEARCH_INDEX: documents-index
✅ AZURE_OPENAI_ENDPOINT: https://your-openai.openai.azure.com
❌ DOCUMENTINTELLIGENCE_ENDPOINT: Not set

Fix: Set DOCUMENTINTELLIGENCE_ENDPOINT to enable Azure DI extraction
```

#### Section 3: Quick Scenario Templates

**Purpose**: Pre-configured scenarios for common use cases.

**Available Templates**:
1. **Scenario 1: Local Development** - Local input/output, no blob storage
2. **Scenario 2: Blob Production** - Full blob storage input/output
3. **Scenario 3: Hybrid Mode** - Blob input, local artifacts (debugging)
4. **Scenario 4: Blob to Local** - Blob input, local output
5. **Scenario 5: Azure Cohere** - Azure Search + Cohere embeddings
6. **Scenario 6: Fully Offline** - ChromaDB + Hugging Face

**Note**: Selecting a scenario automatically updates the UI fields but does NOT change your `.env` file. These are templates to help you understand configurations.

#### Section 4: Input Source Configuration

**Local Input**:
- **Upload File**: Upload a single document (PDF, DOCX, PPTX, TXT, MD, HTML, JSON, CSV)
- **Select Folder**: Choose a local directory to process all files
- **Glob Pattern**: Use wildcard patterns like `*.pdf` or `documents/**/*.docx`

**Blob Storage Input**:
- **Refresh Containers**: Load available containers from your storage account
- **Input Container**: Select the container with your source documents
- **Blob Prefix**: Filter by path prefix (e.g., `2024/reports/`)
- **Blob Filters**: Additional pattern filters (e.g., `*.pdf`)

**Tips**:
- Start with a single file for testing
- Use glob patterns for batch processing
- Check blob container exists before running

#### Section 5: Processing Options

**Document Action**:
- **add** (default): Add new documents or update existing ones
- **remove**: Remove specific documents from the index
- **removeall**: Remove ALL documents from the index (destructive!)

**Office Extractor Mode**:
- **hybrid** (recommended): Try Azure DI first, fallback to MarkItDown
- **azure_di**: Use Azure Document Intelligence only
- **markitdown**: Use MarkItDown library only (offline)

**Additional Options**:
- **Enable offline fallback**: Automatically fall back if Azure services unavailable
- **Setup/Update Index**: Create or update the search index schema before ingestion
- **Verbose Logging**: Enable detailed debug logs

**Advanced Settings**:
- **Max Workers**: Control parallel processing (default: 4, max: 32)

#### Section 6: Run Controls

**Check Index**:
- Verify the search index exists
- Show document count
- Test connectivity
- Provides guidance if index doesn't exist

**Run Pipeline**:
- Starts the document ingestion pipeline
- Streams logs in real-time
- Shows progress and status
- Displays summary statistics on completion

**Stop**:
- Gracefully stops the running pipeline
- Completes current document before stopping
- Shows partial results

**Status Display**:
- Shows current pipeline state (idle, running, completed, error)
- Displays progress messages
- Shows document count and chunks indexed

#### Section 7: Log Streaming

Real-time log output showing:
- Configuration loading
- Document processing steps
- Extraction progress
- Chunking statistics
- Embedding generation
- Upload progress
- Errors and warnings
- Final statistics

---

### Tab 2: Configuration Status

View your current environment configuration and system status.

#### Section 1: Environment Variables Display

**Features**:
- **Real-time Display**: Shows all current environment variables
- **Masked Sensitive Values**: API keys and secrets are partially hidden
- **Color Coding**: Different colors for different variable types
- **Refresh Button**: Reload environment variables

**Variable Categories**:
- **Search Configuration**: Azure Search service, index, credentials
- **Storage Configuration**: Storage account, containers, credentials
- **OpenAI Configuration**: Endpoints, deployments, API keys
- **Document Intelligence**: Endpoint and key
- **Pipeline Settings**: Chunking, processing, input/output modes

**Example Display**:
```
🔍 Azure Search
AZURE_SEARCH_SERVICE: your-search-service
AZURE_SEARCH_KEY: a1b2c3...xyz789 (masked)
AZURE_SEARCH_INDEX: documents-index

🤖 Azure OpenAI
AZURE_OPENAI_ENDPOINT: https://your-openai.openai.azure.com
AZURE_OPENAI_EMBEDDING_DEPLOYMENT: text-embedding-3-large
```

#### Section 2: Auto-Detection Status

**Detected Configuration**:
- **Vector Store**: Azure AI Search or ChromaDB
- **Embeddings Provider**: Azure OpenAI, Hugging Face, Cohere, or OpenAI
- **Office Extractor**: Azure DI, MarkItDown, or Hybrid
- **Input Mode**: Local or Blob
- **Artifact Storage**: Local or Blob

**Status Indicators**:
- ✅ **Configured**: All required variables set
- ⚠️ **Partially Configured**: Some optional variables missing
- ❌ **Not Configured**: Required variables missing

#### Section 3: Check Index Status

**Purpose**: Verify search index connectivity and status.

**Information Provided**:
- Index existence (exists or not found)
- Document count (if index exists)
- Connection status (success or error)
- Suggested actions (create index if needed)

---

### Tab 3: Help & Documentation

Reference materials and usage analytics.

#### Section 1: Environment Variable Reference

**Comprehensive Guide** covering:
- All available environment variables
- Required vs optional variables
- Default values
- Example configurations
- Common pitfalls

**Categories**:
- Input configuration
- Output configuration
- Azure service credentials
- Processing options
- Chunking configuration
- Embedding configuration

#### Section 2: Quick Start Guide

**Step-by-step instructions**:
1. Choose your scenario
2. Configure environment
3. Validate configuration
4. Process documents
5. Review results

#### Section 3: Usage Statistics (Optional)

**Privacy-Preserving Analytics**:
- Local storage only (`.gradio_analytics.json`)
- No personal data collected
- No external API calls
- Opt-out available via checkbox

**Statistics Tracked**:
- Total pipeline runs
- Success vs error counts
- Most common error types
- Feature usage patterns
- Recent activity timeline

**Actions**:
- **Refresh Statistics**: Update displayed stats
- **Clear All Data**: Delete all analytics data
- **Enable/Disable**: Toggle analytics collection

---

### Tab 4: Artifact Management

Clean up blob storage artifacts for documents.

#### What Are Artifacts?

When documents are processed, the pipeline creates several types of artifacts:
- **Pages**: JSON files with extracted page content
- **Chunks**: JSON files with text chunks
- **Images**: Extracted figures and images
- **Citations**: Per-page PDFs for citation links

These are stored in blob storage containers (or local directories in local mode).

#### Section 1: Storage Statistics

**Displays**:
- Total blob count per container
- Total storage size
- Container names
- Last updated timestamp

**Refresh Button**: Update statistics

#### Section 2: Clean Artifacts for Specific Files

**Purpose**: Remove artifacts for specific documents (e.g., after removing from index).

**How to Use**:
1. Enter a filename pattern (e.g., `*.pdf`, `report*`, `MyDocument.docx`)
2. Click "Search Files" to list matching documents
3. Select files from the checkbox list
4. Click "Clean Selected Artifacts"
5. Confirm the operation
6. Monitor the operation log

**Pattern Examples**:
- `*` - All files
- `*.pdf` - All PDF files
- `report*` - Files starting with "report"
- `*2024*` - Files containing "2024"

**What Gets Deleted**:
- All page JSON files for selected documents
- All chunk JSON files
- All extracted images
- All citation PDFs

#### Section 3: Clean ALL Artifacts (DANGER ZONE)

**⚠️ CRITICAL WARNING**: This operation deletes ALL artifacts from ALL containers!

**Triple Confirmation Required**:
1. Check "I understand this will delete ALL artifacts"
2. Check "I understand this action CANNOT be undone"
3. Check "I have backed up any important data"
4. Click "Clean All Artifacts"

**When to Use**:
- Complete system reset
- Switching to different storage account
- Clearing all data before decommissioning

**What Gets Deleted**:
- ALL blobs from pages container
- ALL blobs from chunks container
- ALL blobs from images container
- ALL blobs from citations container

**What Is NOT Affected**:
- Search index documents (use removeall action to clear index)
- Source documents in input container
- Configuration files

---

### Tab 5: Review Index

Search documents in the index and manage document removal.

#### Section 1: Connection Testing

**Purpose**: Test connectivity to Azure Search.

**Buttons**:
- **Test Connection**: Verify search service is accessible
- **Refresh Stats**: Update document count and statistics
- **Clear Search**: Reset search results

**Status Display**:
- Connection status (success or error)
- Total documents in index
- Index name
- Search service endpoint

#### Section 2: Quick Search

**Simple Search Interface**:
- **Search Pattern**: Enter filename or pattern (e.g., `report`, `*.pdf`)
- **Quick Filters**:
  - **All Documents**: Show all documents
  - **PDFs Only**: Filter to PDF files
  - **DOCX Only**: Filter to Word documents
  - **Recent**: Show recently indexed documents

**Search Results**:
- Document filename
- File extension
- Chunk count
- Last modified date
- Click to view details

#### Section 3: Advanced Search

**Advanced Filters**:
- **Category Filter**: Filter by document type or category
- **Date Range**: Filter by indexing date
- **Chunk Count Range**: Filter by number of chunks
- **Custom Filters**: Additional search criteria

**Search Options**:
- **Max Results**: Limit number of results (default: 50)
- **Sort Order**: Sort by relevance, date, or name

#### Section 4: Document Details Viewer

**Chunk Viewer** - When clicking a document:

**Content Tab**:
- View full chunk text
- Navigate between chunks
- Search within chunks
- Export chunk content

**Metadata Tab**:
- Document ID
- Filename and path
- Storage URLs
- Processing date
- Chunk count
- Embedding model used

**Analysis Tab**:
- Token counts
- Character counts
- Chunk overlap statistics
- Processing metadata

**Context Tab**:
- Previous chunk (for context)
- Current chunk
- Next chunk (for context)
- Overlap regions highlighted

**Chunk Navigation**:
- **Reload All Chunks**: Refresh chunk list
- **Export Current**: Export current chunk to file
- **Close Viewer**: Close the chunk viewer

#### Section 5: Document Actions

**Remove Documents**:
1. Search for documents (Quick or Advanced Search)
2. Select documents from results
3. Click "Remove Selected Documents"
4. Confirm removal
5. Documents and chunks removed from index

**Note**: Removing documents from index does NOT delete artifacts. Use Artifact Management tab to clean artifacts.

---

## Common Workflows

### Workflow 1: Testing Different Scenarios with Environment Files

**Use Case**: Test offline mode vs cloud mode without modifying your main `.env` file.

**Steps**:
1. Go to "Run Pipeline" tab
2. In "Environment Configuration" section:
   - Select `.env.chromadb.example` from dropdown
   - Click "Load Selected Environment"
3. Click "Validate Configuration"
   - Verify "Detected Scenario: offline"
   - Check all required variables are set
4. Configure input (upload test PDF)
5. Click "Run Pipeline"
6. Monitor logs and verify success
7. Switch to `.env.cohere.example` and repeat to compare

**Benefits**:
- No need to edit `.env` file
- Easy A/B testing
- Quick scenario switching
- Safe experimentation

### Workflow 2: Running Validation Before Pipeline

**Use Case**: Catch configuration errors before running the pipeline.

**Steps**:
1. Go to "Run Pipeline" tab
2. Load your desired environment file
3. Click "Validate Configuration"
4. Review validation results:
   - ✅ If all green: Proceed to run pipeline
   - ⚠️ If warnings: Review and decide if acceptable
   - ❌ If errors: Fix issues before running
5. Expand "Validation Results" to see details
6. Follow suggested fixes for any errors
7. Re-validate after making changes
8. Run pipeline once validation passes

**Common Issues Caught**:
- Missing API keys
- Invalid endpoints
- Non-existent containers
- Unreachable services
- Missing dependencies

### Workflow 3: Managing Index Operations

**Use Case**: Check index status, create index, and verify documents.

**Steps**:
1. **Check Index** (Run Pipeline tab):
   - Click "Check Index" button
   - Verify index exists and document count
2. **Create Index** (if needed):
   - Enable "Setup/Update Index" checkbox
   - Click "Run Pipeline" (it will create index then stop)
3. **Review Documents** (Review Index tab):
   - Click "Test Connection"
   - Click "All Documents" to see all docs
   - Review document list
4. **Remove Documents** (if needed):
   - Search for specific documents
   - Select documents to remove
   - Click "Remove Selected Documents"
   - Confirm removal

### Workflow 4: Cleaning Artifacts

**Use Case**: Clean up storage after removing documents from index.

**Steps**:
1. **Remove from Index** (Review Index tab):
   - Search for documents
   - Select documents to remove
   - Click "Remove Selected Documents"
2. **Clean Artifacts** (Artifact Management tab):
   - Go to "Clean Artifacts for Specific Files"
   - Enter same filename pattern used for removal
   - Click "Search Files"
   - Select files from list
   - Click "Clean Selected Artifacts"
   - Confirm operation
3. **Verify Cleanup**:
   - Click "Refresh Statistics"
   - Verify blob counts decreased

### Workflow 5: Removing Documents and Cleaning Up

**Use Case**: Completely remove a document from both index and storage.

**Steps**:
1. **Review Index** tab:
   - Search for document by name
   - Note the filename
   - Select document
   - Click "Remove Selected Documents"
   - Confirm removal
2. **Artifact Management** tab:
   - Enter exact filename in search pattern
   - Click "Search Files"
   - Select the file
   - Click "Clean Selected Artifacts"
   - Confirm cleanup
3. **Verify** (Review Index tab):
   - Search for document again
   - Should return no results
4. **Verify** (Artifact Management tab):
   - Refresh statistics
   - Blob count should be reduced

### Workflow 6: Batch Processing with Validation

**Use Case**: Process multiple documents with validation and monitoring.

**Steps**:
1. **Prepare**:
   - Load appropriate environment file
   - Validate configuration
   - Check index exists
2. **Configure Input**:
   - Select "Local" input mode
   - Enter glob pattern: `documents/**/*.pdf`
   - Or select folder with multiple files
3. **Configure Options**:
   - Set Max Workers: 8 (for parallel processing)
   - Enable "Verbose Logging" for detailed output
   - Keep "Setup/Update Index" unchecked (if index exists)
4. **Run**:
   - Click "Run Pipeline"
   - Monitor log streaming
   - Watch progress messages
5. **Review Results**:
   - Check final statistics (documents processed, chunks indexed)
   - Go to "Review Index" tab to verify documents
   - Check "Configuration Status" for updated document count

---

## Troubleshooting

### Issue: "Index does not exist" Error

**Symptoms**:
- Validation shows index not found
- "Check Index" returns "Index not found"
- Pipeline fails with index error

**Solution**:
1. Go to "Run Pipeline" tab
2. Enable "Setup/Update Index" checkbox
3. Click "Run Pipeline"
4. Index will be created automatically
5. Verify with "Check Index" button

**Alternative**:
```bash
# Create index via CLI
python -m ingestor.cli --setup-index
```

### Issue: Validation Fails with "Connection Error"

**Symptoms**:
- Red error badges in validation
- "Could not connect to service" messages
- Timeout errors

**Possible Causes**:
1. **Incorrect Endpoint**: Check service URLs are correct
2. **Invalid Credentials**: Verify API keys are valid
3. **Network Issues**: Check firewall/proxy settings
4. **Service Unavailable**: Check Azure service status

**Solution**:
1. Go to "Configuration Status" tab
2. Check all endpoints and credentials
3. Verify values match Azure portal
4. Test individual connections:
   - "Check Index Status" for Azure Search
   - "Test Connection" in Review Index tab
5. Check Azure portal for service health

### Issue: Environment File Not Loading

**Symptoms**:
- "Failed to load environment file" message
- Variables not updated after loading
- Active environment shows "None"

**Possible Causes**:
1. **File Format Error**: `.env` file has syntax errors
2. **File Not Found**: File moved or deleted
3. **Permission Error**: Cannot read file

**Solution**:
1. Click "Refresh File List"
2. Verify file appears in dropdown
3. Check file format (should be `KEY=value` format)
4. Try uploading file instead of selecting from dropdown
5. Check file permissions

**Example Valid .env Format**:
```bash
# Comments are allowed
AZURE_SEARCH_SERVICE=my-search
AZURE_SEARCH_KEY=abc123
# No spaces around =
# No quotes needed for simple values
```

### Issue: Pipeline Runs But No Documents Indexed

**Symptoms**:
- Pipeline completes successfully
- "0 documents processed" in output
- Log shows "No files found"

**Possible Causes**:
1. **Wrong Input Path**: Files not in specified location
2. **Pattern Mismatch**: Glob pattern doesn't match files
3. **Empty Container**: Blob container has no files
4. **Permission Error**: Cannot read input files

**Solution**:
1. **For Local Input**:
   - Verify files exist at specified path
   - Check glob pattern is correct
   - Try absolute path instead of relative
2. **For Blob Input**:
   - Go to Azure portal and verify container has blobs
   - Check blob prefix is correct
   - Verify storage account credentials
   - Try "Refresh Containers" button
3. **Test with Single File**:
   - Use "Upload File" instead of glob
   - Verify single file processes successfully

### Issue: Validation Passes But Pipeline Fails

**Symptoms**:
- Validation shows all green
- Pipeline starts but fails during processing
- Errors in log streaming

**Possible Causes**:
1. **Transient Errors**: Temporary service issues
2. **Rate Limiting**: Too many concurrent requests
3. **Document Issues**: Corrupted or unsupported files
4. **Token Limits**: Documents too large for embedding model

**Solution**:
1. Check error message in logs
2. Reduce Max Workers (try 2-4)
3. Test with single small document
4. Check Azure service quotas and limits
5. Review document format and size
6. Enable "Verbose Logging" for details

### Issue: Artifact Cleanup Fails

**Symptoms**:
- "Failed to delete artifacts" message
- Some blobs not deleted
- Operation log shows errors

**Possible Causes**:
1. **Permission Error**: No delete permission on container
2. **Blob Locked**: Blob has active lease
3. **Container Not Found**: Container doesn't exist

**Solution**:
1. Check storage account permissions (need delete access)
2. Verify container exists in Azure portal
3. Wait a few minutes and retry (in case of temporary locks)
4. Try cleaning files individually instead of batch
5. Check operation log for specific error details

### Issue: "Out of Memory" Error During Processing

**Symptoms**:
- Pipeline crashes mid-processing
- "MemoryError" in logs
- System becomes unresponsive

**Possible Causes**:
1. **Too Many Workers**: Parallel processing uses too much memory
2. **Large Documents**: Documents are very large
3. **Insufficient RAM**: System resources exhausted

**Solution**:
1. Reduce Max Workers to 2 or 4
2. Process documents in smaller batches
3. Increase system RAM if possible
4. Use pagination for large document sets
5. Process one document at a time for very large files

---

## FAQ

### General Questions

**Q: Do I need to restart the UI after changing environment files?**
A: No! Just use the "Load Selected Environment" feature. The UI will reload the environment variables without restarting.

**Q: Are my API keys safe in the UI?**
A: Yes. The "Configuration Status" tab masks sensitive values (shows only first/last few characters). API keys are never logged or transmitted.

**Q: Can I use the UI and CLI at the same time?**
A: Yes, but avoid running both against the same index simultaneously. The CLI and UI share the same configuration, so changes in one affect the other.

**Q: Where are usage analytics stored?**
A: Analytics are stored locally in `.gradio_analytics.json` in your working directory. No data is sent to external services. You can opt out anytime.

**Q: What happens if I close the browser during pipeline execution?**
A: The pipeline continues running in the background. Reopen the UI and check the logs. To stop execution, use the "Stop" button before closing.

### Environment Files

**Q: How do I create a custom environment file?**
A: Copy an existing example from `envs/` directory and modify values:
```bash
cp envs/.env.example envs/.env.myconfig
# Edit envs/.env.myconfig with your values
```
Then select it in the UI dropdown.

**Q: Can I use the same environment file for CLI and UI?**
A: Yes! Both CLI and UI use the same `.env` file format. You can test with UI and run production with CLI using the same configuration.

**Q: What's the difference between "None (use system environment)" and selecting a file?**
A: "None" uses variables from your current shell environment and the default `.env` file. Selecting a file explicitly loads that file's variables, overriding defaults.

### Validation

**Q: Is validation required before running the pipeline?**
A: No, it's optional but highly recommended. Validation catches configuration errors early and provides helpful fix suggestions.

**Q: What's the difference between validation scenarios?**
A: Scenarios represent common configuration patterns (e.g., "offline" uses ChromaDB + Hugging Face, "azure_full" uses all Azure services). Validation detects your scenario automatically.

**Q: Can I run the pipeline if validation shows warnings?**
A: Yes. Yellow warnings indicate optional features are not configured (e.g., media description). The pipeline will work but skip optional features.

### Index Management

**Q: Do I need to run "Setup/Update Index" every time?**
A: No, only the first time or when you change the index schema. For regular document processing, leave it unchecked.

**Q: What happens if I delete the index?**
A: All documents and chunks are removed from search. You'll need to recreate the index and re-ingest all documents. Artifacts in blob storage are NOT deleted.

**Q: Can I have multiple indexes?**
A: Yes! Create different `.env` files with different `AZURE_SEARCH_INDEX` values. Switch between them using the environment file dropdown.

### Artifact Management

**Q: Should I clean artifacts after removing documents from index?**
A: It's recommended for storage efficiency, but not required. Artifacts don't affect search results. Clean them when storage costs are a concern.

**Q: What happens if I clean artifacts but don't remove from index?**
A: Search results will still show the document, but citation links and artifact references will be broken. Always remove from index first.

**Q: How can I recover deleted artifacts?**
A: You cannot. Artifact deletion is permanent. To restore, you must re-process the original documents.

### Performance

**Q: How many workers should I use?**
A: Start with default (4). Increase to 8-16 for high-end machines and fast network. Decrease to 2-4 if experiencing memory issues or rate limiting.

**Q: Why is processing slow?**
A: Common causes:
- Network latency to Azure services
- Large document sizes
- Complex documents (many tables/images)
- Rate limiting (reduce workers)
- Slow embedding model

**Q: Can I speed up processing?**
A: Yes:
- Increase Max Workers (if resources allow)
- Use faster embedding models
- Enable offline fallback
- Process smaller batches
- Use local artifacts storage

### Errors

**Q: Why do I get "Rate limit exceeded" errors?**
A: Azure services have rate limits. Solutions:
- Reduce Max Workers
- Add delays between requests
- Upgrade Azure service tier
- Process in smaller batches

**Q: What does "ValidationError" mean?**
A: Your configuration is missing required variables or has invalid values. Run validation to see detailed error messages and fixes.

**Q: Why does the UI show "Connection refused"?**
A: Possible causes:
- Azure services are down (check Azure status)
- Firewall blocking connections
- Invalid credentials
- Wrong endpoint URL

---

## Additional Resources

### Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Validation Guide](VALIDATION.md)** - Detailed validation system documentation
- **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
- **[CLI Guide](QUICK_REFERENCE.md)** - Command-line interface reference
- **[Vector Stores Guide](../vector_stores.md)** - Choose your vector database
- **[Embeddings Providers Guide](../embeddings_providers.md)** - Choose your embedding model

### Example Configurations

See the `envs/` directory for ready-to-use configuration examples:
- `.env.chromadb.example` - Fully offline (ChromaDB + Hugging Face)
- `.env.cohere.example` - Cloud with Cohere embeddings
- `.env.hybrid.example` - Hybrid cloud/local
- `.env.scenario-development.example` - Local development
- `.env.scenario-azure-openai-default.example` - Azure full stack

### Need Help?

1. Check this guide's Troubleshooting section
2. Review validation error messages (they include fix suggestions)
3. Check the documentation links above
4. Review logs with verbose logging enabled
5. Test with a single small file first

---

**Last Updated**: 2026-02-12
**Version**: 1.0
