"""
Filesystem locations used by the launcher.

BASE_DIR resolves to the project root — the folder containing main.py and
apps.json — regardless of whether the app is run as a plain script or as a
frozen PyInstaller executable.
"""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Running as a PyInstaller exe — use the folder the .exe lives in,
    # NOT sys._MEIPASS (that's a temp extraction dir, wiped on exit).
    BASE_DIR = Path(sys.executable).parent
else:
    # This file lives at <project_root>/launcher/paths.py, so the project
    # root is two levels up from here.
    BASE_DIR = Path(__file__).resolve().parent.parent

APPS_JSON = BASE_DIR / "apps.json"
APPS_DIR  = BASE_DIR / "plugins"
APPS_DIR.mkdir(exist_ok=True)
