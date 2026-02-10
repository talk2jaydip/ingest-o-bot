#!/bin/bash
# Quick test script for ingestor

echo "============================================================"
echo "ingestor - Test Run"
echo "============================================================"
echo ""

# Navigate to parent directory
cd "$(dirname "$0")/.."

# Check if env.test exists
if [ ! -f "envs/env.test" ]; then
    echo "ERROR: envs/env.test not found!"
    echo "Please create envs/env.test with your Azure credentials."
    exit 1
fi

# Copy test environment
echo "Copying test environment..."
cp envs/env.test .env

# Check if sample PDF exists
if [ ! -f "samples/sample_pages_test.pdf" ]; then
    echo "ERROR: samples/sample_pages_test.pdf not found!"
    echo "Please add a test PDF file."
    exit 1
fi

echo "Sample PDF found: samples/sample_pages_test.pdf"
echo ""

# Run the pipeline
echo "Starting pipeline..."
echo "============================================================"
python -m ingestor.cli --pdf samples/sample_pages_test.pdf

echo ""
echo "============================================================"
echo "Test complete!"
echo ""
echo "Check logs in: logs/run_*"
echo "Check artifacts in: test_artifacts/"
echo "============================================================"
