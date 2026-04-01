"""
Global keyboard listener management for Sunny Whisper.
"""

from pynput import keyboard
from utils import log

_listener = None
_on_press = None
_on_release = None
_capture_callback = None  # when set, redirects key events to shortcut change window


def init(on_press, on_release):
    """Set the callback handlers (call once at startup)."""
    global _on_press, _on_release
    _on_press = on_press
    _on_release = on_release


def set_capture_callback(callback):
    """Redirect key press events to callback (e.g. shortcut change window)."""
    global _capture_callback
    _capture_callback = callback


def clear_capture_callback():
    """Restore normal key press handling."""
    global _capture_callback
    _capture_callback = None


def _press(key):
    if _capture_callback is not None:
        _capture_callback(key)
    else:
        _on_press(key)


def _release(key):
    if _capture_callback is None:
        return _on_release(key)


def start():
    """Start the global keyboard listener."""
    global _listener
    if _listener and _listener.is_alive():
        return
    _listener = keyboard.Listener(on_press=_press, on_release=_release)
    _listener.start()
    log("Listener started")


def stop():
    """Stop the global keyboard listener."""
    global _listener
    if _listener:
        _listener.stop()
        _listener = None
        log("Listener stopped")
