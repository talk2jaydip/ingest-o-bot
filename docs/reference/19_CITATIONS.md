# Image Citation and Display Guide

## Overview
This guide explains how image URLs are stored, indexed, and should be displayed in search results.

## Image Processing Flow

### 1. **Image Extraction and Upload**
When a PDF is processed:

```python
# In pipeline.py (line ~610)
for idx, image in enumerate(page.images):
    # Generate description if media describer is enabled
    if self.media_describer:
        image.description = await self.media_describer.describe_image(image.image_bytes)

    # Upload image with citation burned in
    image.url = await self.artifact_storage.write_image(
        filename,
        image.page_num,
        image.filename,
        image.image_bytes,
        figure_idx=idx  # Prevents naming collisions
    )
```

**Result**: Image stored at `{images_container}/{base_filename}/page_01_fig_01.png`

### 2. **Image URL in Chunk Document**
Each chunk that references an image includes:

```python
# FigureReference object
{
    "figure_id": "fig_abc123",
    "page_num": 0,  # 0-indexed
    "bbox": [100, 200, 300, 400],
    "url": "https://account.blob.core.windows.net/myproject-images/sample_document/page_01_fig_01.png",
    "description": "A bar chart showing quarterly sales trends with three product categories",
    "filename": "figure-1.png",
    "title": "Figure 1: Sales Trends Q1-Q4"
}
```

### 3. **Image URLs in Search Index**
Images are now included in the search index document:

```json
{
  "id": "sample_document_page1_chunk1",
  "content": "This section discusses sales trends. See Figure 1 for details.",
  "images": [
    {
      "url": "https://.../images/sample_document/page_01_fig_01.png",
      "description": "A bar chart showing quarterly sales trends...",
      "page_num": 1,
      "figure_id": "fig_abc123"
    }
  ],
  "storageUrl": "https://.../citations/sample_document/page-0001.pdf",
  "url": "https://.../citations/sample_document.pdf"
}
```

## Image Storage Structure

### Blob Storage (with prefix `myproject`)

**Images Container**: `myproject-images`
```
sample_document/
  page_01_fig_01.png    ← First figure on page 1
  page_01_fig_02.png    ← Second figure on page 1
  page_02_fig_01.png    ← First figure on page 2
  page_03_fig_01.png    ← First figure on page 3
```

**Key Features**:
- **No nested subdirectories**: Flat structure under document folder
- **Naming pattern**: `page_{page_num:02d}_fig_{fig_num:02d}.{ext}`
- **1-based numbering**: page_01 (not page_00) for page 1
- **Citation burned in**: Image includes source document and page info

## Frontend Integration

### Displaying Images in Search Results

When you receive search results from Azure AI Search:

```javascript
const searchResults = await searchClient.search(query);

for (const result of searchResults.results) {
  const chunk = result.document;

  // Display chunk text
  console.log("Content:", chunk.content);

  // Display associated images (if any)
  if (chunk.images && chunk.images.length > 0) {
    for (const image of chunk.images) {
      console.log("Image URL:", image.url);
      console.log("Description:", image.description);
      console.log("Page:", image.page_num);

      // Display in UI
      displayImage({
        src: image.url,
        alt: image.description,
        caption: `Figure from page ${image.page_num}: ${image.description}`,
        citation: chunk.sourcepage
      });
    }
  }

  // Citation link
  console.log("Page Citation:", chunk.storageUrl);  // Per-page PDF
  console.log("Full Document:", chunk.url);          // Complete PDF
}
```

### Example UI Display

```html
<div class="search-result">
  <div class="chunk-content">
    <p>This section discusses sales trends. See Figure 1 for details.</p>
  </div>

  <!-- Images referenced in this chunk -->
  <div class="chunk-images">
    <figure>
      <img
        src="https://.../images/sample_document/page_01_fig_01.png"
        alt="A bar chart showing quarterly sales trends..."
      />
      <figcaption>
        Figure from page 1: A bar chart showing quarterly sales trends...
        <a href="https://.../citations/sample_document/page-0001.pdf">
          View in context
        </a>
      </figcaption>
    </figure>
  </div>

  <!-- Citation links -->
  <div class="citations">
    <a href="https://.../citations/sample_document/page-0001.pdf">
      Page 1 (PDF)
    </a>
    <a href="https://.../citations/sample_document.pdf">
      Full Document (PDF)
    </a>
  </div>
</div>
```

## Index Schema Requirements

To use image URLs in your index, add the `images` field to your Azure AI Search index schema:

```json
{
  "name": "images",
  "type": "Collection(Edm.ComplexType)",
  "fields": [
    {
      "name": "url",
      "type": "Edm.String",
      "searchable": false,
      "filterable": false,
      "retrievable": true
    },
    {
      "name": "description",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true
    },
    {
      "name": "page_num",
      "type": "Edm.Int32",
      "searchable": false,
      "filterable": true,
      "retrievable": true
    },
    {
      "name": "figure_id",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "retrievable": true
    }
  ]
}
```

## Alternative: Retrieve from Chunk Artifacts

If you don't want to update the index schema, you can retrieve image URLs from chunk artifacts:

```javascript
// Option 1: Images in index (RECOMMENDED)
const images = result.document.images;  // Already available ✅

// Option 2: Fetch from chunk artifact (SLOWER)
const chunkArtifactUrl = `https://.../chunks/${docName}/page-${pageNum:04d}/chunk-${chunkIdx:06d}.json`;
const chunkData = await fetch(chunkArtifactUrl).then(r => r.json());
const images = chunkData.figures;  // Need additional HTTP call ❌
```

## Best Practices

### 1. **Image URLs in Index** ⭐
- **DO**: Include image URLs in search index for fast retrieval
- **WHY**: Users expect images to load immediately with search results

### 2. **Image Descriptions**
- **DO**: Use LLM-generated descriptions for accessibility and searchability
- **WHY**: Helps users understand image content without loading the image

### 3. **Citation Links**
- **DO**: Provide both page-specific and full document links
- **WHY**: Users may want specific page or full context

### 4. **Image Caching**
- **DO**: Use CDN or browser caching for image URLs
- **WHY**: Images with citations can be large (burned-in text)

### 5. **Fallback Handling**
- **DO**: Handle missing images gracefully (broken links, 404s)
- **WHY**: Image processing may fail for some figures

## Image Naming Convention

```
{base_filename}/page_{page_num:02d}_fig_{fig_num:02d}.{ext}
```

**Examples**:
- `user_manual/page_01_fig_01.png` - First figure on page 1
- `user_manual/page_01_fig_02.png` - Second figure on page 1
- `user_manual/page_10_fig_03.png` - Third figure on page 10

**Benefits**:
- ✅ Unique names (no collisions)
- ✅ Sortable alphabetically
- ✅ Human-readable
- ✅ Predictable pattern

## Complete Example

### Search Query with Images
```javascript
const response = await searchClient.search("sales trends", {
  select: ["id", "content", "images", "storageUrl", "url", "sourcepage"],
  top: 10
});

for (const result of response.results) {
  const doc = result.document;

  console.log(`Chunk: ${doc.id}`);
  console.log(`Content: ${doc.content}`);
  console.log(`Page Citation: ${doc.storageUrl}`);
  console.log(`Full Document: ${doc.url}`);

  if (doc.images && doc.images.length > 0) {
    console.log(`Contains ${doc.images.length} image(s):`);

    for (const img of doc.images) {
      console.log(`  - ${img.url}`);
      console.log(`    Description: ${img.description}`);
      console.log(`    Page: ${img.page_num}`);
    }
  }
}
```

### Output
```
Chunk: user_manual_page5_chunk2
Content: The quarterly sales analysis shows significant growth in Q3...
Page Citation: https://.../citations/user_manual/page-0005.pdf
Full Document: https://.../citations/user_manual.pdf
Contains 1 image(s):
  - https://.../images/user_manual/page_05_fig_01.png
    Description: A bar chart showing quarterly sales trends with three product categories
    Page: 5
```

## Migration Notes

If you're updating an existing index:

1. **Add `images` field** to index schema (optional, but recommended)
2. **Re-index documents** to populate image URLs
3. **Update frontend** to display images from search results
4. **No breaking changes** - existing fields remain unchanged

## Troubleshooting

### Images not showing in results
- ✅ Check if `images` field is in index schema
- ✅ Verify images were uploaded during ingestion
- ✅ Check blob storage permissions (public read access)

### Broken image links
- ✅ Verify blob container name in URLs
- ✅ Check if blob storage account is accessible
- ✅ Ensure proper CORS settings for browser access

### Missing descriptions
- ✅ Enable media describer in pipeline config
- ✅ Check OpenAI/GPT-4o configuration
- ✅ Verify image bytes are valid
