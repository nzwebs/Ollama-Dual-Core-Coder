# DUAL CORE — Parallel Ollama Coding Engine

A powerful dual-model AI coding assistant that runs two Ollama instances simultaneously for more accurate and reliable code generation. Compare solutions, verify correctness, and reach consensus with confidence.

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

## 🚀 Quick Start

### Windows
```bash
double-click run.bat
```

### Mac / Linux
```bash
chmod +x run.sh
./run.sh
```

### Manual Setup
```bash
pip install -r requirements.txt
python app.py
```

## 📋 Requirements

- **Python 3.8+** (3.10+ recommended)
- **Ollama** — https://ollama.com
- **Two Ollama servers** — Ports 11434 (Alpha) & 11435 (Beta)
- **At least one model per server** — e.g. `ollama pull deepseek-coder`

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

All resizable via drag-and-drop sash dividers:

- **ALPHA OUTPUT** — Response from Model Alpha (Server 1)
- **BETA OUTPUT** — Response from Model Beta (Server 2)
- **CONSENSUS OUTPUT** — Final merged/selected answer
- **Score Bars** — Confidence ratings with progress visualization

## 💾 Persistent State

Automatically remembered across sessions (.window_geometry.json):
- Main window position & size
- Dashboard geometry
- Model Settings geometry
- Vertical pane split positions (as percentage ratios)

## 📚 Recommended Models

- **deepseek-coder** — Fast, specialized for coding
- **mistral** — General purpose, well-balanced
- **neural-chat** — Optimized for conversations
- **llama2** — Meta's open-source model
- **dolphin-mixtral** — Reliable multi-task performer

Pull from [Ollama Hub](https://ollama.ai/library).

## 🎨 Technology Stack

- **Python 3.8+** — Core language
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

## 📝 Advanced Features

### API Endpoints Used
- `/api/generate` — Stream text generation
- `/api/tags` — List available models
- `/api/pull` — Pull new models

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
