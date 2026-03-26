# -*- mode: python ; coding: utf-8 -*-

APP_VERSION = "1.0.0"  # ← меняешь только здесь

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/model', 'model'),
        ('icons/icon-menu-bar.png', '.'),
        # Silero VAD ONNX model required by faster-whisper when vad_filter=True
        ('venv/lib/python3.11/site-packages/faster_whisper/assets/silero_vad_v6.onnx', 'faster_whisper/assets'),
    ],
    hiddenimports=['sounddevice', 'scipy', 'pynput.keyboard._darwin'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sunny Whisper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sunny Whisper',
)

# macOS BUNDLE с Info.plist
app = BUNDLE(
    coll,
    name='Sunny Whisper.app',
    icon="icons/icon.icns",
    bundle_identifier="com.rostyslavyarosh.sunny-whisper",
    version=APP_VERSION,
    info_plist={
        "NSMicrophoneUsageDescription": "App needs microphone access for recording audio",
        "NSAppleEventsUsageDescription": "App needs to listen for keyboard shortcuts",
        "NSAccessibilityUsageDescription": "App needs accessibility access to detect key presses",
    },
)