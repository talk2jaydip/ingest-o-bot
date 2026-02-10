@echo off
REM Quick test script for ingestor

echo ============================================================
echo ingestor - Test Run
echo ============================================================
echo.

REM Check if .env.test exists
if not exist env.test (
    echo ERROR: env.test not found!
    echo Please create env.test with your Azure credentials.
    exit /b 1
)

REM Copy test environment
echo Copying test environment...
copy /Y env.test .env >nul

REM Check if sample PDF exists
if not exist sample_pages_test.pdf (
    echo ERROR: sample_pages_test.pdf not found!
    echo Please add a test PDF file.
    exit /b 1
)

echo Sample PDF found: sample_pages_test.pdf
echo.

REM Run the pipeline
echo Starting pipeline...
echo ============================================================
python -m cli

echo.
echo ============================================================
echo Test complete!
echo.
echo Check logs in: logs\run_*
echo Check artifacts in: test_artifacts\
echo ============================================================

pause

