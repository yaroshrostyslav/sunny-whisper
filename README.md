# Sunny Whisper

A macOS desktop application that provides real-time speech-to-text transcription using OpenAI's Whisper model. Hold the right Shift key to record audio from your microphone, and the transcribed text will be automatically pasted at your cursor position.

## Features

- **Real-time Speech-to-Text**: Uses OpenAI's Whisper large-v3 model for accurate transcription
- **Keyboard Shortcut Control**: Hold right Shift to start/stop recording
- **Automatic Paste**: Transcribed text is automatically pasted at cursor position
- **Background Operation**: Runs silently in the background
- **Local Processing**: All audio processing happens locally on your device
- **Language Detection**: Automatically detects the spoken language
- **Memory Efficient**: Uses int8 quantization for reduced memory usage

## Requirements

- Microphone access
- Accessibility access (for keyboard shortcut detection)
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
python3.11 main.py
```

### Building the Application

To create a standalone macOS app bundle:

```bash
pyinstaller 'Sunny Whisper.spec' -y
```

Or using the direct command:
```bash
pyinstaller --windowed --name 'Sunny Whisper' \
  --hidden-import=sounddevice \
  --hidden-import=scipy \
  --hidden-import=pynput.keyboard._darwin \
  --add-data "model:model" \
  main.py -y
```

**Note**: Before building, run the script once to download the Whisper model from Hugging Face into the `model` directory.

## Usage

1. **Grant Permissions**: On first run, grant microphone and accessibility permissions when prompted
2. **Start Recording**: Hold the right Shift key to begin recording audio
3. **Stop Recording**: Release the right Shift key to stop recording
4. **Automatic Transcription**: The audio will be processed and the transcribed text will be automatically pasted at your cursor position

## How It Works

1. **Model Loading**: On first run, the application downloads the Whisper large-v3 model from Hugging Face. Subsequent launches use the locally cached model.
2. **Audio Capture**: When you hold the right Shift key, audio is captured from your microphone at 44.1kHz
3. **Processing**: When you release the key, the audio is saved as a temporary WAV file
4. **Transcription**: The Whisper model transcribes the audio to text
5. **Cleanup**: The temporary audio file is deleted and the text is pasted

## Configuration

### Model Selection

The default model is `SYSTRAN/faster-whisper-large-v3`. You can change this by modifying the `HF_MODEL_REPO_ID` constant in `main.py`:

```python
HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-small"  # For faster but less accurate transcription
```

### Recording Shortcut

To change the recording shortcut, modify the `RECORD_KEYS` list:

```python
RECORD_KEYS = [keyboard.Key.ctrl_r]  # Use right Ctrl instead of right Shift
```

## Dependencies

- **Python 3.11+**: Required runtime environment
- `faster-whisper`: Whisper model implementation
- `sounddevice`: Audio capture from microphone
- `numpy`: Audio data processing
- `scipy`: WAV file writing
- `pynput`: Keyboard shortcut detection
- `pyperclip`: Clipboard operations
- `psutil`: Memory usage monitoring
- `huggingface-hub`: Model downloading
- `pyinstaller`: Application bundling

## Logging

The application logs debug information to:
```
~/Library/Caches/'Sunny Whisper'/debug.log
```

## Memory Usage

The application uses int8 quantization to reduce memory usage. Typical memory consumption:
- Before model load: ~50MB
- After model load: ~1-2GB (depending on model size)

## Troubleshooting

### Permission Issues

If the app doesn't respond to keyboard shortcuts:
1. Go to System Preferences > Security & Privacy > Privacy
2. Add the app to Accessibility permissions
3. Restart the application

If recording doesn't work:
1. Go to System Preferences > Security & Privacy > Privacy
2. Add the app to Microphone permissions
3. Restart the application

### Model Download Issues

If the model fails to download:
1. Check your internet connection
2. Ensure you have sufficient disk space (~3GB required)
3. Check the debug log for specific error messages

### Performance Issues

If transcription is slow:
1. Consider using a smaller model (`faster-whisper-small`)
2. Close other memory-intensive applications
3. Restart the application to clear memory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [OpenAI](https://github.com/openai/whisper) for the Whisper model
- [SYSTRAN](https://github.com/SYSTRAN/faster-whisper) for the faster-whisper implementation
- [Hugging Face](https://huggingface.co/) for model hosting