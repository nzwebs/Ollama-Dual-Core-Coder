# Dual Core Coder — Dependencies Guide

## Python Version
- **Minimum**: Python 3.8 (for basic Tkinter functionality)
- **Recommended**: Python 3.13.12+ (for full speech features including PyAudio)
- **Note**: Python 3.14 has TTS but needs PyAudio wheels for STT (not yet available)

## Core Dependencies

### 1. **requests** (PyPI)
- **Purpose**: HTTP client for communicating with Ollama API endpoints
- **Version**: >=2.28.0, <3.0.0
- **Install**: `pip install -r requirements.txt`

### 2. **tkinter** (Built-in)
- **Purpose**: GUI framework for the desktop interface
- **Status**: Included with Python 3.8+ standard library
- **Platform-specific installation**:

#### **Windows**
- Included with Python installer (select "tcl/tk and IDLE" during setup)
- If missing: Reinstall Python and select tkinter option

#### **macOS**
- Homebrew Python: `brew install python-tk@3.10` (or your Python version)
- Official Python installer: tkinter included by default

#### **Linux — Debian/Ubuntu**
```bash
sudo apt-get update
sudo apt-get install python3-tk
```

#### **Linux — Fedora/RHEL/CentOS**
```bash
sudo dnf install python3-tkinter
```

#### **Linux — Arch Linux**
```bash
sudo pacman -S tk
```

### 3. **pyttsx3** (PyPI) — Optional for Text-to-Speech
- **Purpose**: Offline text-to-speech engine
- **Version**: >=2.90
- **Status**: Recommended for speech features
- **Install**: `pip install -r requirements.txt`
- **Platform support**: Windows, macOS, Linux

### 4. **SpeechRecognition** (PyPI) — Optional for Speech-to-Text
- **Purpose**: Speech recognition using Google API or offline engines
- **Version**: >=3.10.0
- **Status**: Works with PyAudio on Python 3.13
- **Requires**: PyAudio (see below)
- **Install**: `pip install -r requirements.txt`

### 5. **PyAudio** (PyPI) — Optional for Speech-to-Text microphone access
- **Purpose**: Audio input/output for microphone access
- **Status**: Available for Python ≤3.13, not yet for 3.14
- **Install**: Included in `requirements.txt` (may need manual install)
- **Workaround**: Included in `requirements.txt` but will fail on Python 3.14 (normal, feature disabled gracefully)

### 6. **Built-in modules** (Standard library)
- `tkinter` — GUI framework (included with Python, see platform install below)
- `threading` — Parallel Ollama request handling
- `json` — API response parsing
- `time` — Timing and performance metrics
- `math` — Gauge animations and calculations
- `os` — File and environment operations
- `platform` — OS detection for fonts and themes
- `subprocess` — Launching run scripts

## Installation Steps

### 1. **Verify Python Version**
```bash
python --version  # Should be 3.8+
# or
python3 --version
```

### 2. **Install tkinter** (if not already present)
See platform-specific instructions above.

### 3. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Verify Installation**
```bash
python app.py
# or
python3 app.py
```

## Dependency Breakdown

| Component | Type | Source | Why Needed | Version |
|-----------|------|--------|-----------|----------| 
| requests | External | PyPI | HTTP requests to Ollama API | >=2.28.0 |
| tkinter | Built-in | Python stdlib | Desktop GUI framework & windows | Included |
| pyttsx3 | External | PyPI | Offline text-to-speech | >=2.90 |
| SpeechRecognition | External | PyPI | Speech-to-text with Google API | >=3.10.0 |
| PyAudio | External | PyPI | Microphone access (Python ≤3.13) | Latest |
| threading | Built-in | Python stdlib | Parallel dual-model execution | Included |
| json | Built-in | Python stdlib | API response parsing | Included |
| time | Built-in | Python stdlib | Performance timing metrics | Included |
| math | Built-in | Python stdlib | Gauge animations & calculations | Included |
| os | Built-in | Python stdlib | Config file I/O, environment vars | Included |
| platform | Built-in | Python stdlib | OS detection for fonts/themes | Included |
| subprocess | Built-in | Python stdlib | Launching run scripts | Included |

## Optional: System Requirements

### **Ollama**
- **Purpose**: AI model runtime (required to run the models)
- **Download**: https://ollama.com
- **Setup**: Two instances on ports 11434 (Alpha) and 11435 (Beta)

### **RAM Recommendation**
- Minimum: 8 GB (for small models like deepseek-coder)
- Recommended: 16+ GB (for larger models running in parallel)

## Troubleshooting

### **"No module named 'tkinter'"**
- Install tkinter using platform-specific commands above
- Verify: `python -m tkinter` (should open a test window)

### **"No module named 'requests'"**
```bash
pip install -r requirements.txt
```

### **ImportError on startup**
- Ensure you're using Python 3.8+
- Verify all dependencies installed: `pip list | grep requests`
- On Linux, restart shell after installing tkinter: `source ~/.bashrc` (or equivalent)

### **Connection errors to Ollama**
- This is not a dependency issue; verify Ollama is running on the correct ports
- Test with: `curl http://localhost:11434/api/tags`

## Version Pinning Strategy

- **requests**: Pinned to `>=2.28.0, <3.0.0`
  - Ensures API compatibility
  - Avoids breaking changes in v3+
  
- **pyttsx3**: `>=2.90` (flexible)
  - Compatible with all supported Python versions
  
- **SpeechRecognition**: `>=3.10.0` (flexible)
  - Compatible with Python 3.8-3.14+
  - Gracefully degrades if PyAudio unavailable
  
- **PyAudio**: Not pinned (optional)
  - Available on PyPI for Python ≤3.13
  - Will fail gracefully on Python 3.14 (feature disabled)
  - Can be installed separately or built from source if needed
  
- **Python version**: No upper bound
  - Supports Python 3.8-3.14+
  - Full speech support on 3.13
  - TTS-only mode on 3.14 (waiting for PyAudio wheels)
  
- **tkinter**: Uses system package
  - Version managed by OS Python installation
  - No third-party pin needed

## Development Notes

- All imports are minimal and stable (no heavy framework dependencies)
- The project has zero transitive dependency conflicts
- Compatible with virtual environments: `python -m venv venv`
- CI/CD friendly: Single `pip install -r requirements.txt` command
