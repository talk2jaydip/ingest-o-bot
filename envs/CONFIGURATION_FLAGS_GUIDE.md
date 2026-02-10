# Configuration Flags Reference Guide

Complete reference for all processing flags in prepdocslib_minimal environment configurations.

## Table of Contents

- [Document Intelligence Extraction](#document-intelligence-extraction)
- [PDF Processing](#pdf-processing)
- [Chunking Configuration](#chunking-configuration)
- [Table Processing](#table-processing)
- [Figure/Image Processing](#figureimage-processing)
- [Office Document Processing](#office-document-processing)
- [Performance Tuning](#performance-tuning)
- [Scenario Recommendations](#scenario-recommendations)

---

## Document Intelligence Extraction

### EXTRACTION_METHOD

Controls how Azure Document Intelligence extracts content from PDFs.

**Options**:
- `layout`: Layout analysis only (fast, best for digital PDFs with good text)
- `layout_then_ocr`: Layout first, OCR fallback if low text density (RECOMMENDED)
- `ocr`: Full OCR extraction (slowest, best for scanned documents)
- `prebuilt-layout`: Use prebuilt layout model

**Scenarios**:
```bash
# Development - balanced
EXTRACTION_METHOD=layout_then_ocr

# Production digital PDFs - fastest
EXTRACTION_METHOD=layout

# Production scanned docs - highest quality
EXTRACTION_METHOD=ocr

# Debugging extraction issues
EXTRACTION_METHOD=layout_then_ocr
```

**Cost Impact**: `layout` < `layout_then_ocr` < `ocr`

**Quality**: `layout` (good for digital) < `layout_then_ocr` (balanced) < `ocr` (best for scanned)

### DI_BATCH_SIZE

Number of pages to process per Document Intelligence API call.

**Range**: 1-100

**Recommendations**:
```bash
# Development/Debugging
DI_BATCH_SIZE=4

# Standard Processing
DI_BATCH_SIZE=16

# Production (high throughput)
DI_BATCH_SIZE=32
```

**Trade-offs**:
- Larger batches: Faster overall, higher memory, less granular error handling
- Smaller batches: Slower overall, lower memory, better error isolation

### DI_MAX_RETRIES

Maximum retry attempts for failed Document Intelligence API calls.

**Range**: 0-10

**Recommendations**:
```bash
# Development
DI_MAX_RETRIES=3

# Production
DI_MAX_RETRIES=5

# Debugging (fail fast)
DI_MAX_RETRIES=1
```

---

## PDF Processing

### SPLIT_PDF_BY_PAGE

Split PDFs into individual pages before processing.

**Values**: `true` / `false`

**When to use `true`**:
- ✅ Need page-level citations in search results
- ✅ Large PDFs (>100 pages)
- ✅ Users need to reference specific pages
- ✅ Better granularity for document management

**When to use `false`**:
- ✅ Small documents (<10 pages)
- ✅ Documents are conceptually single units
- ✅ Faster processing (fewer chunks)
- ✅ Cross-page context important

**Configuration**:
```bash
# Production (recommended)
SPLIT_PDF_BY_PAGE=true

# Development (faster processing)
SPLIT_PDF_BY_PAGE=false

# Debugging specific pages
SPLIT_PDF_BY_PAGE=true
```

**Impact**:
- Processing time: +20-30% when enabled
- Number of chunks: Increases significantly
- Search precision: Improves (page-level results)

---

## Chunking Configuration

### CHUNKER_TARGET_TOKEN_COUNT

Target number of tokens per chunk (soft limit).

**Range**: 1000-32000

**Common Values**:
```bash
# High precision (more chunks, precise retrieval)
CHUNKER_TARGET_TOKEN_COUNT=4000

# Balanced (RECOMMENDED)
CHUNKER_TARGET_TOKEN_COUNT=8100

# High context (fewer chunks, more context per chunk)
CHUNKER_TARGET_TOKEN_COUNT=16000
```

**Trade-offs**:

| Size | Pros | Cons | Best For |
|------|------|------|----------|
| 4000 | Precise retrieval, focused results | Less context, more chunks | Q&A, fact finding |
| 8100 | Balanced, good for most cases | - | General purpose |
| 16000 | More context per chunk | Less precise, slower search | Technical docs, code |

**Recommendations by Document Type**:
```bash
# Technical documentation, code
CHUNKER_TARGET_TOKEN_COUNT=16000

# Research papers, articles
CHUNKER_TARGET_TOKEN_COUNT=8100

# Short documents, FAQ
CHUNKER_TARGET_TOKEN_COUNT=4000

# Legal documents (need context)
CHUNKER_TARGET_TOKEN_COUNT=12000
```

### CHUNKER_OVERLAP_TOKEN_COUNT

Number of tokens to overlap between adjacent chunks.

**Range**: 0-1000

**Common Values**:
```bash
# Minimal overlap
CHUNKER_OVERLAP_TOKEN_COUNT=50

# Standard (RECOMMENDED)
CHUNKER_OVERLAP_TOKEN_COUNT=100

# High overlap (better continuity)
CHUNKER_OVERLAP_TOKEN_COUNT=200
```

**Purpose**: Prevents information loss at chunk boundaries

**Guidelines**:
- 1-2% of chunk size is typical
- More overlap = better continuity, more storage
- Less overlap = faster processing, less redundancy

### CHUNKER_DISABLE_CHAR_LIMIT

Disable character-based chunking limits (use tokens only).

**Values**: `true` / `false`

**Recommendation**: `true` (ALWAYS)

```bash
# Modern approach (token-based)
CHUNKER_DISABLE_CHAR_LIMIT=true

# Legacy approach (character-based)
CHUNKER_DISABLE_CHAR_LIMIT=false
```

### CHUNKER_CROSS_PAGE_OVERLAP

Apply overlap to text chunks across page boundaries.

**Values**: `true` / `false`

```bash
# Better continuity across pages
CHUNKER_CROSS_PAGE_OVERLAP=true

# Strict page boundaries
CHUNKER_CROSS_PAGE_OVERLAP=false
```

**When to use `true`**:
- Continuous narrative documents
- Technical documentation
- Books, articles

**When to use `false`**:
- Slide decks (each page independent)
- Forms (page-specific content)
- Compliance documents (page boundaries important)

---

## Table Processing

### TABLE_RENDER_MODE

Format for rendering extracted tables.

**Options**: `markdown` / `html`

**Markdown**:
```bash
TABLE_RENDER_MODE=markdown
```

**Pros**:
- ✅ Human-readable
- ✅ Search-friendly (text-based)
- ✅ Lightweight
- ✅ Works everywhere

**Cons**:
- ❌ No complex cell spanning
- ❌ Limited formatting

**HTML**:
```bash
TABLE_RENDER_MODE=html
```

**Pros**:
- ✅ Full cell spanning (rowspan, colspan)
- ✅ Rich formatting
- ✅ Complex table structures

**Cons**:
- ❌ Requires HTML parser
- ❌ Larger file size
- ❌ Less search-friendly

**Recommendations**:
```bash
# Default (RECOMMENDED)
TABLE_RENDER_MODE=markdown

# Complex tables (financial, scientific)
TABLE_RENDER_MODE=html

# Maximum search compatibility
TABLE_RENDER_MODE=markdown
```

### TABLE_SUMMARIES

Generate AI summaries of tables using Azure OpenAI.

**Values**: `true` / `false`

```bash
# Enable (costs extra OpenAI calls)
TABLE_SUMMARIES=true

# Disable (default)
TABLE_SUMMARIES=false
```

**Benefits**:
- Better table searchability
- Natural language table descriptions
- Improved understanding of table content

**Costs**:
- OpenAI API calls per table
- Processing time increases
- Additional tokens used

**Recommendation**: Enable for production if budget allows

---

## Figure/Image Processing

### MEDIA_DESCRIBER_MODE

Generate descriptions for figures and images.

**Options**: `none` / `gpt4o` / `gpt4o-mini`

**None**:
```bash
MEDIA_DESCRIBER_MODE=none
```
- No descriptions generated
- Fastest, free
- Figures extracted but not described

**GPT-4o**:
```bash
MEDIA_DESCRIBER_MODE=gpt4o
```
- Best quality descriptions
- Highest cost
- Production recommended

**GPT-4o-mini**:
```bash
MEDIA_DESCRIBER_MODE=gpt4o-mini
```
- Good quality descriptions
- Lower cost
- Cost-effective alternative

**Recommendations**:
```bash
# Development (save costs)
MEDIA_DESCRIBER_MODE=none

# Production (best quality)
MEDIA_DESCRIBER_MODE=gpt4o

# Production (cost-conscious)
MEDIA_DESCRIBER_MODE=gpt4o-mini

# Debugging (check quality)
MEDIA_DESCRIBER_MODE=gpt4o
```

**Use Cases**:
- Scientific papers with diagrams → `gpt4o`
- Technical documentation with screenshots → `gpt4o`
- General documents with photos → `gpt4o-mini`
- Text-only documents → `none`

---

## Office Document Processing

### AZURE_OFFICE_EXTRACTOR_MODE

How to process Office documents (DOCX, PPTX).

**Options**: `azure_di` / `markitdown` / `hybrid`

**Azure DI Only**:
```bash
AZURE_OFFICE_EXTRACTOR_MODE=azure_di
```
- ✅ Highest quality extraction
- ✅ LaTeX equations (premium tier)
- ✅ Bounding boxes
- ❌ DOC files not supported
- ❌ Requires Azure DI

**MarkItDown Only**:
```bash
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
```
- ✅ Works offline
- ✅ No Azure costs
- ✅ Supports DOC files
- ❌ Lower quality
- ❌ Requires LibreOffice

**Hybrid (RECOMMENDED)**:
```bash
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true
```
- ✅ Best of both worlds
- ✅ Azure DI first, MarkItDown fallback
- ✅ Maximum reliability
- ❌ Requires both Azure DI + LibreOffice

**Scenario Recommendations**:
```bash
# Development
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true

# Production (best quality)
AZURE_OFFICE_EXTRACTOR_MODE=azure_di

# Offline/Air-gapped
AZURE_OFFICE_EXTRACTOR_MODE=markitdown

# Maximum reliability
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true
```

### AZURE_OFFICE_EQUATION_EXTRACTION

Extract LaTeX equations from Office documents.

**Values**: `true` / `false`

```bash
# Enable (requires Azure DI premium tier)
AZURE_OFFICE_EQUATION_EXTRACTION=true

# Disable
AZURE_OFFICE_EQUATION_EXTRACTION=false
```

**Requirements**:
- Azure DI premium tier
- AZURE_OFFICE_EXTRACTOR_MODE=azure_di or hybrid

**Use Cases**:
- Scientific papers
- Mathematical documentation
- Technical specifications
- Academic content

---

## Performance Tuning

### AZURE_MAX_WORKERS

Maximum concurrent workers for overall processing.

**Range**: 1-16

```bash
# Development
AZURE_MAX_WORKERS=2

# Standard
AZURE_MAX_WORKERS=4

# Production (high throughput)
AZURE_MAX_WORKERS=8

# Debugging (sequential)
AZURE_MAX_WORKERS=1
```

### AZURE_DI_MAX_CONCURRENCY

Maximum concurrent Document Intelligence API requests.

**Range**: 1-20

```bash
# Development
AZURE_DI_MAX_CONCURRENCY=3

# Standard
AZURE_DI_MAX_CONCURRENCY=5

# Production
AZURE_DI_MAX_CONCURRENCY=10
```

**Note**: Respect Azure DI service limits!

### AZURE_OPENAI_MAX_CONCURRENCY

Maximum concurrent OpenAI API requests.

**Range**: 1-30

```bash
# Development
AZURE_OPENAI_MAX_CONCURRENCY=5

# Standard
AZURE_OPENAI_MAX_CONCURRENCY=10

# Production
AZURE_OPENAI_MAX_CONCURRENCY=15
```

### AZURE_EMBED_BATCH_SIZE

Number of text chunks per embedding API call.

**Range**: 1-1000

```bash
# Development
AZURE_EMBED_BATCH_SIZE=64

# Standard
AZURE_EMBED_BATCH_SIZE=128

# Production
AZURE_EMBED_BATCH_SIZE=256
```

**Guidelines**:
- Larger batches: More efficient API usage
- Stay within OpenAI rate limits
- Monitor for timeouts

---

## Scenario Recommendations

### Scenario 1: Local Development

```bash
# Extraction
EXTRACTION_METHOD=layout_then_ocr
DI_BATCH_SIZE=16

# PDF Processing
SPLIT_PDF_BY_PAGE=false          # Faster

# Chunking
CHUNKER_TARGET_TOKEN_COUNT=8100
CHUNKER_OVERLAP_TOKEN_COUNT=100

# Tables/Figures
TABLE_RENDER_MODE=markdown
TABLE_SUMMARIES=false             # Save costs
MEDIA_DESCRIBER_MODE=none         # Save costs

# Office
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
AZURE_OFFICE_OFFLINE_FALLBACK=true

# Performance
AZURE_MAX_WORKERS=4
AZURE_DI_MAX_CONCURRENCY=3
```

### Scenario 2: Production Deployment

```bash
# Extraction - Best quality
EXTRACTION_METHOD=layout_then_ocr
DI_BATCH_SIZE=32

# PDF Processing - Enable citations
SPLIT_PDF_BY_PAGE=true

# Chunking - Balanced
CHUNKER_TARGET_TOKEN_COUNT=8100
CHUNKER_OVERLAP_TOKEN_COUNT=100

# Tables/Figures - Best quality
TABLE_RENDER_MODE=markdown
TABLE_SUMMARIES=true              # If budget allows
MEDIA_DESCRIBER_MODE=gpt4o

# Office - Best quality
AZURE_OFFICE_EXTRACTOR_MODE=azure_di
AZURE_OFFICE_EQUATION_EXTRACTION=true

# Performance - High throughput
AZURE_MAX_WORKERS=8
AZURE_DI_MAX_CONCURRENCY=10
AZURE_OPENAI_MAX_CONCURRENCY=15
```

### Scenario 3: Hybrid Testing

```bash
# Production-like settings for validation
EXTRACTION_METHOD=layout_then_ocr
DI_BATCH_SIZE=16
SPLIT_PDF_BY_PAGE=true
CHUNKER_TARGET_TOKEN_COUNT=8100
CHUNKER_OVERLAP_TOKEN_COUNT=100
TABLE_RENDER_MODE=markdown
MEDIA_DESCRIBER_MODE=gpt4o
AZURE_OFFICE_EXTRACTOR_MODE=hybrid
```

### Scenario 4: Production Debug

```bash
# Slower, more verbose for debugging
EXTRACTION_METHOD=layout_then_ocr
DI_BATCH_SIZE=4                   # Smaller batches
SPLIT_PDF_BY_PAGE=true            # Isolate pages
CHUNKER_TARGET_TOKEN_COUNT=4000   # Smaller chunks
TABLE_RENDER_MODE=markdown
MEDIA_DESCRIBER_MODE=gpt4o
AZURE_MAX_WORKERS=2               # Sequential-ish
LOG_LEVEL=DEBUG                   # Verbose logging
```

### Scenario 5: Fully Offline

```bash
# No Azure DI
# EXTRACTION_METHOD not used

# PDF Processing - pypdf fallback
SPLIT_PDF_BY_PAGE=false

# Chunking - Standard
CHUNKER_TARGET_TOKEN_COUNT=8100
CHUNKER_OVERLAP_TOKEN_COUNT=100

# Tables/Figures - No AI
TABLE_RENDER_MODE=markdown        # Only option
TABLE_SUMMARIES=false             # No OpenAI
MEDIA_DESCRIBER_MODE=none         # No OpenAI

# Office - Local only
AZURE_OFFICE_EXTRACTOR_MODE=markitdown
# Requires LibreOffice!
```

---

## Quick Reference Table

| Flag | Dev | Prod | Test | Debug | Offline |
|------|-----|------|------|-------|---------|
| EXTRACTION_METHOD | layout_then_ocr | layout_then_ocr | layout_then_ocr | layout_then_ocr | N/A |
| DI_BATCH_SIZE | 16 | 32 | 16 | 4 | N/A |
| SPLIT_PDF_BY_PAGE | false | true | true | true | false |
| CHUNKER_TARGET_TOKEN_COUNT | 8100 | 8100 | 8100 | 4000 | 8100 |
| CHUNKER_OVERLAP_TOKEN_COUNT | 100 | 100 | 100 | 100 | 100 |
| TABLE_RENDER_MODE | markdown | markdown | markdown | markdown | markdown |
| TABLE_SUMMARIES | false | true | false | false | false |
| MEDIA_DESCRIBER_MODE | none | gpt4o | gpt4o | gpt4o | none |
| AZURE_OFFICE_EXTRACTOR_MODE | hybrid | azure_di | hybrid | hybrid | markitdown |
| AZURE_MAX_WORKERS | 4 | 8 | 4 | 2 | 4 |

---

## Additional Resources

- [Configuration Matrix](../docs/reference/01_CONFIGURATION_MATRIX.md)
- [Chunking Guide](../docs/reference/06_CHUNKING.md)
- [Document Intelligence Guide](../docs/reference/04_DOCUMENT_INTELLIGENCE.md)
- [Table Processing Guide](../docs/reference/20_TABLE_PROCESSING.md)
- [Scenarios README](README.md)
