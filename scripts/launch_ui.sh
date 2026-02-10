#!/bin/bash
# Launch Gradio UI for Document Indexing Pipeline
# Linux/Mac Shell Script

echo ""
echo "============================================"
echo "  Document Indexing Pipeline - Gradio UI"
echo "============================================"
echo ""

# Check if Gradio is installed
python3 -c "import gradio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Gradio not found. Installing dependencies..."
    pip3 install gradio
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] .env file not found!"
    echo "[WARNING] Please create .env file with your Azure credentials."
    echo "[WARNING] See README_GRADIO.md for instructions."
    echo "[WARNING] The UI will still launch but pipeline execution will fail."
    echo ""
    sleep 5
fi

# Launch Gradio UI
echo ""
echo "[INFO] Launching Gradio UI..."
echo "[INFO] UI will be available at: http://localhost:7860"
echo "[INFO] Press Ctrl+C to stop the server"
echo ""
python3 -m ingestor.gradio_app
