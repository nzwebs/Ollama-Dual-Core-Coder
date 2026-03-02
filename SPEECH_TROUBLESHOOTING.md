# Speech Features - Troubleshooting Guide 🎙️

## Overview

DUAL CORE includes text-to-speech (TTS) and speech-to-text (STT) capabilities:
- **🔊 SPEAK**: Reads outputs aloud using pyttsx3 (works offline)
- **🎤 LISTEN**: Transcribes spoken prompts using SpeechRecognition + Google API

## What Works

### Text-to-Speech (TTS) ✅
- **Status**: **WORKING** ✓
- **Technology**: pyttsx3 (offline, no internet needed)
- **How to use**: Click "🔊 SPEAK" after generating outputs
- **No additional setup needed**

### Speech-to-Text (STT) ⚠️
- **Status**: **Partial support** - needs PyAudio
- **Technology**: SpeechRecognition + Google API (requires internet)
- **Issue**: PyAudio not available for Python 3.14

## Python Version Issue

PyAudio wheels are not yet available for **Python 3.14.0** (too new).

### Solution 1: Downgrade to Python 3.13 (RECOMMENDED) ⭐
```powershell
# Install Python 3.13 from python.org
# Then:
pip install pyaudio
```

### Solution 2: Build PyAudio from Source
Requires Visual C++ build tools:
```powershell
pip install --no-binary :all: pyaudio
```

### Solution 3: Use Python 3.12 or earlier
PyAudio has stable wheels for Python 3.12 and below.

## Testing Speech Features

Run the test script to verify setup:
```powershell
python test_speech.py
```

This will:
- ✅ Test text-to-speech
- 🎤 Test microphone detection  
- 📡 Test Google Speech API
- Show any errors with solutions

## Manual Speech-to-Text (Workaround)

If PyAudio doesn't work, you can:
1. Use online speech-to-text tools (copy-paste results into DUAL CORE)
2. Switch to Python 3.13 (simplest solution)
3. Manually type prompts (TTS still works for reading outputs)

## Requirements

**For Text-to-Speech (🔊 SPEAK):**
- ✅ pyttsx3 installed
- ✅ Speakers/audio output
- ✅ Works offline, no internet needed
- **✓ Already working**

**For Speech-to-Text (🎤 LISTEN):**
- ❌ PyAudio (only for Python ≤ 3.13)
- ✅ Microphone
- ✅ Internet connection (for Google API)
- ⚠️ **Not working on Python 3.14** due to PyAudio

## Alternative Online STT Options

If you can't get PyAudio working:
1. Use Google Docs voice typing (free)
2. Use Windows Narrator transcription
3. Use external transcription tools

## Useful Links

- **PyAudio Docs**: https://people.csail.mit.edu/hubert/pyaudio/
- **SpeechRecognition Docs**: https://github.com/Uberi/speech_recognition
- **Python 3.13 Download**: https://www.python.org/downloads/release/python-3130/

## Status Summary

| Feature | Status | Python 3.14 | Python 3.13 | Requirements |
|---------|--------|-------------|-------------|--------------|
| **🔊 SPEAK (TTS)** | ✅ Works | ✅ Yes | ✅ Yes | pyttsx3, speakers |
| **🎤 LISTEN (STT)** | ⚠️ Version-dependent | ❌ No | ✅ Yes | PyAudio, microphone, internet |
| **UI Buttons** | ✅ Always shown | ✅ Yes | ✅ Yes | N/A |
| **Error Handling** | ✅ Graceful | ✅ Yes | ✅ Yes | N/A |

**Note**: PyAudio not available for Python 3.14.0 yet (wheels pending Q2 2026)

---

**Got Questions?** Check the console output (press F12 or check terminal) for detailed error messages.
