# <img src="icons/icon-full-size.png" width="32" height="32"> Sunny Whisper

A macOS menu bar app for real-time speech-to-text transcription powered by OpenAI's Whisper model. Hold the right Shift key to start recording, release to transcribe — the text is instantly pasted at your cursor position.

All audio processing happens entirely on-device, ensuring your voice data never leaves your Mac.

## Features

- **Local, on-device transcription** — no data sent to servers
- **Simple trigger** — hold right Shift to record, release to transcribe and paste
- **Configurable shortcut, language, and custom dictionary**
- **Word count statistics** — today, this week, all time
- **Auto input device switching** — detects mic changes without restart

## Requirements

- MacOS
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

### Building the macOS Application

Use the build script — it sets up the environment, downloads the model, builds the app, resets TCC permissions, and installs the app to `/Applications`

```bash
bash build.sh
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

## Usage

1. **Grant Permissions**: On first run, grant Microphone, Accessibility, and Input Monitoring permissions when prompted
2. **Start Recording**: Hold the configured shortcut key (default: right Shift)
3. **Stop Recording**: Release the key
4. **Automatic Transcription**: The transcribed text is pasted at your cursor position

### Status Bar Icon States

| Icon | State |
|---|---|
| Default icon | Idle / ready |
| Three dots icon | Recording in progress |
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

Select a language to improve accuracy and speed. Available options: Not selected (auto-detect), English, Russian, Ukrainian. To add more languages, extend the `VALID_LANGUAGES` array in `app/config.py`.

### Custom Dictionary

Click "Change Dictionary" to open the dictionary editor. Add words that should be recognized accurately, or add a style example sentence to guide the output format (e.g. lowercase, punctuation style). Words are joined into `initial_prompt` passed to the Whisper model.

### Model Selection

The default model is `SYSTRAN/faster-whisper-small`. To switch to a larger model, change `HF_MODEL_REPO_ID` in `app/config.py`:

```python
HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-large-v3"
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

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [OpenAI](https://github.com/openai/whisper) for the Whisper model
- [SYSTRAN](https://github.com/SYSTRAN/faster-whisper) for the faster-whisper implementation
- [Hugging Face](https://huggingface.co/) for model hosting