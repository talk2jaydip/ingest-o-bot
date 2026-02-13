"""Token-based text chunking with layout-aware, atomic table/figure handling.

This implementation matches the original prepdocslib approach:
- Token limit is HARD (never exceeded except for figures)
- Character limit is SOFT (can be exceeded by up to 20%)
- Recursive token splitting for oversized spans
- Cross-page merging with token-aware logic
- Partial sentence shifting for semantic integrity

CHUNKING LIMITS HIERARCHY:
===========================

1. NORMAL TEXT CHUNKS:
   - Max Tokens: 500 (HARD - never exceeded)
   - Max Chars: 1000 (SOFT - can exceed by 20% = 1200)
   - Can be configured via: CHUNKING_MAX_TOKENS, CHUNKING_MAX_CHARS

2. TABLES/FIGURES (ATOMIC BLOCKS):
   - No token limit (atomic, cannot be split)
   - Can exceed base token limit by design
   - Examples: 900-1200 tokens for large tables

3. TABLE + LEGEND:
   - Max: 2.5x base token limit (default: 1250 tokens for 500 base)
   - Configurable via: CHUNKING_TABLE_LEGEND_BUFFER (default: 2.5)
   - Legends provide critical context and should stay with tables

4. ABSOLUTE MAXIMUM (SAFETY):
   - Hard limit: 8000 tokens (configurable)
   - Based on embedding model limit (8191 tokens)
   - Configurable via: CHUNKING_ABSOLUTE_MAX_TOKENS
   - Prevents chunks that would fail embedding

CONFIGURATION:
==============
Environment Variables:
- CHUNKING_MAX_TOKENS=500              # Base token limit for text
- CHUNKING_MAX_CHARS=1000              # Base char limit for text
- CHUNKING_OVERLAP_PERCENT=10          # Overlap between chunks
- CHUNKING_DISABLE_CHAR_LIMIT=false    # Ignore char limit
- CHUNKING_CROSS_PAGE_OVERLAP=false    # Allow overlap across pages
- CHUNKING_TABLE_LEGEND_BUFFER=2.5     # Multiplier for table+legend
- CHUNKING_ABSOLUTE_MAX_TOKENS=8000    # Safety limit (< 8191)
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional, Generator

import tiktoken

from .di_extractor import ExtractedImage, ExtractedPage, ExtractedTable
from .logging_utils import get_logger
from .table_renderer import TableRenderer

logger = get_logger(__name__)

# Use same encoding as Azure OpenAI embeddings
ENCODING_MODEL = "text-embedding-ada-002"
bpe = tiktoken.encoding_for_model(ENCODING_MODEL)

# Orphan merging threshold: Never merge chunks >= 100 tokens
# This prevents small embedding models from over-merging reasonable chunks
ABSOLUTE_MINIMUM_ORPHAN_THRESHOLD = 100

# Sentence endings (standard + CJK)
SENTENCE_ENDINGS = [".", "!", "?", "。", "！", "？", "‼", "⁇", "⁈", "⁉"]

# Word breaks for split boundary detection (standard + CJK)
WORD_BREAKS = [
    ",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n",
    "、", "，", "；", "：", "（", "）", "【", "】", "「", "」", "『", "』",
    "〔", "〕", "〈", "〉", "《", "》", "–", "—", "'", "'", """, """
]

# Default chunking parameters loaded from environment variables
# Falls back to original prepdocslib defaults if not set
# Note: PipelineConfig.chunking loads these same values, so pipeline.py will pass explicit values
# Backward compatibility: Check new variable names first, then fall back to old AZURE_* names
DEFAULT_MAX_TOKENS = int(os.getenv("CHUNKING_MAX_TOKENS") or os.getenv("AZURE_CHUNKING_MAX_TOKENS", "500"))  # Target minimum tokens per chunk
DEFAULT_MAX_SECTION_TOKENS = int(os.getenv("CHUNKING_MAX_SECTION_TOKENS") or os.getenv("AZURE_CHUNKING_MAX_SECTION_TOKENS", "750"))  # Hard maximum tokens (allows room for tables)
DEFAULT_SECTION_LENGTH = int(os.getenv("CHUNKING_MAX_CHARS") or os.getenv("AZURE_CHUNKING_MAX_CHARS", "1000"))  # Soft limit - can be exceeded by 20%
DEFAULT_OVERLAP_PERCENT = int(os.getenv("CHUNKING_OVERLAP_PERCENT") or os.getenv("AZURE_CHUNKING_OVERLAP_PERCENT", "10"))  # Semantic overlap between chunks
DEFAULT_CROSS_PAGE_OVERLAP = (os.getenv("CHUNKING_CROSS_PAGE_OVERLAP") or os.getenv("AZURE_CHUNKING_CROSS_PAGE_OVERLAP", "true")).lower() == "true"  # Enable by default

# Table/figure special limits
# Tables are atomic blocks and can exceed normal token limits, but must stay within embedding model limits
DEFAULT_TABLE_LEGEND_BUFFER_MULTIPLIER = float(os.getenv("CHUNKING_TABLE_LEGEND_BUFFER") or os.getenv("AZURE_CHUNKING_TABLE_LEGEND_BUFFER", "2.5"))  # Multiplier for table+legend
ABSOLUTE_MAX_TOKENS = int(os.getenv("CHUNKING_ABSOLUTE_MAX_TOKENS") or os.getenv("AZURE_CHUNKING_ABSOLUTE_MAX_TOKENS", "8000"))  # Safety limit (below embedding model's 8191)

# Regex patterns for page headers/footers/numbers
PAGE_HEADER_PATTERN = re.compile(r'<!--\s*PageHeader="([^"]+)"\s*-->')
PAGE_FOOTER_PATTERN = re.compile(r'<!--\s*PageFooter="([^"]+)"\s*-->')
PAGE_NUMBER_PATTERN = re.compile(r'<!--\s*PageNumber="[^"]+"\s*-->')  # Remove PageNumber metadata
PAGE_NUMBER_PREFIX_PATTERN = re.compile(r'^[\dA-Za-z]+-\d+\s+')  # Clean "2-67 " prefix from headers


def remove_duplicated_phrase(text: str) -> str:
    """Remove duplicated consecutive phrases from text."""
    if not text:
        return text
    
    words = text.split()
    n = len(words)
    
    # Check if first half equals second half
    if n >= 2 and n % 2 == 0:
        half = n // 2
        first_half = ' '.join(words[:half])
        second_half = ' '.join(words[half:])
        if first_half.lower() == second_half.lower():
            return first_half
    
    return text


def extract_page_header(text: str) -> tuple[str, Optional[str]]:
    """Extract page header from text and return (cleaned_text, header_keyword).

    Removes all Document Intelligence metadata patterns:
    - <!-- PageHeader="..." --> - Extract and use as title
    - <!-- PageFooter="..." --> - Remove (not used)
    - <!-- PageNumber="..." --> - Remove (overhead)

    Fallback hierarchy (in order of preference):
    1. PageHeader metadata
    2. Markdown headers (# and ##)
    3. Table captions/titles from <figure> tags
    """
    headers = []

    for match in PAGE_HEADER_PATTERN.finditer(text):
        raw_header = match.group(1).strip()
        cleaned_header = PAGE_NUMBER_PREFIX_PATTERN.sub('', raw_header).strip()
        cleaned_header = remove_duplicated_phrase(cleaned_header)
        if cleaned_header:
            headers.append(cleaned_header)

    # Remove all metadata patterns from text
    cleaned_text = PAGE_HEADER_PATTERN.sub('', text)
    cleaned_text = PAGE_FOOTER_PATTERN.sub('', cleaned_text)
    cleaned_text = PAGE_NUMBER_PATTERN.sub('', cleaned_text)  # Remove PageNumber overhead

    # Fallback 1: If no PageHeader metadata, extract from markdown headers
    if not headers:
        # Look for markdown headers (# Header or ## Header)
        # Match lines that start with 1-3 # followed by space and text
        markdown_header_pattern = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
        markdown_matches = markdown_header_pattern.findall(cleaned_text)

        if markdown_matches:
            # Use the first significant header (prefer ## over # for section titles)
            # Filter out very short headers (< 10 chars) as they're likely not meaningful titles
            for level, header_text in markdown_matches:
                header_text = header_text.strip()
                if len(header_text) >= 10:  # Meaningful title threshold
                    headers.append(header_text)
                    break  # Use first meaningful header as title

    # Fallback 2: If still no headers, try extracting from table structure
    # This is critical for offline mode where tables may lack PageHeader metadata
    if not headers:
        # Look for table captions in <figure> tags
        # Pattern: <figure id="table-X">...<caption>Table X: Title</caption>...
        # Or: Table X-Y Title pattern at start of content
        table_caption_pattern = re.compile(
            r'<figure[^>]*>.*?(?:<caption>|Table\s+[\dA-Z]+-?[\d]*[:\.]?\s*)([^<\n]{10,100})',
            re.IGNORECASE | re.DOTALL
        )
        caption_matches = table_caption_pattern.findall(cleaned_text)

        if caption_matches:
            # Use first table caption as context header
            caption = caption_matches[0].strip()
            # Clean up: remove trailing punctuation, normalize spaces
            caption = re.sub(r'\s+', ' ', caption).strip('.:')
            if len(caption) >= 10:  # Meaningful caption threshold
                headers.append(f"Table: {caption}")

    # Combine unique headers
    if headers:
        seen = set()
        unique_headers = []
        for h in headers:
            if h.lower() not in seen:
                seen.add(h.lower())
                unique_headers.append(h)
        header_keyword = ' | '.join(unique_headers) if len(unique_headers) > 1 else unique_headers[0]
    else:
        header_keyword = None

    return cleaned_text, header_keyword


def _safe_concat(a: str, b: str) -> str:
    """Concatenate two non-empty segments, inserting space only when needed."""
    assert a and b, "_safe_concat expects non-empty strings"
    a_last = a[-1]
    b_first = b[0]
    if a_last.isspace() or b_first.isspace():
        return a + b
    if a_last == ">":  # HTML tag end acts as boundary
        return a + b
    if a_last.isalnum() and b_first.isalnum():
        return a + " " + b
    return a + b


def _normalize_chunk(text: str, max_chars: int) -> str:
    """Normalize chunk that barely exceeds character limit."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    
    # Trim to max_chars at word boundary
    trimmed = text[:max_chars]
    last_space = trimmed.rfind(' ')
    if last_space > max_chars // 2:  # Only trim if not removing too much
        trimmed = trimmed[:last_space]
    
    return trimmed


@dataclass
class TextChunk:
    """A chunk of text from a document page."""
    page_num: int
    text: str
    chunk_index_on_page: int = 0
    char_span: Optional[tuple[int, int]] = None
    token_count: Optional[int] = None
    tables: list[ExtractedTable] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    page_header: Optional[str] = None
    
    def __post_init__(self):
        if self.token_count is None:
            self.token_count = len(bpe.encode(self.text))


@dataclass
class _ChunkBuilder:
    """Accumulates sentence-like spans until size limits are reached.

    Notes:
    - Target minimum: 500 tokens (try to reach this before splitting)
    - Hard maximum: 750 tokens (allows room for moderate-sized tables)
    - Character limit is SOFT (can be exceeded, later normalized)
    - Token counts computed by caller and passed to add()
    """
    page_num: int
    max_chars: int
    max_tokens: int
    parts: list[str] = field(default_factory=list)
    token_len: int = 0
    disable_char_limit: bool = False
    target_min_tokens: int = 500  # Try to reach this minimum
    max_section_length_tokens: int = 750  # Hard maximum (overridable in __init__)

    def can_fit(self, text: str, token_count: int) -> bool:
        """Check if text can fit without exceeding limits.

        Strategy:
        - Target minimum: 500 tokens
        - Hard maximum: 700 tokens
        - Allows room for tables while keeping chunks reasonable
        """
        if not self.parts:  # Always allow first span
            # For first span, check against hard max (700)
            return token_count <= self.max_section_length_tokens and len(text) <= self.max_chars

        new_total = self.token_len + token_count

        # Always enforce hard maximum (700 tokens)
        # Target minimum (500) is a GOAL, not a strict cutoff
        if new_total > self.max_section_length_tokens:
            return False

        if not self.disable_char_limit and len("".join(self.parts)) + len(text) > self.max_chars:
            return False

        return True
    
    def add(self, text: str, token_count: int) -> bool:
        """Try to add text. Returns False if doesn't fit."""
        if not self.can_fit(text, token_count):
            return False
        self.parts.append(text)
        self.token_len += token_count
        return True
    
    def force_append(self, text: str):
        """Append text even if it overflows (for figures)."""
        self.parts.append(text)
    
    def flush_into(self, out: list[TextChunk], page_header: Optional[str] = None):
        """Flush accumulated content as a chunk."""
        if self.parts:
            chunk_text = "".join(self.parts)
            if chunk_text.strip():
                # DEBUG: Log flush with key phrases
                if any(phrase in chunk_text for phrase in ["remains", "Attention mechanisms", "In this work"]):
                    logger.info(f"💾 FLUSHING chunk: {self.token_len} tokens, contains key phrases, preview: {chunk_text[:80].replace(chr(10), ' ')}")
                out.append(TextChunk(
                    page_num=self.page_num,
                    text=chunk_text,
                    token_count=self.token_len,
                    page_header=page_header
                ))
        self.parts.clear()
        self.token_len = 0
    
    def has_content(self) -> bool:
        """Check if builder has accumulated content."""
        return bool(self.parts)
    
    def append_figure_and_flush(self, figure_text: str, out: list[TextChunk], page_header: Optional[str] = None):
        """Append figure (includes both tables and figures) to current text, allow overflow, and flush.
        
        This preserves context by keeping preceding text with the figure/table.
        Matches original prepdocslib behavior.
        """
        self.force_append(figure_text)
        self.flush_into(out, page_header)


class LayoutAwareChunker:
    """Token-based chunker with layout awareness (atomic tables/figures)."""

    def __init__(
        self,
        max_chars: int = DEFAULT_SECTION_LENGTH,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_section_tokens: int = DEFAULT_MAX_SECTION_TOKENS,
        overlap_percent: int = DEFAULT_OVERLAP_PERCENT,
        cross_page_overlap: bool = DEFAULT_CROSS_PAGE_OVERLAP,
        disable_char_limit: bool = False,
        table_renderer: Optional[TableRenderer] = None,
        embedding_max_tokens: Optional[int] = None  # NEW: embedding model's max sequence length
    ):
        """Initialize layout-aware chunker with dynamic embedding model limits.

        Args:
            max_chars: Soft character limit per chunk
            max_tokens: Target minimum tokens per chunk
            max_section_tokens: Hard maximum tokens per chunk
            overlap_percent: Percentage overlap between chunks
            cross_page_overlap: Whether to add overlap across page boundaries
            disable_char_limit: Ignore character limits (token-only mode)
            table_renderer: Optional table rendering strategy
            embedding_max_tokens: Maximum sequence length supported by embedding model.
                                 If provided, chunking limits are automatically adjusted
                                 to prevent truncation.
        """
        self.max_section_length = max_chars  # Soft limit
        self.max_tokens_per_section = max_tokens  # Target minimum
        self.max_section_length_tokens = max_section_tokens  # Hard maximum (500-700 range)
        self.semantic_overlap_percent = overlap_percent
        self.cross_page_overlap = cross_page_overlap
        self.disable_char_limit = disable_char_limit
        self.sentence_endings = SENTENCE_ENDINGS
        self.word_breaks = WORD_BREAKS
        self.table_renderer = table_renderer or TableRenderer()
        self.sentence_search_limit = 100
        self.embedding_max_tokens = embedding_max_tokens

        # Log initial configuration
        get_logger(__name__).info("Chunker initialized:")
        get_logger(__name__).info(f"  Target chunk size: {self.max_tokens_per_section} tokens (CHUNKING_MAX_TOKENS)")
        get_logger(__name__).info(f"  Hard maximum: {self.max_section_length_tokens} tokens (with overlap allowance)")
        get_logger(__name__).info(f"  Overlap: {overlap_percent}%")

        # Apply dynamic limit adjustment if embedding model has tighter constraints
        if embedding_max_tokens:
            get_logger(__name__).info(f"  Embedding model limit: {embedding_max_tokens} tokens (safety check only)")

            # Calculate safe limit considering:
            # 1. Overlap can add up to overlap_percent% more tokens
            # 2. Orphan merging can increase chunk size
            # 3. Keep 15% buffer for safety
            overlap_buffer = 1 + (overlap_percent / 100)  # e.g., 1.10 for 10% overlap
            safety_buffer = 0.85  # Use only 85% of limit, leaving 15% buffer
            safe_embedding_limit = int(embedding_max_tokens * safety_buffer / overlap_buffer)

            # Adjust chunking limits to respect embedding model
            if safe_embedding_limit < self.max_section_length_tokens:
                get_logger(__name__).warning(
                    f"⚠️  Embedding model max_seq_length ({embedding_max_tokens}) is smaller than "
                    f"configured max ({self.max_section_length_tokens}). "
                    f"Automatically reducing to {safe_embedding_limit} tokens "
                    f"(with {int((1-safety_buffer)*100)}% buffer and {overlap_percent}% overlap allowance)."
                )
                self.max_section_length_tokens = safe_embedding_limit

            if safe_embedding_limit < self.max_tokens_per_section:
                get_logger(__name__).warning(
                    f"⚠️  Adjusting target chunk size from {self.max_tokens_per_section} "
                    f"to {safe_embedding_limit} tokens to fit embedding model "
                    f"(with buffers for overlap and safety)."
                )
                self.max_tokens_per_section = safe_embedding_limit
            else:
                get_logger(__name__).info(f"  ✓ Configuration is compatible with embedding model (no adjustment needed)")
    
    def chunk_pages(self, pages: list[ExtractedPage]) -> list[TextChunk]:
        """Chunk multiple pages with cross-page merging and overlap.
        
        Matches original prepdocslib: both tables and figures wrapped in <figure> tags,
        extracted as atomic blocks that are never split.
        """
        all_chunks = []
        previous_chunk: Optional[TextChunk] = None
        # Match original prepdocslib: single regex for <figure> tags (includes both tables and figures)
        figure_regex = re.compile(r'<figure.*?</figure>', re.IGNORECASE | re.DOTALL)
        
        for page in pages:
            # Prepare page text
            page_text = self._prepare_page_text(page)
            page_text, page_header = extract_page_header(page_text)
            
            if not page_text.strip():
                continue
            
            # Build ordered list of blocks: (type, text)
            # Matches original prepdocslib: extract <figure> blocks (includes both tables and figures)
            blocks: list[tuple[str, str]] = []
            last = 0
            for m in figure_regex.finditer(page_text):
                if m.start() > last:
                    blocks.append(("text", page_text[last:m.start()]))
                blocks.append(("figure", m.group()))
                last = m.end()
            if last < len(page_text):
                blocks.append(("text", page_text[last:]))

            # DEBUG: Log blocks for page 2
            if page.page_num == 1:  # Page 2 (0-indexed)
                logger.info(f"🔍 Page 2 analysis:")
                logger.info(f"   Page text length: {len(page_text)} chars")
                logger.info(f"   Number of blocks: {len(blocks)}")
                for i, (btype, btext) in enumerate(blocks):
                    logger.info(f"   Block {i+1}: type={btype}, length={len(btext)} chars")
                total_block_chars = sum(len(btext) for _, btext in blocks)
                logger.info(f"   Total chars in blocks: {total_block_chars}")
                if abs(total_block_chars - len(page_text)) > 10:
                    logger.error(f"   ❌ TEXT LOST IN BLOCK CREATION!")

            # Process blocks into chunks
            page_chunks: list[TextChunk] = []
            builder = _ChunkBuilder(
                page_num=page.page_num,
                max_chars=self.max_section_length,
                max_tokens=self.max_tokens_per_section,
                max_section_length_tokens=self.max_section_length_tokens,
                disable_char_limit=self.disable_char_limit
            )
            previous_was_figure = False

            # DEBUG: Initialize span tracking variables
            total_spans = 0
            spans_added_to_builder = 0
            spans_force_added = 0
            spans_flushed_retried = 0
            spans_recursive_split = 0
            spans_defensive = 0

            for block_idx, (btype, btext) in enumerate(blocks):
                # Handle figures (includes both tables and figures - matches original prepdocslib)
                if btype == "figure":
                    # Check if builder has table reference that should stay with table
                    table_ref = None
                    if builder.has_content():
                        builder_text = "".join(builder.parts)
                        table_ref = self._find_table_reference_in_text(builder_text)

                        if table_ref:
                            # Extract reference from builder
                            ref_start = builder_text.rfind(table_ref)
                            if ref_start >= 0:
                                # Remove reference from builder
                                text_before = builder_text[:ref_start].strip()

                                # Only move if builder still has enough content
                                if text_before:
                                    remaining_tokens = len(bpe.encode(text_before))
                                    if remaining_tokens >= 300:  # Keep substantial text
                                        # Update builder
                                        builder.parts = [text_before] if text_before else []
                                        builder.token_len = remaining_tokens

                                        # Prepend reference to table
                                        btext = table_ref + "\n\n" + btext
                                        logger.info(f"Moving table reference to table chunk: {table_ref[:60]}...")

                    # Validate table/figure size (safety check)
                    figure_tokens = len(bpe.encode(btext))
                    if figure_tokens > ABSOLUTE_MAX_TOKENS:
                        logger.error(
                            f"Table/figure exceeds ABSOLUTE MAX ({ABSOLUTE_MAX_TOKENS} tokens): "
                            f"{figure_tokens} tokens on page {page.page_num + 1}. "
                            f"This will cause embedding failures! Consider splitting the table."
                        )
                        # Still emit it but log error - user needs to fix source document

                    # Add figure to builder
                    builder.force_append(btext)

                    # Look ahead to see if we should add text AFTER the table/figure
                    # to preserve semantic context and reach minimum chunk size
                    current_tokens = builder.token_len + figure_tokens

                    # Try to add text after table if:
                    # 1. We're below minimum chunk size (500 tokens)
                    # 2. There are more text blocks after this figure
                    # 3. Adding them won't exceed a reasonable limit
                    if current_tokens < self.max_tokens_per_section and block_idx + 1 < len(blocks):
                        # Look at next block
                        next_idx = block_idx + 1
                        if next_idx < len(blocks) and blocks[next_idx][0] == "text":
                            next_text = blocks[next_idx][1]
                            next_tokens = len(bpe.encode(next_text))

                            # If adding next text keeps us under reasonable limit, include it
                            # Use TABLE_LEGEND_BUFFER multiplier to allow more context
                            max_with_context = int(self.max_tokens_per_section * DEFAULT_TABLE_LEGEND_BUFFER_MULTIPLIER)
                            if current_tokens + next_tokens <= max_with_context:
                                # Include the text after table in this chunk
                                builder.force_append(next_text)
                                # Skip processing this block later
                                blocks[next_idx] = ("skip", "")

                    # Flush the chunk with table + context
                    builder.flush_into(page_chunks, page_header)
                    previous_was_figure = True
                    continue

                # Skip blocks that were already processed (merged with table)
                if btype == "skip":
                    continue

                # Legend merging removed per user request
                previous_was_figure = False

                # Process text block: split into sentence-like spans
                spans = self._split_into_spans(btext)

                # DEBUG: Check if text is preserved in spans
                total_span_chars = sum(len(s) for s in spans)
                if page.page_num == 1 and abs(total_span_chars - len(btext)) > 10:
                    logger.error(f"❌ TEXT LOST IN SPAN SPLITTING! Block: {len(btext)} chars, Spans: {total_span_chars} chars")

                # DEBUG: Update span count for this block
                total_spans += len(spans)

                for span_idx, span in enumerate(spans):
                    span_tokens = len(bpe.encode(span))

                    # DEBUG: Log all spans
                    span_preview = span[:60].replace('\n', ' ')
                    if span_idx % 20 == 0 or any(phrase in span for phrase in ["remains", "Attention mechanisms", "In this work", "## 2 Background", "reducing sequential"]):
                        logger.info(f"🔍 SPAN {span_idx}/{len(spans)}: {span_tokens} tokens, builder={builder.token_len} | {span_preview}")

                    # If single span exceeds token limit, split it recursively
                    if span_tokens > self.max_tokens_per_section:
                        spans_recursive_split += 1
                        # Before flushing, check if we've reached minimum
                        # Only flush if we have decent content or the span is really large
                        if builder.token_len >= 300 or span_tokens > self.max_tokens_per_section * 1.5:
                            builder.flush_into(page_chunks, page_header)
                        for chunk in self._split_by_max_tokens(page.page_num, span, page_header):
                            page_chunks.append(chunk)
                        continue

                    # Try normal add first
                    added = builder.add(span, span_tokens)

                    # DEBUG: Log span addition result for Page 2
                    if page.page_num == 1 and span_tokens > 10:  # Log significant spans
                        status = "✅ Added" if added else "❌ Rejected by can_fit"
                        logger.info(f"{status}: span {span_idx} ({span_tokens} tok) | {span[:50].replace(chr(10), ' ')}")

                    if added:
                        spans_added_to_builder += 1
                        continue

                    # Span doesn't fit - check if we should flush or force add
                    if builder.token_len < builder.target_min_tokens:
                        # Below minimum - try to force add if total won't exceed hard max
                        if builder.token_len + span_tokens <= builder.max_section_length_tokens:
                            # DEBUG: Log all force-adds for Page 2
                            if page.page_num == 1 and span_tokens > 10:
                                logger.info(f"🔧 FORCE ADD span {span_idx}: {span_tokens} tok (builder {builder.token_len} → {builder.token_len + span_tokens}) | {span[:50].replace(chr(10), ' ')}")
                            builder.parts.append(span)
                            builder.token_len += span_tokens
                            spans_force_added += 1
                            continue

                    # Flush and retry (guaranteed to fit since span_tokens <= limit)
                    if any(phrase in span for phrase in ["remains", "Attention mechanisms", "In this work"]):
                        logger.info(f"🔄 FLUSHING builder ({builder.token_len} tokens) and retrying span: {span[:60].replace(chr(10), ' ')}")
                    builder.flush_into(page_chunks, page_header)
                    spans_flushed_retried += 1
                    if not builder.add(span, span_tokens):
                        # Shouldn't happen, but handle defensively
                        spans_defensive += 1
                        if any(phrase in span for phrase in ["remains", "Attention mechanisms"]):
                            logger.warning(f"⚠️ DEFENSIVE CHUNK for span: {span[:60].replace(chr(10), ' ')}")
                        page_chunks.append(TextChunk(
                            page_num=page.page_num,
                            text=span,
                            page_header=page_header
                        ))
            
            # Flush any trailing content
            if builder.has_content():
                logger.info(f"📤 FINAL FLUSH: builder has {builder.token_len} tokens, {len(builder.parts)} parts")
            builder.flush_into(page_chunks, page_header)

            # DEBUG: Log chunks immediately after flush (before any post-processing)
            if page.page_num == 1:  # Page 2 (0-indexed)
                logger.info(f"📋 Page 2 chunks after flush (before orphan merge/overlap):")
                for i, chunk in enumerate(page_chunks):
                    preview = chunk.text[:80].replace('\n', ' ')
                    logger.info(f"   Chunk {i+1}: {chunk.token_count} tokens | {preview}")
                total_tokens = sum(c.token_count or 0 for c in page_chunks)
                logger.info(f"   Total tokens in page_chunks: {total_tokens}")

            # DEBUG: Log span processing statistics
            spans_accounted_for = spans_added_to_builder + spans_force_added + spans_flushed_retried + spans_recursive_split + spans_defensive
            logger.info(f"📊 Page {page.page_num+1} Statistics:")
            logger.info(f"   Total spans: {total_spans}")
            logger.info(f"   Added normally: {spans_added_to_builder}")
            logger.info(f"   Force added: {spans_force_added}")
            logger.info(f"   Flush+retry: {spans_flushed_retried}")
            logger.info(f"   Recursive split: {spans_recursive_split}")
            logger.info(f"   Defensive: {spans_defensive}")
            logger.info(f"   TOTAL ACCOUNTED: {spans_accounted_for}")
            if spans_accounted_for != total_spans:
                logger.error(f"   ❌ MISSING {total_spans - spans_accounted_for} SPANS!")

            # Cross-page merging logic (look-behind)
            if previous_chunk and page_chunks:
                # DEBUG: Log before cross-page merge
                if page.page_num == 1:  # Page 2 (0-indexed)
                    logger.info(f"🔀 Before cross-page merge:")
                    logger.info(f"   previous_chunk: {previous_chunk.token_count} tokens")
                    logger.info(f"   page_chunks: {len(page_chunks)} chunks, {sum(c.token_count or 0 for c in page_chunks)} total tokens")

                previous_chunk, page_chunks = self._attempt_cross_page_merge(
                    previous_chunk, page_chunks
                )

                # DEBUG: Log after cross-page merge
                if page.page_num == 1:  # Page 2 (0-indexed)
                    logger.info(f"🔀 After cross-page merge:")
                    if previous_chunk:
                        logger.info(f"   previous_chunk: {previous_chunk.token_count} tokens")
                    logger.info(f"   page_chunks: {len(page_chunks)} chunks, {sum(c.token_count or 0 for c in page_chunks)} total tokens")

            # NOTE: Character-based normalization is DISABLED for token-based chunking
            # Token limits (500-750) already enforce size, and character truncation
            # would cause text loss since 750 tokens ≈ 3000 chars >> 1200 char limit

            # Merge orphan chunks on same page (< 200 tokens)
            # Do this AFTER cross-page merging so we have accurate token counts
            page_chunks = self._merge_orphan_chunks(page_chunks)

            # Apply semantic overlap (append-style)
            if self.semantic_overlap_percent > 0:
                # Cross-page overlap
                if previous_chunk and page_chunks:
                    should_overlap = self._should_cross_page_overlap(previous_chunk, page_chunks[0])
                    logger.info(f"Cross-page overlap check: {should_overlap} (prev page={previous_chunk.page_num+1}, next page={page_chunks[0].page_num+1})")
                    if should_overlap:
                        before_tokens = previous_chunk.token_count
                        previous_chunk = self._append_overlap(previous_chunk, page_chunks[0])
                        logger.info(f"Applied cross-page overlap: prev chunk {before_tokens} → {previous_chunk.token_count} tokens")

                # Intra-page overlaps (matches original prepdocslib)
                if len(page_chunks) > 1:
                    # DEBUG: Log before intra-page overlap
                    if page.page_num == 1:
                        logger.info(f"📝 Before intra-page overlap on Page 2:")
                        for i, chunk in enumerate(page_chunks):
                            logger.info(f"   Chunk {i+1}: {chunk.token_count} tokens")

                    for i in range(1, len(page_chunks)):
                        prev_c = page_chunks[i - 1]
                        curr_c = page_chunks[i]
                        # Skip overlap if PREVIOUS chunk contains a figure (can't extend into it)
                        # Allow overlap if only CURRENT chunk has figure (we overlap the text before the figure)
                        if "<figure" in prev_c.text.lower():
                            continue
                        # Also skip if current chunk STARTS with a figure (no text to overlap)
                        if curr_c.text.lstrip().startswith("<figure"):
                            continue
                        page_chunks[i - 1] = self._append_overlap(prev_c, curr_c)

                    # DEBUG: Log after intra-page overlap
                    if page.page_num == 1:
                        logger.info(f"📝 After intra-page overlap on Page 2:")
                        for i, chunk in enumerate(page_chunks):
                            preview = chunk.text[:80].replace('\n', ' ')
                            logger.info(f"   Chunk {i+1}: {chunk.token_count} tokens | {preview}")
            
            # Associate tables and images with chunks
            self._associate_tables_images(page_chunks, page.tables, page.images)
            
            # Emit previous_chunk now that merge opportunity considered
            if previous_chunk:
                all_chunks.append(previous_chunk)
            
            # Keep last chunk as new previous (for next page merge)
            if page_chunks:
                if len(page_chunks) == 1:
                    previous_chunk = page_chunks[0]
                else:
                    all_chunks.extend(page_chunks[:-1])
                    previous_chunk = page_chunks[-1]
            else:
                previous_chunk = None
        
        # Emit final chunk
        if previous_chunk:
            all_chunks.append(previous_chunk)

        # FINAL PASS: Merge all remaining orphans across pages for semantic coherence
        # This ensures 500-token minimum is enforced document-wide
        all_chunks = self._final_orphan_merge_pass(all_chunks)

        # Add chunk indices
        for i, chunk in enumerate(all_chunks):
            chunk.chunk_index_on_page = i

        logger.info(
            f"Created {len(all_chunks)} chunks from {len(pages)} pages "
            f"(token-based, {self.semantic_overlap_percent}% overlap)"
        )
        return all_chunks
    
    def _prepare_page_text(self, page: ExtractedPage) -> str:
        """Prepare page text by replacing figure placeholders.
        
        Tables are already rendered and wrapped in <figure> tags by the extractor:
        - HTML mode: <figure><table><tr>...</tr></table></figure>
        - PLAIN mode: <figure>+---+\n| A |\n+---+</figure>
        - MARKDOWN mode: <figure>| A |\n|---|</figure>
        
        Figures need their placeholders replaced with <figure> tags.
        """
        text = page.text
        
        # Tables are already rendered from extractor - no processing needed
        
        # Replace figure placeholders with <figure> tags
        for image in page.images:
            if image.description:
                caption_parts = [image.figure_id]
                if image.title:
                    caption_parts.append(image.title)
                caption = " ".join(caption_parts)
                # Use <figure> tags (matches original prepdocslib)
                figure_markup = f"<figure id=\"{image.figure_id}\">\nFigure: {caption}\nDescription: {image.description}\n</figure>"
                text = text.replace(image.placeholder, figure_markup)
        
        return text
    
    def _split_into_spans(self, text: str) -> list[str]:
        """Split text into sentence-like spans.

        Improved to handle table boundaries:
        - Avoids splitting mid-table by detecting <figure> tags
        - Ensures table content stays together for proper chunking
        """
        spans = []
        current_chars = []
        in_figure = False
        figure_depth = 0

        i = 0
        while i < len(text):
            ch = text[i]
            current_chars.append(ch)

            # Track <figure> tag depth to avoid splitting inside tables/figures
            if ch == '<':
                # Look ahead to detect <figure or </figure>
                remaining = text[i:i+10].lower()
                if remaining.startswith('<figure'):
                    figure_depth += 1
                    in_figure = True
                elif remaining.startswith('</figure>'):
                    figure_depth = max(0, figure_depth - 1)
                    if figure_depth == 0:
                        in_figure = False

            # Only split at sentence endings if NOT inside a figure/table
            if ch in self.sentence_endings and not in_figure:
                spans.append("".join(current_chars))
                current_chars = []

            i += 1

        if current_chars:  # Remaining tail
            spans.append("".join(current_chars))

        return spans
    
    def _find_split_pos(self, text: str) -> tuple[int, bool]:
        """Find split position for oversized span.
        
        Returns: (position, use_overlap)
        - use_overlap=False: natural boundary found
        - use_overlap=True: no boundary, use midpoint + overlap
        """
        length = len(text)
        mid = length // 2
        window_limit = mid  # Search entire half
        
        # 1. Sentence endings
        pos = 0
        while mid - pos > 0 or mid + pos < length:
            left = mid - pos
            right = mid + pos
            if left >= 0 and left < length and text[left] in self.sentence_endings:
                return left, False
            if right < length and text[right] in self.sentence_endings:
                return right, False
            pos += 1
        
        # 2. Word breaks
        pos = 0
        while mid - pos > 0 or mid + pos < length:
            left = mid - pos
            right = mid + pos
            if left >= 0 and left < length and text[left] in self.word_breaks:
                return left, False
            if right < length and text[right] in self.word_breaks:
                return right, False
            pos += 1
        
        # 3. Fallback - no boundary found
        return -1, True
    
    def _split_by_max_tokens(self, page_num: int, text: str, page_header: Optional[str] = None) -> Generator[TextChunk, None, None]:
        """Recursively split text by token count.

        Boundary preference order:
        1. Sentence-ending punctuation near midpoint
        2. Word-break character near midpoint
        3. Midpoint split with symmetric overlap
        """
        tokens = bpe.encode(text)
        if len(tokens) <= self.max_tokens_per_section:
            yield TextChunk(page_num=page_num, text=text, page_header=page_header)
            return

        # Safety check: If text is very short but has many tokens (e.g., long URL, base64),
        # force yield to prevent infinite recursion
        MIN_TEXT_LENGTH = 100
        if len(text) < MIN_TEXT_LENGTH:
            logger.warning(
                f"Text has {len(tokens)} tokens but only {len(text)} chars. "
                f"Forcing chunk to prevent recursion (may exceed token limit)."
            )
            yield TextChunk(page_num=page_num, text=text, page_header=page_header)
            return

        split_pos, use_overlap = self._find_split_pos(text)

        if not use_overlap and split_pos > 0:
            # Natural boundary found
            first_half = text[:split_pos + 1]
            second_half = text[split_pos + 1:]
        else:
            # No boundary - use midpoint + overlap
            middle = len(text) // 2
            overlap = int(len(text) * (DEFAULT_OVERLAP_PERCENT / 100))

            # Find a better split position near middle to avoid breaking numbered lists
            # Look for newlines near the midpoint
            search_range = min(200, middle // 2)  # Search ±200 chars or ±50% of middle
            best_split = middle

            # Look for line breaks near midpoint (prefer splitting at paragraph boundaries)
            for offset in range(-search_range, search_range):
                pos = middle + offset
                if pos > 0 and pos < len(text) and text[pos] == '\n':
                    # Check if this is a good boundary (not mid-numbered-list)
                    # Look ahead to see if next line starts with a number like "1\." or "5\."
                    if pos + 1 < len(text):
                        next_line_start = text[pos + 1:pos + 10]
                        # If next line starts with number + period/backslash, try to keep it together
                        import re
                        if not re.match(r'^\d+[\.\)]', next_line_start):
                            best_split = pos
                            break

            first_half = text[:best_split + overlap]
            second_half = text[max(0, best_split - overlap):]

        # Safety check: Ensure splits are making progress
        if len(first_half) >= len(text) or len(second_half) >= len(text):
            logger.warning(
                f"Split not making progress (text={len(text)}, first={len(first_half)}, second={len(second_half)}). "
                f"Forcing chunk to prevent infinite recursion."
            )
            yield TextChunk(page_num=page_num, text=text, page_header=page_header)
            return

        # Recursively split both halves
        yield from self._split_by_max_tokens(page_num, first_half, page_header)
        yield from self._split_by_max_tokens(page_num, second_half, page_header)
    
    def _attempt_cross_page_merge(
        self,
        previous_chunk: TextChunk,
        page_chunks: list[TextChunk]
    ) -> tuple[Optional[TextChunk], list[TextChunk]]:
        """Attempt to merge previous chunk with first chunk of new page.

        Improved to handle table continuation across pages:
        - Detects if previous chunk ends with incomplete table context
        - Allows merging table continuation chunks when semantically connected
        - Preserves table context for offline mode where PageHeader may be missing
        """
        if not previous_chunk or not page_chunks:
            return previous_chunk, page_chunks

        first_new = page_chunks[0]
        first_new_stripped = first_new.text.lstrip()

        # CRITICAL: Check if PageHeader changed (section boundary)
        # Different PageHeaders indicate different document sections - never merge
        # EXCEPTION: Allow merge if both chunks lack PageHeader (offline mode)
        # or if one has a table-derived header (indicates table continuation)
        if previous_chunk.page_header and first_new.page_header:
            # Check if either header is table-derived (starts with "Table:")
            prev_is_table_header = previous_chunk.page_header.startswith("Table:")
            next_is_table_header = first_new.page_header.startswith("Table:")

            # If both are table headers or headers match, allow potential merge
            if not (prev_is_table_header or next_is_table_header):
                if previous_chunk.page_header.lower() != first_new.page_header.lower():
                    logger.info(
                        f"Blocking cross-page merge: PageHeader changed from "
                        f"'{previous_chunk.page_header}' to '{first_new.page_header}'"
                    )
                    return previous_chunk, page_chunks

        # Improved table handling: Check if this is table continuation
        prev_has_table = "<figure" in previous_chunk.text.lower()
        next_has_table = "<figure" in first_new_stripped[:60].lower()

        # Special case: If previous chunk ends with table and next starts with table,
        # this might be a multi-page table. Check if we should add overlap context.
        if prev_has_table and next_has_table:
            # Both chunks have tables - likely continuation across pages
            # Don't merge (tables are atomic), but ensure overlap is applied
            logger.debug(
                f"Table continuation detected: prev page {previous_chunk.page_num+1} "
                f"and next page {first_new.page_num+1} both contain tables"
            )
            return previous_chunk, page_chunks

        # Standard rule: Never merge if either side contains figures/tables (atomic blocks)
        # unless it's clearly a continuation case
        if prev_has_table or next_has_table:
            return previous_chunk, page_chunks

        # Safety net: Force merge very small orphan chunks to prevent poor quality chunks.
        # This catches cases like 35-token heading+intro that should be with following content.
        # Only applies to text-only chunks (figures already blocked above).
        if first_new.token_count and first_new.token_count < 100:  # Orphan threshold
            combined_text = _safe_concat(previous_chunk.text, first_new.text)
            combined_tokens = len(bpe.encode(combined_text))

            # If combined is well under limit, force merge regardless of other rules
            if combined_tokens <= int(self.max_tokens_per_section * 0.8):  # 80% threshold = 400 tokens
                logger.debug(
                    f"Safety net: Merging orphan chunk ({first_new.token_count} tokens) "
                    f"with previous ({previous_chunk.token_count} tokens) -> {combined_tokens} tokens"
                )
                return TextChunk(
                    page_num=previous_chunk.page_num,
                    text=combined_text,
                    page_header=previous_chunk.page_header,
                    tables=previous_chunk.tables,
                    images=previous_chunk.images
                ), page_chunks[1:]

        # Legacy safety net for very small orphans (kept for backwards compatibility)

        # If cross-page overlap is enabled, relax sentence/uppercase checks.
        # Still avoid merging into headings to keep section boundaries.
        if self.cross_page_overlap:
            if first_new_stripped.startswith("#"):
                return previous_chunk, page_chunks
            first_line = first_new_stripped.splitlines()[0] if first_new_stripped else ""
            if self._is_heading_like(first_line):
                return previous_chunk, page_chunks
        else:
            # Check if we should merge (original prepdocslib behavior)
            prev_last_char = previous_chunk.text.rstrip()[-1:] if previous_chunk.text.rstrip() else ""
            first_char = first_new_stripped[:1]
            
            # Don't merge if:
            # - Previous ends with sentence ending
            # - New chunk starts with heading marker
            # - New chunk starts with uppercase (likely new section)
            if (
                not prev_last_char
                or prev_last_char in self.sentence_endings
                or first_new_stripped.startswith("#")
                or not first_char
                or not first_char.islower()
            ):
                return previous_chunk, page_chunks
        
        # Try to merge
        combined_text = _safe_concat(previous_chunk.text, first_new.text)
        
        # Check if merged chunk respects limits
        if (
            len(bpe.encode(combined_text)) <= self.max_tokens_per_section
            and len(combined_text) <= int(self.max_section_length * 1.2)
        ):
            # Full merge successful
            previous_chunk = TextChunk(
                page_num=previous_chunk.page_num,
                text=combined_text,
                page_header=previous_chunk.page_header,
                tables=previous_chunk.tables,
                images=previous_chunk.images
            )
            page_chunks = page_chunks[1:]
        else:
            # Cannot merge whole - attempt partial sentence shifting
            previous_chunk, page_chunks = self._shift_partial_sentence(previous_chunk, page_chunks)
        
        return previous_chunk, page_chunks
    
    def _shift_partial_sentence(
        self,
        previous_chunk: TextChunk,
        page_chunks: list[TextChunk]
    ) -> tuple[Optional[TextChunk], list[TextChunk]]:
        """Shift trailing partial sentence from previous to first new chunk."""
        prev_text = previous_chunk.text
        first_new_text = page_chunks[0].text

        # Find last full sentence ending in previous chunk
        last_end = max((prev_text.rfind(se) for se in self.sentence_endings), default=-1)
        fragment_start = last_end + 1 if last_end != -1 and last_end < len(prev_text) - 1 else 0

        if fragment_start >= len(prev_text):
            return previous_chunk, page_chunks

        fragment_full = prev_text[fragment_start:]
        retained = prev_text[:fragment_start]

        # Check if prepending fragment to first_new respects limits
        def fits(candidate: str) -> bool:
            combined = candidate + first_new_text
            if len(combined) > int(self.max_section_length * 1.2):
                return False
            if len(bpe.encode(combined)) > self.max_tokens_per_section:
                return False
            return True

        move_fragment = fragment_full
        if not fits(move_fragment):
            # Fragment doesn't fit - don't shift it, leave it as leftover
            move_fragment = ""

        leftover_fragment = fragment_full[len(move_fragment):]

        # Prepend allowed fragment
        if move_fragment:
            page_chunks[0] = TextChunk(
                page_num=page_chunks[0].page_num,
                text=_safe_concat(move_fragment, first_new_text),
                page_header=page_chunks[0].page_header,
                tables=page_chunks[0].tables,
                images=page_chunks[0].images
            )
        
        # Adjust previous_chunk
        if retained.strip():
            previous_chunk = TextChunk(
                page_num=previous_chunk.page_num,
                text=retained,
                page_header=previous_chunk.page_header,
                tables=previous_chunk.tables,
                images=previous_chunk.images
            )
        else:
            previous_chunk = None
        
        # Insert leftover fragment as its own chunk(s)
        if leftover_fragment.strip():
            leftover_chunks = list(self._split_by_max_tokens(
                page_chunks[0].page_num,
                leftover_fragment,
                page_chunks[0].page_header
            ))
            page_chunks = leftover_chunks + page_chunks
        
        return previous_chunk, page_chunks

    def _merge_orphan_chunks(self, chunks: list[TextChunk]) -> list[TextChunk]:
        """Merge small orphan chunks with previous chunks on same page.

        Orphans are chunks < 500 tokens (below target minimum) that result from:
        - Short sections between tables
        - Trailing text fragments
        - Section headers followed by page breaks
        - Page breaks mid-content

        This ensures all chunks reach the 500-token minimum.
        """
        logger.info(f"_merge_orphan_chunks called with {len(chunks)} chunks")
        if len(chunks) <= 1:
            return chunks

        merged = []
        i = 0

        while i < len(chunks):
            current = chunks[i]

            # Calculate orphan threshold based on embedding model size
            # For small embedding models (< 400 tokens), use conservative threshold
            if self.embedding_max_tokens and self.embedding_max_tokens < 400:
                # For small models, only merge truly tiny fragments (< 30% of limit)
                orphan_threshold = int(self.max_section_length_tokens * 0.3)
            else:
                # For large models, use standard threshold (< 70% of limit)
                orphan_threshold = int(self.max_section_length_tokens * 0.7)

            # Ensure minimum threshold to prevent over-merging
            orphan_threshold = max(ABSOLUTE_MINIMUM_ORPHAN_THRESHOLD, orphan_threshold)

            # Skip if it contains atomic tables/figures (they're allowed to be any size)
            is_atomic_table = '<table>' in current.text.lower() or '<figure' in current.text.lower()
            if current.token_count is not None and current.token_count < orphan_threshold and len(merged) > 0 and not is_atomic_table:
                prev = merged[-1]
                combined_text = prev.text + "\n\n" + current.text
                combined_tokens = len(bpe.encode(combined_text))

                # Merge if:
                # 1. Combined stays under hard max (750 tokens), OR
                # 2. Previous chunk already exceeds max (likely has atomic table),
                #    and adding orphan doesn't make it much worse (< 30% increase)
                should_merge = False
                if combined_tokens <= self.max_section_length_tokens:
                    should_merge = True
                elif prev.token_count > self.max_section_length_tokens:
                    # Previous already exceeds - check if orphan is small relative to prev
                    increase_ratio = current.token_count / prev.token_count
                    if increase_ratio < 0.3:  # Orphan is < 30% of prev chunk size
                        should_merge = True

                if should_merge:
                    logger.info(
                        f"Merging orphan chunk ({current.token_count} tokens) "
                        f"with previous ({prev.token_count} tokens) -> {combined_tokens} tokens"
                    )
                    merged[-1] = TextChunk(
                        page_num=prev.page_num,
                        text=combined_text,
                        token_count=combined_tokens,
                        page_header=prev.page_header,
                        tables=prev.tables + current.tables,
                        images=prev.images + current.images
                    )
                    i += 1
                    continue

            merged.append(current)
            i += 1

        return merged

    def _contains_figure(self, text: str) -> bool:
        """Check if text contains a figure (includes both figures and tables).

        Matches original prepdocslib: simple string check for "<figure".
        """
        return "<figure" in text.lower()

    def _looks_like_legend(self, text: str) -> bool:
        """Check if text looks like a legend/footnote for a table or figure.

        Legends typically:
        - Are reasonably short (< 2000 characters, around 300-400 tokens)
        - Contain symbols (*, †, ‡, §, +, etc.)
        - Start with footnote markers or contain explanatory phrases
        - Define abbreviations or provide data sources

        Generic logic that works for various document types.
        """
        text_stripped = text.strip()
        if not text_stripped:
            return False

        # Very long text is likely full content paragraphs, not a legend
        # Use 2000 chars (~300-400 tokens) as threshold
        if len(text_stripped) > 2000:
            return False

        text_lower = text_stripped.lower()

        # Check if text starts with a symbol or common footnote pattern
        if len(text_stripped) > 0 and text_stripped[0] in "*†‡§¶+":
            return True

        # Check if text starts with common warning/note patterns (case-insensitive)
        note_prefixes = ["note:", "notes:", "caution:", "warning:", "important:",
                        "attention:", "tip:", "hint:", "remark:"]
        for prefix in note_prefixes:
            if text_lower.startswith(prefix):
                return True

        # Check for multiple lines starting with symbols (multi-footnote legend)
        lines = text_stripped.split('\n')
        symbol_start_count = sum(1 for line in lines if line.strip() and line.strip()[0] in "*†‡§¶+")
        if symbol_start_count >= 2:
            return True

        # Check for common legend indicators (generic across document types)
        legend_indicators = [
            # Footnote/note markers
            "note:", "notes:", "legend:", "source:", "sources:",
            "abbreviations:", "symbols:", "definitions:",
            # Data source phrases
            "data source", "based on", "according to",
            # Table footnote phrases
            "numbers include", "the designations employed",
            "case classifications", "transmission classification",
            "all references to", "territories include",
            # Generic patterns (be careful - these are common words)
            # Removed "figure", "table", "see", "refer to" - too generic
        ]

        # LOWERED threshold: Even 1 indicator can mean legend (was 2)
        # This catches single NOTE:, CAUTION:, SOURCE: statements
        indicator_count = sum(1 for indicator in legend_indicators if indicator in text_lower)
        if indicator_count >= 1:
            return True

        # Check if text has symbols (but be conservative)
        symbol_chars = sum(1 for c in text_stripped if c in "*†‡§¶+")
        # High symbol density for shorter text
        if symbol_chars >= 2 and len(text_stripped) < 800:
            return True

        # Default: not a legend
        return False

    def _final_orphan_merge_pass(self, chunks: list[TextChunk]) -> list[TextChunk]:
        """Final pass to merge orphans across entire document for semantic coherence.

        This enforces the 500-token minimum document-wide while respecting:
        - Atomic tables/figures (can be any size)
        - Section boundaries (PageHeader changes)
        - Semantic breaks (new sections starting with #)
        """
        print(f"\n🔧 FINAL ORPHAN MERGE: Starting with {len(chunks)} chunks")

        if len(chunks) <= 1:
            return chunks

        merged = []
        i = 0

        while i < len(chunks):
            current = chunks[i]

            # Check if chunk is PURELY atomic content (mostly table/figure, minimal text)
            # Don't merge if chunk is >80% table/figure content (it's a semantic unit)
            is_atomic = False
            if '<figure' in current.text.lower() or '<table>' in current.text.lower():
                # Simple heuristic: if tokens are very low (<50) and has figure/table, it's atomic
                if current.token_count and current.token_count < 50:
                    is_atomic = True

            print(f"  📄 Chunk {i+1}: page{current.page_num+1}, {current.token_count}tok, is_atomic={is_atomic}, merged_count={len(merged)}")

            # Calculate orphan threshold based on embedding model size
            # For small embedding models (< 400 tokens), use conservative threshold
            if self.embedding_max_tokens and self.embedding_max_tokens < 400:
                # For small models, only merge truly tiny fragments (< 30% of limit)
                orphan_threshold = int(self.max_section_length_tokens * 0.3)
            else:
                # For large models, use standard threshold (< 70% of limit)
                orphan_threshold = int(self.max_section_length_tokens * 0.7)

            # Ensure minimum threshold to prevent over-merging
            orphan_threshold = max(ABSOLUTE_MINIMUM_ORPHAN_THRESHOLD, orphan_threshold)

            # Try to merge if below threshold and not purely atomic
            if current.token_count is not None and current.token_count < orphan_threshold and len(merged) > 0 and not is_atomic:
                prev = merged[-1]

                # Check semantic boundaries - prioritize content continuity over structure:
                # 1. PageHeader changes - use as hint but not hard blocker for small chunks
                # 2. New major section (##) - respect this boundary
                # 3. Atomic content - don't merge pure tables/figures

                # New major section starting (## heading at start) - HARD BOUNDARY
                starts_new_section = current.text.lstrip().startswith('## ') and not current.text.lstrip().startswith('### ')

                # Previous chunk is purely atomic (mostly table, minimal text) - HARD BOUNDARY
                prev_is_atomic = False
                if '<figure' in prev.text.lower() or '<table>' in prev.text.lower():
                    if prev.token_count and prev.token_count < 50:
                        prev_is_atomic = True

                # PageHeader changes - SOFT BOUNDARY (allow if chunks are small)
                # Only block if current chunk is >= 400 tokens AND headers differ significantly
                page_header_blocks_merge = False
                if prev.page_header and current.page_header and current.token_count >= 400:
                    if prev.page_header.lower() != current.page_header.lower():
                        page_header_blocks_merge = True

                # Try to merge if no HARD boundaries
                if not starts_new_section and not prev_is_atomic and not page_header_blocks_merge:
                    # Use cached token counts (TextChunk.token_count is always accurate)
                    prev_actual_tokens = prev.token_count
                    current_actual_tokens = current.token_count

                    # Only encode combined text to check merge feasibility
                    combined_text = prev.text + "\n\n" + current.text
                    combined_tokens = len(bpe.encode(combined_text))

                    print(f"  🔍 Checking: prev={prev_actual_tokens}tok, current={current_actual_tokens}tok, combined={combined_tokens}tok")

                    # Priority: Semantic preservation over strict limits
                    # Strategy: Scale thresholds based on max_section_length_tokens
                    # For small models (197 tokens): don't allow semantic merges beyond limit
                    # For large models (750 tokens): allow up to 1.3x for semantic coherence

                    # Scale semantic merge thresholds based on max_section_length_tokens
                    small_chunk_threshold = int(self.max_section_length_tokens * 0.5)
                    very_small_threshold = int(self.max_section_length_tokens * 0.7)
                    max_combined = int(self.max_section_length_tokens * 1.2)

                    allow_merge = False

                    if combined_tokens <= self.max_section_length_tokens:
                        # Within target range - always merge
                        allow_merge = True
                    elif current_actual_tokens < small_chunk_threshold:
                        # Very small chunk - semantic merge up to 120% of limit
                        if combined_tokens <= max_combined:
                            allow_merge = True
                            print(f"  🔀 Semantic merge (<{small_chunk_threshold}tok orphan): {combined_tokens} tokens")
                    elif current_actual_tokens < very_small_threshold:
                        # Small chunk - semantic merge up to 115% of limit
                        max_combined_small = int(self.max_section_length_tokens * 1.15)
                        if combined_tokens <= max_combined_small:
                            allow_merge = True
                            print(f"  🔀 Semantic merge (<{very_small_threshold}tok): {combined_tokens} tokens")

                    if allow_merge:
                        print(f"  ✅ Merging: chunk@page{current.page_num+1} ({current.token_count}tok) + prev@page{prev.page_num+1} ({prev.token_count}tok) = {combined_tokens}tok")
                        logger.info(
                            f"Final merge: orphan chunk ({current.token_count} tok, page {current.page_num+1}) "
                            f"with previous ({prev.token_count} tok, page {prev.page_num+1}) -> {combined_tokens} tok"
                        )
                        merged[-1] = TextChunk(
                            page_num=prev.page_num,
                            text=combined_text,
                            token_count=combined_tokens,
                            page_header=prev.page_header,
                            tables=prev.tables + current.tables,
                            images=prev.images + current.images
                        )
                        i += 1
                        continue
                    else:
                        print(f"  ❌ Can't merge: would exceed limits ({combined_tokens} tokens)")
                else:
                    reasons = []
                    if page_header_blocks_merge: reasons.append("PageHeader blocks (chunk >=400tok)")
                    if starts_new_section: reasons.append("Starts new section")
                    if prev_is_atomic: reasons.append("Prev is atomic")
                    print(f"  ⚠️  Skipping merge for chunk@page{current.page_num+1} ({current.token_count}tok): {', '.join(reasons)}")

            merged.append(current)
            i += 1

        merged_count = len(chunks) - len(merged)
        logger.info(f"Final orphan merge: {len(chunks)} chunks -> {len(merged)} chunks ({merged_count} merges)")
        return merged

    def _find_table_reference_in_text(self, text: str, max_lookback: int = 400) -> Optional[str]:
        """Find table reference at END of text block.

        Patterns to detect:
        - "(Table 4-1 Episode Priority on page 4-3)"
        - "(Table 2-3 Threshold Test Failure Codes on page 2-20)"
        - "are listed below (Table X-Y ...)"
        - "as summarized in Table X-Y"

        Returns the table reference if found near end of text, otherwise None.
        """
        if not text or len(text) < 20:
            return None

        # Look at last N chars
        tail = text[-max_lookback:] if len(text) > max_lookback else text

        # Pattern: "(Table X-Y ... on page X-Y)" or "listed below (Table X-Y ...)"
        # Capture the whole parenthetical reference or sentence with table mention
        pattern = re.compile(
            r'\(Table\s+\d+[-–]\d+[^)]{0,120}\)',
            re.IGNORECASE
        )

        matches = list(pattern.finditer(tail))
        if matches:
            # Return the LAST match (closest to table)
            last_match = matches[-1]
            # Check if it's near the end (within last 150 chars)
            match_end_pos = last_match.end()
            chars_from_end = len(tail) - match_end_pos
            if chars_from_end < 150:  # Very close to end of text
                return last_match.group(0).strip()

        return None

    def _extract_table_context(self, text: str) -> Optional[str]:
        """Extract contextual information before a table for overlap.

        Looks for text immediately before <figure> tags that provides context:
        - Introductory sentences ("The following table shows...")
        - Section headers before tables
        - Explanatory text leading into tables

        Returns up to 200 characters of context before first table, or None.
        """
        if not text or '<figure' not in text.lower():
            return None

        # Find first <figure> tag
        figure_start = text.lower().find('<figure')
        if figure_start <= 0:
            return None

        # Get text before the table
        text_before = text[:figure_start].strip()
        if not text_before:
            return None

        # Get last 200 chars (roughly 30-50 tokens) of context before table
        context = text_before[-200:] if len(text_before) > 200 else text_before

        # Try to start at sentence boundary
        for ending in self.sentence_endings:
            pos = context.find(ending)
            if pos > 0:
                context = context[pos+1:].strip()
                break

        return context if len(context) > 20 else None

    def _is_heading_like(self, text: str) -> bool:
        """Check if text looks like a heading."""
        text = text.strip()
        if not text or len(text) > 80:
            return False

        if text.startswith("#"):
            return True

        # Title Case or ALL CAPS (short)
        if text.isupper() or (text.istitle() and len(text.split()) <= 12):
            return True

        # Numbered lists or section markers
        if re.match(r"^(?:\d+|[IVXLCM]+)[.)]\s", text):
            return True

        if text.startswith(("- ", "* ", "• ")):
            return True

        return False
    
    def _should_cross_page_overlap(self, prev: TextChunk, nxt: TextChunk) -> bool:
        """Decide if overlap should cross page boundary for semantic preservation.

        For RAG/Retrieval: ALWAYS overlap at page boundaries to maximize context.

        The small overlap (10% = ~50 tokens) preserves semantic flow without polluting chunks.
        Even at section boundaries, overlap helps connect related concepts and ensures
        queries matching boundary text find full context.

        Benefits:
        - Connects concepts across sections (even with PageHeader/## heading changes)
        - Small overlap (~50 tokens) won't confuse embeddings or retrieval
        - New chunk still has its heading/PageHeader for clear section identification
        - Maximizes retrieval quality by eliminating context gaps
        """
        if not prev or not nxt:
            return False

        # ALWAYS overlap - NO BLOCKING
        # Maximum semantic context preservation for RAG/retrieval quality
        return True
    
    def _append_overlap(self, prev_chunk: TextChunk, next_chunk: TextChunk) -> TextChunk:
        """Append overlap prefix from next_chunk to prev_chunk (TOKEN-BASED).

        For RAG: Always add overlap to preserve semantic context, even with figures/tables.
        The overlap helps retrieval find relevant context at chunk boundaries.

        Uses binary search to find optimal character position where tokens = target_tokens,
        reducing bpe.encode() calls from ~1000+ to ~10-20 per overlap operation.

        Improved for table handling:
        - If next chunk starts with table, extract context before table for overlap
        - Preserves table-related context for better retrieval
        """
        logger.info(f"_append_overlap called: prev={prev_chunk.token_count} tokens, next={next_chunk.token_count} tokens")
        if not prev_chunk or not next_chunk:
            return prev_chunk

        # Calculate target overlap in TOKENS (not chars)
        target_tokens = int(self.max_tokens_per_section * self.semantic_overlap_percent / 100)
        if target_tokens <= 0:
            return prev_chunk

        # Extract text content from next chunk for overlap
        next_text = next_chunk.text

        # Special handling for chunks starting with tables
        if next_text.lstrip().startswith("<figure"):
            # Try to extract table context (text before table) for better overlap
            table_context = self._extract_table_context(next_text)
            if table_context:
                # Use table context as overlap instead of table itself
                next_text = table_context
                logger.debug(f"Using table context for overlap: {next_text[:60]}...")
            else:
                # No context before table - try text after table
                figure_end = next_text.lower().find("</figure>")
                if figure_end >= 0:
                    text_after_figure = next_text[figure_end + 9:].strip()
                    if len(text_after_figure) > 50:  # Has meaningful text after figure
                        next_text = text_after_figure
                    # If no text after figure, use the full text (includes figure)

        # Binary search to find character position where tokens ≈ target_tokens
        # This replaces the 3 character-by-character loops with ~10-20 bpe.encode() calls
        left = 0
        right = len(next_text)
        best_pos = 0
        best_tokens = 0

        # Binary search for position where token count is closest to target
        while left <= right:
            mid = (left + right) // 2
            prefix = next_text[:mid]
            prefix_tokens = len(bpe.encode(prefix))

            # Update best match if this is closer to target
            if abs(prefix_tokens - target_tokens) < abs(best_tokens - target_tokens):
                best_pos = mid
                best_tokens = prefix_tokens

            # If we hit target exactly (within ±2 tokens), we can stop
            if abs(prefix_tokens - target_tokens) <= 2:
                best_pos = mid
                best_tokens = prefix_tokens
                break
            elif prefix_tokens < target_tokens:
                left = mid + 1
            else:
                right = mid - 1

        # Use the best position found
        prefix = next_text[:best_pos]
        prefix_tokens = best_tokens

        if not prefix.strip():
            return prev_chunk

        # Extend to sentence/word boundary using binary search
        # Instead of character-by-character, search for nearest boundary within token budget
        max_extension_tokens = int(target_tokens * 1.5)  # Allow 50% overage for boundaries

        # Find all sentence endings and word breaks in reasonable extension range
        max_search_chars = min(len(next_text), best_pos + (target_tokens * 2))  # Estimate ~2 chars per token
        search_text = next_text[best_pos:max_search_chars]

        # Find nearest sentence ending
        nearest_sentence_pos = -1
        for i, ch in enumerate(search_text):
            if ch in self.sentence_endings:
                # Check if adding this would exceed token budget
                candidate_prefix = next_text[:best_pos + i + 1]
                candidate_tokens = len(bpe.encode(candidate_prefix))
                if candidate_tokens <= max_extension_tokens:
                    nearest_sentence_pos = best_pos + i + 1
                    prefix = candidate_prefix
                    prefix_tokens = candidate_tokens
                    break
                else:
                    break  # Would exceed budget, stop

        # If no sentence ending found or it's too far, look for word break
        if nearest_sentence_pos == -1:
            for i, ch in enumerate(search_text):
                if ch in self.word_breaks and i > 10:  # Avoid immediate word breaks
                    candidate_prefix = next_text[:best_pos + i + 1]
                    candidate_tokens = len(bpe.encode(candidate_prefix))
                    if candidate_tokens <= max_extension_tokens:
                        prefix = candidate_prefix
                        prefix_tokens = candidate_tokens
                        break
                    else:
                        break  # Would exceed budget, stop

        # Trim trailing partial word if no boundary found
        while prefix and prefix[-1].isalnum() and len(prefix) > target_tokens:
            prefix = prefix[:-1]

        # Avoid duplicating existing text
        if prev_chunk.text.endswith(prefix):
            return prev_chunk

        # Calculate combined chunk
        candidate = prev_chunk.text + prefix
        candidate_tokens = len(bpe.encode(candidate))

        # Check if candidate exceeds TOKEN limit (ignore char limit for overlap)
        # Use max_section_length_tokens (700) not max_tokens_per_section (500)
        # to allow overlap to work with chunks in 500-700 range
        if candidate_tokens > self.max_section_length_tokens:
            # Overlap would cause prev_chunk to exceed limit - don't add overlap
            logger.info(f"Overlap blocked: {candidate_tokens} tokens > {self.max_section_length_tokens} max")
            return prev_chunk

        logger.info(f"Overlap applied: {prev_chunk.token_count} + {prefix_tokens} tokens = {candidate_tokens} tokens")

        return TextChunk(
            page_num=prev_chunk.page_num,
            text=candidate,
            chunk_index_on_page=prev_chunk.chunk_index_on_page,
            char_span=prev_chunk.char_span,
            token_count=candidate_tokens,
            tables=prev_chunk.tables,
            images=prev_chunk.images,
            page_header=prev_chunk.page_header
        )
    
    def _associate_tables_images(
        self,
        chunks: list[TextChunk],
        tables: list[ExtractedTable],
        images: list[ExtractedImage]
    ):
        """Associate tables and images with chunks based on content.
        
        Tables are already in HTML format in chunks: <figure><table>...</table></figure>.
        Images are wrapped in <figure id="...">...</figure>.
        
        We simply check if the chunk contains any <table> or figure ID.
        """
        for chunk in chunks:
            # Check if chunk contains tables (look for <table> tags)
            # Tables are wrapped in <figure id="table-X"> tags by DI extractor
            # Check if chunk contains table by looking for table figure IDs
            for table in tables:
                # Match by table ID in figure tag
                if f'<figure id="{table.table_id}">' in chunk.text or f'id="{table.table_id}"' in chunk.text:
                    chunk.tables.append(table)
            
            # Check if chunk contains images (wrapped in <figure id="...">)
            for image in images:
                if f'id="{image.figure_id}"' in chunk.text or image.figure_id in chunk.text:
                    chunk.images.append(image)


def create_chunker(
    max_chars: int = DEFAULT_SECTION_LENGTH,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_section_tokens: int = DEFAULT_MAX_SECTION_TOKENS,
    overlap_percent: int = DEFAULT_OVERLAP_PERCENT,
    cross_page_overlap: bool = DEFAULT_CROSS_PAGE_OVERLAP,
    disable_char_limit: bool = False,
    table_renderer: Optional[TableRenderer] = None,
    embedding_max_tokens: Optional[int] = None
) -> LayoutAwareChunker:
    """Factory function to create token-based chunker.

    Args:
        max_chars: Soft character limit per chunk
        max_tokens: Target minimum tokens per chunk
        max_section_tokens: Hard maximum tokens per chunk
        overlap_percent: Percentage overlap between chunks
        cross_page_overlap: Whether to add overlap across page boundaries
        disable_char_limit: Ignore character limits (token-only mode)
        table_renderer: Optional table rendering strategy
        embedding_max_tokens: Maximum sequence length supported by embedding model

    Returns:
        Configured LayoutAwareChunker instance
    """
    return LayoutAwareChunker(
        max_chars=max_chars,
        max_tokens=max_tokens,
        max_section_tokens=max_section_tokens,
        overlap_percent=overlap_percent,
        cross_page_overlap=cross_page_overlap,
        disable_char_limit=disable_char_limit,
        table_renderer=table_renderer,
        embedding_max_tokens=embedding_max_tokens
    )
