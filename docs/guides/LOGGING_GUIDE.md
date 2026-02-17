# Logging Guide

## Overview

The ingestor uses a centralized logging system that provides:
- **Colorful console output** with ANSI colors for different log levels
- Consistent logging across all modules
- Configurable log levels for console and file output
- Optional artifact writing for debugging vs. production
- UTF-8 encoding support for emojis and special characters

## Key Changes

### 1. Colorful Console Logging

The logging system now supports colorful console output with ANSI colors for different log levels:

- **DEBUG**: <span style="color: cyan">Cyan</span> - Detailed debugging information
- **INFO**: <span style="color: green">Green</span> - General informational messages
- **WARNING**: <span style="color: yellow">Yellow</span> - Warning messages
- **ERROR**: <span style="color: red">Red</span> - Error messages
- **CRITICAL**: <span style="color: red; font-weight: bold">Bold Red</span> - Critical errors

**Enable/Disable Colors:**

```python
from ingestor.logging_utils import setup_logging

# Enable colors (default)
logger, log_dir = setup_logging(use_colors=True)

# Disable colors (for CI/CD or piped output)
logger, log_dir = setup_logging(use_colors=False)
```

**CLI Usage:**
```bash
# With colors (default)
python -m ingestor.cli --glob "documents/*.pdf"

# Without colors
python -m ingestor.cli --no-colors --glob "documents/*.pdf"
```

**Environment Variable:**
```bash
# Disable colors via environment
LOG_USE_COLORS=false python -m ingestor.cli --glob "documents/*.pdf"
```

Colors make it easier to visually distinguish log levels in the console during development and debugging. They are automatically disabled when output is piped or redirected, but can also be manually disabled for CI/CD environments.

### 2. Centralized Logger

All modules now use a centralized logger named `"ingestor"`. This ensures consistent formatting and configuration across the entire application.

**Usage:**
```python
from ingestor.logging_utils import get_logger

logger = get_logger(__name__)
logger.info("Processing document")
logger.debug("Detailed debugging information")
```

The `get_logger(__name__)` function creates child loggers that inherit from the main logger, making it easy to trace which module generated each log message.

### 3. Configurable Log Levels

The `setup_logging()` function now accepts configurable log levels:

```python
from ingestor.logging_utils import setup_logging

# Default behavior (INFO to console, DEBUG to file)
logger, log_dir = setup_logging()

# Custom log levels
logger, log_dir = setup_logging(
    log_dir="./logs",
    console_level="WARNING",  # Only show warnings and errors in console
    file_level="DEBUG"         # Capture everything in log files
)
```

**Available log levels:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Typical configurations:**
- **Development:** `console_level="DEBUG"` - See everything in console
- **Production:** `console_level="INFO"` or `"WARNING"` - Cleaner console output
- **Debugging:** `console_level="DEBUG", file_level="DEBUG"` - Maximum verbosity

### 4. Artifact Writing Control

All logging functions now support a `write_artifacts` parameter to control whether detailed artifact files are written. This is useful for production environments where you want logs but not detailed debugging files.

```python
from ingestor.logging_utils import log_di_response, log_chunking_process

# Development: Write all artifacts for debugging
log_di_response(log_dir, doc_name, di_result, write_artifacts=True)
log_chunking_process(log_dir, doc_name, chunks, write_artifacts=True)

# Production: Skip artifact writing to save disk space and I/O
log_di_response(log_dir, doc_name, di_result, write_artifacts=False)
log_chunking_process(log_dir, doc_name, chunks, write_artifacts=False)
```

**Affected functions:**
- `log_di_response()`
- `log_di_summary()`
- `log_chunking_process()`
- `log_table_processing()`
- `log_figure_processing()`

When `write_artifacts=False`, the functions return immediately without writing any files, reducing disk I/O and storage requirements.

### 5. Reduced Console Noise

Artifact save messages now use `DEBUG` level instead of `INFO` level. This means you won't see "DI response saved", "Chunking log saved", etc. in the console unless you set `console_level="DEBUG"`.

```python
# Before: logger.info(f"DI response saved: {response_file}")
# After:  logger.debug(f"DI response saved: {response_file}")
```

This keeps console output focused on the pipeline's progress, while file logs still contain all details.

## Best Practices

### For Development

```python
# Maximum visibility for debugging
logger, log_dir = setup_logging(
    console_level="DEBUG",
    file_level="DEBUG"
)

# Write all artifacts
log_di_response(log_dir, doc_name, result, write_artifacts=True)
```

### For Production

```python
# Clean console output, detailed file logs
logger, log_dir = setup_logging(
    console_level="INFO",
    file_level="DEBUG"
)

# Skip artifact writing to save resources
log_di_response(log_dir, doc_name, result, write_artifacts=False)
```

### For CI/CD or Automated Testing

```python
# Warnings only to console, full debug to file, no colors for clean logs
logger, log_dir = setup_logging(
    console_level="WARNING",
    file_level="DEBUG",
    use_colors=False  # Disable colors for CI/CD
)

# Conditionally write artifacts based on test failure
write_artifacts = test_failed or debug_mode
log_chunking_process(log_dir, doc_name, chunks, write_artifacts=write_artifacts)
```

**Environment variables for CI/CD:**
```bash
# In CI/CD pipeline configuration
LOG_LEVEL=WARNING
LOG_USE_COLORS=false
LOG_ARTIFACTS=false
```

## Log File Structure

When `setup_logging()` is called, it creates a timestamped run directory:

```
logs/
└── run_20260210_143052/
    ├── pipeline.log              # Main log file with all messages
    ├── di_responses/             # Document Intelligence artifacts
    │   ├── doc1_di_response.json
    │   └── doc1_summary.txt
    ├── chunking/                 # Chunking artifacts
    │   └── doc1_chunks.txt
    ├── tables/                   # Table processing artifacts
    │   └── doc1_page1_table1.txt
    ├── figures/                  # Figure processing artifacts
    │   ├── doc1_page1_figure1.txt
    │   └── doc1_page1_figure1.png
    └── pipeline_summary.txt      # Final execution summary
```

## UTF-8 Encoding

The logging system now properly handles UTF-8 characters including emojis:

```python
logger.info("Processing document 📄")
logger.info("✅ Document processed successfully")
```

This works because `setup_logging()` wraps `sys.stdout` and `sys.stderr` in UTF-8 text wrappers and uses UTF-8 encoding for file handlers.

## Migration Guide

If you're updating existing code:

### Old Code
```python
import logging
logger = logging.getLogger(__name__)

# Later...
logger, log_dir = setup_logging()
```

### New Code
```python
from ingestor.logging_utils import get_logger, setup_logging

logger = get_logger(__name__)

# Later...
logger, log_dir = setup_logging(
    console_level="INFO",  # Specify levels
    file_level="DEBUG"
)

# Add write_artifacts parameter to logging functions
log_di_response(log_dir, doc, result, write_artifacts=True)
```

## Troubleshooting

### Issue: Too much console output

**Solution:** Increase console log level
```python
logger, log_dir = setup_logging(console_level="WARNING")
```

### Issue: Missing debug information

**Solution:** Check file logs in `logs/run_*/pipeline.log` - they contain full DEBUG output by default.

### Issue: Disk space concerns

**Solution:** Disable artifact writing in production
```python
log_di_response(log_dir, doc, result, write_artifacts=False)
```

### Issue: Encoding errors with special characters

**Solution:** The logging system now handles UTF-8 automatically. If you still see issues, ensure your terminal supports UTF-8.

### Issue: Colors not appearing in console

**Solution:**
- Check that `use_colors=True` in setup_logging() or `LOG_USE_COLORS=true` in environment
- Some terminals don't support ANSI colors (e.g., older Windows Command Prompt). Use Windows Terminal, PowerShell, or modern terminal emulators
- If piping output (`python -m ingestor.cli | tee log.txt`), colors may be stripped. Use `--no-colors` flag

### Issue: Colors appear as weird characters

**Solution:** Your terminal doesn't support ANSI escape codes. Use `--no-colors` flag or set `LOG_USE_COLORS=false`

## Summary of Changes

| Feature | Before | After |
|---------|--------|-------|
| **Console colors** | Plain text | Colorful ANSI colors for log levels |
| **Log levels** | Hardcoded (INFO/DEBUG) | Configurable parameters |
| **Artifact writing** | Always on | Optional with `write_artifacts` parameter |
| **Console noise** | INFO level for artifact saves | DEBUG level for artifact saves |
| **Logger naming** | Inconsistent | Centralized with `get_logger()` |
| **Encoding** | Platform-dependent | UTF-8 everywhere |

These changes make the logging system more flexible, production-ready, and easier to manage across different environments. The colorful console output improves readability during development and debugging.
