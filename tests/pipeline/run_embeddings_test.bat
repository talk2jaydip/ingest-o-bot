@echo off
REM Test script to check embeddings in Azure AI Search index

echo ======================================================================
echo Running Embeddings Verification Test
echo ======================================================================
echo.

REM Check if we're in the test_pipeline directory
if exist "test_embeddings_check.py" (
    python test_embeddings_check.py
) else (
    REM Try running from parent directory
    python test_pipeline\test_embeddings_check.py
)

echo.
echo ======================================================================
echo Test completed
echo ======================================================================
pause
