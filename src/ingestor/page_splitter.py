"""Per-page PDF splitter for citation storage."""

import io
from pathlib import Path
from typing import Optional

from .logging_utils import get_logger

try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    get_logger(__name__).warning("pypdf not available - per-page PDF splitting disabled")

logger = get_logger(__name__)


class PagePdfSplitter:
    """Splits multi-page PDFs into individual page PDFs for citation purposes."""
    
    def __init__(self):
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required for per-page PDF splitting. Install with: pip install pypdf")
    
    def split_pdf(self, pdf_bytes: bytes, filename: str) -> list[tuple[int, bytes, str]]:
        """Split PDF into individual pages.
        
        Args:
            pdf_bytes: Original PDF bytes
            filename: Original filename
            
        Returns:
            List of (page_num, page_pdf_bytes, page_filename) tuples
        """
        results = []
        
        try:
            # Read PDF
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            total_pages = len(pdf_reader.pages)
            
            logger.info(f"Splitting {filename} into {total_pages} page PDFs")
            
            # Split each page
            for page_num in range(total_pages):
                # Create single-page PDF
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Write to bytes
                page_pdf_io = io.BytesIO()
                pdf_writer.write(page_pdf_io)
                page_pdf_bytes = page_pdf_io.getvalue()
                
                # Generate filename for this page
                base_name = Path(filename).stem
                page_filename = f"{base_name}_page{page_num + 1}.pdf"
                
                results.append((page_num, page_pdf_bytes, page_filename))
                
                logger.debug(f"Split page {page_num + 1}/{total_pages}: {len(page_pdf_bytes)} bytes")
            
            logger.info(f"Successfully split {filename} into {len(results)} page PDFs")
            return results
        
        except Exception as e:
            logger.error(f"Failed to split PDF {filename}: {e}")
            raise
    
    def create_single_page_pdf(self, pdf_bytes: bytes, page_num: int) -> bytes:
        """Extract a single page from PDF.
        
        Args:
            pdf_bytes: Original PDF bytes
            page_num: Page number to extract (0-indexed)
            
        Returns:
            Single-page PDF bytes
        """
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num])
            
            page_pdf_io = io.BytesIO()
            pdf_writer.write(page_pdf_io)
            return page_pdf_io.getvalue()
        
        except Exception as e:
            logger.error(f"Failed to extract page {page_num}: {e}")
            raise

