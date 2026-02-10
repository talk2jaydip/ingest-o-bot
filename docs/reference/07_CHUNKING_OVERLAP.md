# Chunking, Overlap, and Offset Tracking Implementation

## Overview

This document explains the comprehensive chunking implementation in `ingestor`, which now includes semantic overlap and character offset tracking features based on the original `prepdocslib`.

## What Was Implemented ✅

### 1. Semantic Overlap Between Chunks

**Feature**: Chunks now overlap by a configurable percentage (default: 10%) to improve semantic continuity and search recall.

**How It Works**:
- **Intra-Page Overlap**: Adjacent chunks on the same page overlap
  - Previous chunk gets extended with a prefix from the next chunk
  - Overlap is ~10% of the chunk size (in characters)
  - Extended to natural boundaries (sentence endings or word breaks)
  
- **Cross-Page Overlap**: Chunks can overlap across page boundaries when appropriate
  - Only applied when previous chunk doesn't end cleanly (no sentence ending)
  - Next chunk must start with lowercase (continuation, not new section)
  - Next chunk must not start with a heading
  
- **Safety Rules**:
  - No overlap if either chunk contains figures (avoids duplicating images)
  - Token and character limits enforced (with 20% tolerance for overlap)
  - Overlap is shrunk at word/sentence boundaries if needed to fit limits

**Code Reference**:
```python
# In chunk_pages() method
if self.overlap_percent > 0:
    # Cross-page overlap
    if previous_chunk and page_chunks and self._should_cross_page_overlap(previous_chunk, page_chunks[0]):
        previous_chunk = self._append_overlap(previous_chunk, page_chunks[0])
    
    # Intra-page overlaps
    if len(page_chunks) > 1:
        for i in range(1, len(page_chunks)):
            prev_c = page_chunks[i - 1]
            curr_c = page_chunks[i]
            if not (self._contains_figure(prev_c.text) or self._contains_figure(curr_c.text)):
                page_chunks[i - 1] = self._append_overlap(prev_c, curr_c)
```

### 2. Character Offset Tracking

**Feature**: Each chunk now has a `char_span` field tracking its position in the document.

**How It Works**:
- **Document-Level Offsets**: Each `ExtractedPage` has an `offset` field
  - For page 1 with text "hello" (5 chars), page 2 starts at offset 5
  - For page 2 with text "world" (5 chars), page 3 starts at offset 10
  
- **Chunk-Level Spans**: Each `TextChunk` has a `char_span` tuple `(start, end)`
  - `start`: Character position where chunk begins (document-level)
  - `end`: Character position where chunk ends (document-level)
  - Calculated as: `page_offset + position_within_page`

**Benefits**:
- Enables precise location tracking for debugging
- Can map chunks back to specific document regions
- Useful for highlighting or citation generation

**Code Reference**:
```python
# In _split_text_into_chunks()
chunk_start = page_offset + current_chunk_start_pos
chunk_end = chunk_start + len(chunk_text)

chunks.append(TextChunk(
    page_num=page_num,
    chunk_index_on_page=chunk_index,
    text=chunk_text,
    char_span=(chunk_start, chunk_end),  # Document-level character span
    token_count=current_token_count,
    page_header=page_header
))
```

### 3. Page Number Preservation with Overlap

**Feature**: When overlap crosses pages, the chunk retains the original page number.

**How It Works**:
- Previous chunk keeps its `page_num` even when extended with next page's text
- This ensures stable attribution to the originating page
- Example:
  ```
  Page 1 Chunk 3: page_num=0, text="...end of page 1"
  (After overlap with Page 2 Chunk 1)
  Page 1 Chunk 3: page_num=0, text="...end of page 1 start of page 2"
  ```

**Code Reference**:
```python
# In _append_overlap() method
return TextChunk(
    page_num=prev_chunk.page_num,  # Keep original page number
    chunk_index_on_page=prev_chunk.chunk_index_on_page,
    text=candidate,  # Extended text with overlap
    # ... rest of fields
)
```

## Comparison with Original `prepdocslib`

### Similarities ✅

| Feature | Original `prepdocslib` | `ingestor` |
|---------|----------------------|----------------------|
| **Overlap Percentage** | 10% default | 10% default |
| **Overlap Strategy** | Append-style (prefix from next → previous) | Same |
| **Cross-Page Logic** | `_should_cross_page_overlap()` | Same logic |
| **Figure Handling** | Skip overlap if figures present | Same |
| **Boundary Detection** | Extend to sentence/word breaks | Same |
| **Token Limits** | Hard limit enforcement | Same |
| **Page Offset** | Page has `offset` field | Same |

### Differences ⚠️

| Aspect | Original `prepdocslib` | `ingestor` |
|--------|----------------------|----------------------|
| **Chunk Model** | Simple `Chunk` with just `page_num`, `text`, `images` | Rich `TextChunk` with `chunk_index`, `char_span`, `token_count`, `page_header` |
| **Char Span Tracking** | Not in `Chunk` (only `Page.offset`) | `char_span` tuple in every `TextChunk` |
| **Page Header** | Not extracted | Extracted and stored as `page_header` field |
| **Table/Figure Association** | Post-processing | Tracked in chunk's `tables` and `images` lists |

## Example: How Overlap Works

### Input: Two Pages

**Page 1 (offset=0):**
```
This is the introduction to our topic. We will discuss several key concepts that are important for understanding.
```

**Page 2 (offset=120):**
```
the underlying mechanisms. First, we examine the basic principles.
```

### Without Overlap:

**Chunk 1** (Page 1):
```
text: "This is the introduction to our topic. We will discuss several key concepts that are important for understanding."
char_span: (0, 119)
page_num: 0
```

**Chunk 2** (Page 2):
```
text: "the underlying mechanisms. First, we examine the basic principles."
char_span: (120, 187)
page_num: 1
```

### With 10% Overlap (Cross-Page):

**Chunk 1** (Page 1, extended):
```
text: "This is the introduction to our topic. We will discuss several key concepts that are important for understanding. the underlying mechanisms."
char_span: (0, 119)  # Original span (overlap not in span calculation)
page_num: 0  # Original page
```

**Chunk 2** (Page 2, unchanged):
```
text: "the underlying mechanisms. First, we examine the basic principles."
char_span: (120, 187)
page_num: 1
```

**Why Cross-Page Overlap Applied**:
- ✅ Previous chunk doesn't end with sentence ending (ends with ".")... wait, it does!
- Actually, in this case, cross-page overlap would NOT apply because Chunk 1 ends with a period.

Let me revise:

### Better Example (Overlap Applied):

**Page 1 (offset=0):**
```
This is the introduction to our topic. We will discuss several key concepts that are important for understanding
```
(Note: no period at the end)

**Page 2 (offset=119):**
```
the underlying mechanisms. First, we examine the basic principles.
```

**With 10% Overlap (Cross-Page)**:

**Chunk 1** (Page 1, extended):
```
text: "This is the introduction to our topic. We will discuss several key concepts that are important for understanding the underlying mechanisms."
char_span: (0, 118)  # Original span before overlap
page_num: 0
```

✅ Overlap applied because:
- Previous chunk doesn't end with sentence ending
- Next chunk starts with lowercase "the" (continuation)
- Next chunk doesn't start with a heading

## Configuration

### Environment Variables

```bash
# Chunking parameters (optional, defaults shown)
AZURE_CHUNKING_MAX_CHARS=1000
AZURE_CHUNKING_MAX_TOKENS=500
AZURE_CHUNKING_OVERLAP_PERCENT=10
```

### Programmatic Configuration

```python
from ingestor.chunker import LayoutAwareChunker

chunker = LayoutAwareChunker(
    max_chars=1000,
    max_tokens=500,
    overlap_percent=10  # 10% overlap
)

chunks = chunker.chunk_pages(extracted_pages)
```

## Benefits of This Implementation

### 1. Improved Search Recall
- Overlapping chunks ensure edge content appears in multiple chunks
- Reduces chance of missing relevant content at chunk boundaries

### 2. Semantic Continuity
- Cross-page overlap preserves context when content spans pages
- Only applied when semantically appropriate (lowercase start, no heading)

### 3. Precise Location Tracking
- `char_span` enables exact position mapping
- Useful for:
  - Debugging chunking behavior
  - Generating precise citations
  - Highlighting matched text in original document

### 4. Page Header Keywords
- Extracted headers improve keyword search
- Example: "Pacing Therapies" from page header helps find relevant chunks

## Testing Recommendations

### Test Case 1: Intra-Page Overlap
```python
# Create a page with multiple sentences
page = ExtractedPage(
    page_num=0,
    text="Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5.",
    tables=[],
    images=[],
    offset=0
)

chunks = chunker.chunk_page(page)

# Verify:
# - Adjacent chunks overlap
# - Overlap is ~10% of chunk size
# - No figures in chunks (overlap applied)
```

### Test Case 2: Cross-Page Overlap
```python
# Page 1 ends without sentence ending
page1 = ExtractedPage(
    page_num=0,
    text="This is a continuation",  # No period
    tables=[],
    images=[],
    offset=0
)

# Page 2 starts with lowercase
page2 = ExtractedPage(
    page_num=1,
    text="of the previous thought. New sentence.",
    tables=[],
    images=[],
    offset=23
)

chunks = chunker.chunk_pages([page1, page2])

# Verify:
# - Last chunk of page 1 extended with prefix of page 2
# - Page 2 chunk unchanged
# - Overlap applied correctly
```

### Test Case 3: No Overlap (Figure Present)
```python
page = ExtractedPage(
    page_num=0,
    text="Text before figure. [FIGURE:fig1:START]...[FIGURE:fig1:END] Text after figure.",
    tables=[],
    images=[],
    offset=0
)

chunks = chunker.chunk_page(page)

# Verify:
# - No overlap between chunks with figures
# - Figures not duplicated
```

## Performance Considerations

### Memory
- Overlap increases total text volume by ~10%
- Example: 100 chunks of 500 tokens each
  - Without overlap: 50,000 tokens
  - With overlap: ~55,000 tokens (+10%)

### Indexing
- More tokens to embed and index
- Slightly longer indexing time
- Benefit: Improved search recall outweighs cost

### Token Limits
- Overlap respects `max_tokens` limit (hard limit)
- Can allow up to 20% overflow for overlap
- Overlap shrunk if necessary to fit limits

## Troubleshooting

### Issue: Overlap Not Applied

**Check 1: Figure Present?**
```python
if "<figure" in chunk.text.lower() or "FIGURE:" in chunk.text.upper():
    # Overlap will not be applied
```

**Check 2: Previous Chunk Ends Cleanly?**
```python
if prev_chunk.text.rstrip()[-1] in SENTENCE_ENDINGS:
    # Cross-page overlap will not be applied
```

**Check 3: Next Chunk Starts with Uppercase?**
```python
if next_chunk.text.lstrip()[0].isupper():
    # Cross-page overlap will not be applied (likely new section)
```

### Issue: `char_span` Seems Incorrect

**Note**: `char_span` is calculated on processed text (after placeholder replacements), not original PDF positions.

- `char_span` is relative to the processed page text
- Original DI offsets are not preserved in final chunks
- Use `page_num` + `chunk_index_on_page` for stable identification

## Summary

The implemented chunking system in `ingestor` now fully supports:

✅ **Semantic overlap** (intra-page and cross-page)  
✅ **Character offset tracking** (document-level char_span)  
✅ **Page number preservation** (stable attribution with overlap)  
✅ **Atomic table/figure handling** (no splitting, no duplication)  
✅ **Page header extraction** (keyword search enhancement)  

This implementation is **functionally equivalent** to the original `prepdocslib` for core chunking features, with additional metadata tracking (`char_span`, `page_header`, `chunk_index_on_page`) for enhanced debugging and analysis capabilities.
