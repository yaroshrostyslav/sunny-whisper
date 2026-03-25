from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel
from pathlib import Path
import multiprocessing, subprocess, time, psutil, os, sys
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pynput import keyboard
from pynput.keyboard import Controller, Key
import pyperclip
from AppKit import NSApplication, NSStatusBar, NSVariableStatusItemLength, NSImage, NSObject, NSApplicationTerminateReply
from PyObjCTools import AppHelper
import threading

# --- Constants and Global Variables ---
APP_NAME = "Sunny Whisper"
HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-small"
# HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-large-v3"
CACHE_DIR = Path.home() / "Library" / "Caches" / APP_NAME
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = os.path.join(CACHE_DIR, "debug.log")

FS = 44100
RECORD_KEYS = [keyboard.Key.shift_r] # Shortcut to start audio capture from microphone

# --- Global Variables ---
base_dir = None
recording = []
is_recording = False
stream = None
model = None

class AppDelegate(NSObject):
    def applicationShouldTerminate_(self, sender):
        log("applicationShouldTerminate_ called")
        cleanup()
        return 1  # NSTerminateNow

    def applicationWillTerminate_(self, notification):
        log("applicationWillTerminate_ called")
        cleanup()

# --- Functions ---
# --- Logging Function ---
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def detect_base_dir():
    global base_dir
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
        log(f"Base dir: {base_dir}")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log(f"Base dir: {base_dir}")

def get_base_dir():
    global base_dir
    if not base_dir:
        detect_base_dir()
    return base_dir

# --- Key and Audio Capture Functions ---
def callback(indata, frames, time, status):
    global recording
    if is_recording:
        recording.append(indata.copy())

def start_recording():
    global is_recording, recording, stream
    if is_recording:
        return
    recording = []
    is_recording = True
    stream = sd.InputStream(samplerate=FS, channels=1, callback=callback)
    stream.start()
    log("Recording...")

def stop_recording():
    global is_recording, stream
    if not is_recording:
        return
    is_recording = False
    if stream:
        stream.stop()
        stream.close()
    if not recording:
        log("No audio captured")
        return
    audio = np.concatenate(recording, axis=0)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = CACHE_DIR / f"rec_{timestamp}.wav"
    write(str(output_file), FS, audio)
    log(f"Saved {output_file}")
    process_audio(str(output_file))
    delete_audio(str(output_file))

def process_audio(file):
    log(f"Processing {file}")
    full_text = transcribe_audio(str(file))
    # Check that text is not empty
    if not full_text or not full_text.strip():
        log("Empty transcription, skip paste")
        return
    # Copy to clipboard
    try:
        pyperclip.copy(full_text)
        kb = Controller()
        with kb.pressed(Key.cmd):
            kb.press('v')
        log("Text pasted")
    except Exception as e:
        log(f"Clipboard error: {e}")

def delete_audio(file):
    path = Path(file)
    if path.exists():
        path.unlink()
        log(f"Deleted audio file: {path}")
    else:
        log(f"Audio file not found: {path}")

def on_press(key):
    try:
        if key in RECORD_KEYS:
            start_recording()
    except Exception as e:
        log(f"Press error: {e}")

def on_release(key):
    try:
        if key in RECORD_KEYS:
            stop_recording()
    except Exception as e:
        log(f"Release error: {e}")

def load_model():
    global model
    base_dir = get_base_dir()
    if getattr(sys, "frozen", False):
        model_path = os.path.join(base_dir, "model")
        log(f"Running as frozen app. Base dir: {base_dir}, model path: {model_path}")
    else:
        log(f"Running as script. Base dir: {base_dir}")
        log("Downloading model snapshot...")
        model_cache_dir = snapshot_download(repo_id=HF_MODEL_REPO_ID)
        log(f"Model cached at: {model_cache_dir}")

        model_path = os.path.join(base_dir, "model")
        if Path(model_path).exists():
            log(f"Removing existing model at {model_path}")
            subprocess.run(["rm", "-rf", model_path], check=True)
        log(f"Copying model from cache to {model_path} ...")
        subprocess.run(["cp", "-Lr", model_cache_dir, model_path], check=True)
        log("Model copy completed.")

    process = psutil.Process(os.getpid())
    log(f"Memory usage before model load: {process.memory_info().rss / 1024 ** 2:.2f} MB")

    log(f"Loading Whisper model from {model_path} ...")
    start_time = time.time()
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    log(f"Model loaded in {time.time() - start_time:.2f} sec")
    log(f"Memory usage after model load: {process.memory_info().rss / 1024 ** 2:.2f} MB")
    log("Model loaded successfully.")

def transcribe_audio(audio_file: str) -> str:
    """
    Transcribes audio file using Whisper model,
    logs the process and returns the full text.
    """
    log(f"Starting transcription for {audio_file}...")
    start_time = time.time()

    segments, info = model.transcribe(audio_file, beam_size=5)

    elapsed = time.time() - start_time
    log(f"Transcription completed in {elapsed:.2f} sec")
    log(f"Detected language: {info.language} with probability {info.language_probability}")

    # Form the full text
    full_text = "".join(segment.text for segment in segments)

    log("Transcribed text preview:")
    log(full_text[:500] + "..." if len(full_text) > 500 else full_text)

    return full_text

def cleanup():
    global stream, model, is_recording

    log("Cleanup started...")

    is_recording = False

    if stream:
        try:
            stream.stop()
            stream.close()
            stream = None
            log("Audio stream closed")
        except Exception as e:
            log(f"Stream close error: {e}")

    if model is not None:
        try:
            model = None
            log("Model released")
        except Exception as e:
            log(f"Model release error: {e}")

    log("Cleanup finished")


def create_menu_bar():
    base_dir = get_base_dir()
    status_bar = NSStatusBar.systemStatusBar()
    status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

    icon_path = os.path.join(base_dir, "icon-menu-bar.png")
    icon = NSImage.alloc().initByReferencingFile_(icon_path)
    icon.setSize_((18, 18))

    status_item.button().setImage_(icon)

    return status_item

def run_event_loop():
    AppHelper.runEventLoop()


def main():
    log("Starting app...")
    # Load Whisper model in a background thread to avoid blocking app startup
    threading.Thread(target=load_model, daemon=True).start()

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Load Whisper model in a background thread to avoid blocking app startup
    app = NSApplication.sharedApplication()

    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    # Create menu bar icon in macOS status bar
    status_item = create_menu_bar()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    main()
    AppHelper.runEventLoop()