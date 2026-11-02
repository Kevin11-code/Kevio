# Kevio Project Summary

Kevio is a Windows desktop speech-to-text app that listens to your microphone, transcribes speech locally with Vosk, and types the recognized text into whatever application currently has focus.

## What It Does

- Captures microphone audio in real time
- Uses voice activity detection to segment speech from silence
- Runs offline speech recognition with Vosk
- Injects transcribed text at the cursor using `pynput`
- Provides a floating control panel, system tray icon, and global `F9` hotkey

## Main Components

- `kevio.py` - application entry point and lifecycle orchestration
- `src/main.py` - `SpeechToTextAgent`, which coordinates capture, VAD, recognition, and typing
- `src/audio_capture.py` - microphone stream handling via `sounddevice`
- `src/vad.py` - simple RMS-based voice activity detection and audio buffering
- `src/speech_recognition.py` - Vosk model wrapper and chunk processing
- `src/text_injection.py` - keyboard text injection using `pynput`
- `src/config.py` - JSON config stored at `~/.kevio/config.json`
- `src/ui.py` - floating Tkinter control panel with status indicator
- `src/system_tray.py` - tray menu and status icon via `pystray`

## Runtime Flow

1. The app loads configuration and starts the tray icon and floating UI.
2. The Vosk model is preloaded in a background thread.
3. Pressing `F9` or the UI toggle starts or pauses listening.
4. Audio chunks are read from the microphone stream.
5. VAD detects speech, while Vosk accumulates recognized segments.
6. When silence ends an utterance, the final transcription is typed into the active window.

## Dependencies

- `sounddevice`
- `vosk`
- `numpy`
- `pynput`
- `pystray`
- `Pillow`

## Platform Notes

- Targeted at Windows for keyboard injection and the current UI behavior
- Requires Python 3.8+
- Needs a local Vosk model in the configured `model_path`

## Configuration

Default settings include:

- `model_path`: `models/vosk-model-en-in-0.5`
- `hotkey`: `F9`
- `typing_delay`: `0.01`
- `vad_aggressiveness`: `1`
- `silence_timeout_ms`: `2000`
- `sample_rate`: `16000`
