# -*- mode: python ; coding: utf-8 -*-
#
# Audio Converter Pro — PyInstaller build spec
#
# Why this file exists:
# customtkinter uses Pillow internally to render its rounded/scaled widget
# images. Pillow only imports its tkinter bridge module (PIL._tkinter_finder)
# the moment a widget actually needs to draw — PyInstaller's static import
# scanner never sees that need, so it gets left out of the frozen exe.
# Result: the app launches, but anything that needs to render (buttons,
# comboboxes, etc.) silently fails. customtkinter also ships its own
# theme JSON / asset files that PyInstaller won't pick up on its own.
#
# collect_all('customtkinter') grabs both of those in one shot; the explicit
# hidden import is a second safety net for the Pillow bridge module.
#
# Build with:
#   pyinstaller build.spec
#
# (Do NOT run `pyinstaller main.py` directly once this file exists —
# always build from the spec so these fixes are applied.)

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ["PIL._tkinter_finder"]

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")
datas += ctk_datas
binaries += ctk_binaries
hiddenimports += ctk_hiddenimports

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="AudioConverterPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
