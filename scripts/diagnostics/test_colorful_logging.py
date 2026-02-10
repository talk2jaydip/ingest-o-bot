"""Test script to demonstrate colorful logging.

Run this script to see colored log output for different log levels.

Usage:
    python scripts/diagnostics/test_colorful_logging.py
    python scripts/diagnostics/test_colorful_logging.py --no-colors
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ingestor.logging_utils import setup_logging, get_logger


def main():
    """Demonstrate colorful logging with all log levels."""
    parser = argparse.ArgumentParser(description="Test colorful logging")
    parser.add_argument(
        "--no-colors",
        action="store_true",
        help="Disable colorful output"
    )
    args = parser.parse_args()

    # Setup logging with colors
    use_colors = not args.no_colors
    logger, log_dir = setup_logging(
        console_level="DEBUG",
        file_level="DEBUG",
        use_colors=use_colors
    )

    print("\n" + "="*70)
    print("Colorful Logging Test")
    print("="*70 + "\n")

    if use_colors:
        print("✨ Colors are ENABLED")
        print("You should see different colors for each log level below:\n")
    else:
        print("🚫 Colors are DISABLED")
        print("All logs will appear in plain text:\n")

    # Test all log levels
    logger.debug("🔍 DEBUG: This is a debug message - detailed diagnostic information")
    logger.info("ℹ️  INFO: This is an info message - general informational updates")
    logger.warning("⚠️  WARNING: This is a warning message - something to watch out for")
    logger.error("❌ ERROR: This is an error message - something went wrong")
    logger.critical("🔥 CRITICAL: This is a critical message - immediate attention needed")

    print("\n" + "="*70)
    print("Log levels should appear as follows when colors are enabled:")
    print("  DEBUG    = Cyan")
    print("  INFO     = Green")
    print("  WARNING  = Yellow")
    print("  ERROR    = Red")
    print("  CRITICAL = Bold Red")
    print("="*70 + "\n")

    print(f"📁 Full logs saved to: {log_dir}")
    print(f"📄 Log file: {log_dir / 'pipeline.log'}\n")

    # Test with child logger
    child_logger = get_logger("test_module")
    print("Testing child logger (should show as 'ingestor.test_module'):")
    child_logger.info("This is from a child logger")
    child_logger.warning("Child logger warning message")

    print("\n✅ Test complete!\n")


if __name__ == "__main__":
    main()
