"""
Audio recording functionality for Sunny Whisper.
"""

import ctypes
import ctypes.util
import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly
from math import gcd
from config import FS, TARGET_SR, get_config_value
from config import log

# Global variables
recording = []
is_recording = False
stream = None

# Keep reference to CoreAudio listener to prevent GC
_ca_listener = None

def _setup_device_change_listener():
    """Register a CoreAudio listener that reinitializes PortAudio on default input device change."""
    global _ca_listener
    ca = ctypes.CDLL(ctypes.util.find_library("CoreAudio"))

    @ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)
    def _listener(*_):
        if not is_recording:
            log("Default input device changed, reinitializing audio...")
            sd._terminate()
            sd._initialize()
            log(f"Audio input device: {sd.query_devices(kind='input')['name']}")
        return 0

    # AudioObjectPropertyAddress: mSelector, mScope, mElement
    prop = (ctypes.c_uint32 * 3)(
        0x64496E20,  # kAudioHardwarePropertyDefaultInputDevice 'dIn '
        0x676C6F62,  # kAudioObjectPropertyScopeGlobal 'glob'
        0,  # kAudioObjectPropertyElementMain
    )
    ca.AudioObjectAddPropertyListener(ctypes.c_uint32(1), prop, _listener, None)
    _ca_listener = _listener  # prevent GC

_setup_device_change_listener()
log(f"Audio input device: {sd.query_devices(kind='input')['name']}")

def callback_recording_stream(indata, frames, time, status):
    """Audio stream callback function."""
    global recording
    if is_recording:
        recording.append(indata.copy())

def start_recording():
    """Start audio recording from microphone."""
    # Log available audio input devices
    # log(f"Audio input device: {sd.query_devices(kind='input')['name']}")
    # for i, dev in enumerate(sd.query_devices()):
    #     if dev['max_input_channels'] > 0:
    #         default_mark = " [default]" if i == sd.default.device[0] else ""
    #         log(f"Audio input device {i}: {dev['name']}{default_mark}")
    global is_recording, recording, stream
    if is_recording:
        return
    recording = []
    is_recording = True
    try:
        stream = sd.InputStream(samplerate=FS, channels=1, callback=callback_recording_stream)
        stream.start()
    except Exception as e:
        log(f"Failed to open audio stream: {e}")
        is_recording = False
        stream = None
        return
    log("Recording...")
    from macos_ui import set_status_icon
    set_status_icon("recording")

def stop_recording():
    """Stop audio recording and process the captured audio."""
    global is_recording, stream
    if not is_recording:
        return
    is_recording = False
    if stream:
        stream.stop()
        stream.close()
        stream = None
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
        if hasattr(key, "name") and key.name in get_config_value("RECORD_KEYS"):
            start_recording()
        elif hasattr(key, "char") and key.char and key.char in get_config_value("RECORD_KEYS"):
            start_recording()
    except Exception as e:
        log(f"Press error: {e}")

def on_release(key):
    """Handle key release events."""
    try:
        if hasattr(key, "name") and key.name in get_config_value("RECORD_KEYS"):
            return stop_recording()
        elif hasattr(key, "char") and key.char and key.char in get_config_value("RECORD_KEYS"):
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
