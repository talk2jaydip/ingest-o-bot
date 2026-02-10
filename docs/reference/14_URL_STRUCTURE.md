# Complete URL Structure for Citations and Images

## Summary of Changes

This document provides a complete overview of how URLs are structured and stored for proper citation and image display.

## Storage Containers

With prefix `myproject`:

### 1. Citations Container (`myproject-citations`)
```
sample_document.pdf                          ← Full original PDF
```

### 2. Pages Container (`myproject-pages`)
```
sample_document_page_0001.pdf               ← Per-page PDF (page 1)
sample_document_page_0002.pdf               ← Per-page PDF (page 2)
sample_document/page-0001.json              ← Page 1 metadata
sample_document/page-0002.json              ← Page 2 metadata
```

### 3. Chunks Container (`myproject-chunks`)
```
sample_document/page-0001/chunk-000001.json ← Page 1, Chunk 1
sample_document/page-0001/chunk-000002.json ← Page 1, Chunk 2
sample_document/page-0002/chunk-000001.json ← Page 2, Chunk 1
```

### 4. Images Container (`myproject-images`)
```
sample_document/page_01_fig_01.png          ← Page 1, Figure 1
sample_document/page_01_fig_02.png          ← Page 1, Figure 2
sample_document/page_02_fig_01.png          ← Page 2, Figure 1
```

## URLs in Search Index

Each indexed chunk document contains:

```json
{
  "id": "sample_document_page1_chunk1",
  "content": "Text content of the chunk...",
  "sourcefile": "sample_document",
  "sourcepage": "sample_document/page-0001.pdf#page=1",
  "pageNumber": 1,

  // FULL ORIGINAL PDF (for complete document access)
  "url": "https://account.blob.core.windows.net/myproject-citations/sample_document.pdf",

  // PER-PAGE PDF (for direct page citation)
  "storageUrl": "https://account.blob.core.windows.net/myproject-pages/sample_document_page_0001.pdf",

  // IMAGES (for visual context) - NEW!
  "images": [
    {
      "url": "https://account.blob.core.windows.net/myproject-images/sample_document/page_01_fig_01.png",
      "description": "LLM-generated description of the image",
      "page_num": 1,
      "figure_id": "fig_abc123"
    }
  ],

  "title": "Section Title",
  "embeddings": [...]
}
```

## Use Cases and Which URL to Use

### 1. **User wants to read full document**
Use: `url` field
```
https://.../citations/sample_document.pdf
```
Opens: Complete original PDF

### 2. **User wants to see cited page**
Use: `storageUrl` field
```
https://.../pages/sample_document_page_0001.pdf
```
Opens: Single-page PDF for specific page

### 3. **User wants to view images/figures**
Use: `images[].url` field
```
https://.../images/sample_document/page_01_fig_01.png
```
Displays: Image with citation burned in

### 4. **User wants page reference**
Use: `sourcepage` field
```
sample_document/page-0001.pdf#page=1
```
Shows: Human-readable page reference

## Key Features

### ✅ Flat Structure (No Excessive Nesting)
- **Page PDFs**: `{base_filename}_page_0001.pdf` (flat, underscore separator)
- **Page JSON**: `{base_filename}/page-0001.json` (single folder level)
- **Chunks**: `{base_filename}/page-0001/chunk-000001.json` (two folder levels)
- **Images**: `{base_filename}/page_01_fig_01.png` (single folder level)

### ✅ Base Filename (No Extension in Folder Names)
- `sample_document/` (not `sample_document.pdf/`)
- Extracted using `Path(filename).stem`

### ✅ 1-Based Numbering for Display
- `page-0001.pdf` for page 1 (not `page-0000.pdf`)
- `page_01_fig_01.png` for first figure on page 1

### ✅ Unique Image Names (No Collisions)
- Format: `page_{page_num:02d}_fig_{fig_num:02d}.{ext}`
- Uses `figure_idx` parameter to prevent naming conflicts
- Multiple figures per page handled correctly

### ✅ Full PDF Upload
- Original PDF uploaded when input is local and artifacts are blob
- Ensures `url` field always points to valid blob location

### ✅ Image URLs in Index
- Images immediately available with search results
- No additional API calls needed to display images
- Includes LLM-generated descriptions for context

## Integration with Frontend

### When displaying search results:

```javascript
const result = searchResult.document;

// Show chunk content
displayContent(result.content);

// Show images if available
if (result.images && result.images.length > 0) {
  for (const image of result.images) {
    displayImage({
      src: image.url,
      alt: image.description,
      caption: `Figure from page ${image.page_num}: ${image.description}`
    });
  }
}

// Provide citation links
displayCitations({
  pageLink: result.storageUrl,      // Direct to specific page
  documentLink: result.url,          // Full document
  pageReference: result.sourcepage   // Human-readable reference
});
```

## Migration from Previous Structure

### Old Structure (Before Changes)
```
sample_document.pdf/pages/page-0001.pdf
sample_document.pdf/chunks/page-0001/chunk-000001.json
sample_document.pdf/images/page-0001/figure-1.png
```

### New Structure (After Changes)
```
Citations container:
  sample_document.pdf                     ← Full PDF at root

Pages container:
  sample_document_page_0001.pdf           ← Flat, underscore separator
  sample_document/page-0001.json          ← Page metadata

Chunks container:
  sample_document/page-0001/chunk-000001.json ← Flattened

Images container:
  sample_document/page_01_fig_01.png     ← Renamed & flattened
```

### Benefits of New Structure
1. ✅ **Shorter paths**: Less nesting = shorter URLs
2. ✅ **Cleaner URLs**: More readable and predictable
3. ✅ **Better organization**: Folder = document, files = pages/images
4. ✅ **No extension in folder names**: Cleaner hierarchy
5. ✅ **Full PDF available**: Proper document URL for citations

## Index Schema Requirements

To support image URLs, ensure your index schema includes:

```json
{
  "name": "images",
  "type": "Collection(Edm.ComplexType)",
  "fields": [
    {"name": "url", "type": "Edm.String", "retrievable": true},
    {"name": "description", "type": "Edm.String", "searchable": true},
    {"name": "page_num", "type": "Edm.Int32", "filterable": true},
    {"name": "figure_id", "type": "Edm.String", "filterable": true}
  ]
}
```

## Verification Checklist

After running the pipeline, verify:

### ✅ Citations Container
- [ ] Full PDF at root: `sample_document.pdf`

### ✅ Pages Container
- [ ] Per-page PDFs: `sample_document_page_0001.pdf`, etc. (flat, underscore separator)
- [ ] Page metadata JSON: `sample_document/page-0001.json`, etc.

### ✅ Chunks Container
- [ ] Chunks: `sample_document/page-0001/chunk-000001.json`, etc.

### ✅ Images Container
- [ ] Images: `sample_document/page_01_fig_01.png`, etc.
- [ ] No nested subdirectories under document folder
- [ ] Images have citation burned in

### ✅ Search Index
- [ ] `url` field points to full PDF
- [ ] `storageUrl` field points to per-page PDF
- [ ] `images` field contains image URLs and descriptions
- [ ] All URLs are valid and accessible

## Next Steps

1. **Update index schema** to include `images` field (optional but recommended)
2. **Re-run pipeline** to populate new structure
3. **Update frontend** to display images from search results
4. **Test all URL types** (full PDF, per-page PDF, images)
5. **Verify blob permissions** for public read access

## Files Changed

- [artifact_storage.py](artifact_storage.py) - Storage structure and full PDF upload
- [pipeline.py](pipeline.py) - Full PDF upload logic and URL handling
- [models.py](models.py) - Added images field to search index
- [STORAGE_URL_FLOW.md](STORAGE_URL_FLOW.md) - Documented URL flow
- [IMAGE_CITATION_GUIDE.md](IMAGE_CITATION_GUIDE.md) - Image handling guide
- [COMPLETE_URL_STRUCTURE.md](COMPLETE_URL_STRUCTURE.md) - This document
