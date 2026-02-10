"""Office document extraction (DOCX/PPTX/DOC) with Azure DI and MarkItDown.

Phase 1: Azure DI only for DOCX/PPTX ✅
Phase 2: MarkItDown fallback + DOC support ✅
Phase 3: Equation extraction with GPT-4o Vision ✅
"""

import asyncio
import io
import re
from pathlib import Path
from typing import Optional

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .config import DocumentIntelligenceConfig, OfficeExtractorConfig, OfficeExtractorMode
from .di_extractor import ExtractedImage, ExtractedPage, ExtractedTable
from .logging_utils import get_logger

# Phase 2: MarkItDown imports (optional dependency)
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

logger = get_logger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
RETRY_MIN_WAIT = 5
RETRY_MAX_WAIT = 30


class OfficeExtractor:
    """Extracts content from Office documents (DOCX/PPTX/DOC) with Azure DI and MarkItDown.

    Phase 1: Azure DI only ✅
    Phase 2: MarkItDown fallback + DOC support ✅
    Phase 3: Equation extraction with GPT-4o Vision ✅

    Supports three extraction modes:
    - azure_di: Azure DI only (DOCX/PPTX, best quality, premium equation LaTeX)
    - markitdown: MarkItDown only (all formats including DOC, offline, basic equations)
    - hybrid: Try Azure DI first, fallback to MarkItDown (recommended)

    Equation extraction (Phase 3):
    - Azure DI: Automatic detection with LaTeX representation (premium feature)
    - MarkItDown: XML parsing for equation detection
    - GPT-4o Vision: Automatic descriptions for all detected equations
    """

    def __init__(
        self,
        di_config: DocumentIntelligenceConfig,
        office_config: OfficeExtractorConfig,
        table_renderer=None
    ):
        self.di_config = di_config
        self.office_config = office_config
        self.table_renderer = table_renderer
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Log configuration on initialization
        office_config.log_configuration(logger)

        # Phase 2: Initialize MarkItDown if available and needed
        self.markitdown = None
        if office_config.mode in [OfficeExtractorMode.MARKITDOWN, OfficeExtractorMode.HYBRID]:
            if MARKITDOWN_AVAILABLE:
                self.markitdown = MarkItDown()
                logger.info("✅ MarkItDown initialized successfully")
            else:
                if office_config.mode == OfficeExtractorMode.MARKITDOWN:
                    raise ImportError(
                        "MarkItDown is required for markitdown mode. "
                        "Install with: pip install markitdown"
                    )
                else:
                    logger.warning(
                        "⚠️  MarkItDown not available. Hybrid mode will only use Azure DI. "
                        "Install with: pip install markitdown"
                    )
        elif office_config.mode == OfficeExtractorMode.AZURE_DI:
            # Conditionally initialize for DOC fallback if enabled
            if office_config.offline_fallback:
                if MARKITDOWN_AVAILABLE:
                    self.markitdown = MarkItDown()
                    logger.info("✅ MarkItDown initialized for DOC fallback support")
                else:
                    logger.warning(
                        "⚠️  MarkItDown not available. DOC files will fail in azure_di mode. "
                        "Install with: pip install markitdown"
                    )

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.di_config.max_concurrency)
        return self._semaphore

    def _before_retry_sleep(self, retry_state):
        """Log retry attempts."""
        logger.info(
            f"Office document extraction failed (attempt {retry_state.attempt_number}/{DEFAULT_MAX_RETRIES}), "
            f"sleeping before retrying..."
        )

    async def extract_office_document(
        self,
        file_bytes: bytes,
        filename: str
    ) -> list[ExtractedPage]:
        """Extract pages from Office document (DOCX/PPTX/DOC).

        Phase 2: Supports all three modes (azure_di, markitdown, hybrid)

        Args:
            file_bytes: Document bytes
            filename: Original filename

        Returns:
            List of ExtractedPage objects
        """
        file_ext = Path(filename).suffix.lower()

        # Check file size
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > self.office_config.max_file_size_mb:
            raise ValueError(
                f"File size ({file_size_mb:.1f}MB) exceeds maximum "
                f"({self.office_config.max_file_size_mb}MB): {filename}"
            )

        if self.office_config.verbose:
            logger.info(f"🔍 [VERBOSE] Processing {file_ext.upper()} file: {filename} ({file_size_mb:.2f}MB)")
            logger.info(f"🔍 [VERBOSE] Active mode: {self.office_config.mode.value}")

        # Mode 1: Azure DI Only
        if self.office_config.mode == OfficeExtractorMode.AZURE_DI:
            # Special case: DOC files use MarkItDown fallback if enabled
            if file_ext == '.doc':
                if self.office_config.offline_fallback and self.markitdown:
                    logger.info(
                        f"📄 [AZURE_DI MODE] DOC format detected → Using MarkItDown fallback: {filename}"
                    )
                    return await self._extract_with_markitdown(file_bytes, filename)
                else:
                    # Provide clear guidance on how to enable DOC support
                    error_msg = (
                        f"❌ Legacy DOC format not supported in azure_di mode: {filename}\n"
                        f"\n"
                        f"💡 To enable DOC support in azure_di mode:\n"
                        f"   1. Install MarkItDown: pip install markitdown\n"
                        f"   2. Set AZURE_OFFICE_OFFLINE_FALLBACK=true\n"
                        f"\n"
                        f"Alternative: Use hybrid mode for automatic DOC support\n"
                        f"   AZURE_OFFICE_EXTRACTOR_MODE=hybrid\n"
                    )
                    raise ValueError(error_msg)

            logger.info(f"☁️  [AZURE_DI MODE] Extracting {filename}")
            return await self._extract_with_azure_di(file_bytes, filename)

        # Mode 2: MarkItDown Only
        elif self.office_config.mode == OfficeExtractorMode.MARKITDOWN:
            logger.info(f"📝 [MARKITDOWN MODE] Extracting {filename}")
            return await self._extract_with_markitdown(file_bytes, filename)

        # Mode 3: Hybrid (Default)
        elif self.office_config.mode == OfficeExtractorMode.HYBRID:
            # Always use MarkItDown for DOC (Azure DI doesn't support)
            if file_ext == '.doc':
                logger.info(f"📄 [HYBRID MODE] DOC format detected → Using MarkItDown: {filename}")
                return await self._extract_with_markitdown(file_bytes, filename)

            # Try Azure DI first for DOCX/PPTX
            try:
                logger.info(f"🔄 [HYBRID MODE] Attempting Azure DI first: {filename}")
                return await self._extract_with_azure_di(file_bytes, filename)
            except Exception as e:
                if self.office_config.offline_fallback and self.markitdown:
                    logger.warning(
                        f"⚠️  [HYBRID MODE] Azure DI failed: {e.__class__.__name__}. "
                        f"Falling back to MarkItDown..."
                    )
                    if self.office_config.verbose:
                        logger.info(f"🔍 [VERBOSE] Fallback details: {str(e)[:200]}")
                    return await self._extract_with_markitdown(file_bytes, filename)
                else:
                    logger.error(f"❌ [HYBRID MODE] Azure DI failed and fallback disabled/unavailable: {filename}")
                    raise

        else:
            raise ValueError(f"Unknown office extractor mode: {self.office_config.mode}")

    async def _extract_with_azure_di(
        self,
        file_bytes: bytes,
        filename: str
    ) -> list[ExtractedPage]:
        """Extract using Azure Document Intelligence (Phase 1).

        Supports: DOCX, PPTX
        Does NOT support: DOC (use Phase 2 hybrid/markitdown mode)
        """
        semaphore = self._get_semaphore()

        async with semaphore:
            if self.office_config.verbose:
                logger.info(f"🔍 [VERBOSE] Starting Azure DI extraction for {filename}")

            credential = AzureKeyCredential(self.di_config.key) if self.di_config.key else None

            async with DocumentIntelligenceClient(
                endpoint=self.di_config.endpoint,
                credential=credential
            ) as di_client:
                analyze_result: Optional[AnalyzeResult] = None

                # Start analysis with retry logic
                async for attempt in AsyncRetrying(
                    retry=retry_if_exception_type((ServiceRequestError, HttpResponseError)),
                    wait=wait_random_exponential(min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
                    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
                    before_sleep=self._before_retry_sleep
                ):
                    with attempt:
                        # Use prebuilt-layout model for Office documents
                        # Note: Same model as PDF, but Azure DI handles Office formats

                        # Phase 3: Add formula extraction if enabled
                        # Note: 'formulas' feature is NOT supported for DOCX/PPTX files
                        # It's only available for PDFs and other formats
                        features = []
                        file_ext = Path(filename).suffix.lower()
                        if self.office_config.equation_extraction:
                            if file_ext in ['.docx', '.pptx', '.doc']:
                                logger.info(
                                    f"⚠️  Formula extraction not supported for {file_ext.upper()} files in Azure DI. "
                                    f"Use MarkItDown mode for basic equation detection."
                                )
                            else:
                                # Only enable for supported file types (e.g., PDF)
                                features.append("formulas")
                                logger.info("Equation extraction enabled for Azure DI analysis")

                        poller = await di_client.begin_analyze_document(
                            model_id="prebuilt-layout",
                            body=AnalyzeDocumentRequest(bytes_source=file_bytes),
                            output=["figures"],  # Extract figures from Office documents
                            output_content_format="markdown",
                            features=features if features else None
                        )
                        analyze_result = await poller.result()

            # Parse results (pass file_bytes to extract images from ZIP)
            pages = await self._parse_office_result(analyze_result, filename, file_bytes)

            logger.info(f"Extracted {len(pages)} pages/slides from {filename}")
            return pages

    async def _parse_office_result(
        self,
        result: AnalyzeResult,
        filename: str,
        file_bytes: bytes
    ) -> list[ExtractedPage]:
        """Parse Azure DI result into ExtractedPage objects.

        For PPTX: Each page = one slide
        For DOCX: Pages may be split by sections or kept as-is
        """
        pages = []
        file_ext = Path(filename).suffix.lower()
        is_presentation = file_ext == '.pptx'

        if self.office_config.verbose:
            logger.info(f"🔍 [VERBOSE] Parsing Azure DI result for {filename}")
            logger.info(f"🔍 [VERBOSE] Document type: {'Presentation (PPTX)' if is_presentation else 'Document (DOCX)'}")
            logger.info(f"🔍 [VERBOSE] Pages: {len(result.pages)}, Tables: {len(result.tables) if result.tables else 0}, "
                      f"Figures: {len(result.figures) if result.figures else 0}")

        # Extract all images from Office ZIP structure first
        office_images = self._extract_images_from_office_zip(file_bytes, file_ext)

        # Extract tables
        all_tables = []
        if result.tables:
            if self.office_config.verbose:
                logger.info(f"🔍 [VERBOSE] Extracting {len(result.tables)} tables...")
            for table_idx, table in enumerate(result.tables):
                extracted_table = self._extract_table(table, table_idx)
                all_tables.append(extracted_table)

        # Extract figures/images
        # Match Azure DI figure detections with actual image bytes from ZIP
        all_figures = []

        # For PPTX: Always parse slide relationships to get correct page numbers
        # (Azure DI sometimes assigns all images to the last slide)
        image_to_slide_map = {}
        if file_ext == '.pptx' and office_images:
            image_to_slide_map = self._map_pptx_images_to_slides(file_bytes, office_images)
            logger.info(f"Mapped {len(image_to_slide_map)} images to slides for PPTX")

        if result.figures:
            logger.info(f"Azure DI detected {len(result.figures)} figures, extracted {len(office_images)} images from ZIP")
            for figure_idx, figure in enumerate(result.figures):
                try:
                    # Try to match figure with actual image from ZIP
                    extracted_image = self._extract_figure_from_office(
                        figure,
                        figure_idx,
                        office_images,
                        image_to_slide_map if file_ext == '.pptx' else None
                    )
                    if extracted_image:
                        all_figures.append(extracted_image)
                except Exception as e:
                    logger.error(f"Error extracting figure {figure_idx}: {e}")
        elif office_images:
            # No figures detected by Azure DI, but images exist in ZIP
            # Create figures for all extracted images with proper slide mapping
            logger.info(f"No figures detected by Azure DI, but found {len(office_images)} images in ZIP. Creating figures.")

            # For PPTX: Map images to slides by parsing slide relationships
            if file_ext == '.pptx':
                image_to_slide_map = self._map_pptx_images_to_slides(file_bytes, office_images)
            else:
                # For DOCX: distribute images across pages based on result.pages
                image_to_slide_map = self._map_docx_images_to_pages(result, office_images)

            for idx, (img_name, img_bytes) in enumerate(office_images.items()):
                try:
                    figure_id = f"figure_{idx}"
                    # Use mapped page number or default to 0
                    page_num = image_to_slide_map.get(img_name, 0)

                    extracted_image = ExtractedImage(
                        figure_id=figure_id,
                        page_num=page_num,
                        bbox=(0, 0, 0, 0),  # No bbox from Azure DI
                        image_bytes=img_bytes,
                        filename=f"{figure_id}.png",
                        title=img_name,
                        placeholder=f'<figure id="{figure_id}"></figure>',
                        mime_type=f"image/{img_name.split('.')[-1]}"
                    )
                    all_figures.append(extracted_image)
                except Exception as e:
                    logger.error(f"Error creating figure from ZIP image {img_name}: {e}")

        # Phase 3: Extract equations/formulas if present
        if self.office_config.equation_extraction and hasattr(result, 'formulas') and result.formulas:
            logger.info(f"Found {len(result.formulas)} equations in document")
            for formula_idx, formula in enumerate(result.formulas):
                try:
                    extracted_equation = self._extract_equation_from_azure_di(formula, formula_idx)
                    if extracted_equation:
                        all_figures.append(extracted_equation)  # Equations treated as special figures
                except Exception as e:
                    logger.error(f"Error extracting equation {formula_idx}: {e}")
        elif self.office_config.equation_extraction:
            logger.info("No equations detected in document")

        # Process each page/slide
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

        return pages

    def _extract_table(self, table, table_idx: int) -> ExtractedTable:
        """Extract table from Azure DI result."""
        # Get page numbers this table spans
        page_nums = []
        if table.bounding_regions:
            for region in table.bounding_regions:
                page_num = region.page_number - 1  # Convert to 0-indexed
                if page_num not in page_nums:
                    page_nums.append(page_num)

        # Extract cells
        cells = []
        if table.cells:
            for cell in table.cells:
                cells.append({
                    'row_index': cell.row_index,
                    'column_index': cell.column_index,
                    'row_span': getattr(cell, 'row_span', 1),
                    'column_span': getattr(cell, 'column_span', 1),
                    'content': cell.content or '',
                    'kind': getattr(cell, 'kind', 'content')
                })

        # Get bounding box (use first region if multiple)
        bbox = None
        if table.bounding_regions:
            region = table.bounding_regions[0]
            if region.polygon:
                # Convert polygon to bbox (x1, y1, x2, y2)
                coords = region.polygon
                x_coords = [coords[i] for i in range(0, len(coords), 2)]
                y_coords = [coords[i] for i in range(1, len(coords), 2)]
                bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

        table_id = f"table_{table_idx}"

        return ExtractedTable(
            table_id=table_id,
            di_table_index=table_idx,
            page_nums=page_nums,
            cells=cells,
            row_count=table.row_count,
            column_count=table.column_count,
            bbox=bbox
        )

    def _extract_figure_from_office(
        self,
        figure,
        figure_idx: int,
        office_images: dict[str, bytes],
        image_to_slide_map: Optional[dict[str, int]] = None
    ) -> Optional[ExtractedImage]:
        """Extract figure/image from Office document via Azure DI.

        Matches Azure DI figure detection with actual image bytes from Office ZIP.

        Args:
            figure: Azure DI figure object
            figure_idx: Index of the figure
            office_images: Dictionary of image filename -> image bytes from ZIP
            image_to_slide_map: Optional mapping of image filename -> correct slide number (0-indexed)
                               Used for PPTX to override Azure DI's sometimes-incorrect page assignments
        """
        # Get page number from Azure DI
        page_num = 0
        if figure.bounding_regions:
            page_num = figure.bounding_regions[0].page_number - 1  # Convert to 0-indexed

        # Get bounding box
        bbox = (0, 0, 0, 0)  # Default
        if figure.bounding_regions:
            region = figure.bounding_regions[0]
            if region.polygon:
                coords = region.polygon
                x_coords = [coords[i] for i in range(0, len(coords), 2)]
                y_coords = [coords[i] for i in range(1, len(coords), 2)]
                bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

        figure_id = f"figure_{figure_idx}"

        # Use caption or default title
        title = ""
        if hasattr(figure, 'caption') and figure.caption:
            title = figure.caption.content if hasattr(figure.caption, 'content') else str(figure.caption)

        # Try to match with actual image from Office ZIP
        # Strategy: Match by order (figure_idx corresponds to image order in ZIP)
        image_bytes = None
        image_filename = f"{figure_id}.png"
        matched_img_name = None

        if office_images:
            # Convert to list for index-based access
            images_list = list(office_images.items())

            if figure_idx < len(images_list):
                # Match by index order
                img_name, img_bytes = images_list[figure_idx]
                matched_img_name = img_name
                image_bytes = img_bytes
                # Preserve original extension
                ext = img_name.split('.')[-1].lower()
                image_filename = f"{figure_id}.{ext}"
                logger.debug(f"Matched Azure DI figure {figure_idx} with ZIP image {img_name}")
            else:
                logger.warning(f"Figure {figure_idx} has no matching image in ZIP (only {len(images_list)} images)")

        # Override page number with corrected slide mapping if provided (for PPTX)
        if image_to_slide_map and matched_img_name and matched_img_name in image_to_slide_map:
            corrected_page_num = image_to_slide_map[matched_img_name]
            if corrected_page_num != page_num:
                logger.debug(
                    f"Correcting page number for {matched_img_name}: "
                    f"Azure DI said page {page_num + 1}, actual slide {corrected_page_num + 1}"
                )
                page_num = corrected_page_num

        # Fallback to placeholder if no match
        if not image_bytes:
            logger.warning(f"No image bytes found for figure {figure_idx}, using placeholder")
            image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        return ExtractedImage(
            figure_id=figure_id,
            page_num=page_num,
            bbox=bbox,
            image_bytes=image_bytes,
            filename=image_filename,
            title=title,
            placeholder=f'<figure id="{figure_id}"></figure>',
            mime_type=f"image/{image_filename.split('.')[-1]}"
        )

    def _extract_equation_from_azure_di(self, formula, formula_idx: int) -> Optional[ExtractedImage]:
        """Extract equation/formula from Office document via Azure DI (Phase 3).

        Azure DI automatically detects formulas and provides:
        - LaTeX representation (premium feature)
        - Bounding box
        - Confidence score

        Equations are returned as ExtractedImage objects with special metadata.
        """
        # Get page number
        page_num = 0
        if hasattr(formula, 'bounding_regions') and formula.bounding_regions:
            page_num = formula.bounding_regions[0].page_number - 1  # Convert to 0-indexed

        # Get bounding box
        bbox = (0, 0, 0, 0)  # Default
        if hasattr(formula, 'bounding_regions') and formula.bounding_regions:
            region = formula.bounding_regions[0]
            if hasattr(region, 'polygon') and region.polygon:
                coords = region.polygon
                x_coords = [coords[i] for i in range(0, len(coords), 2)]
                y_coords = [coords[i] for i in range(1, len(coords), 2)]
                bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

        figure_id = f"equation_{formula_idx}"

        # Extract LaTeX if available (premium feature)
        latex = None
        if hasattr(formula, 'value') and formula.value:
            latex = formula.value
            logger.info(f"Equation {formula_idx} LaTeX: {latex[:100]}...")  # Log first 100 chars

        # Get confidence score
        confidence = None
        if hasattr(formula, 'confidence'):
            confidence = formula.confidence

        # Create placeholder image bytes (will be replaced with rendered equation or described by GPT-4o)
        # For Phase 3, we use a placeholder since equation rendering requires additional libraries
        placeholder_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        # Create ExtractedImage with equation-specific metadata
        equation_image = ExtractedImage(
            figure_id=figure_id,
            page_num=page_num,
            bbox=bbox,
            image_bytes=placeholder_bytes,
            filename=f"{figure_id}.png",
            title="Equation",
            placeholder=f'<figure id="{figure_id}" type="equation"></figure>',
            mime_type="image/png"
        )

        # Store equation-specific metadata
        # Note: ExtractedImage doesn't have these fields, so we'll add them as attributes
        # The media describer will use these to generate better descriptions
        equation_image.latex = latex  # type: ignore
        equation_image.figure_type = "equation"  # type: ignore
        equation_image.equation_confidence = confidence  # type: ignore

        logger.info(
            f"Extracted equation {formula_idx}: "
            f"LaTeX={'available' if latex else 'not available'}, "
            f"confidence={confidence:.2f if confidence else 'N/A'}"
        )

        return equation_image

    def _extract_images_from_office_zip(
        self,
        file_bytes: bytes,
        file_ext: str
    ) -> dict[str, bytes]:
        """Extract all images from Office ZIP structure.

        Returns mapping of image filename -> image bytes.
        """
        images_map = {}

        try:
            import zipfile
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as office_zip:
                # Determine image directory based on format
                if file_ext == '.pptx':
                    image_dir = 'ppt/media/'
                elif file_ext in ['.docx', '.doc']:
                    image_dir = 'word/media/'
                else:
                    return images_map

                # Extract all images from media directory
                for file_info in office_zip.filelist:
                    if file_info.filename.startswith(image_dir):
                        # Get just the filename (e.g., "image1.png" from "ppt/media/image1.png")
                        image_filename = file_info.filename.split('/')[-1]
                        image_bytes = office_zip.read(file_info.filename)
                        images_map[image_filename] = image_bytes
                        logger.debug(f"Extracted image {image_filename} ({len(image_bytes)} bytes)")

        except Exception as e:
            logger.warning(f"Failed to extract images from Office ZIP: {e}")

        if images_map:
            logger.info(f"Extracted {len(images_map)} images from Office document")

        return images_map

    def _map_pptx_images_to_slides(
        self,
        file_bytes: bytes,
        office_images: dict[str, bytes]
    ) -> dict[str, int]:
        """Map PPTX images to their slides by parsing slide relationships.

        Returns: dict mapping image filename -> slide number (0-indexed)
        """
        logger.debug(f"[PPTX MAPPING] Starting mapping for {len(office_images)} images: {list(office_images.keys())}")
        image_to_slide = {}
        num_slides = 1  # Default

        try:
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(io.BytesIO(file_bytes)) as pptx_zip:
                # Get list of slides
                slide_files = [f for f in pptx_zip.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
                slide_files.sort()  # Ensure correct order
                num_slides = len(slide_files) if slide_files else 1

                for slide_idx, slide_file in enumerate(slide_files):
                    try:
                        logger.debug(f"[PPTX MAPPING] Processing {slide_file} (slide {slide_idx + 1})")
                        # Parse slide XML
                        slide_xml = pptx_zip.read(slide_file)
                        root = ET.fromstring(slide_xml)

                        # Find all image references in this slide
                        # Images are referenced with relationships (r:embed or r:id)
                        # We need to parse the slide's .rels file to map r:id to image files

                        # Get slide's .rels file
                        # IMPORTANT: .rels files are in _rels subdirectory
                        # e.g., ppt/slides/slide1.xml → ppt/slides/_rels/slide1.xml.rels
                        slide_dir = '/'.join(slide_file.split('/')[:-1])  # Get directory path
                        slide_name = slide_file.split('/')[-1]  # Get filename
                        rels_file = f"{slide_dir}/_rels/{slide_name}.rels"
                        logger.debug(f"[PPTX MAPPING] Looking for relationships file: {rels_file}")
                        if rels_file in pptx_zip.namelist():
                            logger.debug(f"[PPTX MAPPING] ✓ Found {rels_file}")
                            rels_xml = pptx_zip.read(rels_file)
                            rels_root = ET.fromstring(rels_xml)

                            # Find image relationships
                            # Example: <Relationship Id="rId2" Type="http://...image" Target="../media/image1.png"/>
                            all_rels = rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
                            logger.debug(f"[PPTX MAPPING] Found {len(all_rels)} total relationships in {rels_file}")
                            for rel in all_rels:
                                rel_type = rel.get('Type', '')
                                if 'image' in rel_type.lower():
                                    target = rel.get('Target', '')
                                    # Extract image filename from target (e.g., "../media/image1.png" -> "image1.png")
                                    image_filename = target.split('/')[-1]
                                    logger.debug(f"[PPTX MAPPING] Slide {slide_idx + 1}: Found image ref '{image_filename}' in relationships")
                                    if image_filename in office_images:
                                        image_to_slide[image_filename] = slide_idx
                                        logger.debug(f"[PPTX MAPPING] ✓ Mapped {image_filename} to slide {slide_idx + 1}")
                                    else:
                                        logger.debug(f"[PPTX MAPPING] ✗ Image {image_filename} NOT in office_images keys: {list(office_images.keys())}")

                    except Exception as e:
                        logger.warning(f"Error parsing slide {slide_file}: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Error mapping PPTX images to slides: {e}")

        # If mapping failed for some images, assign them sequentially
        unmapped_images = [img for img in office_images.keys() if img not in image_to_slide]
        logger.debug(f"[PPTX MAPPING] After XML parsing: {len(image_to_slide)} mapped, {len(unmapped_images)} unmapped")
        logger.debug(f"[PPTX MAPPING] Mapped images: {image_to_slide}")
        logger.debug(f"[PPTX MAPPING] Unmapped images: {unmapped_images}")
        if unmapped_images:
            logger.warning(f"{len(unmapped_images)} images could not be mapped to slides, distributing sequentially")
            for idx, img_name in enumerate(unmapped_images):
                image_to_slide[img_name] = idx % num_slides

        logger.debug(f"[PPTX MAPPING] Final mapping: {image_to_slide}")
        return image_to_slide

    def _map_docx_images_to_pages(
        self,
        result,
        office_images: dict[str, bytes]
    ) -> dict[str, int]:
        """Map DOCX images to pages by distributing sequentially.

        For DOCX, without detailed parsing, we distribute images across pages.
        Returns: dict mapping image filename -> page number (0-indexed)
        """
        image_to_page = {}

        num_pages = len(result.pages) if result.pages else 1
        num_images = len(office_images)

        # Distribute images evenly across pages
        # This is a heuristic since we don't have exact image-to-page mapping from Azure DI
        image_filenames = list(office_images.keys())

        for idx, image_filename in enumerate(image_filenames):
            # Distribute sequentially across pages
            page_num = idx % num_pages
            image_to_page[image_filename] = page_num

        logger.debug(f"Distributed {num_images} DOCX images across {num_pages} pages")

        return image_to_page

    async def _extract_with_markitdown(
        self,
        file_bytes: bytes,
        filename: str
    ) -> list[ExtractedPage]:
        """Extract using MarkItDown (Phase 2).

        Supports: DOCX, PPTX, DOC (all formats)
        Differences from Azure DI:
        - Tables: Markdown format (not structured cells)
        - Images: No bounding boxes
        - Layout: Basic structure (not advanced layout analysis)
        """
        if not self.markitdown:
            raise RuntimeError(
                "MarkItDown not initialized. "
                "Install with: pip install markitdown"
            )

        if self.office_config.verbose:
            logger.info(f"🔍 [VERBOSE] Starting MarkItDown extraction for {filename}")

        file_ext = Path(filename).suffix.lower()

        try:
            # Extract all images from Office ZIP first
            office_images = self._extract_images_from_office_zip(file_bytes, file_ext)

            if self.office_config.verbose:
                logger.info(f"🔍 [VERBOSE] Extracted {len(office_images)} images from Office ZIP")

            # Write bytes to temp file for MarkItDown
            # MarkItDown works with file paths for Office documents
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            if self.office_config.verbose:
                logger.info(f"🔍 [VERBOSE] Converting to markdown...")

            try:
                # Phase 3: Detect equations before converting (if enabled)
                equations = []
                if self.office_config.equation_extraction:
                    equations = self._detect_equations_in_office(file_bytes, file_ext, filename)
                    if equations:
                        logger.info(f"✅ Detected {len(equations)} equations in {filename}")
                    else:
                        if self.office_config.verbose:
                            logger.info(f"🔍 [VERBOSE] No equations found in {filename}")

                # Convert to markdown
                result = self.markitdown.convert(tmp_path)
                markdown_text = result.text_content if hasattr(result, 'text_content') else str(result)

                if self.office_config.verbose:
                    logger.info(f"🔍 [VERBOSE] Markdown conversion complete ({len(markdown_text)} chars)")
            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            # Split into pages/slides based on format
            # Pass office_images so they can be matched with markdown references
            pages = []
            if file_ext == '.pptx':
                # PPTX: Split by slide markers
                pages = self._split_pptx_markdown(markdown_text, filename, office_images)
            else:
                # DOCX/DOC: Split by sections or treat as single page
                pages = self._split_docx_markdown(markdown_text, filename, office_images)

            # Phase 3: Add equations to pages if detected
            if equations:
                self._add_equations_to_pages(pages, equations)

            logger.info(
                f"MarkItDown extracted {len(pages)} pages from {filename} "
                f"(note: no bounding boxes, markdown tables)"
            )
            return pages

        except Exception as e:
            logger.error(f"MarkItDown extraction failed for {filename}: {e}")
            raise

    def _extract_images_from_markdown(
        self,
        markdown_text: str,
        page_num: int,
        filename: str,
        office_images: dict[str, bytes]
    ) -> tuple[str, list[ExtractedImage]]:
        """Extract images from MarkItDown markdown text.

        MarkItDown outputs images as file references: ![alt](PictureN.jpg)
        We match these references to images extracted from the Office ZIP.

        Also supports base64 data URLs for future compatibility: ![alt](data:image/TYPE;base64,DATA)

        Returns:
            - Modified text with image placeholders
            - List of ExtractedImage objects
        """
        images = []
        modified_text = markdown_text

        # Pattern 1: Match file references (MarkItDown default)
        # ![alt text](Picture2.jpg) or ![alt](image1.png)
        file_pattern = r'!\[([^\]]*)\]\(([^)]+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\)'
        file_matches = list(re.finditer(file_pattern, markdown_text, re.IGNORECASE))

        # Get list of available images (sorted for consistent index-based matching)
        available_images = sorted(office_images.items())

        for idx, match in enumerate(file_matches):
            alt_text = match.group(1) or f"Figure {idx + 1}"
            image_filename = match.group(2)

            try:
                # Strategy 1: Try exact name match (case-insensitive)
                image_bytes = None
                matched_filename = None
                for key, value in office_images.items():
                    if key.lower() == image_filename.lower():
                        image_bytes = value
                        matched_filename = key
                        break

                # Strategy 2: If no name match, use index-based matching
                # (MarkItDown references may not match actual ZIP filenames)
                if not image_bytes and idx < len(available_images):
                    matched_filename, image_bytes = available_images[idx]
                    logger.debug(
                        f"Image {image_filename} not found by name, "
                        f"using index-based match: {matched_filename}"
                    )

                if not image_bytes:
                    logger.warning(
                        f"Image {image_filename} referenced in markdown at index {idx} "
                        f"but no matching image found (have {len(available_images)} images)"
                    )
                    continue

                # Determine image type from matched filename
                image_ext = matched_filename.split('.')[-1].lower()
                if image_ext == 'jpg':
                    image_ext = 'jpeg'

                # Create figure ID
                figure_id = f"figure_{page_num}_{idx}"

                # Create ExtractedImage object
                extracted_image = ExtractedImage(
                    figure_id=figure_id,
                    page_num=page_num,
                    bbox=(0, 0, 0, 0),  # MarkItDown doesn't provide bounding boxes
                    image_bytes=image_bytes,
                    filename=f"{figure_id}.{image_ext}",
                    title=alt_text,
                    placeholder=f'<figure id="{figure_id}"></figure>',
                    mime_type=f"image/{image_ext}"
                )

                images.append(extracted_image)

                # Replace in text with placeholder
                placeholder = f'<figure id="{figure_id}"></figure>'
                modified_text = modified_text.replace(match.group(0), placeholder, 1)

                logger.debug(f"Extracted image {figure_id} from markdown ({len(image_bytes)} bytes)")

            except Exception as e:
                logger.warning(f"Failed to extract image {image_filename} on page {page_num}: {e}")

        # Pattern 2: Match base64 data URLs (for future compatibility)
        # ![alt text](data:image/png;base64,iVBORw0KGgoAAAA...)
        base64_pattern = r'!\[([^\]]*)\]\(data:image/([^;]+);base64,([^)]+)\)'
        base64_matches = list(re.finditer(base64_pattern, markdown_text))

        for idx, match in enumerate(base64_matches, start=len(file_matches)):
            alt_text = match.group(1) or f"Figure {idx + 1}"
            image_type = match.group(2)  # png, jpeg, etc.
            base64_data = match.group(3)

            try:
                # Decode base64 to bytes
                import base64
                image_bytes = base64.b64decode(base64_data)

                # Create figure ID
                figure_id = f"figure_{page_num}_{idx}"

                # Create ExtractedImage object
                extracted_image = ExtractedImage(
                    figure_id=figure_id,
                    page_num=page_num,
                    bbox=(0, 0, 0, 0),  # MarkItDown doesn't provide bounding boxes
                    image_bytes=image_bytes,
                    filename=f"{figure_id}.{image_type}",
                    title=alt_text,
                    placeholder=f'<figure id="{figure_id}"></figure>',
                    mime_type=f"image/{image_type}"
                )

                images.append(extracted_image)

                # Replace in text with placeholder
                placeholder = f'<figure id="{figure_id}"></figure>'
                modified_text = modified_text.replace(match.group(0), placeholder, 1)

                logger.debug(f"Extracted base64 image {figure_id} from markdown ({len(image_bytes)} bytes)")

            except Exception as e:
                logger.warning(f"Failed to decode base64 image {idx} on page {page_num}: {e}")

        if images:
            logger.info(f"Extracted {len(images)} images from markdown (page {page_num})")

        return modified_text, images

    def _split_pptx_markdown(
        self,
        markdown_text: str,
        filename: str,
        office_images: dict[str, bytes]
    ) -> list[ExtractedPage]:
        """Split PPTX markdown by slides.

        MarkItDown formats PPTX with slide numbers.
        """
        pages = []

        # Look for slide markers (MarkItDown typically uses "## Slide N" format)
        slide_pattern = r'##\s+Slide\s+(\d+)'
        splits = re.split(slide_pattern, markdown_text)

        if len(splits) > 1:
            # Found slide markers
            for i in range(1, len(splits), 2):
                if i + 1 < len(splits):
                    page_num = int(splits[i]) - 1  # Convert to 0-indexed
                    text = splits[i + 1].strip()

                    # Extract images from markdown
                    text, images = self._extract_images_from_markdown(text, page_num, filename, office_images)

                    page = ExtractedPage(
                        page_num=page_num,
                        text=text,
                        tables=[],  # Tables are embedded in markdown
                        images=images,  # Now includes extracted images
                        offset=0
                    )
                    pages.append(page)
        else:
            # No clear slide markers, split by major headings
            sections = re.split(r'\n(?=##?\s)', markdown_text)
            for idx, section in enumerate(sections):
                if section.strip():
                    # Extract images from markdown
                    text, images = self._extract_images_from_markdown(section.strip(), idx, filename, office_images)

                    page = ExtractedPage(
                        page_num=idx,
                        text=text,
                        tables=[],
                        images=images,
                        offset=0
                    )
                    pages.append(page)

        # If no splits found, treat as single page
        if not pages:
            text, images = self._extract_images_from_markdown(markdown_text.strip(), 0, filename, office_images)
            pages = [ExtractedPage(
                page_num=0,
                text=text,
                tables=[],
                images=images,
                offset=0
            )]

        return pages

    def _split_docx_markdown(
        self,
        markdown_text: str,
        filename: str,
        office_images: dict[str, bytes]
    ) -> list[ExtractedPage]:
        """Split DOCX/DOC markdown by sections.

        Split by major headings or treat as single page.
        """
        pages = []

        # Split by major headings (## or #)
        sections = re.split(r'\n(?=##?\s)', markdown_text)

        for idx, section in enumerate(sections):
            if section.strip():
                # Extract images from markdown
                text, images = self._extract_images_from_markdown(section.strip(), idx, filename, office_images)

                page = ExtractedPage(
                    page_num=idx,
                    text=text,
                    tables=[],
                    images=images,  # Now includes extracted images
                    offset=0
                )
                pages.append(page)

        # If no sections found, treat as single page
        if not pages:
            text, images = self._extract_images_from_markdown(markdown_text.strip(), 0, filename, office_images)
            pages = [ExtractedPage(
                page_num=0,
                text=text,
                tables=[],
                images=images,
                offset=0
            )]

        return pages

    def _detect_equations_in_office(
        self,
        file_bytes: bytes,
        file_ext: str,
        filename: str
    ) -> list[dict]:
        """Detect equations in Office documents for MarkItDown mode (Phase 3).

        For DOCX/DOC: Parse Office XML to find <m:oMath> elements
        For PPTX: Look for equation shapes

        Returns list of equation metadata dicts (without images - those would require rendering)
        """
        equations = []

        try:
            import zipfile

            if file_ext in ['.docx', '.doc']:
                # DOCX/DOC: Parse document.xml for math elements
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as office_zip:
                    try:
                        xml_content = office_zip.read('word/document.xml')

                        # Check for Office Math elements
                        if b'<m:oMath' in xml_content:
                            # Count equations (simple approach - count opening tags)
                            equation_count = xml_content.count(b'<m:oMath')
                            logger.info(f"Found {equation_count} equation markers in {filename}")

                            # Create placeholder equation entries
                            for i in range(equation_count):
                                equations.append({
                                    'equation_idx': i,
                                    'page_num': 0,  # Default to first page
                                    'bbox': (0, 0, 0, 0),
                                    'latex': None,  # Not available in MarkItDown mode
                                    'confidence': None
                                })

                    except KeyError:
                        logger.debug(f"No document.xml found in {filename}")

            elif file_ext == '.pptx':
                # PPTX: Check for equation shapes in slides
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as office_zip:
                    # Check all slide files
                    slide_files = [f for f in office_zip.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]

                    for slide_idx, slide_file in enumerate(slide_files):
                        try:
                            slide_content = office_zip.read(slide_file)

                            # Look for equation/math elements in slide
                            if b'<m:oMath' in slide_content or b'mathml' in slide_content.lower():
                                equation_count = slide_content.count(b'<m:oMath')
                                logger.info(f"Found {equation_count} equations in slide {slide_idx + 1}")

                                for i in range(equation_count):
                                    equations.append({
                                        'equation_idx': len(equations),
                                        'page_num': slide_idx,
                                        'bbox': (0, 0, 0, 0),
                                        'latex': None,
                                        'confidence': None
                                    })

                        except KeyError:
                            continue

        except Exception as e:
            logger.warning(f"Error detecting equations in {filename}: {e}")

        return equations

    def _add_equations_to_pages(
        self,
        pages: list[ExtractedPage],
        equations: list[dict]
    ) -> None:
        """Add detected equations to pages as ExtractedImage objects (Phase 3).

        MarkItDown mode: Equations detected but not rendered.
        Creates placeholder images that will be described by GPT-4o Vision.
        """
        for eq_data in equations:
            page_num = eq_data['page_num']

            # Find matching page
            matching_page = None
            for page in pages:
                if page.page_num == page_num:
                    matching_page = page
                    break

            if not matching_page and pages:
                # If page not found, add to first page
                matching_page = pages[0]

            if matching_page:
                # Create placeholder equation image
                equation_idx = eq_data['equation_idx']
                figure_id = f"equation_{equation_idx}"

                # Placeholder PNG (1x1 transparent pixel)
                placeholder_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

                equation_image = ExtractedImage(
                    figure_id=figure_id,
                    page_num=page_num,
                    bbox=eq_data['bbox'],
                    image_bytes=placeholder_bytes,
                    filename=f"{figure_id}.png",
                    title="Equation",
                    placeholder=f'<figure id="{figure_id}" type="equation"></figure>',
                    mime_type="image/png"
                )

                # Add equation metadata
                equation_image.latex = eq_data.get('latex')  # type: ignore
                equation_image.figure_type = "equation"  # type: ignore
                equation_image.equation_confidence = eq_data.get('confidence')  # type: ignore

                matching_page.images.append(equation_image)

                logger.debug(f"Added equation {equation_idx} to page {page_num}")

    def _build_page_text(
        self,
        result: AnalyzeResult,
        page,
        tables_on_page: list[ExtractedTable],
        figures_on_page: list[ExtractedImage]
    ) -> str:
        """Build page text with table and figure placeholders inserted."""
        # Get the markdown content for this page
        page_text = ""

        # Azure DI provides page-level content
        if hasattr(page, 'words') and page.words:
            # Reconstruct text from words
            words = [word.content for word in page.words if hasattr(word, 'content')]
            page_text = ' '.join(words)

        # Alternative: Use the content from result if available
        if result.content and hasattr(result, 'pages'):
            # Find the span for this page
            # For now, use simple approach: get content from page spans
            if hasattr(page, 'spans') and page.spans:
                for span in page.spans:
                    if span.offset is not None and span.length is not None:
                        page_text = result.content[span.offset:span.offset + span.length]
                        break

        # Insert table placeholders
        for table in tables_on_page:
            placeholder = f'<table id="{table.table_id}"></table>'
            # Try to find a good insertion point (for now, append at end)
            page_text += f"\n\n{placeholder}\n\n"

        # Insert figure placeholders
        for figure in figures_on_page:
            page_text += f"\n\n{figure.placeholder}\n\n"

        return page_text.strip()
