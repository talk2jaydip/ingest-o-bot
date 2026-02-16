@echo off
REM Validate all env example files

echo ============================================================
echo Validating All Environment Files
echo ============================================================
echo.

echo [1/7] Scenario 01: Azure Full Local
python -m ingestor.scenario_validator --env-file envs/.env.scenario-01-azure-full-local.example
echo.

echo [2/7] Scenario 02: Azure Full Blob
python -m ingestor.scenario_validator --env-file envs/.env.scenario-02-azure-full-blob.example
echo.

echo [3/7] Scenario 03: Azure DI + ChromaDB
python -m ingestor.scenario_validator --env-file envs/.env.scenario-03-azure-di-chromadb.example
echo.

echo [4/7] Scenario 04: Integrated Vectorization
python -m ingestor.scenario_validator --env-file envs/.env.scenario-04-azure-integrated-vectorization.example
echo.

echo [5/7] Scenario 05: Vision Heavy
python -m ingestor.scenario_validator --env-file envs/.env.scenario-05-azure-vision-heavy.example
echo.

echo [6/7] Scenario 06: Multilingual
python -m ingestor.scenario_validator --env-file envs/.env.scenario-06-azure-multilingual.example
echo.

echo [7/7] Azure Local Input (Current)
python -m ingestor.scenario_validator --env-file envs/.env.azure-local-input.example
echo.

echo ============================================================
echo Validation Complete
echo ============================================================
