# Features Documentation

Comprehensive guide to all features in ingestor.

---

## 1. Document Extraction

### Azure Document Intelligence Integration

Uses the `prebuilt-layout` model with:
- **OCR High Resolution** for better text extraction
- **Markdown output** for structured content
- **Figure extraction** for images and diagrams
- **Table extraction** with cell-level data

### Multi-Format Support

| Format | Method |
|--------|--------|
| PDF | Azure Document Intelligence |
| TXT, MD | Direct UTF-8 extraction |
| HTML | Tag stripping + text extraction |
| JSON | Pretty-print formatting |
| CSV | Markdown table conversion |

### Hyperlink Extraction

**For PDFs (✅ Supported):**
- Uses **PyMuPDF** to extract hyperlinks from PDF link annotations
- Converts hyperlinks to markdown format: `[text](url)`
- Preserves both external URLs and internal page references
- Extracts URLs from PageFooter comments

**Features:**
- Automatic hyperlink detection in PDFs
- Multi-line link support with intelligent merging
- Quote-aware text matching
- Preserves link context in searchable text

**Limitations:**
- Azure Document Intelligence API does not provide hyperlink extraction
- Office documents (DOCX/PPTX) do not have hyperlink extraction implemented
- See [Known Limitations](23_KNOWN_LIMITATIONS.md) for details

**Example:**
```markdown
# Before extraction:
His speech can be found here.

# After extraction:
His speech can be found [here.](https://example.com/speech)
```

---

## 2. Chunking

### Layout-Aware Chunking

- Respects document structure (tables, figures)
- Sentence-aware splitting
- Configurable chunk size (default: 2000 chars, 500 tokens)
- Overlap between chunks (default: 10%)

### Page Header Extraction

Automatically extracts `<!-- PageHeader="..." -->` markers:
- Cleans page number prefixes (e.g., "2-2 ")
- Deduplicates repeated phrases
- Stores as `title` field for keyword search

---

## 3. Embeddings

### Proper Batching

Implements token-aware batching matching prepdocslib:
- **Token limit:** 8100 tokens per batch
- **Max batch size:** 16 items per batch
- Automatic splitting respecting both limits

### Custom Dimensions

For `text-embedding-3-*` models:

```bash
MINI_AOAI_EMB_DIMENSIONS=1536
```

| Model | Dimensions |
|-------|-----------|
| text-embedding-ada-002 | 1536 (fixed) |
| text-embedding-3-small | 512-1536 |
| text-embedding-3-large | 256-3072 |

### Embedding Modes

| Mode | Setting | Description |
|------|---------|-------------|
| Client-Side | `MINI_USE_INTEGRATED_VECTORIZATION=false` | Generate embeddings locally |
| Integrated | `MINI_USE_INTEGRATED_VECTORIZATION=true` | Azure Search generates embeddings |

---

## 4. Table Processing

### Rendering Modes

| Mode | Output |
|------|--------|
| `plain` | Structured text with row/column headers |
| `markdown` | Markdown table format |

### Table Summaries

Optional GPT-4o summarization:

```bash
MINI_TABLE_SUMMARIES=true
```

---

## 5. Figure Processing

### Extraction

- Crops figures from PDF using PyMuPDF
- Stores as PNG images
- Associates with pages and chunks

### Description

Uses GPT-4o vision for automatic captioning:

```bash
MINI_MEDIA_DESCRIBER=gpt4o
```

---

## 6. Citation System

### Per-Page PDF Splitting

Split documents into individual page PDFs for direct citation links:

```bash
MINI_GENERATE_PAGE_PDFS=true
```

### Citation URLs

| Field | Description |
|-------|-------------|
| `storageUrl` | Page-specific PDF URL (for direct page access) |
| `url` | Full document URL |
| `sourcepage` | Path with page anchor (e.g., `doc/pages/page-0001.pdf#page=1`) |

---

## 7. Document Actions

### Add (Default)

Process and index documents:

```bash
python -m ingestor.cli --glob "*.pdf"
```

### Remove

Remove specific documents by filename:

```bash
python -m ingestor.cli --action remove --glob "old_doc.pdf"
```

### Remove All

⚠️ Remove ALL documents from index:

```bash
python -m ingestor.cli --action removeall
```

---

## 8. Retry Configuration

All API calls use configurable retry logic:

| Service | Default Retries | Wait Strategy |
|---------|----------------|---------------|
| Azure OpenAI | 3 | Exponential (15-60s) |
| Document Intelligence | 3 | Exponential (5-30s) |
| GPT-4o | 3 | Exponential (1-20s) |

Configure via:

```bash
MINI_AOAI_MAX_RETRIES=3
```

---

## 9. Batch Upload

Azure AI Search upload features:
- **Batch size:** 1000 documents per batch
- **merge_or_upload:** Idempotent operations (update if exists)
- **Error handling:** Logs failed documents

---

## 10. Artifact Storage

### Local Storage

```
artifacts/
└── MyDoc.pdf/
    ├── pages/page-0001.json
    ├── chunks/page-0001/chunk-000001.json
    ├── images/page-0001/figure_abc.png
    └── manifest.json
```

### Blob Storage

```bash
MINI_ARTIFACTS_MODE=blob
MINI_BLOB_CONTAINER_OUT_PAGES=pages
MINI_BLOB_CONTAINER_OUT_CHUNKS=chunks
MINI_BLOB_CONTAINER_OUT_IMAGES=images
```

Containers are auto-created if they don't exist.

