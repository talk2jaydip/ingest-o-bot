@echo off
REM ============================================================================
REM CLI Examples - Quick Reference Script
REM ============================================================================
REM
REM This script demonstrates all possible CLI commands and combinations.
REM Uncomment the commands you want to run.
REM
REM ⚠️  SAFETY NOTE: Some commands are marked as DESTRUCTIVE - use carefully!
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║           ingest-o-bot CLI - All Commands Examples              ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM ============================================================================
REM 1. VALIDATION & DIAGNOSTICS
REM ============================================================================
echo [SECTION 1] VALIDATION ^& DIAGNOSTICS
echo ========================================
echo.

REM Basic validation
echo Example: python -m ingestor.cli --validate
REM python -m ingestor.cli --validate

REM Validation with verbose
echo Example: python -m ingestor.cli --validate --verbose
REM python -m ingestor.cli --validate --verbose

REM Check specific env file
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate

REM Use scenario validator
echo Example: python -m ingestor.scenario_validator
REM python -m ingestor.scenario_validator

REM Scenario validator with env file
echo Example: python -m ingestor.scenario_validator --env-file .env.test
REM python -m ingestor.scenario_validator --env-file .env.test

echo.
pause
echo.

REM ============================================================================
REM 2. INDEX MANAGEMENT
REM ============================================================================
echo [SECTION 2] INDEX MANAGEMENT
echo ========================================
echo.

REM Check if index exists
echo Example: python -m ingestor.cli --check-index
REM python -m ingestor.cli --check-index

REM Setup/create index
echo Example: python -m ingestor.cli --setup-index
REM python -m ingestor.cli --setup-index

REM Setup index only (no ingestion)
echo Example: python -m ingestor.cli --index-only
REM python -m ingestor.cli --index-only

REM Update index schema
echo Example: python -m ingestor.cli --setup-index --skip-ingestion
REM python -m ingestor.cli --setup-index --skip-ingestion

echo.
echo ⚠️  DESTRUCTIVE OPERATIONS (commented out for safety):
echo.

REM Delete index (DESTRUCTIVE)
echo Example: python -m ingestor.cli --delete-index
REM ⚠️  python -m ingestor.cli --delete-index

REM Force recreate index (DESTRUCTIVE)
echo Example: python -m ingestor.cli --force-index
REM ⚠️  python -m ingestor.cli --force-index

echo.
pause
echo.

REM ============================================================================
REM 3. DOCUMENT PROCESSING - INPUT SOURCES
REM ============================================================================
echo [SECTION 3] DOCUMENT PROCESSING
echo ========================================
echo.

REM Process single PDF
echo Example: python -m ingestor.cli --pdf data/sample.pdf
REM python -m ingestor.cli --pdf data/sample.pdf

REM Process with --file alias
echo Example: python -m ingestor.cli --file data/sample.pdf
REM python -m ingestor.cli --file data/sample.pdf

REM Process multiple files with glob
echo Example: python -m ingestor.cli --glob "data/*.pdf"
REM python -m ingestor.cli --glob "data/*.pdf"

REM Recursive glob pattern
echo Example: python -m ingestor.cli --glob "data/**/*.pdf"
REM python -m ingestor.cli --glob "data/**/*.pdf"

REM Process all supported file types
echo Example: python -m ingestor.cli --glob "data/**/*"
REM python -m ingestor.cli --glob "data/**/*"

echo.
pause
echo.

REM ============================================================================
REM 4. DOCUMENT ACTIONS
REM ============================================================================
echo [SECTION 4] DOCUMENT ACTIONS
echo ========================================
echo.

REM Add documents (default action)
echo Example: python -m ingestor.cli --glob "data/*.pdf"
REM python -m ingestor.cli --glob "data/*.pdf"

REM Explicitly specify add action
echo Example: python -m ingestor.cli --action add --glob "data/*.pdf"
REM python -m ingestor.cli --action add --glob "data/*.pdf"

REM Remove specific documents
echo Example: python -m ingestor.cli --action remove --glob "old_document.pdf"
REM python -m ingestor.cli --action remove --glob "old_document.pdf"

echo.
echo ⚠️  DESTRUCTIVE OPERATION (commented out for safety):
echo.

REM Remove ALL documents (DESTRUCTIVE)
echo Example: python -m ingestor.cli --action removeall
REM ⚠️  python -m ingestor.cli --action removeall

echo.
pause
echo.

REM ============================================================================
REM 5. ENVIRONMENT FILES
REM ============================================================================
echo [SECTION 5] ENVIRONMENT FILES
echo ========================================
echo.

REM Default .env
echo Example: python -m ingestor.cli --validate
REM python -m ingestor.cli --validate

REM Scenario 01: Azure Full Local
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-01-azure-full-local.example --validate

REM Scenario 02: Azure Full Blob
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-02-azure-full-blob.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-02-azure-full-blob.example --validate

REM Scenario 03: ChromaDB
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-03-azure-di-chromadb.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-03-azure-di-chromadb.example --validate

REM Scenario 04: Integrated Vectorization
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-04-azure-integrated-vectorization.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-04-azure-integrated-vectorization.example --validate

REM Scenario 05: Vision Heavy
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-05-azure-vision-heavy.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-05-azure-vision-heavy.example --validate

REM Scenario 06: Multilingual
echo Example: python -m ingestor.cli --env-file envs/.env.scenario-06-azure-multilingual.example --validate
REM python -m ingestor.cli --env-file envs/.env.scenario-06-azure-multilingual.example --validate

REM Custom env file
echo Example: python -m ingestor.cli --env-file C:\configs\.env.custom --validate
REM python -m ingestor.cli --env-file C:\configs\.env.custom --validate

echo.
pause
echo.

REM ============================================================================
REM 6. LOGGING & OUTPUT
REM ============================================================================
echo [SECTION 6] LOGGING ^& OUTPUT
echo ========================================
echo.

REM Verbose logging
echo Example: python -m ingestor.cli --verbose --glob "data/*.pdf"
REM python -m ingestor.cli --verbose --glob "data/*.pdf"

REM No colors (for CI/CD)
echo Example: python -m ingestor.cli --no-colors --glob "data/*.pdf"
REM python -m ingestor.cli --no-colors --glob "data/*.pdf"

REM Verbose + No colors
echo Example: python -m ingestor.cli --verbose --no-colors --validate
REM python -m ingestor.cli --verbose --no-colors --validate

REM Log to file
echo Example: python -m ingestor.cli --verbose --no-colors --glob "data/*.pdf" ^> processing.log 2^>^&1
REM python -m ingestor.cli --verbose --no-colors --glob "data/*.pdf" > processing.log 2>&1

echo.
pause
echo.

REM ============================================================================
REM 7. ARTIFACT MANAGEMENT
REM ============================================================================
echo [SECTION 7] ARTIFACT MANAGEMENT
echo ========================================
echo.

REM Clean artifacts for specific files
echo Example: python -m ingestor.cli --action remove --glob "old_document.pdf" --clean-artifacts
REM python -m ingestor.cli --action remove --glob "old_document.pdf" --clean-artifacts

echo.
echo ⚠️  DESTRUCTIVE OPERATION (commented out for safety):
echo.

REM Clean all artifacts (DESTRUCTIVE)
echo Example: python -m ingestor.cli --clean-all-artifacts
REM ⚠️  python -m ingestor.cli --clean-all-artifacts

REM Remove all + clean all artifacts (DESTRUCTIVE)
echo Example: python -m ingestor.cli --action removeall --clean-all-artifacts
REM ⚠️  python -m ingestor.cli --action removeall --clean-all-artifacts

echo.
pause
echo.

REM ============================================================================
REM 8. ADVANCED COMBINATIONS
REM ============================================================================
echo [SECTION 8] ADVANCED COMBINATIONS
echo ========================================
echo.

REM Setup index + process documents
echo Example: python -m ingestor.cli --setup-index --glob "data/*.pdf"
REM python -m ingestor.cli --setup-index --glob "data/*.pdf"

REM Setup + verbose + specific env
echo Example: python -m ingestor.cli --env-file .env.test --verbose --setup-index --glob "data/*.pdf"
REM python -m ingestor.cli --env-file .env.test --verbose --setup-index --glob "data/*.pdf"

REM Process with all logging options
echo Example: python -m ingestor.cli --verbose --no-colors --glob "data/*.pdf" ^> full.log 2^>^&1
REM python -m ingestor.cli --verbose --no-colors --glob "data/*.pdf" > full.log 2>&1

REM Complete pipeline
echo Example: Validate, setup, process
REM python -m ingestor.cli --validate
REM python -m ingestor.cli --setup-index
REM python -m ingestor.cli --glob "data/*.pdf"

echo.
pause
echo.

REM ============================================================================
REM 9. COMMON WORKFLOWS
REM ============================================================================
echo [SECTION 9] COMMON WORKFLOWS
echo ========================================
echo.

echo WORKFLOW 1: First-Time Setup
echo   1. python -m ingestor.cli --validate
echo   2. python -m ingestor.cli --setup-index
echo   3. python -m ingestor.cli --glob "documents/*.pdf"
echo.

echo WORKFLOW 2: Add New Documents
echo   python -m ingestor.cli --glob "new_documents/*.pdf"
echo.

echo WORKFLOW 3: Update Existing Documents
echo   python -m ingestor.cli --glob "updated_documents/*.pdf"
echo.

echo WORKFLOW 4: Remove Old Documents
echo   python -m ingestor.cli --action remove --glob "old/*.pdf" --clean-artifacts
echo.

echo WORKFLOW 5: Switch Environments
echo   python -m ingestor.cli --env-file .env.dev --validate
echo   python -m ingestor.cli --env-file .env.staging --validate
echo   python -m ingestor.cli --env-file .env.prod --validate
echo.

echo WORKFLOW 6: Complete Reset (DESTRUCTIVE)
echo   python -m ingestor.cli --force-index
echo   python -m ingestor.cli --glob "documents/*.pdf"
echo.

echo.
pause
echo.

REM ============================================================================
REM SUMMARY
REM ============================================================================
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                         EXAMPLES SUMMARY                         ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo ✓ All CLI commands and combinations demonstrated
echo ✓ Destructive operations clearly marked with ⚠️
echo ✓ Ready to uncomment and test specific commands
echo.
echo 📖 Full documentation: docs\guides\CLI_COMPLETE_GUIDE.md
echo 📖 Testing guide: docs\CLI-TESTING-SUMMARY.md
echo 📖 Quick reference: docs\guides\QUICK_REFERENCE.md
echo.
echo To run a command:
echo   1. Edit this file (cli_examples.bat)
echo   2. Uncomment the command you want (remove REM)
echo   3. Run: cli_examples.bat
echo.
echo Or copy-paste commands directly to your terminal!
echo.
pause
