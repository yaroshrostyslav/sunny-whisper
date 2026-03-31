# Sunny Whisper

A macOS menu bar app for real-time speech-to-text transcription using OpenAI's Whisper model. Hold the right Shift key to record audio, release to transcribe — the text is automatically pasted at your cursor position.

## Features

- **Real-time Speech-to-Text**: Uses faster-whisper (small model) for fast on-device transcription
- **Configurable Shortcut**: Change the recording key via the menu bar
- **Language Selection**: Choose recognition language or use auto-detection
- **Custom Dictionary**: Add words or style examples to improve recognition accuracy
- **Word Count Statistics**: Track transcribed words — today, this week, all time
- **Auto Device Switching**: Automatically detects default input device changes without restart
- **Animated Status Icon**: Visual feedback for idle / recording / transcribing states
- **Automatic Paste**: Transcribed text is pasted at cursor position (layout-independent)
- **Menu Bar Operation**: Runs silently as a menu bar app with no Dock icon
- **Local Processing**: All audio processing happens on-device, no data sent to servers
- **VAD Filter**: Silences are skipped automatically for faster transcription
- **Memory Efficient**: Uses int8 quantization

## Requirements

- macOS
- Microphone access
- Accessibility access (required for pasting text)
- Input Monitoring access (required for global key listening)
- Internet connection (for initial model download only)

## Installation

### Prerequisites

Install FFmpeg (required for audio processing):
```bash
brew install ffmpeg
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yaroshrostyslav/sunny-whisper.git
cd sunny-whisper
```

2. Create and activate a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
cd app
python3.11 main.py
```

### Building the Application

Use the build script — it sets up the environment, downloads the model, builds the app, and resets TCC permissions:

```bash
bash build.sh
```

Or manually:

```bash
pyinstaller 'Sunny Whisper.spec' -y
```

> **Note**: The model must be present in `app/model/` before building. `build.sh` handles this automatically via `python3.11 app/transcriber.py`.

## Usage

1. **Grant Permissions**: On first run, grant Microphone, Accessibility, and Input Monitoring permissions when prompted
2. **Start Recording**: Hold the configured shortcut key (default: right Shift)
3. **Stop Recording**: Release the key
4. **Automatic Transcription**: The transcribed text is pasted at your cursor position

### Status Bar Icon States

| Icon | State |
|---|---|
| Default icon | Idle / ready |
| Microphone icon | Recording in progress |
| Animated spinner | Transcribing audio |

### Menu Bar

Click the menu bar icon to access settings:

| Item | Description |
|---|---|
| Shortcut: \<key\> | Currently configured recording key |
| Language: \<lang\> | Currently selected recognition language |
| Change Shortcut | Open shortcut change window |
| Change Language | Open language selection window |
| Change Dictionary | Open custom dictionary window |
| Statistics | View word count statistics |
| Quit | Exit the application |

## Configuration

User settings are stored in `~/Library/Caches/Sunny Whisper/user_config.json` and persist across launches.

### Recording Shortcut

Click "Change Shortcut" in the menu bar and press any key to reassign the recording trigger.

### Language

Select a language to improve accuracy and speed. Available options: Not selected (auto-detect), English, Russian, Ukrainian.

### Custom Dictionary

Click "Change Dictionary" to open the dictionary editor. Add words that should be recognized accurately, or add a style example sentence to guide the output format (e.g. lowercase, punctuation style). Words are joined into `initial_prompt` passed to the Whisper model.

### Model Selection

The default model is `SYSTRAN/faster-whisper-small`. To switch to a larger model, change `HF_MODEL_REPO_ID` in `app/config.py`:

```python
HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-large-v3"
```

## How It Works

1. **Model Loading**: On first run, the Whisper model is downloaded from Hugging Face and cached in `app/model/`
2. **Audio Capture**: Holding the shortcut key captures audio at 44.1kHz
3. **Processing**: On key release, audio is resampled to 16kHz
4. **Transcription**: Whisper transcribes the audio (VAD filter skips silent parts; dictionary words passed as `initial_prompt`)
5. **Paste**: Text is copied to clipboard and pasted via Cmd+V (Quartz CGEvent, layout-independent)

## Logging

Debug logs are written to:
```
~/Library/Caches/Sunny Whisper/debug.log
```

## Troubleshooting

### Text is not pasted after transcription

1. Open **System Settings → Privacy & Security → Accessibility** — add the app
2. Restart the application

### App doesn't respond to keyboard shortcuts

1. Open **System Settings → Privacy & Security → Input Monitoring** — add the app
2. Restart the application

### Recording doesn't work

1. Open **System Settings → Privacy & Security → Microphone** — add the app
2. Restart the application

### "Cannot open application" on macOS

If macOS blocks the app with "Cannot open", remove the quarantine attribute:
```bash
xattr -cr "/Applications/Sunny Whisper.app"
```

### Transcription is slow

- Selecting a specific language (instead of auto-detect) speeds up transcription
- The app uses the `faster-whisper-small` model by default, which is already optimized
- Close other memory-intensive applications

## Dependencies

- `faster-whisper` — Whisper model inference
- `sounddevice` — microphone audio capture
- `numpy`, `scipy` — audio data processing and resampling
- `pynput` — global keyboard listener
- `pyperclip` — clipboard operations
- `psutil` — memory monitoring
- `huggingface-hub` — model downloading
- `pyinstaller` — application bundling
- `PyObjC` / `AppKit` — macOS native UI and system integration

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [OpenAI](https://github.com/openai/whisper) for the Whisper model
- [SYSTRAN](https://github.com/SYSTRAN/faster-whisper) for the faster-whisper implementation
- [Hugging Face](https://huggingface.co/) for model hosting