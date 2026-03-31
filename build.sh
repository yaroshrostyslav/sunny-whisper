#!/bin/bash
set -e

echo "==> Setting up virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Downloading model..."
python3.11 app/transcriber.py

echo "==> Cleaning previous build..."
rm -rf build dist

echo "==> Building app..."
pyinstaller 'Sunny Whisper.spec' -y

echo "==> Resetting TCC permissions..."
tccutil reset Accessibility com.rostyslavyarosh.sunny-whisper || true
tccutil reset ListenEvent com.rostyslavyarosh.sunny-whisper || true

echo "==> Done. App is at dist/Sunny Whisper.app"
echo "    Note: grant Accessibility and Input Monitoring permissions on first launch."