@echo off
REM Quick test script for ingestor

echo ============================================================
echo ingestor - Test Run
echo ============================================================
echo.

REM Navigate to parent directory
cd /d "%~dp0.."

REM Check if env.test exists
if not exist envs\env.test (
    echo ERROR: envs\env.test not found!
    echo Please create envs\env.test with your Azure credentials.
    exit /b 1
)

REM Copy test environment
echo Copying test environment...
copy /Y envs\env.test .env >nul

REM Check if sample PDF exists
if not exist samples\sample_pages_test.pdf (
    echo ERROR: samples\sample_pages_test.pdf not found!
    echo Please add a test PDF file.
    exit /b 1
)

echo Sample PDF found: samples\sample_pages_test.pdf
echo.

REM Run the pipeline
echo Starting pipeline...
echo ============================================================
python -m ingestor.cli --pdf samples\sample_pages_test.pdf

echo.
echo ============================================================
echo Test complete!
echo.
echo Check logs in: logs\run_*
echo Check artifacts in: test_artifacts\
echo ============================================================

pause
