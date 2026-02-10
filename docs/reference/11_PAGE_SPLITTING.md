# Per-Page PDF Splitting and Citation Storage

## What This Feature Does

Your pipeline now:

1. ✅ **Splits PDF page-by-page** using pypdf
2. ✅ **Stores each page PDF separately** for citations
3. ✅ **Creates blob container** with "-experiment" suffix: `{container}-experiment-citations`
4. ✅ **Chunks reference page PDFs** with URLs in metadata
5. ✅ **Page-wise organization** throughout

---

## Architecture

```
Original PDF (MyDoc.pdf)
    ↓
Split into page PDFs
    ↓
├─ page-0001.pdf → Blob: {container}-experiment-citations/MyDoc/page-0001.pdf
├─ page-0002.pdf → Blob: {container}-experiment-citations/MyDoc/page-0002.pdf
└─ page-0003.pdf → Blob: {container}-experiment-citations/MyDoc/page-0003.pdf
    ↓
Document Intelligence extracts each page
    ↓
Chunks created with metadata:
    - sourcepage: "MyDoc.pdf#page=2"
    - citationUrl: "https://storage.../MyDoc/page-0002.pdf"
    - pageNumber: 2
    - storageUrl: URL to chunk JSON
```

---

## Flow

### 1. PDF Splitting
```
Input: MyDoc.pdf (multi-page)
Output: 
  - page-0001.pdf
  - page-0002.pdf
  - page-0003.pdf
```

### 2. Page PDF Storage
**Local Mode:**
```
artifacts/
└── MyDoc.pdf/
    └── pages/
        ├── page-0001.pdf  ← Citation source
        ├── page-0002.pdf
        └── page-0003.pdf
```

**Blob Mode:**
```
Container: {base-container}-experiment-citations
Blobs:
  - MyDoc/page-0001.pdf
  - MyDoc/page-0002.pdf
  - MyDoc/page-0003.pdf
```

### 3. Document Intelligence
Each page PDF is sent to DI:
- Tables extracted
- Figures extracted
- Text extracted
- Bounding boxes captured

### 4. Chunking with Page Metadata
Each chunk gets:
```json
{
  "id": "MyDoc_page2_chunk1",
  "content": "...",
  "page_num": 1,  // 0-indexed
  "sourcepage": "MyDoc.pdf#page=2",
  "citationUrl": "https://storage.../MyDoc/page-0002.pdf",
  "pageNumber": 2,  // 1-indexed for display
  "storageUrl": "https://storage.../chunks/page-0001/chunk-0001.json"
}
```

---

## Configuration

### Environment Variables

**Enable Page Splitting:**
```bash
MINI_GENERATE_PAGE_PDFS=true
```

**Citations Container (auto-generated if not specified):**
```bash
MINI_BLOB_CONTAINER_CITATIONS={base}-experiment-citations
```

Example with your config:
```bash
# Base container
AZURE_STORAGE_CONTAINER=my-improvement-index

# Auto-generated citations container
# → myproject-citations
```

---

## Benefits

### 1. **Direct Page Access**
- Users can click directly to specific page PDFs
- No need to open full PDF and navigate

### 2. **Better Citations**
- Each chunk points to exact page PDF
- Citation URL is a direct download link
- Original page formatting preserved

### 3. **Page-wise Processing**
- Each page processed independently
- Better concurrency control
- Easier error recovery

### 4. **Flexible Storage**
- Local for testing
- Blob for production
- Separate citations container keeps organization clean

---

## Search Index Fields

Your chunks will populate these fields in `myproject-index`:

| Field | Value | Example |
|-------|-------|---------|
| `filename` | Source PDF name | `"MyDoc.pdf"` |
| `sourcepage` | Page reference | `"MyDoc.pdf#page=2"` |
| `pageNumber` | Page number (1-indexed) | `2` |
| `url` | **Page PDF URL** | `"https://.../MyDoc/page-0002.pdf"` |
| `storageUrl` | Chunk JSON URL | `"https://.../chunks/page-0001/chunk-0001.json"` |

---

## Testing

The test will show:

1. **PDF Splitting Log**
   ```
   Splitting MyDoc.pdf into 5 page PDFs
   Split page 1/5: 12,345 bytes
   Split page 2/5: 13,456 bytes
   ...
   ```

2. **Page PDFs Stored**
   ```
   test_artifacts/sample_pages_test.pdf/pages/
   ├── page-0001.pdf
   ├── page-0002.pdf
   └── ...
   ```

3. **Chunk Metadata**
   ```
   test_artifacts/sample_pages_test.pdf/chunks/page-0001/chunk-0001.json
   {
     "citationUrl": "file:///.../ page-0001.pdf",
     "sourcepage": "sample_pages_test.pdf#page=1",
     "pageNumber": 1
   }
   ```

---

## Implementation Details

### 1. **PagePdfSplitter** (`page_splitter.py`)
```python
from page_splitter import PagePdfSplitter

splitter = PagePdfSplitter()
page_pdfs = splitter.split_pdf(pdf_bytes, filename)
# Returns: [(page_num, pdf_bytes, page_filename), ...]
```

### 2. **Storage** (`artifact_storage.py`)
```python
# Store page PDF
page_pdf_url = await storage.write_page_pdf(
    doc_name="MyDoc.pdf",
    page_num=0,
    pdf_bytes=page_pdf_bytes
)
```

### 3. **Metadata** (`pipeline.py`)
```python
chunk_metadata = {
    "sourcepage": f"{filename}#page={page_num + 1}",
    "citationUrl": page_pdf_url,
    "pageNumber": page_num + 1,
    "storageUrl": source_url
}
```

---

## What You'll See in Logs

```
[INFO] Splitting sample_pages_test.pdf into 3 page PDFs
[INFO] Split page 1/3: 45,123 bytes
[INFO] Split page 2/3: 46,234 bytes
[INFO] Split page 3/3: 44,567 bytes
[INFO] Successfully split sample_pages_test.pdf into 3 page PDFs
[INFO] Stored page PDF 1: file:///.../page-0001.pdf
[INFO] Stored page PDF 2: file:///.../page-0002.pdf
[INFO] Stored page PDF 3: file:///.../page-0003.pdf
[INFO] Extracting content from page 1
[INFO] Extracting content from page 2
[INFO] Extracting content from page 3
[INFO] Chunking document: sample_pages_test.pdf
[INFO] Created 15 chunks with page citations
```

---

## Ready to Test!

The page splitting feature is now integrated. When you run:
```cmd
run_test.bat
```

You'll see:
1. PDF split into individual page PDFs
2. Each page PDF stored (locally or in blob)
3. Chunks referencing specific page PDFs
4. Citation URLs in metadata

Check the logs to see it all in action! 🎉

