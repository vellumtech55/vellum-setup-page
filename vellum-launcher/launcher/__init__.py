"""
Vellum App Launcher
────────────────────
A dark-themed desktop launcher for downloading, updating, and running
Vellum's suite of small tools.

Package layout:
    theme.py     – colors, fonts, platform detection
    paths.py     – filesystem locations (apps.json, plugins/)
    data.py      – registry load/save + background update checks
    download.py  – downloading and launching plugin scripts
    widgets.py   – reusable UI primitives (buttons, badges, scroll frame)
    dialogs.py   – Toast notifications + download progress dialog
    app.py       – the Launcher window and all pages
"""
