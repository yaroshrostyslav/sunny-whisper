"""
Clipboard operations for Sunny Whisper.
"""

import pyperclip
import Quartz
from config import log

def paste_text(text):
    """Copy text to clipboard and paste it."""
    if not text or not text.strip():
        log("Empty transcription, skip paste")
        return False

    try:
        pyperclip.copy(text + " ")
        src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
        # Key code 9 = V key (layout-independent)
        for is_down in (True, False):
            event = Quartz.CGEventCreateKeyboardEvent(src, 9, is_down)
            Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        log("Text pasted")
        return True
    except Exception as e:
        log(f"Clipboard error: {e}")
        return False
