# Document Handling & Identification

Guide to how `ingestor` handles document identification, deletion, and updates.

---

## 📋 **Document Action Modes**

The pipeline supports three document action modes via `AZURE_DOCUMENT_ACTION`:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `add` (default) | **Delete existing → Add new** (full replace) | Normal ingestion & re-indexing |
| `remove` | Remove specific documents by filename | Delete specific docs |
| `removeall` | Remove ALL documents from index | ⚠️ Clear entire index |

---

## 🔑 **Document Identification**

### How Documents Are Identified

Documents are identified in the search index by the **`sourcefile`** field, which contains:

**Base filename without extension**

```python
# Example transformations:
"sample_pages_test.pdf" → "sample_pages_test"
"path/to/document.pdf" → "document"
"MyManual.pdf" → "MyManual"
```

### Why Base Filename?

1. ✅ **Consistent**: Same identifier regardless of path
2. ✅ **Simple**: Easy to match and filter
3. ✅ **Readable**: Human-friendly in search results
4. ✅ **Matches prepdocs**: Compatible with original implementation

---

## 🔄 **Default "add" Mode: Full Replace**

### Behavior

When you run the pipeline with `AZURE_DOCUMENT_ACTION=add` (default):

1. **Check for existing chunks**: Search index for documents with matching `sourcefile`
2. **Delete existing chunks**: Remove all chunks from the previous version
3. **Process new document**: Extract, chunk, embed
4. **Index new chunks**: Upload fresh chunks to search index

### Why Full Replace?

**Problem with Merge:**
- Old chunks remain if document shrinks
- Stale data from previous versions
- Inconsistent chunk numbering

**Solution with Replace:**
- ✅ Clean slate for each document
- ✅ No stale chunks
- ✅ Consistent state
- ✅ Idempotent re-indexing

### Example Flow

```
Document: "manual.pdf" (10 pages)
First run:
  → No existing chunks found
  → Process document
  → Index 50 chunks

Document updated: "manual.pdf" (8 pages, content changed)
Second run:
  → Found 50 existing chunks
  → Delete 50 old chunks
  → Process new document
  → Index 40 new chunks
  
Result: Clean 40 chunks, no stale data
```

---

## 🔍 **How Existing Documents Are Found**

### Search Filter

The code uses Azure AI Search OData filter:

```python
filter = f"sourcefile eq '{base_filename}'"
```

### Example Queries

```python
# For "document.pdf"
filter = "sourcefile eq 'document'"

# For "My Manual.pdf"
filter = "sourcefile eq 'My Manual'"

# For filenames with apostrophes (escaped)
# "O'Reilly's Guide.pdf"
filter = "sourcefile eq 'O''Reilly''s Guide'"
```

### Batch Deletion

If a document has > 1000 chunks:

1. Search for up to 1000 chunks
2. Delete batch
3. Wait 2 seconds (for index to update)
4. Repeat until no more chunks found

This matches the original `prepdocs` behavior.

---

## 📊 **Implementation Details**

### In `search_uploader.py`

```python
async def delete_documents_by_filename(self, filename: str) -> int:
    """Delete all documents with a specific sourcefile.
    
    Args:
        filename: Full filename (e.g., "document.pdf")
                 Will use basename without extension for matching.
    
    Returns number of documents deleted.
    """
    # Get base filename without extension
    base_filename = os.path.splitext(os.path.basename(filename))[0]
    
    # Escape single quotes for OData filter
    escaped_filename = base_filename.replace("'", "''")
    
    # Loop until no more documents found
    while True:
        search_result = await self.client.search(
            search_text="",
            filter=f"sourcefile eq '{escaped_filename}'",
            select=["id"],
            top=1000
        )
        
        # Collect document IDs
        doc_ids = [{"id": result["id"]} async for result in search_result]
        
        if not doc_ids:
            break
        
        # Delete batch
        await self.client.delete_documents(documents=doc_ids)
        
        # Wait for index to update
        await asyncio.sleep(2)
```

### In `pipeline.py`

```python
async def _run_add_pipeline(self):
    """Run the ADD pipeline: delete existing → extract → chunk → embed → index."""
    
    async for filename, file_bytes, source_url in self.input_source.list_files():
        # Step 0: Delete existing document chunks first
        deleted_count = await self.search_uploader.delete_documents_by_filename(filename)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} existing chunks for {filename}")
        
        # Step 1-4: Process new document
        pages = await self.extract_document(filename, file_bytes, source_url)
        chunks = await self.chunk_document(filename, pages, source_url)
        await self.embed_chunks(chunks)
        await self.index_chunks(chunks)
```

---

## 🎯 **Use Cases**

### 1. **Initial Ingestion**

```bash
# First time indexing documents
AZURE_DOCUMENT_ACTION=add
python -m cli --glob "data/*.pdf"
```

**Result:**
- No existing chunks found
- All documents processed and indexed

### 2. **Re-indexing (Update Documents)**

```bash
# Documents have been updated, re-index them
AZURE_DOCUMENT_ACTION=add
python -m cli --glob "data/*.pdf"
```

**Result:**
- Existing chunks deleted
- New versions processed and indexed
- Clean, consistent state

### 3. **Remove Specific Documents**

```bash
# Remove specific documents
AZURE_DOCUMENT_ACTION=remove
python -m cli --file "old_manual.pdf"
```

**Result:**
- All chunks for "old_manual" deleted
- Other documents untouched

### 4. **Clear Entire Index**

```bash
# Remove ALL documents (use with caution!)
AZURE_DOCUMENT_ACTION=removeall
python -m cli
```

**Result:**
- ⚠️ ALL documents deleted from index
- Index is empty

---

## 🔧 **Configuration**

### Environment Variable

```bash
# Default: Full replace on add
AZURE_DOCUMENT_ACTION=add

# Remove specific documents
AZURE_DOCUMENT_ACTION=remove

# Clear entire index
AZURE_DOCUMENT_ACTION=removeall
```

### CLI Override

```bash
# Override via CLI
python -m cli --action remove --file old_doc.pdf
python -m cli --action removeall
```

---

## ⚠️ **Important Notes**

### 1. **Document Identity**

The `sourcefile` field is the **key identifier**. If you rename a file:

```bash
# Original
"manual_v1.pdf" → sourcefile: "manual_v1"

# Renamed
"manual_v2.pdf" → sourcefile: "manual_v2"
```

These are treated as **different documents**. The old chunks remain unless explicitly removed.

### 2. **Chunk IDs**

Chunk IDs are generated as:

```python
chunk_id = f"{filename_stem}_page{page_num}_chunk{chunk_num}"
```

Example: `manual_page1_chunk1`, `manual_page1_chunk2`

### 3. **Escaping Special Characters**

Filenames with single quotes are properly escaped:

```python
"O'Reilly's Guide.pdf" → filter: "sourcefile eq 'O''Reilly''s Guide'"
```

### 4. **Index Update Delay**

After deleting chunks, the code waits 2 seconds for the search index to update. This matches `prepdocs` behavior and prevents race conditions.

---

## 🆚 **Comparison with prepdocs**

| Feature | ingestor | ingestor |
|---------|-------------------|----------|
| Document identification | `sourcefile` (base filename) | `sourcefile` (base filename) |
| Default add behavior | Delete → Add (full replace) | Merge (update existing) |
| Batch deletion | Yes (1000 per batch) | Yes (1000 per batch) |
| Index update delay | 2 seconds | 2 seconds |
| OData filter escaping | Yes | Yes |

**Key Difference:** `ingestor` defaults to **full replace** for cleaner updates, while `prepdocs` uses **merge** by default.

---

## 📚 **Related Documentation**

- [Configuration Guide](../guides/CONFIGURATION.md)
- [Environment Variables Guide](12_ENVIRONMENT_VARIABLES.md)
- [Architecture Guide](04_ARCHITECTURE.md)

