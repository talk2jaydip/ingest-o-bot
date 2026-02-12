@echo off
REM Quick test script for Windows - Test all environment scenarios
REM Usage: test-scenarios.bat

echo ====================================
echo Testing All Environment Scenarios
echo ====================================

REM Check if test document exists
if not exist "test-documents" mkdir test-documents
if not exist "test-documents\sample.pdf" (
    echo WARNING: No test document found at test-documents\sample.pdf
    echo Please add a test PDF file or update TEST_PDF variable
    set TEST_PDF=
) else (
    set TEST_PDF=test-documents\sample.pdf
)

REM Backup current .env
if exist .env (
    echo Backing up current .env to .env.backup
    copy /Y .env .env.backup > nul
)

echo.
echo ====================================
echo Test 1: Azure Local Input
echo ====================================
copy /Y envs\.env.azure-local-input.example .env > nul
echo Copied template: .env.azure-local-input.example

echo Validating configuration...
python -m ingestor.scenario_validator azure_full
if errorlevel 1 (
    echo ERROR: Validation failed for Azure Local Input
    goto :restore
)

echo Running pre-check...
python -m ingestor.cli --validate
if errorlevel 1 (
    echo ERROR: Pre-check failed for Azure Local Input
    goto :restore
)

if defined TEST_PDF (
    echo Testing with: %TEST_PDF%
    python -m ingestor.cli --pdf %TEST_PDF%
    if errorlevel 1 (
        echo ERROR: Processing failed for Azure Local Input
        goto :restore
    )
)

echo SUCCESS: Azure Local Input tests passed
echo.

REM Test 2: Azure + ChromaDB
echo ====================================
echo Test 2: Azure + ChromaDB Hybrid
echo ====================================
copy /Y envs\.env.azure-chromadb-hybrid.example .env > nul
echo Copied template: .env.azure-chromadb-hybrid.example

echo Validating configuration...
python -m ingestor.scenario_validator hybrid
if errorlevel 1 (
    echo ERROR: Validation failed for Azure + ChromaDB
    goto :restore
)

echo Running pre-check...
python -m ingestor.cli --validate
if errorlevel 1 (
    echo ERROR: Pre-check failed for Azure + ChromaDB
    goto :restore
)

if defined TEST_PDF (
    echo Testing with: %TEST_PDF%
    python -m ingestor.cli --pdf %TEST_PDF%
    if errorlevel 1 (
        echo ERROR: Processing failed for Azure + ChromaDB
        goto :restore
    )
)

echo SUCCESS: Azure + ChromaDB tests passed
echo.

REM Test 3: Fully Offline
echo ====================================
echo Test 3: Fully Offline
echo ====================================
copy /Y envs\.env.offline-with-vision.example .env > nul
echo Copied template: .env.offline-with-vision.example

echo Validating configuration...
python -m ingestor.scenario_validator offline
if errorlevel 1 (
    echo ERROR: Validation failed for Offline mode
    goto :restore
)

echo Running pre-check...
python -m ingestor.cli --validate
if errorlevel 1 (
    echo ERROR: Pre-check failed for Offline mode
    goto :restore
)

if defined TEST_PDF (
    echo Testing with: %TEST_PDF%
    python -m ingestor.cli --pdf %TEST_PDF%
    if errorlevel 1 (
        echo ERROR: Processing failed for Offline mode
        goto :restore
    )
)

echo SUCCESS: Offline tests passed
echo.

:restore
REM Restore original .env
if exist .env.backup (
    echo.
    echo Restoring original .env from backup
    copy /Y .env.backup .env > nul
    del .env.backup
)

echo.
echo ====================================
echo All Scenario Tests Completed!
echo ====================================
pause
