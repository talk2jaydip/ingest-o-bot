"""Azure Document Intelligence extraction with batching, concurrency controls, and retry logic."""

import asyncio
import io
import uuid
from typing import Optional

import pymupdf
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    DocumentFigure,
    DocumentTable,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceRequestError, HttpResponseError
from azure.identity.aio import DefaultAzureCredential
from PIL import Image
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .config import DocumentIntelligenceConfig
from .logging_utils import get_logger

logger = get_logger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
RETRY_MIN_WAIT = 5
RETRY_MAX_WAIT = 30


class ExtractedImage:
    """Represents an extracted image/figure from a document."""
    
    def __init__(
        self,
        figure_id: str,
        page_num: int,
        bbox: tuple[float, float, float, float],
        image_bytes: bytes,
        filename: str,
        title: str = "",
        placeholder: str = "",
        mime_type: str = "image/png"
    ):
        self.figure_id = figure_id
        self.page_num = page_num
        self.bbox = bbox
        self.image_bytes = image_bytes
        self.filename = filename
        self.title = title
        self.placeholder = placeholder or f'<figure id="{figure_id}"></figure>'
        self.mime_type = mime_type
        self.description: Optional[str] = None  # Set later by media describer
        self.url: Optional[str] = None  # Set later when uploaded


class ExtractedTable:
    """Represents an extracted table from a document."""
    
    def __init__(
        self,
        table_id: str,
        di_table_index: int,
        page_nums: list[int],
        cells: list[dict],
        row_count: int,
        column_count: int,
        bbox: Optional[tuple[float, float, float, float]] = None,
        caption: Optional[str] = None
    ):
        self.table_id = table_id
        # Index into AnalyzeResult.tables for retrieving the correct spans.
        # This avoids heuristics like matching by row_count which can mask the wrong region.
        self.di_table_index = di_table_index
        self.page_nums = page_nums
        self.cells = cells
        self.row_count = row_count
        self.column_count = column_count
        self.bbox = bbox
        self.caption = caption  # Figure/table caption from DI (e.g., "Figure 3. LIR snippet...")
        self.rendered_text: Optional[str] = None  # Set later by table renderer
        self.summary: Optional[str] = None  # Optionally set by GPT-4o


class PageHyperlink:
    """Represents a hyperlink found in a PDF page."""

    def __init__(
        self,
        page_num: int,
        bbox: tuple[float, float, float, float],
        url: str,
        link_text: str = ""
    ):
        self.page_num = page_num
        self.bbox = bbox
        self.url = url
        self.link_text = link_text


class ExtractedPage:
    """Represents an extracted page with text, tables, and figures."""

    def __init__(
        self,
        page_num: int,
        text: str,
        tables: list[ExtractedTable],
        images: list[ExtractedImage],
        hyperlinks: list[PageHyperlink] = None,
        offset: int = 0
    ):
        self.page_num = page_num
        self.text = text
        self.tables = tables
        self.images = images
        self.hyperlinks = hyperlinks or []
        self.offset = offset


class DocumentIntelligenceExtractor:
    """Extracts content from PDFs using Azure Document Intelligence."""
    
    def __init__(self, config: DocumentIntelligenceConfig, table_renderer=None, max_figure_concurrency: int = 5):
        self.config = config
        self.table_renderer = table_renderer  # Optional: for rendering tables in extractor
        self.max_figure_concurrency = max_figure_concurrency
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._di_client: Optional[DocumentIntelligenceClient] = None
        self._credential = None
    
    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrency)
        return self._semaphore

    def _get_di_client(self) -> DocumentIntelligenceClient:
        """Get or create persistent Document Intelligence client."""
        if self._di_client is None:
            # Create credential once
            if self._credential is None:
                if hasattr(self.config, 'use_managed_identity') and self.config.use_managed_identity:
                    self._credential = DefaultAzureCredential()
                else:
                    self._credential = AzureKeyCredential(self.config.key) if self.config.key else None

            # Create persistent client
            self._di_client = DocumentIntelligenceClient(
                endpoint=self.config.endpoint,
                credential=self._credential
            )
            logger.info("Created persistent DocumentIntelligenceClient")

        return self._di_client

    async def close(self):
        """Close Document Intelligence client and release resources."""
        if self._di_client:
            await self._di_client.close()
            self._di_client = None
            logger.info("Closed DocumentIntelligenceClient")

        # Close managed identity credential if it exists
        if self._credential and hasattr(self._credential, 'close'):
            await self._credential.close()
            self._credential = None

    def _before_retry_sleep(self, retry_state):
        """Log retry attempts."""
        logger.info(
            f"Document Intelligence request failed (attempt {retry_state.attempt_number}/{DEFAULT_MAX_RETRIES}), "
            f"sleeping before retrying..."
        )
    
    async def extract_document(
        self,
        pdf_bytes: bytes,
        filename: str,
        process_figures: bool = True
    ) -> list[ExtractedPage]:
        """Extract pages, tables, and figures from a PDF document.
        
        Includes retry logic with up to 3 attempts for transient failures.
        """
        semaphore = self._get_semaphore()
        
        async with semaphore:
            logger.info(f"Extracting content from {filename} using Azure Document Intelligence")

            # Use persistent client
            di_client = self._get_di_client()

            analyze_result: Optional[AnalyzeResult] = None

            # Start analysis with retry logic
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type((ServiceRequestError, HttpResponseError)),
                wait=wait_random_exponential(min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
                stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
                before_sleep=self._before_retry_sleep
            ):
                with attempt:
                    if process_figures:
                        try:
                            poller = await di_client.begin_analyze_document(
                                model_id="prebuilt-layout",
                                body=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
                                output=["figures"],
                                features=["ocrHighResolution"],
                                output_content_format="markdown"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to analyze with figures: {e}. Retrying without figures.")
                            process_figures = False
                            raise  # Trigger retry

                    if not process_figures:
                        poller = await di_client.begin_analyze_document(
                            model_id="prebuilt-layout",
                            body=AnalyzeDocumentRequest(bytes_source=pdf_bytes)
                        )

                    analyze_result = await poller.result()
            
            # Parse results
            pages = await self._parse_analyze_result(
                analyze_result,
                pdf_bytes if process_figures else None,
                filename
            )
            
            logger.info(f"Extracted {len(pages)} pages from {filename}")
            return pages
    
    async def _parse_analyze_result(
        self,
        result: AnalyzeResult,
        pdf_bytes: Optional[bytes],
        filename: str
    ) -> list[ExtractedPage]:
        """Parse DI analyze result into ExtractedPage objects."""
        pages = []

        # Open PDF with PyMuPDF if we need to crop figures or extract hyperlinks
        doc_for_pymupdf = None
        if pdf_bytes:
            doc_for_pymupdf = pymupdf.open(stream=io.BytesIO(pdf_bytes))

        # Extract hyperlinks from all pages using PyMuPDF
        all_hyperlinks = []
        if doc_for_pymupdf:
            all_hyperlinks = self._extract_hyperlinks(doc_for_pymupdf)

        # Extract tables
        all_tables = []
        if result.tables:
            for table_idx, table in enumerate(result.tables):
                extracted_table = self._extract_table(table, table_idx)
                all_tables.append(extracted_table)

            # Apply header carry-forward for multi-page table continuations
            all_tables = self._apply_header_carryforward(all_tables)
        
        # Extract figures in parallel
        all_figures = []
        if result.figures and doc_for_pymupdf:
            # Collect all figure extraction tasks
            figure_tasks = [
                self._extract_figure(figure, idx, doc_for_pymupdf)
                for idx, figure in enumerate(result.figures)
            ]

            # Extract all figures in parallel with controlled concurrency
            if figure_tasks:
                logger.info(f"Extracting {len(figure_tasks)} figures in parallel (max concurrency: {self.max_figure_concurrency})")
                figure_semaphore = asyncio.Semaphore(self.max_figure_concurrency)

                async def extract_with_semaphore(task):
                    async with figure_semaphore:
                        return await task

                extracted_figures = await asyncio.gather(*[
                    extract_with_semaphore(task) for task in figure_tasks
                ], return_exceptions=True)

                # Filter out exceptions and collect successfully extracted figures
                for idx, result_item in enumerate(extracted_figures):
                    if isinstance(result_item, Exception):
                        logger.error(f"Error extracting figure {idx}: {result_item}")
                    else:
                        all_figures.append(result_item)
        
        # Process each page
        offset = 0
        for page in result.pages:
            page_num = page.page_number - 1  # Convert to 0-indexed

            # Get tables on this page
            tables_on_page = [
                t for t in all_tables
                if page_num in t.page_nums
            ]

            # Get figures on this page
            figures_on_page = [
                f for f in all_figures
                if f.page_num == page_num
            ]

            # Get hyperlinks on this page
            hyperlinks_on_page = [
                h for h in all_hyperlinks
                if h.page_num == page_num
            ]

            # Build page text with tables, figures, and hyperlinks inserted
            page_text = self._build_page_text(
                result,
                page,
                tables_on_page,
                figures_on_page,
                hyperlinks_on_page
            )

            extracted_page = ExtractedPage(
                page_num=page_num,
                text=page_text,
                tables=tables_on_page,
                images=figures_on_page,
                hyperlinks=hyperlinks_on_page,
                offset=offset
            )

            pages.append(extracted_page)
            offset += len(page_text)
        
        if doc_for_pymupdf:
            doc_for_pymupdf.close()
        
        return pages
    
    def _extract_table(self, table: DocumentTable, table_idx: int) -> ExtractedTable:
        """Extract table structure from DI result."""
        table_id = f"table_{table_idx}"
        
        # Get page numbers
        page_nums = []
        if table.bounding_regions:
            page_nums = [r.page_number - 1 for r in table.bounding_regions]
        
        # Extract cells
        cells = []
        for cell in table.cells:
            cells.append({
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                "row_span": cell.row_span if cell.row_span else 1,
                "column_span": cell.column_span if cell.column_span else 1,
                "content": cell.content,
                "kind": cell.kind if cell.kind else "content"
            })
        
        # Get bounding box (from first region)
        bbox = None
        if table.bounding_regions and table.bounding_regions[0].polygon:
            poly = table.bounding_regions[0].polygon
            bbox = (poly[0], poly[1], poly[4], poly[5])

        # Extract caption if present (e.g., "Figure 3. LIR snippet for sample program...")
        caption = None
        if hasattr(table, 'caption') and table.caption:
            if hasattr(table.caption, 'content'):
                caption = table.caption.content
            else:
                # In case caption is already a string
                caption = str(table.caption)

        return ExtractedTable(
            table_id=table_id,
            di_table_index=table_idx,
            page_nums=page_nums,
            cells=cells,
            row_count=table.row_count,
            column_count=table.column_count,
            bbox=bbox,
            caption=caption
        )

    def _apply_header_carryforward(self, tables: list[ExtractedTable]) -> list[ExtractedTable]:
        """Apply header carry-forward logic for multi-page table continuations.

        When Document Intelligence splits a multi-page table into separate table objects,
        only the first table has headers. This method detects continuations and copies
        headers from the first table to subsequent pages.

        Detection criteria:
        - Tables on consecutive pages
        - Same column count
        - Current table's first row contains data (not headers) based on content analysis
        """
        if len(tables) <= 1:
            return tables

        for i in range(1, len(tables)):
            current_table = tables[i]
            previous_table = tables[i - 1]

            # Check if this is a continuation:
            # 1. Same column count
            if current_table.column_count != previous_table.column_count:
                continue

            # 2. Consecutive pages (or at least close pages)
            if not current_table.page_nums or not previous_table.page_nums:
                continue

            current_page = min(current_table.page_nums)
            previous_page = max(previous_table.page_nums)

            # Allow 1 page gap for tables that might have content between them
            if current_page - previous_page > 2:
                continue

            # 3. Analyze row content to determine if it's a header or data
            # DI often mismarks data rows as headers, so we check content
            first_row_cells = [c for c in current_table.cells if c["row_index"] == 0]
            if not first_row_cells:
                continue

            prev_first_row = [c for c in previous_table.cells if c["row_index"] == 0]
            if not prev_first_row:
                continue

            # Check if previous table's first row looks like headers
            prev_looks_like_headers = self._row_looks_like_headers(prev_first_row)

            # Check if current table's first row looks like headers or data
            current_looks_like_headers = self._row_looks_like_headers(first_row_cells)

            # Only apply header carry-forward if:
            # - Previous table has headers
            # - Current table does NOT have headers (has data instead)
            if not prev_looks_like_headers or current_looks_like_headers:
                continue

            # This is a continuation! Copy headers from previous table
            logger.info(
                f"Detected table continuation: {current_table.table_id} on page {current_page} "
                f"continues from {previous_table.table_id} on page {previous_page}"
            )

            # Extract header cells from previous table
            header_cells = [c.copy() for c in prev_first_row]

            # Shift all current table cells down by 1 row
            for cell in current_table.cells:
                cell["row_index"] += 1

            # Insert headers as row 0
            for header_cell in header_cells:
                new_header = header_cell.copy()
                new_header["row_index"] = 0
                current_table.cells.insert(header_cell["column_index"], new_header)

            # Update row count
            current_table.row_count += 1

            logger.debug(
                f"Added {len(header_cells)} header cells to {current_table.table_id}, "
                f"new row count: {current_table.row_count}"
            )

        return tables

    def _row_looks_like_headers(self, row_cells: list[dict]) -> bool:
        """Determine if a row looks like headers based on content analysis.

        Headers typically:
        - Contain descriptive text (not primarily numbers)
        - Have longer text content
        - Don't look like country names or short identifiers

        Data rows typically:
        - Contain numbers, especially in multiple columns
        - Are shorter
        - Look like country names or identifiers
        """
        if not row_cells:
            return False

        # Count cells that are primarily numeric
        numeric_count = 0
        text_cells = []

        for cell in row_cells:
            content = cell["content"].strip()
            if not content:
                continue

            # Check if cell is primarily numeric (numbers, commas, decimals)
            numeric_chars = sum(c.isdigit() or c in ",.%" for c in content)
            if numeric_chars > len(content) * 0.5:  # More than 50% numeric
                numeric_count += 1
            else:
                text_cells.append(content)

        # If more than half the cells are numeric, it's likely a data row
        non_empty_cells = len([c for c in row_cells if c["content"].strip()])
        if numeric_count > non_empty_cells // 2:
            return False

        # Check text content - headers typically have longer, descriptive text
        if text_cells:
            avg_length = sum(len(t) for t in text_cells) / len(text_cells)
            # Headers usually have longer text (> 15 chars average)
            # Data rows often have short country/region names (< 15 chars average)
            if avg_length < 15:
                return False

            # Check if first text cell looks like a header
            first_text = text_cells[0].lower()
            # Headers often contain these words
            header_indicators = ["total", "country", "region", "territory", "area", "name", "type",
                                "classification", "status", "date", "number", "count", "days"]
            if any(indicator in first_text for indicator in header_indicators):
                return True

            # If first text is very long (> 30 chars), likely a header
            if len(text_cells[0]) > 30:
                return True

        # Default to treating it as headers if we can't determine
        # (conservative approach - better to have duplicate headers than missing them)
        return True

    async def _extract_figure(
        self,
        figure: DocumentFigure,
        figure_idx: int,
        doc: pymupdf.Document
    ) -> ExtractedImage:
        """Extract and crop figure from PDF."""
        figure_id = figure.id or f"fig_{uuid.uuid4().hex[:8]}"
        figure_title = (figure.caption and figure.caption.content) or ""
        figure_filename = f"figure{figure_id.replace('.', '_')}.png"
        placeholder = f'<figure id="{figure_id}"></figure>'
        
        if not figure.bounding_regions:
            return ExtractedImage(
                figure_id=figure_id,
                page_num=0,
                bbox=(0, 0, 0, 0),
                image_bytes=b"",
                filename=figure_filename,
                title=figure_title,
                placeholder=placeholder
            )
        
        if len(figure.bounding_regions) > 1:
            logger.warning(f"Figure {figure_id} has multiple regions, using first")
        
        first_region = figure.bounding_regions[0]
        bbox_inches = (
            first_region.polygon[0],
            first_region.polygon[1],
            first_region.polygon[4],
            first_region.polygon[5],
        )
        page_number = first_region.page_number - 1  # 0-indexed
        
        # Crop image from PDF
        cropped_img, bbox_pixels = self._crop_image_from_pdf(
            doc, page_number, bbox_inches
        )
        
        return ExtractedImage(
            figure_id=figure_id,
            page_num=page_number,
            bbox=bbox_pixels,
            image_bytes=cropped_img,
            filename=figure_filename,
            title=figure_title,
            placeholder=placeholder
        )
    
    def _extract_hyperlinks(self, doc: pymupdf.Document) -> list[PageHyperlink]:
        """Extract hyperlinks from PDF using PyMuPDF.

        Returns a list of PageHyperlink objects with URL and bounding box information.
        """
        hyperlinks = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Get links from the page
            links = page.get_links()

            for link in links:
                # Get link rectangle/bbox
                rect = link.get("from", pymupdf.Rect())
                bbox = (rect.x0, rect.y0, rect.x1, rect.y1)

                # Get URL - can be external (uri) or internal (page reference)
                url = link.get("uri", "")

                if not url:
                    # Internal link to another page
                    if "page" in link:
                        url = f"#page-{link['page'] + 1}"

                if url:
                    # Try to extract text within the link bbox
                    link_text = ""
                    try:
                        words = page.get_text("words", clip=rect)
                        if words:
                            # Combine words within the bbox
                            link_text = " ".join(word[4] for word in words)
                    except Exception as e:
                        logger.debug(f"Could not extract link text: {e}")

                    hyperlink = PageHyperlink(
                        page_num=page_num,
                        bbox=bbox,
                        url=url,
                        link_text=link_text
                    )
                    hyperlinks.append(hyperlink)

        logger.info(f"Extracted {len(hyperlinks)} hyperlinks from PDF")
        return hyperlinks

    @staticmethod
    def _crop_image_from_pdf(
        doc: pymupdf.Document,
        page_number: int,
        bbox_inches: tuple[float, float, float, float]
    ) -> tuple[bytes, tuple[float, float, float, float]]:
        """Crop image region from PDF page."""
        bbox_dpi = 72
        x0, y0, x1, y1 = (round(x * bbox_dpi, 2) for x in bbox_inches)
        bbox_pixels = (x0, y0, x1, y1)
        rect = pymupdf.Rect(bbox_pixels)

        page_dpi = 300
        page = doc.load_page(page_number)

        # Get page boundaries and clip the rect to ensure it doesn't extend outside
        page_rect = page.rect
        clipped_rect = rect & page_rect  # Intersection of rect and page_rect

        # If the intersection is empty, log a warning and use a minimal valid rect
        if clipped_rect.is_empty or clipped_rect.is_infinite:
            logger.warning(
                f"Figure bbox {bbox_pixels} is outside page {page_number} bounds {tuple(page_rect)}. "
                f"Using page center as fallback."
            )
            # Use a small rect at page center as fallback
            center_x = (page_rect.x0 + page_rect.x1) / 2
            center_y = (page_rect.y0 + page_rect.y1) / 2
            clipped_rect = pymupdf.Rect(center_x - 50, center_y - 50, center_x + 50, center_y + 50)

        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(page_dpi / bbox_dpi, page_dpi / bbox_dpi),
            clip=clipped_rect
        )

        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        bytes_io = io.BytesIO()
        img.save(bytes_io, format="PNG")
        return bytes_io.getvalue(), tuple(clipped_rect)
    
    def _build_page_text(
        self,
        result: AnalyzeResult,
        page,
        tables_on_page: list[ExtractedTable],
        figures_on_page: list[ExtractedImage],
        hyperlinks_on_page: list[PageHyperlink] = None
    ) -> str:
        """Build page text with tables, figures, and hyperlinks inserted."""
        if hyperlinks_on_page is None:
            hyperlinks_on_page = []

        page_offset = page.spans[0].offset
        page_length = page.spans[0].length
        
        # Create mask for which characters belong to tables/figures
        mask_chars = [None] * page_length
        
        def find_table_tag_range_in_span(content: str, span_offset: int, span_length: int) -> tuple[int, int]:
            """Return absolute (start, end) indices of the <table>...</table> inside a DI span.
            
            DI table spans sometimes include additional text after </table> (e.g. footnotes).
            We must only mask the actual <table>...</table> region so trailing text is preserved.
            
            If we can't find tags, fall back to masking the entire span.
            """
            span_start = span_offset
            span_end = span_offset + span_length
            span_text = content[span_start:span_end]
            lower = span_text.lower()
            table_start_rel = lower.find("<table")
            if table_start_rel == -1:
                return span_start, span_end
            table_end_rel = lower.find("</table>", table_start_rel)
            if table_end_rel == -1:
                return span_start, span_end
            table_end_rel += len("</table>")
            return span_start + table_start_rel, span_start + table_end_rel
        
        # Mark table positions
        for table_idx, table in enumerate(tables_on_page):
            if not result.tables:
                continue
            if table.di_table_index < 0 or table.di_table_index >= len(result.tables):
                continue
            
            result_table = result.tables[table.di_table_index]
            for span in (result_table.spans or []):
                abs_start, abs_end = find_table_tag_range_in_span(result.content, span.offset, span.length)
                for abs_i in range(abs_start, abs_end):
                    idx = abs_i - page_offset
                    if 0 <= idx < page_length:
                        mask_chars[idx] = ("table", table_idx)
        
        # Mark figure positions
        for figure_idx, figure in enumerate(figures_on_page):
            # Find the figure in result.figures
            if result.figures:
                for result_figure in result.figures:
                    if result_figure.id == figure.figure_id or (
                        result_figure.bounding_regions and
                        result_figure.bounding_regions[0].page_number - 1 == figure.page_num
                    ):
                        for span in result_figure.spans:
                            for i in range(span.length):
                                idx = span.offset - page_offset + i
                                if 0 <= idx < page_length:
                                    mask_chars[idx] = ("figure", figure_idx)
        
        # Build text with placeholders
        page_text = ""
        added_objects = set()
        
        for idx, mask_char in enumerate(mask_chars):
            if mask_char is None:
                page_text += result.content[page_offset + idx]
            elif mask_char not in added_objects:
                obj_type, obj_idx = mask_char
                if obj_type == "table":
                    # Render table based on configured mode, wrapped in <figure> tags for atomic chunking
                    table = tables_on_page[obj_idx]
                    if self.table_renderer:
                        # Use configured renderer (supports HTML, PLAIN, MARKDOWN)
                        rendered = self.table_renderer.render(table)
                        # Wrap in <figure> tags so chunker treats as atomic block
                        page_text += f'<figure id="{table.table_id}">\n{rendered}\n</figure>'
                    else:
                        # Fallback: use placeholder (will be rendered in chunker)
                        page_text += f'<table id="{table.table_id}"></table>'
                elif obj_type == "figure":
                    page_text += figures_on_page[obj_idx].placeholder
                added_objects.add(mask_char)
        
        # Apply hyperlinks by replacing text with markdown links
        page_text = self._apply_hyperlinks(page, page_text, hyperlinks_on_page)

        # Extract and preserve URLs from PageFooter comments
        page_text = self._preserve_pagefooter_urls(page_text)

        # Clean up
        page_text = page_text.replace("<!-- PageBreak -->", "")
        page_text = page_text.strip()

        return page_text

    def _apply_hyperlinks(
        self,
        page,
        page_text: str,
        hyperlinks: list[PageHyperlink]
    ) -> str:
        """Apply hyperlinks to page text by replacing text with markdown links.

        Uses the link_text extracted by PyMuPDF from the link bbox.
        Handles multi-line links by merging consecutive links with the same URL.
        """
        if not hyperlinks:
            return page_text

        # Group links by URL to handle multi-line links
        # Multi-line links often get split but point to the same URL
        from collections import defaultdict
        links_by_url = defaultdict(list)
        for hyperlink in hyperlinks:
            links_by_url[hyperlink.url].append(hyperlink)

        # Merge links with the same URL
        merged_hyperlinks = []
        for url, link_group in links_by_url.items():
            if len(link_group) == 1:
                # Single link, no merging needed
                merged_hyperlinks.append(link_group[0])
            else:
                # Multiple links with same URL - merge them
                merged_text = " ".join(link.link_text.strip() for link in link_group)
                merged = PageHyperlink(
                    page_num=link_group[0].page_num,
                    bbox=link_group[0].bbox,
                    url=url,
                    link_text=merged_text
                )
                merged_hyperlinks.append(merged)
                logger.info(f"Merged {len(link_group)} links for URL {url[:50]}... merged_text='{merged_text}'")

        # Build replacements list
        link_replacements = []

        for hyperlink in merged_hyperlinks:
            # Use the link_text that was extracted from the PDF
            link_text = hyperlink.link_text.strip()

            if not link_text:
                logger.debug(f"Skipping hyperlink with no text: {hyperlink.url}")
                continue

            # Strip leading/trailing quotes that might be part of the bbox but not the link
            # Be careful to preserve punctuation after closing quotes (e.g., "text".)
            link_text_cleaned = link_text.lstrip('\'"''""').rstrip('\'"''""')

            # Create markdown link with cleaned text
            markdown_link = f"[{link_text_cleaned}]({hyperlink.url})"

            # Try to find the text in page_text
            if link_text_cleaned in page_text:
                link_replacements.append((link_text_cleaned, markdown_link))
            elif link_text in page_text:
                # Use original if it matches better
                markdown_link = f"[{link_text}]({hyperlink.url})"
                link_replacements.append((link_text, markdown_link))
            else:
                # Try with flexible whitespace (for multi-line links)
                import re
                # Replace spaces with \s+ to match any whitespace including newlines
                flexible_pattern = re.escape(link_text_cleaned).replace(r'\ ', r'\s+')
                match = re.search(flexible_pattern, page_text, re.MULTILINE)
                if match:
                    original_multiline = match.group()
                    markdown_multiline = f"[{original_multiline}]({hyperlink.url})"
                    link_replacements.append((original_multiline, markdown_multiline))
                    logger.debug(f"Found multi-line link: '{original_multiline}' -> '{hyperlink.url}'")
                else:
                    # Try without trailing punctuation
                    link_text_no_punct = link_text_cleaned.rstrip('.,;:!?')
                    if link_text_no_punct in page_text:
                        # Find the text with its original punctuation in the page
                        pattern = re.escape(link_text_no_punct) + r'[.,;:!?]?'
                        match = re.search(pattern, page_text)
                        if match:
                            original_with_punct = match.group()
                            markdown_with_punct = f"[{original_with_punct}]({hyperlink.url})"
                            link_replacements.append((original_with_punct, markdown_with_punct))
                    else:
                        logger.debug(f"Could not find link text in page: '{link_text}' (cleaned: '{link_text_cleaned}')")

        # Apply replacements carefully to avoid double-linking
        # When multiple links have the same text (e.g., multiple "here."), we need to replace them
        # one at a time, ensuring we don't replace text that's already inside markdown brackets
        for original_text, markdown_link in link_replacements:
            # Find the first occurrence that's NOT already inside a markdown link
            import re
            # Pattern to match the original text not preceded by '[' and not followed by ']('
            # This prevents replacing text that's already been made into a link
            escaped_text = re.escape(original_text)
            pattern = f'(?<!\\[){escaped_text}(?!\\]\\()'

            match = re.search(pattern, page_text)
            if match:
                # Replace this specific occurrence
                start, end = match.span()
                page_text = page_text[:start] + markdown_link + page_text[end:]
                logger.info(f"Applied hyperlink: '{original_text}' -> '{markdown_link}'")

        return page_text

    def _preserve_pagefooter_urls(self, page_text: str) -> str:
        """Extract URLs from PageFooter HTML comments and append them as footnotes.

        PageFooter comments often contain URLs that should be preserved.
        Example: <!-- PageFooter="... https://example.com" -->
        """
        import re

        # Find PageFooter comments
        pagefooter_pattern = r'<!-- PageFooter="(.+?)" -->'
        matches = re.findall(pagefooter_pattern, page_text)

        for footer_content in matches:
            # Extract URLs from footer content
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            urls = re.findall(url_pattern, footer_content)

            for url in urls:
                # Check if URL is already in the visible text (not in comment)
                visible_text = re.sub(pagefooter_pattern, '', page_text)
                if url not in visible_text:
                    # Add URL as footnote before the comment
                    page_text = page_text.replace(
                        f'<!-- PageFooter="{footer_content}" -->',
                        f'\n\n**Reference:** {url}\n\n<!-- PageFooter="{footer_content}" -->',
                        1
                    )
                    logger.debug(f"Extracted PageFooter URL: {url}")

        return page_text

