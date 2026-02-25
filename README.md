# Kevio

Real-time speech-to-text desktop application that types what you speak directly into any application.

## Features

- **Real-time Speech Recognition** - Uses Vosk for offline, low-latency speech recognition
- **Automatic Text Injection** - Types recognized text directly at your cursor position
- **Global Hotkey** - Press F9 to toggle listening on/off from anywhere
- **System Tray** - Runs in background with tray icon and menu
- **Floating Control Panel** - Compact, draggable UI to control listening state
- **Voice Activity Detection** - Automatically detects speech and silence
- **Configurable Settings** - Customizable model path, typing delay, VAD aggressiveness, and more

## Requirements

- Python 3.8+
- Windows (for text injection via pynput)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Kevio
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download a Vosk model:
   - Get models from https://alphacephei.com/vosk/models
   - Extract to `models/` directory (default: `models/vosk-model-en-in-0.5`)
   - The included model is `vosk-model-en-in-0.5` (English - India)

## Usage

Run the application:
```bash
python kevio.py
```

### Controls

- **F9** - Toggle listening on/off
- **UI Button** - Click Start/Stop Listening in the floating panel
- **System Tray** - Right-click for menu (Toggle, Show Settings, Exit)

### Configuration

On first run, a config file is created at `~/.kevio/config.json`. Options include:

| Setting | Default | Description |
|---------|---------|-------------|
| `language` | `en` | Language code |
| `model_path` | `models/vosk-model-en-in-0.5` | Path to Vosk model |
| `vad_aggressiveness` | `1` | Voice activity detection level (0-3) |
| `typing_delay` | `0.01` | Delay between keystrokes (seconds) |
| `hotkey` | `F9` | Global toggle hotkey |
| `silence_timeout_ms` | `2000` | Silence duration to end utterance |
| `sample_rate` | `16000` | Audio sample rate |

## Architecture

```
kevio.py              # Main entry point
src/
  main.py             # SpeechToTextAgent - orchestrates components
  speech_recognition.py  # Vosk speech recognizer wrapper
  audio_capture.py    # Microphone audio capture
  vad.py              # Voice activity detection
  text_injection.py   # Keyboard text injection
  config.py           # Configuration manager
  ui.py               # Tkinter floating control panel
  system_tray.py      # System tray integration
```

## License

MIT
