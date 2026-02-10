#!/bin/bash
# Debug chunking behavior for test documents

echo ""
echo "======================================================================"
echo "CHUNKING DEBUG TEST"
echo "======================================================================"
echo ""

# Get script directory and navigate to parent
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

# Run the test
python test_pipeline/test_chunking_debug.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Chunking debug test failed!"
    exit 1
fi

echo ""
echo "Test completed successfully!"
