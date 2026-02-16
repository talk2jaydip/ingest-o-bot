@echo off
REM Launch Gradio UI for Document Indexing Pipeline
REM Windows Batch Script

echo.
echo ============================================
echo   Document Indexing Pipeline - Gradio UI
echo ============================================
echo.

REM Change to project root directory
cd /d "%~dp0\.."

REM Set PYTHONPATH to include src directory for local development
set PYTHONPATH=%CD%\src;%PYTHONPATH%
echo [INFO] PYTHONPATH set to: %PYTHONPATH%

REM Check if Gradio is installed
python -c "import gradio" 2>nul
if errorlevel 1 (
    echo [INFO] Gradio not found. Installing UI dependencies...
    pip install -r requirements-gradio.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo [WARNING] Please create .env file with your Azure credentials.
    echo [WARNING] See docs for instructions.
    echo [WARNING] The UI will still launch but pipeline execution may fail.
    echo.
)

REM Launch Gradio UI
echo.
echo [INFO] Launching Gradio UI...
echo [INFO] UI will be available at: http://localhost:7860
echo [INFO] Press Ctrl+C to stop the server
echo.
echo [INFO] Running: python -m ingestor.gradio_app
echo.
python -m ingestor.gradio_app

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to launch UI. Common issues:
    echo   - Missing dependencies: pip install -r requirements-gradio.txt
    echo   - Package not installed: pip install -e .
    echo.
)

pause
