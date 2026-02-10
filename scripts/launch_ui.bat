@echo off
REM Launch Gradio UI for Document Indexing Pipeline
REM Windows Batch Script

echo.
echo ============================================
echo   Document Indexing Pipeline - Gradio UI
echo ============================================
echo.

REM Check if Gradio is installed
python -c "import gradio" 2>nul
if errorlevel 1 (
    echo [INFO] Gradio not found. Installing dependencies...
    pip install gradio
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo [WARNING] Please create .env file with your Azure credentials.
    echo [WARNING] See README_GRADIO.md for instructions.
    echo [WARNING] The UI will still launch but pipeline execution will fail.
    echo.
    timeout /t 5
)

REM Launch Gradio UI
echo.
echo [INFO] Launching Gradio UI...
echo [INFO] UI will be available at: http://localhost:7860
echo [INFO] Press Ctrl+C to stop the server
echo.
python -m ingestor.gradio_app

pause
