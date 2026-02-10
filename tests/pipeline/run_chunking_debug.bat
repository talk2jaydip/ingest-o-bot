@echo off
REM Debug chunking behavior for test documents

echo.
echo ======================================================================
echo CHUNKING DEBUG TEST
echo ======================================================================
echo.

cd /d "%~dp0.."
python test_pipeline/test_chunking_debug.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Chunking debug test failed!
    pause
    exit /b 1
)

echo.
echo Test completed successfully!
pause
