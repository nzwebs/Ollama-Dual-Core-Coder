````markdown
# Dual Core Coder — Architecture & Interface Guide

## Primary Interface: Tkinter (Desktop)

**Status**: ✅ Production-Ready  
**File**: `app.py` (2,481 lines of fully-featured GUI)  
**Start**: `python app.py` or double-click `run.bat` / `./run.sh`  
**Platform**: Windows, macOS, Linux

### Why Tkinter?
- ✓ Native desktop application
- ✓ Zero external GUI dependencies (built-in)
- ✓ Persistent window geometry across sessions
- ✓ Fully functional and tested
- ✓ Direct Ollama API access (no proxy/CORS issues)
- ✓ Better performance for local development
- ✓ Straightforward distribution via run scripts

### Features
- **Real-time dual-model generation** with streaming output
- **Three consensus modes**: 
  - Parallel: Both models run simultaneously, best solution selected
  - Debate: Both answer, then synthesis produces final answer
  - Verify: Alpha codes, Beta reviews & improves, final merged
- **Live metrics dashboard** with confidence scores, token counts, generation speed, elapsed time
- **Model manager** with pull, search, filter, and per-server control
- **Resizable output panes** with persistent layout across sessions
- **Professional dark theme** optimized for long coding sessions (GitHub-inspired)
- **Speech features**: TTS (working), STT (Python 3.13+)
- **Multiple output windows**: Detachable Alpha, Beta, and Consensus output panels

### Quick Start
```bash
# Windows
double-click run.bat

# Mac/Linux
chmod +x run.sh
./run.sh

# Manual
python app.py
```

---

## Alternative Interface: HTML/JavaScript (Web)

**Status**: ⚠️ Experimental / Reference  
**File**: `dual-ollama-coder.html`  
**Note**: Requires additional setup; not recommended for standard use

### Why Experimental?
- ✗ Requires CORS headers on Ollama (`OLLAMA_ORIGINS="*"`)
- ✗ Hardcoded proxy URLs (localhost:8080) need manual configuration
- ✗ Browser same-origin policy restrictions
- ✗ No persistent state management
- ✓ Educational reference for web-based architecture
- ✓ Could be basis for future web deployment with proper backend

### When to Use
- Learning how to build web UI for Ollama
- As foundation for deploying via Flask/FastAPI backend
- Reference implementation for JavaScript streaming

### Setup (Advanced)
```bash
# 1. Start Ollama with CORS enabled
OLLAMA_ORIGINS="*" ollama serve
OLLAMA_HOST=0.0.0.0:11435 OLLAMA_ORIGINS="*" ollama serve &

# 2. Open HTML in browser
# File → Open... → dual-ollama-coder.html

# 3. Configure server URLs in browser
# Edit "HOST URL" fields to match Ollama endpoints
```

---

## Code Organization

### Tkinter (app.py — 2,481 lines)
```
├── Configuration
│   ├── Emoji & font setup    — Cross-platform (Windows/macOS/Linux)
│   ├── Color palette         — Dark theme with accent colors
│   └── Persistent storage    — Window geometry, model selections
│
├── Speech Classes
│   ├── TextToSpeech          — TTS via pyttsx3 (offline)
│   └── SpeechToText          — STT via SpeechRecognition + Google API
│
├── API & Utilities
│   ├── query_ollama()        — Stream-based Ollama API calls
│   ├── test_connection()     — Server connectivity check
│   ├── estimate_confidence() — Heuristic quality scoring
│   └── build_consensus_prompt()  — Mode-specific synthesis
│
├── Window Classes (Tkinter.Toplevel)
│   ├── DashboardWindow       — Live metrics with animated gauges
│   ├── OutputWindow          — Detachable output panes
│   └── ModelSettingsWindow   — Model browser & pull interface
│
└── Main Application (DualCoreApp class)
    ├── UI Layout             — Grid-based responsive layout
    ├── Server Config         — Alpha & Beta server URLs
    ├── Mode Selector         — Parallel/Debate/Verify buttons
    ├── Prompt Area           — Input box with speech buttons
    ├── Output Area           — PanedWindow with 3 resizable sections
    ├── Consensus Modes       — Three independent execution strategies
    └── State Management      — Threading, stop events, session persistence
```

### HTML (dual-ollama-coder.html)
```
├── Styles
│   ├── Dark theme CSS
│   ├── Responsive grid layout
│   └── Animation definitions
│
├── HTML Structure
│   ├── Server configuration cards
│   ├── Mode selector (Parallel/Debate/Verify)
│   ├── Prompt input area
│   ├── Output panels (Alpha/Beta/Consensus)
│   └── Score display
│
└── JavaScript (Client-side)
    ├── queryOllama()         — Streaming API handler
    ├── testServer()          — Connection testing
    ├── run()                 — Consensus mode orchestration
    └── copyText()            — Clipboard utilities
```

---

## Dependencies

See **[DEPENDENCIES.md](DEPENDENCIES.md)** for details.

**Tkinter**: 1 external (requests) + 6 built-in modules  
**HTML**: Browser with fetch API support

---

## Development Guidelines

### When to Modify Tkinter (app.py)
- Adding features to desktop UI
- Improving consensus algorithms
- Adding model management features
- Enhancing performance or responsiveness

### When to Reference HTML
- Learning web UI patterns
- As template for Flask/FastAPI integration
- Contributing web deployment version
- Educational purposes

### Consolidation Notes
- **Primary development target**: app.py
- **HTML kept as**: Reference/educational resource
- **No sync required**: They are independent implementations
- **Future direction**: Consider web app via Flask + Tkinter → HTML

---

## Performance Characteristics

| Metric | Tkinter | HTML |
|--------|---------|------|
| Startup | ~500ms | Instant (already open) |
| Memory | ~50-100 MB | ~5-10 MB (browser overhead) |
| API calls | Direct to Ollama | Via proxy/CORS |
| State persistence | ✓ JSON file | ✗ Session storage only |
| Threading | ✓ Native | ✗ Async/await only |
| Real-time streaming | ✓ Smooth | ⚠️ Buffer-dependent |

---

## Future Roadmap

1. **Short-term (Tkinter focus)**
   - Continue feature development in app.py
   - Improve consensus algorithms
   - Add more streaming format support

2. **Medium-term (Optional Web)**
   - Create Flask/FastAPI backend wrapper
   - Serve HTML via backend with proper session management
   - Enable multi-user concurrent access

3. **Long-term (Possible)**
   - Containerized deployment (Docker)
   - Cloud version with shared model registry
   - API service for third-party integrations

---

## How to Report Issues

- **Tkinter issues**: Describe steps in app.py, include Python version
- **HTML experimental issues**: Document as educational feedback only
- **Ollama connectivity**: Verify both servers running and accessible

---

## Summary

**Use Tkinter (`app.py`) for normal operation.**  
**Refer to HTML for learning web UI architecture.**  
**Both exist independently; maintain as separate implementations.**

````
