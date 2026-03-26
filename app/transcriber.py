"""
Whisper model loading and transcription functionality.
"""

import os
import sys
import time
import subprocess
import psutil
from pathlib import Path
from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel
from config import HF_MODEL_REPO_ID, BEAM_SIZE
from utils import log, get_base_dir

# Global variable
model = None

def load_model():
    """Load Whisper model from cache or download if needed."""
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

def transcribe_audio(audio):
    """Transcribe audio array using Whisper model."""
    if model is None:
        log("Model not loaded")
        return ""

    log("Starting transcription...")
    start_time = time.time()

    # faster-whisper accepts numpy array directly
    segments, info = model.transcribe(
        audio,
        beam_size=5,
        vad_filter=True,  # skip silent parts to speed up transcription
    )

    elapsed = time.time() - start_time
    log(f"Transcription completed in {elapsed:.2f} sec")
    log(f"Detected language: {info.language} ({info.language_probability:.2f})")

    # Time the full text formation
    text_start_time = time.time()
    full_text = "".join(segment.text for segment in segments)
    text_elapsed = time.time() - text_start_time
    log(f"Full text formation completed in {text_elapsed:.4f} sec")
    
    log(full_text[:500] + "..." if len(full_text) > 500 else full_text)
    return full_text

def cleanup_model():
    """Clean up model resources."""
    global model

    if model is not None:
        try:
            model = None
            log("Model released")
            return True
        except Exception as e:
            log(f"Model release error: {e}")
            return False
    return True
