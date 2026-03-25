"""
Configuration constants for Sunny Whisper application.
"""

from pathlib import Path

# Application Info
APP_NAME = "Sunny Whisper"

# Model Configuration
HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-small"
# HF_MODEL_REPO_ID = "SYSTRAN/faster-whisper-large-v3"

# Paths
CACHE_DIR = Path.home() / "Library" / "Caches" / APP_NAME
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Audio Configuration
FS = 44100  # Sample rate
TARGET_SR = 16000  # Target sample rate for transcription
RECORD_KEYS = ["shift_r"]  # Shortcut to start audio capture

# Transcription Configuration
BEAM_SIZE = 5
