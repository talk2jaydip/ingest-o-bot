#!/bin/bash
# Launch Gradio UI for Document Indexing Pipeline
# Linux/Mac Shell Script

echo ""
echo "============================================"
echo "  Document Indexing Pipeline - Gradio UI"
echo "============================================"
echo ""

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Set PYTHONPATH to include src directory for local development
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
echo "[INFO] PYTHONPATH set to: $PYTHONPATH"

# Check if Gradio is installed
python3 -c "import gradio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Gradio not found. Installing UI dependencies..."
    pip3 install -r requirements-gradio.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies"
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] .env file not found!"
    echo "[WARNING] Please create .env file with your Azure credentials."
    echo "[WARNING] See docs for instructions."
    echo "[WARNING] The UI will still launch but pipeline execution may fail."
    echo ""
fi

# Launch Gradio UI
echo ""
echo "[INFO] Launching Gradio UI..."
echo "[INFO] UI will be available at: http://localhost:7860"
echo "[INFO] Press Ctrl+C to stop the server"
echo ""
echo "[INFO] Running: python3 -m ingestor.gradio_app"
echo ""
python3 -m ingestor.gradio_app

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to launch UI. Common issues:"
    echo "  - Missing dependencies: pip3 install -r requirements-gradio.txt"
    echo "  - Package not installed: pip3 install -e ."
    echo ""
fi
