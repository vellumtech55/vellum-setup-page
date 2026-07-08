"""
Toast notifications and the "get this app" dialog.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .theme import C, FONT, MONO
from .data import save_registry
from .download import open_download_page, import_downloaded_file


class Toast(tk.Toplevel):
    def __init__(self, root, message, kind="info"):
        super().__init__(root)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        bg = {"info": C["accent"], "success": "#166534", "error": "#7F1D1D"}.get(kind, C["accent"])
        self.configure(bg=bg)

        tk.Label(self, text=message, bg=bg, fg=C["white"],
                 font=(FONT, 10), padx=20, pady=12).pack()

        # Position bottom-right of root
        root.update_idletasks()
        rx, ry = root.winfo_x(), root.winfo_y()
        rw, rh = root.winfo_width(), root.winfo_height()
        self.update_idletasks()
        tw, th = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{rx+rw-tw-24}+{ry+rh-th-24}")
        self.after(2800, self.destroy)


class GetAppDialog(tk.Toplevel):
    """
    Two steps, matching what actually has to happen with a Gumroad link:
      1. Open the product page in the real browser — you check out /
         click download there, same as you always would.
      2. Once the file's landed in your Downloads folder (or wherever),
         point the launcher at it and it gets copied into plugins/.

    Pass is_update=True to use update-specific copy and correctly stamp
    installed_version on completion.
    """
    def __init__(self, root, app, registry, on_complete, is_update=False):
        super().__init__(root)
        action = "Update" if is_update else "Get"
        self.title(f"{action} {app['name']}")
        self.geometry("420x270")
        self.configure(bg=C["card"])
        self.resizable(False, False)
        self.grab_set()
        self._root = root
        self._app = app
        self._registry = registry
        self._on_complete = on_complete
        self._is_update = is_update

        title_text = app["name"]
        if is_update:
            old_v = app.get("installed_version", "?")
            new_v = app.get("version", "?")
            title_text += f"  {old_v} → {new_v}"
        tk.Label(self, text=title_text, font=(FONT, 13, "bold"),
                 bg=C["card"], fg=C["white"]).pack(pady=(22, 2))
        tk.Label(self, text=app.get("download_url", ""),
                 font=(MONO, 7), bg=C["card"], fg=C["muted"]).pack()

        body = tk.Frame(self, bg=C["card"])
        body.pack(fill="both", expand=True, padx=24, pady=18)

        step1_text = ("Download the latest version from the product page."
                      if is_update else
                      "Open the product page and download it as usual.")
        tk.Label(body, text="Step 1", font=(FONT, 8, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w")
        tk.Label(body, text=step1_text,
                 font=(FONT, 9), bg=C["card"], fg=C["sub"], justify="left",
                 wraplength=360).pack(anchor="w", pady=(0, 6))
        from .widgets import HoverButton, GhostButton
        HoverButton(body, "Open in browser", self._open_browser,
                    padx=14, pady=6).pack(anchor="w")

        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=16)

        step2_text = ("Once downloaded, select the file and I'll replace the old version."
                      if is_update else
                      "Once it's downloaded, select the file and I'll install it.")
        tk.Label(body, text="Step 2", font=(FONT, 8, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w")
        tk.Label(body, text=step2_text,
                 font=(FONT, 9), bg=C["card"], fg=C["sub"], justify="left",
                 wraplength=360).pack(anchor="w", pady=(0, 6))
        btn_text = "Select update file…" if is_update else "Select downloaded file…"
        HoverButton(body, btn_text, self._pick_file,
                    padx=14, pady=6).pack(anchor="w")

        self._status = tk.Label(body, text="", font=(FONT, 9),
                                bg=C["card"], fg=C["muted"])
        self._status.pack(anchor="w", pady=(10, 0))

    def _open_browser(self):
        open_download_page(self._app)

    def _pick_file(self):
        title = (f"Select the update file for {self._app['name']}"
                 if self._is_update else
                 f"Select the downloaded file for {self._app['name']}")
        path = filedialog.askopenfilename(title=title)
        if not path:
            return
        verb = "Updating…" if self._is_update else "Installing…"
        self._status.config(text=verb, fg=C["sub"])
        self.update_idletasks()
        try:
            if self._is_update:
                # Remove old installed files before extracting the new version
                from .download import uninstall_app
                uninstall_app(self._app)
            installed_path = import_downloaded_file(self._app, path)
            self._done(installed_path)
        except Exception as ex:
            self._status.config(text=f"Failed: {ex}", fg=C["red"])

    def _done(self, installed_path):
        new_version = self._app.get("version", "")
        for a in self._registry["apps"]:
            if a["id"] == self._app["id"]:
                a["installed"]         = True
                a["installed_path"]    = installed_path
                a["installed_version"] = new_version   # always stamp the catalog version
                a["has_update"]        = False
        save_registry(self._registry)
        self.destroy()
        verb = "updated" if self._is_update else "installed"
        Toast(self._root, f"✓  {self._app['name']} {verb} to v{new_version}", "success")
        self._on_complete()
