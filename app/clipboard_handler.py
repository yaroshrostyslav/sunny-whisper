"""
Clipboard operations for Sunny Whisper.
"""

import subprocess
import pyperclip
from utils import log

def paste_text(text):
    """Copy text to clipboard and paste it."""
    if not text or not text.strip():
        log("Empty transcription, skip paste")
        return False

    try:
        pyperclip.copy(text)
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
            check=True,
            capture_output=True,
        )
        log("Text pasted")
        return True
    except Exception as e:
        log(f"Clipboard error: {e}")
        return False
