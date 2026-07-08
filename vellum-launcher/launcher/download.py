"""
Getting apps onto disk, and running them.

Gumroad product links are checkout pages, not direct file URLs — there's
no way to script your way past that (and no reason to try). So the flow
here mirrors what you'd actually do by hand:

  1. open_download_page(app)   — opens the Gumroad page in your real
                                  default browser. You check out / hit
                                  the download button there, same as
                                  always.
  2. import_downloaded_file()  — once the file has landed wherever your
                                  browser saves downloads, you point the
                                  launcher at it and it copies (or, for a
                                  zip, extracts) it into plugins/.

Nothing is renamed or guessed at — whatever file or folder you hand it is
exactly what ends up installed, and that exact path is recorded on the
app's registry entry as "installed_path" so launching knows precisely
where to look.
"""

import os
import shutil
import subprocess
import sys
import webbrowser
import zipfile
from pathlib import Path
from tkinter import messagebox

from .paths import APPS_DIR, BASE_DIR


def open_download_page(app):
    """Open the app's Gumroad page in the system's default browser."""
    url = app.get("download_url", "")
    if not url:
        messagebox.showerror("No link", "No download URL configured for this app.")
        return False
    webbrowser.open(url)
    return True


def import_downloaded_file(app, src_path):
    """
    Take a file the user picked (already downloaded via their browser) and
    install it into plugins/. Returns the installed_path to store on the
    app's registry entry, or raises on failure.
    """
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"File not found:\n{src}")

    if zipfile.is_zipfile(src):
        before = {p.name for p in APPS_DIR.iterdir()}
        with zipfile.ZipFile(src) as zf:
            zf.extractall(APPS_DIR)
        new_entries = sorted({p.name for p in APPS_DIR.iterdir()} - before)
        return new_entries[0] if len(new_entries) == 1 else src.name
    else:
        dest = APPS_DIR / src.name
        shutil.copy2(src, dest)
        return src.name


def _find_python():
    """
    Return a command usable to run a .py plugin script.
    When running unfrozen (plain `python main.py`), sys.executable
    IS Python — use it. When frozen by PyInstaller, sys.executable is
    the launcher .exe itself, so we must locate a real interpreter
    on the system PATH instead.
    """
    if not getattr(sys, "frozen", False):
        return sys.executable
    for candidate in ("python", "python3", "py"):
        found = shutil.which(candidate)
        if found:
            return found
    return None


def _is_native_binary(p):
    """True for a compiled executable: .exe on Windows, or an
    extension-less file with the executable bit set on Mac/Linux."""
    if p.suffix.lower() == ".exe":
        return True
    return not p.suffix and os.access(p, os.X_OK)


def _entry_point(loc):
    """
    If loc is a single file, that's the entry point. If it's a folder,
    find the thing to run inside it — prefers a native executable
    (.exe / Mac-Linux binary) over a .py script, since a compiled app
    doesn't need a Python interpreter and is the common case for
    already-built products.
    """
    if loc.is_file():
        return loc
    for name in ("main.exe", "app.exe", "run.exe", "main.py", "app.py", "run.py"):
        cand = loc / name
        if cand.exists():
            return cand
    for p in sorted(loc.iterdir()):
        if p.is_file() and _is_native_binary(p):
            return p
    py_files = sorted(loc.glob("*.py"))
    return py_files[0] if py_files else None


def launch_app(app):
    installed = app.get("installed_path")
    candidates = [APPS_DIR / installed] if installed else []
    candidates += [APPS_DIR / app.get("script", ""), BASE_DIR / app.get("script", "")]

    for loc in candidates:
        if loc and loc.exists():
            entry = _entry_point(loc)
            if not entry:
                messagebox.showerror("Not found", f"No runnable app found in:\n{loc}")
                return
            try:
                if entry.suffix.lower() == ".py":
                    py = _find_python()
                    if not py:
                        messagebox.showerror(
                            "Python not found",
                            "This app needs a Python interpreter to run, but none "
                            "was found on your system PATH.\n\n"
                            "Install Python from python.org and try again."
                        )
                        return
                    subprocess.Popen([py, str(entry)], cwd=str(entry.parent))
                else:
                    # Compiled executable — run it directly, no interpreter needed.
                    subprocess.Popen([str(entry)], cwd=str(entry.parent))
            except Exception as ex:
                messagebox.showerror("Launch error", str(ex))
            return
    messagebox.showerror("Not found", f"Couldn't find an installed copy of {app['name']}.")


def uninstall_app(app):
    """Remove everything downloaded for this app."""
    installed = app.get("installed_path")
    if installed:
        target = APPS_DIR / installed
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()
