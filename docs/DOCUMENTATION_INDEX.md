````markdown
# Documentation Index

Quick reference to all documentation files in Dual Core Coder.

## 📖 Getting Started

| File | Purpose |
|------|---------|
| **README.md** | Overview, features, quick start |
| **DEPENDENCIES.md** | Python dependencies and setup by OS |
| **check-deps.py** | Automated dependency verification script |

## 🏗️ Architecture & Design

| File | Purpose |
|------|---------|
| **ARCHITECTURE.md** | Interface design, code organization, future roadmap |
| **INTERFACE_CHOICE.md** | Decision log, interface selection rationale |

## 💻 Application Files

| File | Purpose |
|------|---------|
| **app.py** (2,481 lines) | PRIMARY: Tkinter desktop GUI application |
| **windows_speech_api.py** | Windows speech API utilities (reference) |
| **dual-ollama-coder.html** (950 lines) | EXPERIMENTAL: Web interface reference (not recommended) |
| **run.bat** | Windows startup script (batch) |
| **run.ps1** | Windows startup script (PowerShell) |
| **run.sh** | Mac/Linux startup script (Bash) |
| **check-deps.py** | Dependency verification script |

## 📋 Requirements

| File | Purpose |
|------|---------|
| **requirements.txt** | Python package dependencies |

---

## Documentation Navigation

### For New Users
1. Start with **README.md** — Feature overview and quick start
2. Check **DEPENDENCIES.md** — Verify your environment
3. Run **check-deps.py** — Validate setup
4. Start app with `python app.py`

### For Developers
1. Read **ARCHITECTURE.md** — Understand code organization
2. Review **INTERFACE_CHOICE.md** — Know which interface is primary
3. Edit **app.py** for features
4. Refer to **DEPENDENCIES.md** when adding requirements

### For Learning Web UI
1. Read **ARCHITECTURE.md#alternative-interface** — Understand design
2. Study **dual-ollama-coder.html** — Learn JavaScript patterns
3. Reference **INTERFACE_CHOICE.md** — Context on why it's experimental

### For Deployment/CI
1. Use **requirements.txt** — Install dependencies
2. Run **check-deps.py** — Verify environment
3. Execute **run.bat** or **run.sh** — Start application

---

## Quick Links

- **Need help?** → See troubleshooting in DEPENDENCIES.md or README.md
- **Architecture questions?** → ARCHITECTURE.md
- **Interface confusion?** → INTERFACE_CHOICE.md or ARCHITECTURE.md
- **Setup problems?** → DEPENDENCIES.md
- **Missing features?** → Review requirements.txt and ARCHITECTURE.md

---

## File Relationship Map

```
README.md (entry point)
├── DEPENDENCIES.md (setup & troubleshooting)
│   └── check-deps.py (verification script)
├── QUICKSTART.md (step-by-step guide)
├── ARCHITECTURE.md (design & code organization)
│   ├── INTERFACE_CHOICE.md (Tkinter vs HTML decision)
│   └── SPEECH_* (speech features documentation)
├── app.py (PRIMARY - Tkinter GUI, 2,481 lines)
│   ├── run.bat / run.ps1 (Windows startup)
│   ├── run.sh (Mac/Linux startup)
│   └── windows_speech_api.py (speech utilities)
└── dual-ollama-coder.html (EXPERIMENTAL web interface)
```

---

## Documentation Summary

| Aspect | File | Status |
|--------|------|--------|
| User features | README.md | ✓ Complete |
| Setup & environment | DEPENDENCIES.md | ✓ Complete |
| Architecture | ARCHITECTURE.md | ✓ Complete |
| Interface decision | INTERFACE_CHOICE.md | ✓ Complete |
| Dependencies automation | check-deps.py | ✓ Complete |
| Dependencies list | requirements.txt | ✓ Complete |

**Last Updated**: 2026-03-01  
**Primary Interface**: Tkinter (app.py)  
**Status**: Production-ready with reference web interface

````
