# Figure/Image Processing Flow - Complete Guide

## Overview

This document explains **exactly** how figures/images are extracted, processed, described, and chunked in both the original `prepdocslib` and `ingestor`.

---

## 🔑 Key Answer to Your Question

**Q: Is OCR extracting text from figures?**

**A: NO.** Here's what actually happens:

1. ✅ **Document Intelligence extracts the IMAGE** (not OCR text from it)
2. ✅ **PyMuPDF crops the figure** from the PDF as a PNG image
3. ✅ **MediaDescriber generates a TEXT DESCRIPTION** of the image using AI
4. ✅ **The description (NOT OCR) is embedded in the chunk**
5. ✅ **The actual image is stored separately** in blob storage

**OCR is NOT used on figures.** Instead, a **vision model describes what's in the image**.

---

## 📊 Complete Processing Flow

### Step 1: Document Intelligence Extraction

**Location:** `di_extractor.py` (lines 133-256)

```python
# 1. Send PDF to Document Intelligence
poller = await di_client.begin_analyze_document(
    model_id="prebuilt-layout",           # Required for figures
    body=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
    output=["figures"],                   # ✅ MUST request figures explicitly
    features=["ocrHighResolution"],       # Better detection
    output_content_format="markdown"
)

result: AnalyzeResult = await poller.result()
```

**What DI Returns:**
```python
result.figures = [
    DocumentFigure(
        id="fig_3_1",
        caption={"content": "Figure 1: Sales Chart"},
        bounding_regions=[
            {
                "page_number": 3,
                "polygon": [x1, y1, x2, y2, x3, y3, x4, y4]  # 8 coordinates
            }
        ]
    )
]
```

**Important:**
- ✅ DI identifies WHERE the figure is (bounding box)
- ✅ DI may extract a caption if present
- ❌ DI does NOT extract or OCR the image content itself
- ❌ DI does NOT provide the actual image bytes

### Step 2: Extract Figure Image from PDF

**Location:** `di_extractor.py` (lines 294-342)

```python
async def _extract_figure(self, figure: DocumentFigure, figure_idx: int, doc: pymupdf.Document):
    """Extract and crop figure from PDF."""
    
    # Get bounding box from DI
    first_region = figure.bounding_regions[0]
    bbox_inches = (
        first_region.polygon[0],  # x1
        first_region.polygon[1],  # y1
        first_region.polygon[4],  # x2
        first_region.polygon[5],  # y2
    )
    page_number = first_region.page_number - 1
    
    # Crop image from PDF using PyMuPDF
    cropped_img, bbox_pixels = self._crop_image_from_pdf(
        doc, page_number, bbox_inches
    )
    
    return ExtractedImage(
        figure_id=figure.id,
        page_num=page_number,
        bbox=bbox_pixels,
        image_bytes=cropped_img,  # PNG bytes
        filename=f"figure{figure_id}.png",
        title=figure.caption.content if figure.caption else "",
        placeholder=f'<figure id="{figure_id}"></figure>'
    )
```

**What Happens:**
```python
# PyMuPDF crops the region
def _crop_image_from_pdf(doc, page_number, bbox_inches):
    page = doc[page_number]
    
    # Convert inches to pixels
    x1_pixels = bbox_inches[0] * 72  # 72 DPI
    y1_pixels = bbox_inches[1] * 72
    x2_pixels = bbox_inches[2] * 72
    y2_pixels = bbox_inches[3] * 72
    
    # Crop region from page
    rect = pymupdf.Rect(x1_pixels, y1_pixels, x2_pixels, y2_pixels)
    pix = page.get_pixmap(clip=rect, dpi=300)  # High resolution
    
    # Convert to PNG
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    
    return img_bytes.getvalue(), (x1_pixels, y1_pixels, x2_pixels, y2_pixels)
```

**Result:**
- ✅ We now have the actual figure as PNG bytes
- ✅ High resolution (300 DPI)
- ✅ Cropped to exact bounding box

### Step 3: Generate Description (MediaDescriber)

**Location:** `pipeline.py` (lines 628-638)

```python
for page in pages:
    for idx, image in enumerate(page.images):
        # Describe image using AI vision model
        if self.media_describer:
            logger.info(f"Generating description for figure {image.figure_id}")
            
            # ✅ This is where the DESCRIPTION is generated
            image.description = await self.media_describer.describe_image(
                image.image_bytes  # Send PNG bytes to vision model
            )
```

**MediaDescriber Implementation:**

**Option 1: GPT-4o Vision** (default)

**Location:** `media_describer.py` (lines 30-80)

```python
class GPT4oMediaDescriber(MediaDescriber):
    async def describe_image(self, image_bytes: bytes) -> str:
        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_datauri = f"data:image/png;base64,{image_base64}"
        
        # Send to GPT-4o with vision
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=500,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that describes images from organizational documents."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "text": "Describe image with no more than 5 sentences. Do not speculate about anything you don't know.",
                            "type": "text"
                        },
                        {
                            "image_url": {"url": image_datauri, "detail": "auto"},
                            "type": "image_url"
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content
```

**Example Description Generated:**
```
"The image shows a bar chart comparing quarterly sales across three product categories: 
Electronics, Furniture, and Accessories. Electronics shows the highest sales in Q4 at 
approximately $450K, while Furniture maintains steady growth throughout the year. The 
chart uses blue, green, and orange colors to distinguish the categories."
```

**Option 2: Content Understanding** (alternative)

**Location:** `media_describer.py` (lines 82-160)

```python
class ContentUnderstandingMediaDescriber(MediaDescriber):
    async def describe_image(self, image_bytes: bytes) -> str:
        # Send to Azure AI Content Understanding service
        result = await self.cu_client.analyze_document(
            body={"bytes": image_bytes},
            features=["caption", "dense_captions"]
        )
        
        return result["caption"]["content"]
```

**Key Points:**
- ❌ **NOT OCR** - This is AI-generated description, not text extraction
- ✅ Vision model "sees" the image and describes it in natural language
- ✅ More useful than OCR for charts, diagrams, photos
- ✅ Includes context like "bar chart", "showing trends", etc.

### Step 4: Upload Image to Blob Storage

**Location:** `pipeline.py` (lines 640-647)

```python
# Upload image
image.url = await self.artifact_storage.write_image(
    filename,
    image.page_num,
    image.filename,
    image.image_bytes,
    figure_idx=idx
)
```

**Result:**
```
URL: https://account.blob.core.windows.net/myproject-images/sample_document/page_03_fig_01.png
```

### Step 5: Insert Placeholder in Page Text

**Location:** `di_extractor.py` (lines 234-240)

```python
# During page text building
page_text = self._build_page_text(
    result,
    page,
    tables_on_page,
    figures_on_page  # ✅ Figures inserted as placeholders
)
```

**Method:** `_build_page_text()` (lines 384-410)

```python
def _build_page_text(self, result, page, tables, figures):
    page_text = result.content  # Base markdown text from DI
    
    # Replace figure placeholders
    for figure in figures:
        # DI puts a placeholder like "![Figure 1](figures/3)"
        # We replace with: <figure id="fig_3_1"></figure>
        placeholder = f'<figure id="{figure.figure_id}"></figure>'
        page_text = page_text.replace(
            f"![{figure.title}](figures/{figure_idx})",
            placeholder
        )
    
    return page_text
```

**Page Text Example:**
```markdown
This section discusses quarterly sales trends.

<figure id="fig_3_1"></figure>

As shown in the chart above, Electronics sales peaked in Q4.
```

### Step 6: Chunking with Figure Markup

**Location:** `chunker.py` (lines 207-219, 416-433)

```python
# Prepare page text
def _prepare_page_text(self, page: ExtractedPage) -> str:
    text = page.text
    
    # Replace figure placeholders with descriptions
    for image in page.images:
        if image.description:
            caption_parts = [image.figure_id]
            if image.title:
                caption_parts.append(image.title)
            caption = " ".join(caption_parts)
            
            # Build figure markup with description
            figure_markup = f"""

[FIGURE:{image.figure_id}:START]
Figure: {caption}
Description: {image.description}
[FIGURE:{image.figure_id}:END]

"""
            # Replace placeholder
            text = text.replace(image.placeholder, figure_markup)
    
    return text
```

**Result - Text Used for Chunking:**
```markdown
This section discusses quarterly sales trends.

[FIGURE:fig_3_1:START]
Figure: fig_3_1 Figure 1: Sales Chart
Description: The image shows a bar chart comparing quarterly sales across three product 
categories: Electronics, Furniture, and Accessories. Electronics shows the highest sales 
in Q4 at approximately $450K, while Furniture maintains steady growth throughout the year.
[FIGURE:fig_3_1:END]

As shown in the chart above, Electronics sales peaked in Q4.
```

**Chunking Behavior:**
- ✅ Figures treated as **atomic blocks** (never split)
- ✅ Figure description is **searchable text**
- ✅ If chunk has text before figure, figure appended even if exceeds token limit
- ✅ Figure markers used to associate image metadata with chunk

### Step 7: Store Chunk with Image References

**Location:** `pipeline.py` (lines 474-502)

```python
def chunk_document(self, pages, doc_meta):
    # Chunk pages
    text_chunks = self.chunker.chunk_pages(pages)
    
    for chunk in text_chunks:
        # Build chunk metadata
        chunk_meta = ChunkMetadata(
            chunk_id=f"{doc_meta.sourcefile}_page{chunk.page_num + 1}_chunk{chunk.chunk_index_on_page}",
            page=page_meta,
            chunk=chunk,
            document=doc_meta
        )
        
        # Convert to search document
        search_doc = chunk_meta.to_search_document()
        
        # search_doc now includes:
        # {
        #   "content": "...text with figure description...",
        #   "images": [
        #     {
        #       "figure_id": "fig_3_1",
        #       "page_num": 2,
        #       "url": "https://.../page_03_fig_01.png",
        #       "description": "The image shows a bar chart...",
        #       "title": "Figure 1: Sales Chart"
        #     }
        #   ]
        # }
```

---

## 🔄 Flow Diagram

```
PDF Document
    ↓
[Document Intelligence]
    ├─→ Extract text (markdown)
    ├─→ Identify table locations
    └─→ Identify figure locations (bounding boxes)
         ↓
[PyMuPDF]
    └─→ Crop figure regions from PDF → PNG bytes
         ↓
[MediaDescriber (GPT-4o Vision)]
    └─→ Generate description from PNG → Text description
         ↓
[Page Text Builder]
    ├─→ Insert <figure id="..."></figure> placeholders
    └─→ Keep figure metadata (bytes, description, title)
         ↓
[Chunker]
    ├─→ Replace placeholders with [FIGURE:...:START]...[FIGURE:...:END]
    ├─→ Treat figures as atomic blocks (never split)
    └─→ Include description in searchable text
         ↓
[Search Index]
    ├─→ content: "...text with figure description..."
    └─→ images: [{url, description, ...}]
```

---

## 📋 Comparison: Original vs Minimal

| Aspect | Original `prepdocslib` | `ingestor` |
|--------|----------------------|----------------------|
| **DI Figure Detection** | ✅ Same (`output=["figures"]`) | ✅ Same |
| **Image Extraction** | ✅ PyMuPDF cropping | ✅ Same |
| **MediaDescriber** | ✅ GPT-4o or Content Understanding | ✅ Same |
| **Description Generation** | ✅ AI vision model | ✅ Same |
| **Figure Placeholder** | HTML `<figure>` tags | HTML `<figure>` tags |
| **Chunking Markup** | Not explicitly marked | `[FIGURE:...:START/END]` markers |
| **Atomic Treatment** | ✅ Never split figures | ✅ Same |
| **Image Storage** | Blob storage | ✅ Same |
| **Search Index** | Images in separate field | ✅ Same |

**Core Difference:**
- Original: Figures wrapped in HTML `<figure>` tags throughout
- Minimal: Uses bracketed markers `[FIGURE:...]` for clearer parsing in chunker

**Both implementations:**
- ✅ Do NOT use OCR on figures
- ✅ Use AI vision models for descriptions
- ✅ Treat figures as atomic (never split)
- ✅ Store descriptions as searchable text

---

## ⚙️ Configuration

### Enable Figure Processing

```bash
# In .env file
AZURE_MEDIA_DESCRIBER=gpt4o  # or content_understanding

# For GPT-4o (default)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_VISION=gpt-4o
AZURE_OPENAI_KEY=your-key

# For Content Understanding (alternative)
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://your-cu.cognitiveservices.azure.com/
```

### Disable Figure Processing

```bash
AZURE_MEDIA_DESCRIBER=disabled
```

---

## 🧪 Example: Complete Flow

### Input PDF Page 3

```
[Sales Analysis]

The quarterly report shows strong growth in Q4.

[FIGURE: Bar chart image here]

As shown above, Electronics led all categories.
```

### After DI Extraction

```python
{
    "page_number": 3,
    "content": "The quarterly report shows strong growth in Q4.\n\n![Figure 1: Sales Chart](figures/0)\n\nAs shown above...",
    "figures": [
        {
            "id": "fig_3_1",
            "caption": {"content": "Figure 1: Sales Chart"},
            "bounding_regions": [{"page_number": 3, "polygon": [2.1, 4.5, 6.8, 7.2, ...]}]
        }
    ]
}
```

### After PyMuPDF Cropping

```python
ExtractedImage(
    figure_id="fig_3_1",
    page_num=2,  # 0-indexed
    bbox=(151.2, 324.0, 489.6, 518.4),  # pixels
    image_bytes=b'\x89PNG\r\n\x1a\n...',  # PNG data
    filename="figurefig_3_1.png",
    title="Figure 1: Sales Chart"
)
```

### After MediaDescriber

```python
image.description = "The image shows a bar chart comparing quarterly sales across three product categories: Electronics, Furniture, and Accessories. Electronics shows the highest sales in Q4 at approximately $450K."
```

### Page Text for Chunking

```markdown
The quarterly report shows strong growth in Q4.

[FIGURE:fig_3_1:START]
Figure: fig_3_1 Figure 1: Sales Chart
Description: The image shows a bar chart comparing quarterly sales across three product categories: Electronics, Furniture, and Accessories. Electronics shows the highest sales in Q4 at approximately $450K.
[FIGURE:fig_3_1:END]

As shown above, Electronics led all categories.
```

### Final Search Document

```json
{
  "id": "sales_report_page3_chunk0",
  "content": "The quarterly report shows strong growth in Q4.\n\n[FIGURE:fig_3_1:START]\nFigure: fig_3_1 Figure 1: Sales Chart\nDescription: The image shows a bar chart comparing quarterly sales across three product categories: Electronics, Furniture, and Accessories. Electronics shows the highest sales in Q4 at approximately $450K.\n[FIGURE:fig_3_1:END]\n\nAs shown above, Electronics led all categories.",
  "embeddings": [0.123, -0.456, ...],
  "images": [
    {
      "figure_id": "fig_3_1",
      "page_num": 2,
      "url": "https://account.blob.core.windows.net/myproject-images/sales_report/page_03_fig_01.png",
      "description": "The image shows a bar chart comparing quarterly sales across three product categories...",
      "title": "Figure 1: Sales Chart",
      "bbox": [151.2, 324.0, 489.6, 518.4],
      "filename": "figurefig_3_1.png"
    }
  ]
}
```

---

## ✅ Summary

### What DOES Happen ✅

1. ✅ Document Intelligence **identifies** where figures are (bounding boxes)
2. ✅ PyMuPDF **crops** the figure region from PDF as PNG image
3. ✅ GPT-4o Vision **describes** what's in the image (AI-generated text)
4. ✅ Description is embedded in chunk as **searchable text**
5. ✅ Original image is **stored in blob storage**
6. ✅ Figure is treated as **atomic** (never split across chunks)
7. ✅ Image URL and metadata are **included in search index**

### What DOES NOT Happen ❌

1. ❌ OCR is NOT used on figures
2. ❌ Text from images is NOT extracted character-by-character
3. ❌ Figures are NOT split across chunks
4. ❌ Image bytes are NOT stored in search index

### Why This Approach?

**Benefits:**
- ✅ AI descriptions are more useful than raw OCR (especially for charts, diagrams)
- ✅ Descriptions include context ("bar chart showing", "diagram illustrating")
- ✅ Better for semantic search (description explains what the figure shows)
- ✅ Handles non-text images (photos, logos, illustrations)

**When You Might Want OCR:**
- If figures contain important text (labels, annotations)
- If using Content Understanding (includes some text extraction)
- Consider post-processing with separate OCR if needed

---

**Conclusion:** The system uses **AI vision models** (not OCR) to generate **natural language descriptions** of figures, which are then embedded in chunks as searchable text. This is more powerful than OCR for most use cases!
