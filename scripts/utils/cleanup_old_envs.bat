@echo off
REM Cleanup script to remove old .env files
REM Keeps only: .env (production) and the 6 new scenario files

echo Cleaning up old environment files...
echo.

REM Delete old envs/*.example files
cd envs
del /F .env.azure-chromadb-hybrid.example
del /F .env.azure-local-input
del /F .env.chromadb.example
del /F .env.cohere.example
del /F .env.example
del /F .env.example.dev
del /F .env.example.prod
del /F .env.example.staging
del /F .env.hybrid.example
del /F .env.hybrid-scenarios.example
del /F .env.offline-with-vision.example
del /F .env.scenario-azure-cohere.example
del /F .env.scenario-azure-openai-default.example
del /F .env.scenario-cost-optimized.example
del /F .env.scenario-development.example
del /F .env.scenario-multilingual.example
del /F .env.scenarios.example
del /F env.office-scenario1-azure-di-only.example
del /F env.office-scenario2-markitdown-only.example
del /F env.office-scenario3-hybrid-fallback.example
del /F env.scenario1-local-dev.example
del /F env.scenario2-blob-prod.example
del /F env.scenario3-local-to-blob.example
del /F env.scenario4-blob-to-local.example
del /F env.scenario5-offline.example
cd ..

REM Delete examples/playbooks .env files
cd examples\playbooks
del /F .env.production.example
del /F .env.basic-pdf.example
cd ..\..

REM Delete root backup files
del /F .env.backup
del /F .env.example
del /F .env.azure-chromadb-test
del /F .env.GLOBAL-ALL-VARIABLES
del /F .env.local-dev
del /F test-env-file.env

echo.
echo Cleanup complete!
echo.
echo KEPT FILES:
echo   - .env (production)
echo   - envs\.env.azure-local-input.example (reference)
echo   - envs\.env.scenario-01-azure-full-local.example
echo   - envs\.env.scenario-02-azure-full-blob.example
echo   - envs\.env.scenario-03-azure-di-chromadb.example
echo   - envs\.env.scenario-04-azure-integrated-vectorization.example
echo   - envs\.env.scenario-05-azure-vision-heavy.example
echo   - envs\.env.scenario-06-azure-multilingual.example
echo.
pause
