#!/bin/bash

echo ""
echo "  =========================================================="
echo "    DUAL CORE — Parallel Ollama Coding Engine"
echo "  =========================================================="
echo ""
echo "  Make sure you have TWO Ollama servers running:"
echo "    Terminal 1: ollama serve"
echo "    Terminal 2: OLLAMA_HOST=0.0.0.0:11435 ollama serve"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ERROR: python3 not found. Install from python.org or use:"
    echo "    brew install python3  (macOS)"
    echo "    apt install python3   (Linux)"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
echo "  Python version: $PYTHON_VERSION"

# Install/check dependencies
echo "  Checking dependencies..."
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  Installing requirements..."
    pip3 install -r requirements.txt || {
        echo "  ERROR: Failed to install requirements"
        exit 1
    }
fi

echo ""
echo "  Launching DUAL CORE..."
echo ""

# Run the application
python3 app.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "  ERROR: Application exited with code $EXIT_CODE"
    exit 1
fi
