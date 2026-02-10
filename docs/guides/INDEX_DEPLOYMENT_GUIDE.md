# Index Deployment Integration Guide

How to deploy the Azure AI Search index and run ingestion in one command.

---

## 🚀 **Quick Start**

### Deploy Index + Ingest Documents (One Command)

```bash
ingestor --setup-index --glob "documents/*.pdf"
```

This will:
1. ✅ Deploy/update the Azure AI Search index
2. ✅ Process and ingest your documents

---

## 📋 **Command Options**

### Index Management Flags

| Flag | Description |
|------|-------------|
| `--index-only` | Deploy/update index ONLY (skip ingestion) |
| `--delete-index` | Delete index ONLY (skip ingestion) |
| `--setup-index` | Deploy/update the index before ingestion |
| `--force-index` | Force delete and recreate index (standalone or with `--setup-index`, ⚠️ destroys all data) |
| `--skip-ingestion` | Skip document ingestion (useful with index operations) |
| `--verbose` | Enable verbose/debug logging |

### Document Ingestion Flags

| Flag | Description |
|------|-------------|
| `--pdf PATH` or `--file PATH` | Process a single file |
| `--glob PATTERN` | Process files matching glob pattern |
| `--action {add\|remove\|removeall}` | Document action mode |

---

## 🎯 **Common Scenarios**

### 1. **Index Management Only (No Ingestion)**

#### 1a. Deploy/Update Index Only
```bash
# Update index schema without processing documents
ingestor --index-only
```

**What happens:**
1. ✅ Creates or updates the index
2. ✅ Configures BM25, analyzers, vector search
3. ⏭️ Skips document ingestion

**Use when:**
- Setting up a new environment
- Updating index schema
- Testing index configuration

#### 1b. Delete Index Only
```bash
# Delete index without running ingestion
ingestor --delete-index
```

**What happens:**
1. ⚠️ **Deletes existing index** (all data lost)
2. ⏭️ Exits immediately (no ingestion)

**Use when:**
- Cleaning up test indexes
- Removing old indexes
- Resetting environment

**Graceful error handling:**
- If index doesn't exist: Shows info message, exits cleanly (not an error)
- If deletion fails: Shows error, exits with error code

#### 1c. Force Recreate Index Only (Standalone)
```bash
# Delete and recreate index without running ingestion
ingestor --force-index
```

**What happens:**
1. ⚠️ **Deletes existing index** (all data lost)
2. ✅ Creates fresh index
3. ⏭️ Exits immediately (no ingestion)

**Use when:**
- Need fresh index schema
- Testing index configuration changes
- Want to recreate index without ingesting yet

**Graceful error handling:**
- If index doesn't exist: Just creates new index (not an error)
- If deletion fails: Shows error, exits with error code
- If creation fails: Shows error, exits with error code

---

### 2. **First Time Setup (New Index + Ingest)**

```bash
# Deploy index and ingest documents
ingestor \
  --setup-index \
  --glob "documents/*.pdf"
```

**What happens:**
1. ✅ Creates new index with optimized settings
2. ✅ Configures BM25, analyzers, vector search
3. ✅ Processes and indexes documents

---

### 3. **Force Recreate Index (Clean Slate)**

```bash
# WARNING: This deletes all existing data!
ingestor \
  --setup-index \
  --force-index \
  --glob "documents/*.pdf"
```

**What happens:**
1. ⚠️ **Deletes existing index** (all data lost)
2. ✅ Creates fresh index
3. ✅ Processes and indexes documents

**Use when:**
- Index schema changed
- Need to start fresh
- Testing new configurations

---

### 4. **Update Index Settings (No Data Loss)**

```bash
# Update index without deleting data
ingestor \
  --setup-index \
  --glob "documents/*.pdf"
```

**What happens:**
1. ✅ Updates index settings (if possible)
2. ⚠️ If incompatible changes, will prompt for `--force-index`
3. ✅ Processes and indexes documents

---

### 5. **Verbose Logging (Debug Mode)**

```bash
# See detailed steps
ingestor \
  --setup-index \
  --force-index \
  --verbose \
  --glob "documents/*.pdf"
```

**Output includes:**
- Index creation steps
- Field configurations
- Scoring profile details
- Vector search settings
- Document processing details

---

## 📊 **What Gets Deployed**

When you use `--setup-index`, the following are configured:

### 1. **BM25 Similarity**
```
k1 = 1.5 (boost term frequency)
b = 0.5 (reduce document length penalty)
```

### 2. **Analyzers**
- `title`: `standard.lucene` (page headers)
- `productTradeNames`: `standard.lucene` (product names)
- `filename`, `sourcefile`, `sourcepage`: `keyword` (exact match)

### 3. **Scoring Profiles**
- `productBoostingProfile`: For product searches
- `contentRAGProfile`: For general RAG queries

### 4. **Semantic Configuration**
- Title field: `title`
- Content fields: `content`, `applicableTo`
- Keywords: `productTradeNames`, `product_family`, `partNumber`, `model`, `category`

### 5. **Vector Search**
- HNSW algorithm: `m=16`, `ef_construction=400`, `ef_search=500`
- Scalar quantization: `int8` with `default_oversampling=20.0`
- Embeddings field: `retrievable=True`

### 6. **Suggester**
- Autocomplete on: `title`, `productTradeNames`, `product_family`, `partNumber`

---

## 🔍 **Validation**

After deployment, the script automatically validates:

✅ BM25 similarity configured  
✅ Semantic title field set to 'title'  
✅ Title analyzer is 'standard.lucene'  
✅ Embeddings field is retrievable  
✅ Vector compression configured  
✅ Vector search algorithms configured  
✅ Scoring profiles present  

---

## 📝 **Example Workflows**

### Workflow 1: Development Setup

```bash
# Option A: Standalone force recreate (no ingestion)
# 1. Recreate index only
ingestor --force-index

# 2. Test with sample file
ingestor --pdf "samples/test.pdf"

# 3. Ingest all documents
ingestor --glob "documents/**/*"
```

```bash
# Option B: All-in-one (recreate + ingest)
# 1. Recreate index and ingest in one command
ingestor --setup-index --force-index --glob "documents/**/*"

# 2. Test with specific file
ingestor --pdf "samples/test.pdf"
```

### Workflow 2: Production Deployment

```bash
# 1. Deploy index (first time)
ingestor \
  --setup-index \
  --verbose \
  --glob "production_docs/*.pdf"

# 2. Re-index specific document
ingestor --pdf "updated_manual.pdf"

# 3. Remove old document
ingestor \
  --action remove \
  --pdf "old_manual.pdf"
```

### Workflow 3: Schema Update

```bash
# 1. Backup data (manual step - export from Azure Portal if needed)

# 2. Force recreate with new schema
ingestor \
  --setup-index \
  --force-index \
  --verbose

# 3. Re-ingest all documents
ingestor --glob "all_documents/**/*"
```

---

## ⚠️ **Important Notes**

### 1. **`--force-index` is Destructive**

```bash
# Standalone: Deletes and recreates index, then EXITS (no ingestion)
ingestor --force-index

# With --setup-index: Deletes, recreates, THEN ingests documents
ingestor --setup-index --force-index --glob "documents/*.pdf"
```

**Both modes DELETE ALL DATA in the index!**

**Before using `--force-index`:**
- ✅ Backup important data
- ✅ Confirm you want to delete everything
- ✅ Have source documents ready to re-ingest (if using with `--setup-index`)

### 2. **Index Must Match Schema**

Your index schema must match `my_index.json`. If you've customized the schema, update `index.py` accordingly.

### 3. **Credentials Required**

Ensure these environment variables are set:
```bash
AZURE_SEARCH_SERVICE=your-service
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=your-index-name
```

### 4. **OpenAI for Integrated Vectorizer (Optional)**

If you want integrated vectorization:
```bash
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_KEY=your-key
```

---

## 🐛 **Troubleshooting**

### Error: "Index already exists"

```bash
# Option A: Standalone - recreate index only (no ingestion)
ingestor --force-index

# Option B: Recreate and ingest
ingestor --setup-index --force-index --glob "documents/*.pdf"
```

### Error: "Cannot update index"

Some index changes require recreation:
```bash
# Option A: Standalone - recreate index only (no ingestion)
ingestor --force-index

# Option B: Recreate and ingest
ingestor --setup-index --force-index --glob "documents/*.pdf"
```

### Error: "Import failed"

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Want to see detailed steps?

```bash
# Use --verbose
ingestor --setup-index --verbose
```

---

## 📚 **Related Documentation**

- [Index Improvements Summary](INDEX_IMPROVEMENTS_SUMMARY.md)
- [Index Validation Guide](06_INDEX_VALIDATION.md)
- [Scoring Profiles Guide](SCORING_PROFILES_GUIDE.md)
- [Configuration Guide](CONFIGURATION.md)

---

## 🎉 **Complete Example**

```bash
# Full workflow: Deploy index + Ingest documents + Verbose logging
ingestor \
  --setup-index \
  --force-index \
  --verbose \
  --glob "documents/**/*.pdf"
```

**Output:**
```
======================================================================
STEP 1: Azure AI Search Index Deployment
======================================================================
Search endpoint: https://mysearchservice.search.windows.net
Index name: myproject-index
Force recreate: True

📦 Backing up current index: myproject-index
✅ Backup saved to: backups/myproject-index_backup_20260108_123456.json

⚠️  Index 'myproject-index' already exists.
    Deleting existing index...
[OK] Index deleted

🔧 Creating improved index configuration
   ✅ Integrated vectorizer configured: vectorizer-myproject-index
✅ Improved index configuration created
   BM25 similarity: k1=1.5, b=0.5 (tuned for technical content)

🔄 Applying index improvements...

✅ Index updated successfully!
📊 Index: myproject-index
📝 Fields: 23
⭐ Scoring profiles: 2
🔍 Suggesters: 1

🔍 Validating deployment...
   ✓ BM25 similarity configured
   ✓ Semantic title field correctly set to 'title'
   ✓ Title field uses standard.lucene analyzer
   ✓ Embeddings field is retrievable
   ✓ Vector compression configured
   ✓ Vector search algorithms configured (1)
   ✓ Product boosting profile found
   ✓ Content RAG profile found
   ✓ 2 scoring profiles configured
   ✓ 2 content fields in semantic config
   ✓ 5 keyword fields in semantic config
   ✓ Suggester configured for autocomplete
   ✅ All critical validations passed

✅ Deployment completed successfully!
📦 Backup saved: backups/myproject-index_backup_20260108_123456.json

✅ Index deployment completed successfully

======================================================================
STEP 2: Document Ingestion Pipeline
======================================================================
Loading configuration from environment variables...
Configuration loaded:
  Document action: add
  Input mode: InputMode.LOCAL
  Input source: documents/**/*.pdf
  ...

Processing document: manual.pdf
Checking for existing chunks of manual.pdf
No existing chunks found for manual.pdf
Extracting document with Azure Document Intelligence...
Extracted 50 pages from manual.pdf
Chunking manual.pdf
Generated 245 chunks
Generating embeddings client-side...
Generated 245 embeddings
Uploading 245 documents to index 'myproject-index'
Successfully uploaded all 245 documents

======================================================================
✅ Pipeline completed successfully
======================================================================
```

