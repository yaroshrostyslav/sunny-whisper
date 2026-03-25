"""
Clipboard operations for Sunny Whisper.
"""

import pyperclip
from pynput.keyboard import Controller, Key
from utils import log

def paste_text(text):
    """Copy text to clipboard and paste it."""
    if not text or not text.strip():
        log("Empty transcription, skip paste")
        return False

    try:
        pyperclip.copy(text)
        kb = Controller()
        with kb.pressed(Key.cmd):
            kb.press('v')
        log("Text pasted")
        return True
    except Exception as e:
        log(f"Clipboard error: {e}")
        return False
