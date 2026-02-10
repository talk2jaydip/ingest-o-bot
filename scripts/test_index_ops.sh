#!/bin/bash
# Test Index Operations Script
# Tests the new --index-only and --delete-index features

echo "========================================"
echo "Testing Index Operations"
echo "========================================"
echo

echo "Test 1: Check Index Status"
echo "----------------------------"
python -m ingestor.cli --index-only --verbose
if [ $? -ne 0 ]; then
    echo "FAILED: Index check failed"
    exit 1
fi
echo "PASSED: Index check succeeded"
echo

echo "Test 2: Delete Index (if exists)"
echo "---------------------------------"
python -m ingestor.cli --delete-index
if [ $? -ne 0 ]; then
    echo "FAILED: Delete operation failed"
    exit 1
fi
echo "PASSED: Delete operation succeeded"
echo

echo "Test 3: Recreate Index"
echo "-----------------------"
python -m ingestor.cli --index-only
if [ $? -ne 0 ]; then
    echo "FAILED: Index creation failed"
    exit 1
fi
echo "PASSED: Index created successfully"
echo

echo "========================================"
echo "All tests passed!"
echo "========================================"
echo
echo "You can now run ingestion with:"
echo "python -m ingestor.cli --glob 'documents/*.pdf'"
