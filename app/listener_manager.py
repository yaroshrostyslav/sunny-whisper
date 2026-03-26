"""
Global keyboard listener management for Sunny Whisper.
"""

from pynput import keyboard
from utils import log

_listener = None
_on_press = None
_on_release = None
_paused = False

def init(on_press, on_release):
    """Set the callback handlers (call once at startup)."""
    global _on_press, _on_release
    _on_press = on_press
    _on_release = on_release

def _press(key):
    if not _paused:
        _on_press(key)

def _release(key):
    if not _paused:
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

def pause():
    """Pause event handling without stopping the listener thread."""
    global _paused
    _paused = True
    log("Listener paused")

def resume():
    """Resume event handling."""
    global _paused
    _paused = False
    log("Listener resumed")

def restart():
    """Restart the listener (e.g. after shortcut change)."""
    stop()
    start()
