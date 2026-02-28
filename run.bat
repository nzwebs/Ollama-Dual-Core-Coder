@echo off
echo.
echo  ==========================================================
echo    DUAL CORE - Parallel Ollama Coding Engine
echo  ==========================================================
echo.
echo    Running two AI models simultaneously for better code...
echo.
echo  Make sure you have TWO Ollama servers running:
echo    Terminal 1: ollama serve
echo    Terminal 2: OLLAMA_HOST=0.0.0.0:11435 ollama serve
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
echo  Checking dependencies...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo  Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  ERROR: Failed to install requirements
        pause
        exit /b 1
    )
)

echo.
echo  Launching DUAL CORE...
echo.
python app.py

if errorlevel 1 (
    echo.
    echo  ERROR: Application failed to start
    pause
    exit /b 1
)

