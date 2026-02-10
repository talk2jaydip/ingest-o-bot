#!/bin/bash
# Quick test script for ingestor

echo "============================================================"
echo "ingestor - Test Run"
echo "============================================================"
echo ""

# Check if env.test exists
if [ ! -f "env.test" ]; then
    echo "ERROR: env.test not found!"
    echo "Please create env.test with your Azure credentials."
    exit 1
fi

# Copy test environment
echo "Copying test environment..."
cp env.test .env

# Check if sample PDF exists
if [ ! -f "sample_pages_test.pdf" ]; then
    echo "ERROR: sample_pages_test.pdf not found!"
    echo "Please add a test PDF file."
    exit 1
fi

echo "Sample PDF found: sample_pages_test.pdf"
echo ""

# Run the pipeline
echo "Starting pipeline..."
echo "============================================================"
python -m cli

echo ""
echo "============================================================"
echo "Test complete!"
echo ""
echo "Check logs in: logs/run_*"
echo "Check artifacts in: test_artifacts/"
echo "============================================================"

