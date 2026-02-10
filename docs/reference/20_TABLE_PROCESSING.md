# Table Processing

> Comprehensive guide to table extraction, rendering, and chunking in ingestor

## Overview

The pipeline provides sophisticated table processing capabilities:
- Extraction from PDFs, DOCX, PPTX via Azure Document Intelligence
- Multiple rendering formats (Markdown, HTML)
- Intelligent chunking that respects table boundaries
- Alignment verification and quality checks

## Table Extraction

Tables are extracted using Azure Document Intelligence's layout analysis:
- Preserves cell structure and relationships
- Maintains row/column spanning
- Captures cell content with formatting
- Extracts table captions and metadata

## Rendering Modes

### Markdown Rendering (Default)
```bash
TABLE_RENDER_MODE=markdown
```

**Advantages**:
- Human-readable format
- Compatible with most markdown renderers
- Preserves basic structure
- Lightweight and portable

**Limitations**:
- No complex cell spanning
- Limited formatting options

### HTML Rendering
```bash
TABLE_RENDER_MODE=html
```

**Advantages**:
- Full cell spanning support (rowspan, colspan)
- Rich formatting options
- Preserves complex table structures
- Better for rendering in web UIs

**Limitations**:
- Requires HTML parser for search
- Larger file size
- Less readable as plain text

## Table Chunking

### Alignment with Document Structure

The chunker treats tables as atomic units when possible:

1. **Small Tables**: Kept in single chunk with surrounding context
2. **Large Tables**: Split row-by-row if exceeds token limit
3. **Boundary Respect**: Chunks break at table boundaries, not mid-table

### Configuration

```bash
# Allow tables up to this size before splitting
TABLE_MAX_TOKENS=4000

# Minimum tokens to reserve for table in chunk
TABLE_MIN_TOKENS=1000
```

### Verification

The pipeline includes table chunking verification:
- Ensures no tables are split incorrectly
- Validates table boundaries in chunks
- Reports table sizes and distribution
- Logs warnings for oversized tables

## Best Practices

### For Dense Tables
```bash
TABLE_RENDER_MODE=markdown
CHUNKER_TARGET_TOKEN_COUNT=16000
TABLE_MAX_TOKENS=8000
```

### For Complex Tables
```bash
TABLE_RENDER_MODE=html
# HTML preserves complex structures better
```

### For Search Optimization
```bash
TABLE_RENDER_MODE=markdown
# More search-friendly format
```

## Examples

### Simple Table (Markdown)
```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### Complex Table (HTML)
```html
<table>
  <tr>
    <th rowspan="2">Category</th>
    <th colspan="2">Values</th>
  </tr>
  <tr>
    <th>Min</th>
    <th>Max</th>
  </tr>
  <tr>
    <td>Type A</td>
    <td>10</td>
    <td>100</td>
  </tr>
</table>
```

## Troubleshooting

### Tables Not Rendering Correctly
**Problem**: Tables appear malformed or missing cells

**Solution**:
- Try switching to HTML mode: `TABLE_RENDER_MODE=html`
- Check table extraction quality in artifacts
- Verify Document Intelligence results

### Tables Split Across Chunks
**Problem**: Table content appears in multiple chunks

**Solution**:
- Increase chunk size: `CHUNKER_TARGET_TOKEN_COUNT=16000`
- Increase table max tokens: `TABLE_MAX_TOKENS=8000`
- Check chunking logs for table boundary handling

### Large Tables Timeout
**Problem**: Processing fails on large tables

**Solution**:
- Enable table splitting: `TABLE_SPLIT_LARGE=true`
- Reduce DI batch size: `DI_BATCH_SIZE=8`
- Process files with large tables separately

## Related Documentation

- [Chunking Guide](06_CHUNKING.md): Overall chunking strategy
- [Document Intelligence](04_DOCUMENT_INTELLIGENCE.md): Table extraction details
- [Configuration Matrix](01_CONFIGURATION_MATRIX.md): All configuration options

## Implementation Details

### Table Detection
Location: `di_extractor.py`
- Uses DI's table detection API
- Extracts cell coordinates and content
- Builds table structure from cells

### Rendering
Location: `table_renderer.py`
- Converts DI table format to Markdown/HTML
- Handles cell spanning and formatting
- Validates output structure

### Chunking Integration
Location: `chunker.py`
- Identifies table boundaries
- Reserves tokens for tables
- Ensures atomic table handling when possible

---

For detailed API information, see the source code in:
- `table_renderer.py` - Rendering logic
- `di_extractor.py` - Extraction logic
- `chunker.py` - Chunking integration
