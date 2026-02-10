#!/bin/bash

# =============================================================================
# Ingestor CLI Examples - All Usage Patterns
# =============================================================================
#
# This script demonstrates all the different ways to use the ingestor CLI.
# Copy and paste the examples you need.
#
# Prerequisites:
# - .env file with Azure credentials
# - Sample documents in appropriate directories
#
# =============================================================================

echo "Ingestor CLI Examples"
echo "===================="
echo ""
echo "Copy and paste these commands to your terminal:"
echo ""

# =============================================================================
# BASIC USAGE
# =============================================================================

echo "=== BASIC USAGE ==="
echo ""

# Single document
echo "# Process single document:"
echo "python -m ingestor.cli --input \"samples/document.pdf\""
echo ""

# Multiple documents with glob
echo "# Process all PDFs in directory:"
echo "python -m ingestor.cli --input \"samples/*.pdf\""
echo ""

# Recursive glob
echo "# Process all PDFs recursively:"
echo "python -m ingestor.cli --input \"documents/**/*.pdf\""
echo ""

# Multiple file types
echo "# Process multiple file types:"
echo "python -m ingestor.cli --input \"documents/**/*.{pdf,docx,pptx}\""
echo ""

# =============================================================================
# PERFORMANCE OPTIMIZATIONS
# =============================================================================

echo "=== PERFORMANCE OPTIMIZATIONS ==="
echo ""

# With parallel processing
echo "# With parallel processing (4 workers):"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --max-workers 4"
echo ""

# With high concurrency
echo "# With high concurrency:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" \\"
echo "  --max-workers 4 \\"
echo "  --openai-concurrency 10 \\"
echo "  --di-concurrency 5"
echo ""

# With integrated vectorization
echo "# With integrated vectorization (fastest):"
echo "python -m ingestor.cli --input \"docs/*.pdf\" \\"
echo "  --max-workers 4 \\"
echo "  --integrated-vectorization"
echo ""

# Full optimization
echo "# Full optimization (recommended):"
echo "python -m ingestor.cli --input \"docs/**/*.pdf\" \\"
echo "  --max-workers 4 \\"
echo "  --openai-concurrency 10 \\"
echo "  --di-concurrency 5 \\"
echo "  --integrated-vectorization"
echo ""

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

echo "=== ENVIRONMENT CONFIGURATION ==="
echo ""

# Default .env
echo "# Use default .env file:"
echo "python -m ingestor.cli --input \"docs/*.pdf\""
echo ""

# Custom .env
echo "# Use custom .env file:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --env-path \".env.production\""
echo ""

# Development environment
echo "# Development environment:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --env-path \".env.development\""
echo ""

# Staging environment
echo "# Staging environment:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --env-path \".env.staging\""
echo ""

# =============================================================================
# CUSTOM INDEX
# =============================================================================

echo "=== CUSTOM INDEX ==="
echo ""

# Custom index name
echo "# Use custom index:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --search-index \"my-custom-index\""
echo ""

# Override env with custom index
echo "# Override env with custom index:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" \\"
echo "  --env-path \".env\" \\"
echo "  --search-index \"temporary-index\""
echo ""

# =============================================================================
# CHUNKING CONFIGURATION
# =============================================================================

echo "=== CHUNKING CONFIGURATION ==="
echo ""

# Custom chunk size
echo "# Custom chunk size:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --chunking-max-tokens 1500"
echo ""

# Custom overlap
echo "# Custom overlap:"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --chunking-overlap 20"
echo ""

# Both chunking options
echo "# Custom chunking (size + overlap):"
echo "python -m ingestor.cli --input \"docs/*.pdf\" \\"
echo "  --chunking-max-tokens 1500 \\"
echo "  --chunking-overlap 20"
echo ""

# =============================================================================
# DOCUMENT ACTIONS
# =============================================================================

echo "=== DOCUMENT ACTIONS ==="
echo ""

# Add (default)
echo "# Add documents (default):"
echo "python -m ingestor.cli --input \"docs/*.pdf\" --action add"
echo ""

# Remove specific documents
echo "# Remove specific documents:"
echo "python -m ingestor.cli --input \"old_document.pdf\" --action remove"
echo ""

# Remove all documents
echo "# Remove ALL documents (WARNING!):"
echo "python -m ingestor.cli --action remove-all"
echo ""

# =============================================================================
# COMMON SCENARIOS
# =============================================================================

echo "=== COMMON SCENARIOS ==="
echo ""

# Scenario 1: Quick single document
echo "# Scenario 1: Quick single document:"
echo "python -m ingestor.cli --input \"document.pdf\""
echo ""

# Scenario 2: Batch with optimization
echo "# Scenario 2: Optimized batch processing:"
echo "python -m ingestor.cli --input \"documents/**/*.pdf\" \\"
echo "  --max-workers 4 \\"
echo "  --integrated-vectorization"
echo ""

# Scenario 3: Production ingestion
echo "# Scenario 3: Production ingestion:"
echo "python -m ingestor.cli --input \"data/**/*.pdf\" \\"
echo "  --env-path \".env.production\" \\"
echo "  --max-workers 8 \\"
echo "  --openai-concurrency 15 \\"
echo "  --integrated-vectorization"
echo ""

# Scenario 4: Update existing documents
echo "# Scenario 4: Update existing documents:"
echo "python -m ingestor.cli --input \"updated/*.pdf\" --action add"
echo "# (Automatically removes old versions)"
echo ""

# Scenario 5: Clean up old documents
echo "# Scenario 5: Remove old documents:"
echo "python -m ingestor.cli --input \"archive/*.pdf\" --action remove"
echo ""

# Scenario 6: Process Office documents
echo "# Scenario 6: Process Office documents:"
echo "python -m ingestor.cli --input \"reports/**/*.{docx,pptx}\""
echo ""

# =============================================================================
# CONVENIENCE WRAPPER
# =============================================================================

echo "=== CONVENIENCE WRAPPER ==="
echo ""

# Using run_cli.py wrapper
echo "# Using convenience wrapper (same options):"
echo "python examples/scripts/run_cli.py --input \"docs/*.pdf\" --max-workers 4"
echo ""

# =============================================================================
# BATCH SCRIPTS
# =============================================================================

echo "=== BATCH SCRIPTS ==="
echo ""

# Daily ingestion
echo "# Daily document ingestion script:"
echo "#!/bin/bash"
echo "python -m ingestor.cli --input \"/data/daily/**/*.pdf\" \\"
echo "  --env-path \".env.production\" \\"
echo "  --max-workers 4 \\"
echo "  --integrated-vectorization"
echo ""

# Cleanup script
echo "# Cleanup old documents script:"
echo "#!/bin/bash"
echo "python -m ingestor.cli --input \"/data/archive/*.pdf\" --action remove"
echo ""

# =============================================================================
# DEBUGGING AND TESTING
# =============================================================================

echo "=== DEBUGGING AND TESTING ==="
echo ""

# Test with single file
echo "# Test with single file:"
echo "python -m ingestor.cli --input \"samples/test.pdf\" --env-path \".env.development\""
echo ""

# Conservative settings for debugging
echo "# Conservative settings (for debugging):"
echo "python -m ingestor.cli --input \"docs/*.pdf\" \\"
echo "  --max-workers 1 \\"
echo "  --openai-concurrency 3 \\"
echo "  --di-concurrency 2"
echo ""

# =============================================================================
# HELP
# =============================================================================

echo "=== HELP ==="
echo ""

# Show help
echo "# Show all available options:"
echo "python -m ingestor.cli --help"
echo ""
echo "# Show wrapper script help:"
echo "python examples/scripts/run_cli.py --help"
echo ""

# =============================================================================
# TIPS
# =============================================================================

echo "=== TIPS ==="
echo ""
echo "1. Always test with a small dataset first"
echo "2. Use --max-workers based on your Azure quota"
echo "3. Enable --integrated-vectorization for best performance"
echo "4. Use different .env files for different environments"
echo "5. Monitor logs for rate limit warnings"
echo "6. Start with conservative settings and increase gradually"
echo ""

echo "=== DOCUMENTATION ==="
echo ""
echo "Full documentation:"
echo "  - QUICK_START_OPTIMIZATIONS.md"
echo "  - BATCH_PROCESSING_SUPPORT.md"
echo "  - examples/notebooks/00_quick_playbook.ipynb"
echo ""

echo "Test scripts:"
echo "  - python examples/scripts/test_parallel_quick.py"
echo "  - python examples/scripts/test_parallel_performance.py"
echo ""
