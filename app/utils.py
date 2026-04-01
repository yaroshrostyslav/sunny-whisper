"""
Utility functions for Sunny Whisper application.
"""

import os
import sys
import time
from config import APP_NAME, CACHE_DIR

# Global variables
base_dir = None
LOG_FILE = os.path.join(CACHE_DIR, "debug.log")

def log(msg):
    """Log message to console and file with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def detect_base_dir():
    """Detect base directory for the application (frozen vs script)."""
    global base_dir
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
        log(f"Base dir: {base_dir}")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log(f"Base dir: {base_dir}")

def get_base_dir():
    """Get base directory, detecting if necessary."""
    global base_dir
    if not base_dir:
        detect_base_dir()
    return base_dir
