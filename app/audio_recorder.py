"""
Audio recording functionality for Sunny Whisper.
"""

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly
from math import gcd
from config import FS, TARGET_SR, RECORD_KEYS
from utils import log

# Global variables
recording = []
is_recording = False
stream = None

def callback_recording_stream(indata, frames, time, status):
    """Audio stream callback function."""
    global recording
    if is_recording:
        recording.append(indata.copy())

def start_recording():
    """Start audio recording from microphone."""
    global is_recording, recording, stream
    if is_recording:
        return
    recording = []
    is_recording = True
    stream = sd.InputStream(samplerate=FS, channels=1, callback=callback_recording_stream)
    stream.start()
    log("Recording...")

def stop_recording():
    """Stop audio recording and process the captured audio."""
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

    audio = np.concatenate(recording, axis=0).flatten().astype(np.float32)
    # Resampling 44100 → 16000 Hz
    g = gcd(FS, TARGET_SR)
    audio = resample_poly(audio, TARGET_SR // g, FS // g)
    return audio

def on_press(key):
    """Handle key press events."""
    try:
        if hasattr(key, 'name') and key.name in RECORD_KEYS:
            start_recording()
        elif hasattr(key, 'char') and key.char and key.char in RECORD_KEYS:
            start_recording()
    except Exception as e:
        log(f"Press error: {e}")

def on_release(key):
    """Handle key release events."""
    try:
        if hasattr(key, 'name') and key.name in RECORD_KEYS:
            return stop_recording()
        elif hasattr(key, 'char') and key.char and key.char in RECORD_KEYS:
            return stop_recording()
    except Exception as e:
        log(f"Release error: {e}")

def cleanup_recording():
    """Clean up recording resources."""
    global stream, is_recording

    is_recording = False

    if stream:
        try:
            stream.stop()
            stream.close()
            return True
        except Exception as e:
            log(f"Stream close error: {e}")
            return False
    return True
