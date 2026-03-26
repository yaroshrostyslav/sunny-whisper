import multiprocessing
import threading
from pynput import keyboard

# Import modular components
from utils import log
from audio_recorder import on_press, on_release, cleanup_recording
from transcriber import load_model, transcribe_audio, cleanup_model
from clipboard_handler import paste_text
from macos_ui import create_status_bar, run_event_loop, setup_app, cleanup

def process_audio(audio):
    """Process recorded audio through transcription and clipboard."""
    log("Processing audio...")
    full_text = transcribe_audio(audio)
    paste_text(full_text)

def on_release_wrapper(key):
    """Wrapper for on_release that handles audio processing."""
    audio = on_release(key)
    if audio is not None:
        threading.Thread(target=process_audio, args=(audio,), daemon=True).start()

def main():
    # Load Whisper model in a background thread to avoid blocking app startup
    threading.Thread(target=load_model, daemon=True).start()

if __name__ == "__main__":
    log("Starting app...")
    multiprocessing.freeze_support()

    # Setup macOS application
    app, delegate = setup_app()

    # Create menu bar icon in macOS status bar
    status_item = create_status_bar()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release_wrapper)
    listener.start()

    main()
    run_event_loop()