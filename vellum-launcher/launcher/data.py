"""
Registry I/O and remote catalog sync.

apps.json bundled with the launcher is the *offline fallback* — the full
product list plus install state for THIS machine (installed,
installed_path, installed_version). If CATALOG_URL below is set, the
launcher fetches it at startup and merges it in: add a product, or bump a
"version", in the hosted catalog and every launcher picks it up on next
open — nobody re-downloads the launcher itself.

Local install state is never touched by a sync — only catalog-level
fields (name, description, category, icon, script, download_url,
version) get refreshed from the remote copy.
"""

import json
import ssl
import sys
import threading
import urllib.request
from tkinter import messagebox

from .paths import APPS_JSON

# Explicitly point at certifi's cert bundle rather than relying on
# PyInstaller to auto-detect and include the system's default CA store —
# that detection is inconsistent across platforms/PyInstaller versions and
# is the #1 cause of "catalog sync silently does nothing in the .exe but
# works fine with `python main.py`". certifi ships its cacert.pem as
# package data, which PyInstaller *does* reliably bundle once certifi is
# an explicit import (unlike the OS cert store, which it can't see).
try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = None  # falls back to Python's default behavior


def _urlopen(url, timeout=6):
    return urllib.request.urlopen(url, timeout=timeout, context=_SSL_CONTEXT)

# Fields that describe local install state, not the product catalog —
# a sync never overwrites these even if somehow present in remote data.
_LOCAL_FIELDS = {"installed", "installed_path", "installed_version", "has_update"}


def load_registry():
    if not APPS_JSON.exists():
        messagebox.showerror("Error", f"apps.json not found:\n{APPS_JSON}")
        sys.exit(1)
    with open(APPS_JSON) as f:
        return json.load(f)


def save_registry(data):
    with open(APPS_JSON, "w") as f:
        json.dump(data, f, indent=2)


def installed_apps(apps):  return [a for a in apps if a.get("installed")]
def update_apps(apps):     return [a for a in apps if a.get("has_update")]


# ── Remote catalog ───────────────────────────────────────────────────────
# Host this JSON anywhere that serves a direct URL — a GitHub raw link is
# the easiest option, no server needed. Same shape as apps.json (a
# "launcher" info block, a "categories" list, and an "apps" list). Add a
# product or bump a "version" there and it shows up for everyone on next
# launch.
CATALOG_URL = "https://raw.githubusercontent.com/vellumtech55/Vellum-catalog/refs/heads/main/catalog.json"  # ← set this, e.g. https://raw.githubusercontent.com/you/repo/main/catalog.json


def sync_catalog(registry, on_done):
    """
    Fetch CATALOG_URL in a background thread and merge it into `registry`
    in place, then save the merged result back to apps.json (so it's
    cached for the next offline launch). Calls on_done() when finished
    either way — including immediately if CATALOG_URL isn't set.
    """
    if not CATALOG_URL:
        _recompute_updates(registry["apps"])
        on_done()
        return

    def _run():
        try:
            with _urlopen(CATALOG_URL) as r:
                remote = json.loads(r.read().decode("utf-8"))

            by_id = {a["id"]: a for a in registry["apps"]}
            for remote_app in remote.get("apps", []):
                rid = remote_app.get("id")
                if not rid:
                    continue
                catalog_fields = {k: v for k, v in remote_app.items() if k not in _LOCAL_FIELDS}
                if rid in by_id:
                    by_id[rid].update(catalog_fields)
                else:
                    new_app = dict(catalog_fields)
                    new_app.setdefault("installed", False)
                    registry["apps"].append(new_app)
                    by_id[rid] = new_app

            if remote.get("categories"):
                registry["categories"][:] = remote["categories"]
            if remote.get("launcher"):
                registry["launcher"].update(remote["launcher"])

            _recompute_updates(registry["apps"])
            save_registry(registry)
        except Exception:
            pass  # offline / unreachable — keep using the cached local copy
        on_done()

    threading.Thread(target=_run, daemon=True).start()


def _recompute_updates(apps):
    for a in apps:
        installed_ver = a.get("installed_version")
        a["has_update"] = bool(a.get("installed") and installed_ver and installed_ver != a.get("version"))
