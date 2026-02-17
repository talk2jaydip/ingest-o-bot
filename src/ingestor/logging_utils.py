"""Enhanced logging utilities for ingest-o-bot.

Provides centralized logging configuration with console and file handlers,
UTF-8 encoding support, and configurable log levels.
"""

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
        # Extract just the last part of the module name for cleaner logs
        module_name = name.split('.')[-1]
        return logging.getLogger(f"{LOGGER_NAME}.{module_name}")
    return logging.getLogger(LOGGER_NAME)


def setup_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    use_colors: bool = True,
    log_dir: str = "./logs"
) -> tuple[logging.Logger, Path]:
    """Setup comprehensive logging for the pipeline.

    Args:
        console_level: Logging level for console output (INFO, DEBUG, WARNING, ERROR)
        file_level: Logging level for file output (DEBUG recommended for troubleshooting)
        use_colors: Whether to use colorful console output (requires colorama)
        log_dir: Directory for log files

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
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with configurable level
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))

    if use_colors:
        try:
            from colorama import Fore, Style, init as colorama_init
            colorama_init(autoreset=True)

            class ColoredFormatter(logging.Formatter):
                """Formatter that adds colors to console output."""

                COLORS = {
                    'DEBUG': Fore.CYAN,
                    'INFO': Fore.GREEN,
                    'WARNING': Fore.YELLOW,
                    'ERROR': Fore.RED,
                    'CRITICAL': Fore.RED + Style.BRIGHT,
                }

                def format(self, record):
                    levelname = record.levelname
                    if levelname in self.COLORS:
                        record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
                    return super().format(record)

            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        except ImportError:
            # colorama not available, use plain formatter
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with configurable level - with UTF-8 encoding for full content logging
    file_handler = logging.FileHandler(run_log_dir / "pipeline.log", encoding='utf-8')
    file_handler.setLevel(getattr(logging, file_level.upper()))
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

            # Full text content for debugging
            f.write(f"\n--- TEXT CONTENT (FULL) ---\n")
            f.write(f"{'-'*60}\n")
            f.write(f"{page.text}\n")
            f.write(f"{'-'*60}\n")
            f.write(f"(Total length: {len(page.text)} characters)\n")

    get_logger().info(f"DI summary saved: {summary_file}")


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


# Stub functions for pipeline (full implementation needed for document ingestion)
def log_chunking_process(*args, **kwargs):
    """Stub for chunking process logging."""
    pass


def log_di_response(*args, **kwargs):
    """Stub for DI response logging."""
    pass


def log_di_summary(*args, **kwargs):
    """Stub for DI summary logging."""
    pass


def log_figure_processing(*args, **kwargs):
    """Stub for figure processing logging."""
    pass


def log_table_processing(*args, **kwargs):
    """Stub for table processing logging."""
    pass
