"""Enhanced logging utilities for ingestor."""

import io
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional


# Centralized logger name
LOGGER_NAME = "ingestor"


def get_logger(name: str = None) -> logging.Logger:
    """Get the centralized logger instance.

    Args:
        name: Optional module name for context. If not provided, returns the root logger.

    Returns:
        Configured logger instance

    Usage:
        from ingestor.logging_utils import get_logger
        logger = get_logger(__name__)
    """
    if name and name != LOGGER_NAME:
        # Return a child logger that inherits from the main logger
        return logging.getLogger(f"{LOGGER_NAME}.{name.split('.')[-1]}")
    return logging.getLogger(LOGGER_NAME)


def setup_logging(log_dir: str = "./logs") -> tuple[logging.Logger, Path]:
    """Setup comprehensive logging for the pipeline.

    Returns:
        Tuple of (logger, log_directory_path)
    """
    # Re-wrap stdout and stderr in UTF-8 to make console writes safe
    # This fixes encoding issues with emojis and special characters
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        # If stdout/stderr don't have a buffer attribute (e.g., already wrapped or in some IDEs)
        pass

    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log_dir = log_path / f"run_{timestamp}"
    run_log_dir.mkdir(parents=True, exist_ok=True)

    # Setup main logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler (INFO level) - now uses UTF-8 wrapped stdout
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (DEBUG level) - with UTF-8 encoding for full content logging
    file_handler = logging.FileHandler(run_log_dir / "pipeline.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Run logs: {run_log_dir}")
    return logger, run_log_dir


def log_di_response(log_dir: Path, doc_name: str, di_result: Any) -> None:
    """Log Document Intelligence response to file.
    
    Args:
        log_dir: Directory to save logs
        doc_name: Document name
        di_result: Document Intelligence result object
    """
    di_log_dir = log_dir / "di_responses"
    di_log_dir.mkdir(exist_ok=True)
    
    # Save full DI response
    response_file = di_log_dir / f"{doc_name}_di_response.json"
    
    try:
        # Convert DI result to dict
        if hasattr(di_result, 'as_dict'):
            result_dict = di_result.as_dict()
        elif hasattr(di_result, '__dict__'):
            result_dict = di_result.__dict__
        else:
            result_dict = {"raw": str(di_result)}
        
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, default=str)

        get_logger().info(f"DI response saved: {response_file}")
    except Exception as e:
        get_logger().error(f"Failed to save DI response: {e}")


def log_di_summary(log_dir: Path, doc_name: str, pages: list) -> None:
    """Log summary of DI extraction results.
    
    Args:
        log_dir: Directory to save logs
        doc_name: Document name
        pages: List of extracted pages
    """
    # Create directory first to avoid FileNotFoundError
    di_log_dir = log_dir / "di_responses"
    di_log_dir.mkdir(exist_ok=True)
    
    summary_file = di_log_dir / f"{doc_name}_summary.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Document Intelligence Extraction Summary\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Document: {doc_name}\n")
        f.write(f"Total Pages: {len(pages)}\n\n")
        
        for page in pages:
            f.write(f"\n{'='*60}\n")
            f.write(f"Page {page.page_num + 1}\n")
            f.write(f"{'='*60}\n\n")
            
            f.write(f"Text Length: {len(page.text)} characters\n")
            f.write(f"Tables: {len(page.tables)}\n")
            f.write(f"Figures: {len(page.images)}\n\n")
            
            # Table details
            if page.tables:
                f.write(f"\n--- TABLES ---\n")
                for idx, table in enumerate(page.tables):
                    f.write(f"\nTable {idx + 1}:\n")
                    f.write(f"  ID: {table.table_id}\n")
                    f.write(f"  Rows: {table.row_count}\n")
                    f.write(f"  Columns: {table.column_count}\n")
                    f.write(f"  Pages: {table.page_nums}\n")
                    if table.rendered_text:
                        f.write(f"  Rendered Text (FULL):\n")
                        f.write(f"  {'-'*60}\n")
                        f.write(f"{table.rendered_text}\n")
                        f.write(f"  {'-'*60}\n")
                    if table.summary:
                        f.write(f"  Summary: {table.summary}\n")
            
            # Figure details
            if page.images:
                f.write(f"\n--- FIGURES ---\n")
                for idx, figure in enumerate(page.images):
                    f.write(f"\nFigure {idx + 1}:\n")
                    f.write(f"  ID: {figure.figure_id}\n")
                    f.write(f"  Filename: {figure.filename}\n")
                    f.write(f"  Size: {len(figure.image_bytes)} bytes\n")
                    f.write(f"  BBox: {figure.bbox}\n")
                    if figure.title:
                        f.write(f"  Title: {figure.title}\n")
                    if figure.description:
                        f.write(f"  Description: {figure.description}\n")
                    if figure.url:
                        f.write(f"  URL: {figure.url}\n")
            
            # Full text content for debugging
            f.write(f"\n--- TEXT CONTENT (FULL) ---\n")
            f.write(f"{'-'*60}\n")
            f.write(f"{page.text}\n")
            f.write(f"{'-'*60}\n")
            f.write(f"(Total length: {len(page.text)} characters)\n")
    
    get_logger().info(f"DI summary saved: {summary_file}")


def log_chunking_process(log_dir: Path, doc_name: str, chunks: list) -> None:
    """Log chunking process details.
    
    Args:
        log_dir: Directory to save logs
        doc_name: Document name
        chunks: List of generated chunks
    """
    chunk_log_dir = log_dir / "chunking"
    chunk_log_dir.mkdir(exist_ok=True)
    
    chunk_file = chunk_log_dir / f"{doc_name}_chunks.txt"
    
    with open(chunk_file, 'w', encoding='utf-8') as f:
        f.write(f"Chunking Process Log\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Document: {doc_name}\n")
        f.write(f"Total Chunks: {len(chunks)}\n\n")
        
        # Group chunks by page
        chunks_by_page: Dict[int, list] = {}
        for chunk in chunks:
            page_num = chunk.page_num
            if page_num not in chunks_by_page:
                chunks_by_page[page_num] = []
            chunks_by_page[page_num].append(chunk)
        
        # Write page by page
        for page_num in sorted(chunks_by_page.keys()):
            page_chunks = chunks_by_page[page_num]
            f.write(f"\n{'='*60}\n")
            f.write(f"Page {page_num + 1} - {len(page_chunks)} chunk(s)\n")
            f.write(f"{'='*60}\n\n")
            
            for idx, chunk in enumerate(page_chunks):
                f.write(f"\n--- Chunk {chunk.chunk_index_on_page + 1} ---\n")
                f.write(f"Index on Page: {chunk.chunk_index_on_page}\n")
                f.write(f"Page: {chunk.page_num + 1}\n")
                f.write(f"Content Length: {len(chunk.text)} characters\n")
                f.write(f"Token Count: {chunk.token_count}\n")
                
                # Check if chunk contains tables or figures
                if chunk.tables:
                    f.write(f"Contains: {len(chunk.tables)} TABLE(S)\n")
                    for table in chunk.tables:
                        f.write(f"  - Table ID: {table.table_id}\n")
                if chunk.images:
                    f.write(f"Contains: {len(chunk.images)} FIGURE(S)\n")
                    for image in chunk.images:
                        f.write(f"  - Figure ID: {image.figure_id}\n")
                
                f.write(f"\nContent:\n")
                f.write(f"{'-'*60}\n")
                f.write(f"{chunk.text}\n")
                f.write(f"{'-'*60}\n\n")
                
                # Additional info
                if chunk.char_span:
                    f.write(f"Character Span: {chunk.char_span}\n")
                f.write(f"\n")
    
    get_logger().info(f"Chunking log saved: {chunk_file}")


def log_table_processing(log_dir: Path, doc_name: str, page_num: int, table_idx: int, 
                         table: Any, rendered_text: str) -> None:
    """Log table processing details.
    
    Args:
        log_dir: Directory to save logs
        doc_name: Document name
        page_num: Page number
        table_idx: Table index on page
        table: Original table object
        rendered_text: Rendered text from TableRenderer
    """
    table_log_dir = log_dir / "tables"
    table_log_dir.mkdir(exist_ok=True)
    
    table_file = table_log_dir / f"{doc_name}_page{page_num+1}_table{table_idx+1}.txt"
    
    with open(table_file, 'w', encoding='utf-8') as f:
        f.write(f"Table Processing Log\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Document: {doc_name}\n")
        f.write(f"Page: {page_num + 1}\n")
        f.write(f"Table: {table_idx + 1}\n")
        f.write(f"Table ID: {table.table_id}\n\n")
        
        f.write(f"Structure:\n")
        f.write(f"  Rows: {table.row_count}\n")
        f.write(f"  Columns: {table.column_count}\n")
        f.write(f"  Pages: {table.page_nums}\n")
        f.write(f"  Cells: {len(table.cells)}\n")
        f.write(f"\n")
        
        f.write(f"Original Cells (from DI) - FULL:\n")
        f.write(f"{'-'*60}\n")
        # Show ALL cells with full content for debugging
        for i, cell in enumerate(table.cells):
            f.write(f"  Cell[{cell['row_index']},{cell['column_index']}]: {cell['content']}\n")
        f.write(f"{'-'*60}\n")
        f.write(f"Total cells: {len(table.cells)}\n\n")
        
        f.write(f"Rendered Text (for chunking):\n")
        f.write(f"{'-'*60}\n")
        f.write(f"{rendered_text}\n")
        f.write(f"{'-'*60}\n\n")
    
    get_logger().info(f"Table processing log saved: {table_file}")


def log_figure_processing(log_dir: Path, doc_name: str, page_num: int, figure_idx: int,
                          figure: Any, description: Optional[str] = None) -> None:
    """Log figure processing details.
    
    Args:
        log_dir: Directory to save logs
        doc_name: Document name
        page_num: Page number
        figure_idx: Figure index on page
        figure: Original figure object
        description: Generated description
    """
    figure_log_dir = log_dir / "figures"
    figure_log_dir.mkdir(exist_ok=True)
    
    figure_file = figure_log_dir / f"{doc_name}_page{page_num+1}_figure{figure_idx+1}.txt"
    
    with open(figure_file, 'w', encoding='utf-8') as f:
        f.write(f"Figure Processing Log\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Document: {doc_name}\n")
        f.write(f"Page: {page_num + 1}\n")
        f.write(f"Figure: {figure_idx + 1}\n")
        f.write(f"Figure ID: {figure.figure_id}\n\n")
        
        f.write(f"Properties:\n")
        f.write(f"  Filename: {figure.filename}\n")
        f.write(f"  MIME Type: {figure.mime_type}\n")
        f.write(f"  Size: {len(figure.image_bytes)} bytes\n")
        f.write(f"  BBox: {figure.bbox}\n")
        if figure.title:
            f.write(f"  Title: {figure.title}\n")
        if figure.placeholder:
            f.write(f"  Placeholder: {figure.placeholder}\n")
        f.write(f"\n")
        
        if description:
            f.write(f"Generated Description:\n")
            f.write(f"{'-'*60}\n")
            f.write(f"{description}\n")
            f.write(f"{'-'*60}\n\n")
        
        # Save image file
        image_file = figure_log_dir / f"{doc_name}_page{page_num+1}_figure{figure_idx+1}.png"
        with open(image_file, 'wb') as img_f:
            img_f.write(figure.image_bytes)
        f.write(f"Image saved to: {image_file.name}\n")
    
    get_logger().info(f"Figure processing log saved: {figure_file}")


def log_pipeline_summary(log_dir: Path, stats: Dict[str, Any]) -> None:
    """Log overall pipeline execution summary.
    
    Args:
        log_dir: Directory to save logs
        stats: Statistics dictionary
    """
    summary_file = log_dir / "pipeline_summary.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Pipeline Execution Summary\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    
    get_logger().info(f"Pipeline summary saved: {summary_file}")

