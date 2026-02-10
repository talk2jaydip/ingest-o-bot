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


class ExtractedPage:
    """Represents an extracted page with text, tables, and figures."""
    
    def __init__(
        self,
        page_num: int,
        text: str,
        tables: list[ExtractedTable],
        images: list[ExtractedImage],
        offset: int = 0
    ):
        self.page_num = page_num
        self.text = text
        self.tables = tables
        self.images = images
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

        # Open PDF with PyMuPDF if we need to crop figures
        doc_for_pymupdf = None
        if pdf_bytes:
            doc_for_pymupdf = pymupdf.open(stream=io.BytesIO(pdf_bytes))

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
            
            # Build page text with tables and figures inserted
            page_text = self._build_page_text(
                result,
                page,
                tables_on_page,
                figures_on_page
            )
            
            extracted_page = ExtractedPage(
                page_num=page_num,
                text=page_text,
                tables=tables_on_page,
                images=figures_on_page,
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
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(page_dpi / bbox_dpi, page_dpi / bbox_dpi),
            clip=rect
        )
        
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        bytes_io = io.BytesIO()
        img.save(bytes_io, format="PNG")
        return bytes_io.getvalue(), bbox_pixels
    
    def _build_page_text(
        self,
        result: AnalyzeResult,
        page,
        tables_on_page: list[ExtractedTable],
        figures_on_page: list[ExtractedImage]
    ) -> str:
        """Build page text with tables and figures inserted as placeholders."""
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
        
        # Clean up
        page_text = page_text.replace("<!-- PageBreak -->", "")
        page_text = page_text.strip()
        
        return page_text

