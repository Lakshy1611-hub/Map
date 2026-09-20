# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project = Path(SPEC).resolve().parent

a = Analysis(
    ["main.py"],
    pathex=[str(project)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "edge_tts",
        "pygame",
        "pyttsx3",
        "pystray",
        "PIL",
        "google.genai",
        "google.genai.types",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
