#!/bin/bash
set -e

echo "==> Setting up virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Downloading model..."
python3.11 app/transcriber.py

echo "==> Stopping running app (if any)..."
killall "Sunny Whisper" 2>/dev/null || true

echo "==> Cleaning previous build..."
rm -rf build dist

echo "==> Building app..."
pyinstaller 'Sunny Whisper.spec' -y

echo "==> Copying app to /Applications..."
rm -rf "/Applications/Sunny Whisper.app"
cp -r "dist/Sunny Whisper.app" "/Applications/Sunny Whisper.app"

echo "==> Resetting TCC permissions..."
tccutil reset Accessibility com.rostyslavyarosh.sunny-whisper || true
tccutil reset ListenEvent com.rostyslavyarosh.sunny-whisper || true

echo "==> Done. App installed at /Applications/Sunny Whisper.app"
echo "    Note: grant Accessibility and Input Monitoring permissions on first launch."