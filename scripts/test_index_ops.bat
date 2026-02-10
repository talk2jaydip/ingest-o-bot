@echo off
REM Test Index Operations Script
REM Tests the new --index-only and --delete-index features

echo ========================================
echo Testing Index Operations
echo ========================================
echo.

echo Test 1: Check Index Status
echo ----------------------------
python -m ingestor.cli --index-only --verbose
if %ERRORLEVEL% NEQ 0 (
    echo FAILED: Index check failed
    exit /b 1
)
echo PASSED: Index check succeeded
echo.

echo Test 2: Delete Index (if exists)
echo ---------------------------------
python -m ingestor.cli --delete-index
if %ERRORLEVEL% NEQ 0 (
    echo FAILED: Delete operation failed
    exit /b 1
)
echo PASSED: Delete operation succeeded
echo.

echo Test 3: Recreate Index
echo -----------------------
python -m ingestor.cli --index-only
if %ERRORLEVEL% NEQ 0 (
    echo FAILED: Index creation failed
    exit /b 1
)
echo PASSED: Index created successfully
echo.

echo ========================================
echo All tests passed!
echo ========================================
echo.
echo You can now run ingestion with:
echo python -m ingestor.cli --glob "documents/*.pdf"
