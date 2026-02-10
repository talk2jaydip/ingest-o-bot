#!/bin/bash
# Test script to check embeddings in Azure AI Search index

echo "======================================================================"
echo "Running Embeddings Verification Test"
echo "======================================================================"
echo ""

# Check if we're in the test_pipeline directory
if [ -f "test_embeddings_check.py" ]; then
    python test_embeddings_check.py
else
    # Try running from parent directory
    python test_pipeline/test_embeddings_check.py
fi

echo ""
echo "======================================================================"
echo "Test completed"
echo "======================================================================"
