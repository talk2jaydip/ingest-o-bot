@echo off
REM Script to remove duplicate and old env files
REM Run this to clean up unnecessary env files

echo ============================================
echo Cleaning up duplicate/old env files
echo ============================================
echo.

echo Removing old/duplicate files...

REM Remove root duplicate
if exist .env.example (
    del .env.example
    echo Removed: .env.example
)

REM Remove old envs/ files
cd envs

if exist .env.chromadb.example (
    del .env.chromadb.example
    echo Removed: envs/.env.chromadb.example
)

if exist .env.cohere.example (
    del .env.cohere.example
    echo Removed: envs/.env.cohere.example
)

if exist .env.example (
    del .env.example
    echo Removed: envs/.env.example
)

if exist .env.example.dev (
    del .env.example.dev
    echo Removed: envs/.env.example.dev
)

if exist .env.example.prod (
    del .env.example.prod
    echo Removed: envs/.env.example.prod
)

if exist .env.example.staging (
    del .env.example.staging
    echo Removed: envs/.env.example.staging
)

if exist .env.hybrid.example (
    del .env.hybrid.example
    echo Removed: envs/.env.hybrid.example
)

if exist .env.scenario-azure-cohere.example (
    del .env.scenario-azure-cohere.example
    echo Removed: envs/.env.scenario-azure-cohere.example
)

if exist .env.scenario-azure-openai-default.example (
    del .env.scenario-azure-openai-default.example
    echo Removed: envs/.env.scenario-azure-openai-default.example
)

if exist .env.scenario-cost-optimized.example (
    del .env.scenario-cost-optimized.example
    echo Removed: envs/.env.scenario-cost-optimized.example
)

if exist .env.scenario-development.example (
    del .env.scenario-development.example
    echo Removed: envs/.env.scenario-development.example
)

if exist .env.scenario-multilingual.example (
    del .env.scenario-multilingual.example
    echo Removed: envs/.env.scenario-multilingual.example
)

if exist .env.scenarios.example (
    del .env.scenarios.example
    echo Removed: envs/.env.scenarios.example
)

cd ..

echo.
echo ============================================
echo Cleanup complete!
echo ============================================
echo.
echo KEPT files (6 total):
echo   envs/.env.azure-local-input.example
echo   envs/.env.azure-chromadb-hybrid.example
echo   envs/.env.offline-with-vision.example
echo   envs/.env.hybrid-scenarios.example
echo   examples/playbooks/.env.basic-pdf.example
echo   examples/playbooks/.env.production.example
echo.
echo Now run: git add -A
echo Then: git commit -m "chore: Remove duplicate env files"
echo.
pause
