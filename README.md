# DUAL CORE — Parallel Ollama Coding Engine

A powerful dual-model AI coding assistant that runs two Ollama instances simultaneously for more accurate and reliable code generation. Compare solutions, verify correctness, and reach consensus with confidence.

**Primary Interface**: Tkinter Desktop Application (`app.py` — 2,481 lines)  
**Status**: ✅ Production-Ready  
**[See ARCHITECTURE.md](docs/ARCHITECTURE.md) for interface & design details**

## ✨ Features

### Core Capabilities
- **Parallel Model Execution** — Run two different AI models at the same time
- **Three Consensus Modes** — Parallel, Debate, or Verify workflows
- **Code & General Questions** — Toggle between code generation and general Q&A modes
- **Real-time Dashboard** — Monitor confidence scores, token counts, and generation speed
- **Model Manager** — Pull and manage models directly from the UI
- **Persistent State** — Window sizes, positions, and pane splits remembered across sessions

### UI Features
- **Live Metrics Dashboard** — Separate window with real-time monitoring:
  - Confidence scores (smooth digital gauges with easing animations)
  - Token counts and generation speed
  - Elapsed time tracking
  - Model names and quality delta (+/-)
  - Status indicators

- **Responsive Layout** — Grid-based with fully resizable panes:
  - Draggable vertical sash dividers
  - Resizable output sections
  - Persistent split positions
  
- **Professional Dark Theme** — Optimized for long coding sessions

### Model Management
- **Quick Pull** — Pull models with single name + server selection
- **Model Browser** — Search through all available models
- **Per-Server Control** — Independently manage Alpha and Beta models
- **Auto-Refresh** — Models auto-load on startup

### Speech Features 🎙️
- **🔊 Speak** ✅ **WORKING** — Read consensus/alpha outputs aloud using pyttsx3 (offline, no internet needed)
  - Button status: Fully functional on all Python versions
  - Uses Windows/macOS/Linux native voices
  
- **🎤 Listen** ⚠️ **PARTIAL** — Transcribe spoken prompts into the prompt box
  - Status: Works on Python 3.13, blocked on Python 3.14
  - Uses SpeechRecognition + Google API (requires internet)
  - Issue: PyAudio wheels not yet available for Python 3.14
  - Solution: Downgrade to Python 3.13 for full speech support
  
- **Status Indicators** — Real-time feedback during listening/speaking
- **Graceful Fallbacks** — Clear error messages with solutions when features unavailable

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.13.12+ (recommended for speech features)
- **Ollama**: Two instances running on localhost:11434 and localhost:11435
  - Download from: https://ollama.com

### Windows (Recommended: PowerShell)
```powershell
# Option 1: Double-click run.bat
run.bat

# Option 2: PowerShell with colors
.\run.ps1

# Option 3: Manual
python app.py
```

### Mac / Linux
```bash
chmod +x run.sh
./run.sh
```

### Manual Setup (Any Platform)
```bash
# 1. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Start two Ollama instances
# Terminal 1
ollama serve

# Terminal 2
export OLLAMA_HOST=0.0.0.0:11435  # On Windows: $env:OLLAMA_HOST = "0.0.0.0:11435"
ollama serve

# 4. Run the app
python app.py
```

### Verify Dependencies
```bash
python check-deps.py
```

**📌 Python Version Notes:**
- **Python 3.13**: Full speech support (both listening & speaking)
- **Python 3.14**: TTS works, STT blocked (PyAudio wheels not available yet)
- **Fallback**: Use Python 3.13 for complete feature set

## 📋 Requirements

- **Python** — 3.13.12+ (for full speech features including PyAudio)
  - Python 3.14 has TTS but needs PyAudio wheels for STT
- **Ollama** — https://ollama.com (two instances on ports 11434 & 11435)
- **Dependencies** — See [DEPENDENCIES.md](docs/DEPENDENCIES.md) or run `pip install -r requirements.txt`
- **Two Ollama servers** — Ports 11434 (Alpha) & 11435 (Beta)
- **At least one model per server** — e.g. `ollama pull deepseek-coder`

### Python Dependencies

See **[DEPENDENCIES.md](docs/DEPENDENCIES.md)** for:
- Complete dependency list with versions
- Platform-specific installation instructions (Windows, macOS, Linux)
- Troubleshooting guide

## 🔧 Running Two Ollama Servers

### Same Machine Setup

**Terminal 1 — Server Alpha (port 11434):**
```bash
ollama serve
```

**Terminal 2 — Server Beta (port 11435):**

Mac/Linux:
```bash
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

Windows PowerShell:
```powershell
$env:OLLAMA_HOST="0.0.0.0:11435"
ollama serve
```

Windows CMD:
```cmd
set OLLAMA_HOST=0.0.0.0:11435
ollama serve
```

## 🧠 Consensus Modes

| Mode | Description | Best For |
|------|-------------|----------|
| **⚡ Parallel** | Both models answer simultaneously, best selected by confidence | Quick generation, redundancy |
| **⚔️ Debate** | Both answer, consensus synthesizes both perspectives | Complex problems |
| **✓ Verify** | Alpha generates, Beta reviews & improves, merged final result | Production code |

## 🎮 UI Controls

### Main Window
- **◈ PROMPT** — Enter your question or code request
- **💻 Code / ❓ General** — Toggle between modes
- **▶ ENGAGE DUAL CORE** — Start dual-model generation
- **✕ CLEAR** — Clear all outputs
- **◐ DASHBOARD** — Open live metrics window
- **⚙ MODEL SETTINGS** — Open model manager

### Output Windows
Each output section (Alpha, Beta, Consensus) features:
- **≣ Button** — Open output in a dedicated, resizable window
- **COPY Button** — Copy output to clipboard
- **Independent Windows** — Each output can be viewed and copied separately
- **Persistent Geometry** — Window sizes and positions are saved across sessions

### Dashboard Window
- Real-time confidence scores (smooth easing animations)
- Token counts and generation speed
- Elapsed time tracking
- Model names and quality delta comparison
- Status indicators

### Model Settings Window
- **Quick Pull** — Model name + server selection
- **Model Browser** — Search all available models
- **📥 PULL NEW MODEL** — Popular models dialog
- **🔄 REFRESH** — Reload model list
- **Show Info** — View model details

## 💾 Output Sections

All resizable via drag-and-drop sash dividers. Each output supports:

- **ALPHA OUTPUT** — Response from Model Alpha (Server 1) — Click **≣** to open in new window
- **BETA OUTPUT** — Response from Model Beta (Server 2) — Click **≣** to open in new window
- **CONSENSUS OUTPUT** — Final merged/selected answer — Click **≣** to open in new window
- **Score Bars** — Confidence ratings with progress visualization
- **COPY & WINDOW BUTTONS** — Next to each output header for easy access to independent windows

## 🎙️ Speech Features

### Text-to-Speech (Speak) ✅
- **Click 🔊 SPEAK** to hear the consensus output read aloud
- **Technology**: Offline pyttsx3 engine (no internet needed)
- **Works on**: Windows, macOS, Linux
- **No setup required** — Just speak into your speakers!

### Speech-to-Text (Listen) 🎤
- **Click 🎤 LISTEN** to dictate your prompts
- **Technology**: Google Cloud Speech API (requires internet + microphone)
- **Current Version**: Python 3.13.12
- **Note**: Python 3.14+ has no pre-built PyAudio wheels yet; use Python 3.13 for full speech features
- **See [SPEECH_TROUBLESHOOTING.md](docs/SPEECH_TROUBLESHOOTING.md) for setup**

## 💾 Persistent State

Automatically remembered across sessions (.window_geometry.json):
- Main window position & size
- Dashboard geometry
- Model Settings geometry
- Output window geometries (Alpha, Beta, Consensus)
- Vertical pane split positions (as percentage ratios)

## 📚 Recommended Models

- **deepseek-coder** — Fast, specialized for coding
- **mistral** — General purpose, well-balanced
- **neural-chat** — Optimized for conversations
- **llama2** — Meta's open-source model
- **dolphin-mixtral** — Reliable multi-task performer

Pull from [Ollama Hub](https://ollama.ai/library).

## 🎨 Technology Stack

- **Python 3.13.12** — Core language (PyAudio compatible)
- **Tkinter** — GUI framework (built-in)
- **Requests** — HTTP client for Ollama API
- **Ollama** — AI model runtime
- **Dark theme** — Professional color scheme with emoji support

## 🐛 Troubleshooting

### Models Not Showing
- Verify Ollama is running on both ports (11434, 11435)
- Check in terminals: `ollama list`
- Click **🔄 REFRESH** in Model Settings

### Connection Refused
- Start Ollama: `ollama serve`
- Check port availability
- Windows: May need firewall adjustment

### Slow Generation
- Use smaller models (deepseek-coder)
- Reduce model parameters
- Ensure sufficient system RAM

### Window State Corrupted
- Delete `.window_geometry.json` and restart

## � Troubleshooting

### Tkinter Error ("Can't find usable init.tcl")
**Issue**: If you have Python 3.14 installed, it may interfere with Python 3.13's Tkinter.

**Solution**:
1. Use the provided `run.bat` or `run.ps1` launchers (they set environment variables automatically)
2. Or manually set before running:
   ```powershell
   $env:TCL_LIBRARY = "C:\Users\<username>\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
   $env:TK_LIBRARY = "C:\Users\<username>\AppData\Local\Programs\Python\Python313\tcl\tk8.6"
   python app.py
   ```

### PyAudio Not Found
**Issue**: Speech recognition (🎤 LISTEN) doesn't work.

**Solution**:
- Ensure Python 3.13.12 is installed (not 3.14)
- Run: `pip install pyaudio`
- Verify: `python -m pip list | findstr pyaudio`

### Microphone Not Detected
**Issue**: PyAudio is installed but microphone not found.

**Solution**:
1. Check Windows audio settings—verify microphone is enabled
2. Unplug/replug microphone
3. Try a different USB port
4. Test with Windows built-in voice recorder first

## 📁 Advanced Features

### API Endpoints Used
- `/api/generate` — Stream text generation
- `/api/tags` — List available models
- `/api/pull` — Pull new models

### Experimental Web Interface
An HTML/JavaScript web-based version (`dual-ollama-coder.html`) is included as a reference implementation. **This is not recommended for standard use** but can serve as:
- Educational reference for web UI patterns
- Foundation for future Flask/FastAPI web deployment
- Template for JavaScript streaming implementation

See **[ARCHITECTURE.md](docs/ARCHITECTURE.md#alternative-interface-htmljavascript-web)** for details.

### Custom Workflows
Easily modify consensus prompts and add new modes in `app.py`

### Extensible Architecture
- Model agnostic (works with any Ollama model)
- Clean separation of concerns
- Well-documented code

## 📄 License

Open source. Build, modify, and improve freely!

---

**DUAL CORE** — Where two minds are better than one! 🧠🤖
