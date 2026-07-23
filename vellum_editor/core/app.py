import os
import sys
import platform
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from core.settings import Settings
from core.theme import THEMES, DEFAULT_THEME

APP_NAME    = "Vellum"
APP_VERSION = "2.0"
DEBUG_MODE  = False   # toggled at runtime from the Debug menu


class VellumTool(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.settings    = Settings()
        theme_name       = self.settings.get("theme", DEFAULT_THEME)
        self.theme       = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self._theme_name = theme_name

        ctk.set_appearance_mode("light" if theme_name != "Dark" else "dark")

        self.title(APP_NAME)
        self.geometry("980x660")
        self.minsize(760, 500)
        self.configure(bg=self.theme["bg"])

        self.page = None
        self._verbose = False

        self._build_menu()
        self._build_ui()
        self._mount_tool()

    # ── layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        t = self.theme

        self.grid_rowconfigure(0, minsize=52, weight=0)   # topbar
        self.grid_rowconfigure(1, minsize=1,  weight=0)   # divider
        self.grid_rowconfigure(2, weight=1)                # content
        self.grid_rowconfigure(3, minsize=30, weight=0)   # status bar
        self.grid_columnconfigure(0, weight=1)

        # ── TOP BAR ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=t["topbar"], height=52)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)

        left = tk.Frame(topbar, bg=t["topbar"])
        left.pack(side="left", padx=20, fill="y")

        # Accent dot logo
        canvas = tk.Canvas(left, width=28, height=28, bg=t["topbar"],
                            highlightthickness=0)
        canvas.pack(side="left", pady=12, padx=(0, 10))
        canvas.create_oval(4, 4, 24, 24, fill=t["accent"], outline="")
        canvas.create_oval(10, 10, 18, 18, fill=t["topbar"], outline="")

        tk.Label(
            left, text=APP_NAME,
            font=("Segoe UI", 14, "bold"),
            fg=t["text"], bg=t["topbar"]
        ).pack(side="left")

        tk.Label(
            left, text=f"v{APP_VERSION}",
            font=("Segoe UI", 9),
            fg=t["text_dim"], bg=t["topbar"]
        ).pack(side="left", padx=(6, 0), pady=16)

        # right side: theme
        right = tk.Frame(topbar, bg=t["topbar"])
        right.pack(side="right", padx=20, fill="y")

        tk.Label(
            right, text="Theme",
            font=("Segoe UI", 9),
            fg=t["text_muted"], bg=t["topbar"]
        ).pack(side="left", padx=(0, 8), pady=17)

        self._theme_var = tk.StringVar(value=self._theme_name)
        ctk.CTkOptionMenu(
            right,
            values=list(THEMES.keys()),
            variable=self._theme_var,
            command=self._on_theme_change,
            fg_color=t["panel_alt"],
            button_color=t["accent"],
            button_hover_color=t["accent_hover"],
            dropdown_fg_color=t["panel"],
            dropdown_hover_color=t["panel_alt"],
            text_color=t["text"],
            font=("Segoe UI", 10),
            height=30,
            corner_radius=6,
            width=120,
        ).pack(side="left", pady=11)

        # ── DIVIDER ───────────────────────────────────────────────────────────
        tk.Frame(self, height=1, bg=t["border"]).grid(
            row=1, column=0, sticky="ew"
        )

        # ── CONTENT ───────────────────────────────────────────────────────────
        self._content = tk.Frame(self, bg=t["bg"])
        self._content.grid(row=2, column=0, sticky="nsew")

        # ── STATUS BAR ────────────────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=t["topbar"], height=30)
        status_bar.grid(row=3, column=0, sticky="ew")
        status_bar.grid_propagate(False)

        tk.Frame(status_bar, width=1, bg=t["border"]).pack(side="left")

        self._status_dot = tk.Label(
            status_bar, text="●",
            font=("Segoe UI", 8),
            fg=t["success"], bg=t["topbar"]
        )
        self._status_dot.pack(side="left", padx=(14, 5), pady=6)

        self._status_lbl = tk.Label(
            status_bar, text="Ready",
            font=("Segoe UI", 9),
            fg=t["text_muted"], bg=t["topbar"], anchor="w"
        )
        self._status_lbl.pack(side="left")

    # ── mount tool ────────────────────────────────────────────────────────────
    def _mount_tool(self):
        try:
            from tool.editor_page import EditorPage
            page = EditorPage(self._content, self)
            page.pack(fill="both", expand=True)
            self.page = page
        except Exception as e:
            import traceback
            self._render_error(traceback.format_exc())

    # ── debug menu ────────────────────────────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self)

        debug_menu = tk.Menu(menubar, tearoff=0)
        debug_menu.add_command(label="Show app state…", command=self._debug_show_state)
        debug_menu.add_command(label="Show editor config…", command=self._debug_show_editor_config)
        debug_menu.add_command(label="Show settings.json…", command=self._debug_show_settings_file)
        debug_menu.add_separator()

        self._verbose_var = tk.BooleanVar(value=False)
        debug_menu.add_checkbutton(
            label="Verbose console logging",
            variable=self._verbose_var,
            command=self._debug_toggle_verbose,
        )
        debug_menu.add_command(label="Reload theme", command=self._debug_reload_theme)
        debug_menu.add_command(label="Open output folder", command=self._debug_open_output_folder)
        debug_menu.add_separator()
        debug_menu.add_command(label="Clear activity log", command=self._debug_clear_log)
        debug_menu.add_command(label="Force test error", command=self._debug_force_error)

        menubar.add_cascade(label="Debug", menu=debug_menu)
        self.configure(menu=menubar)

    def _debug_show_state(self):
        p = self.page
        lines = [
            f"App version: {APP_VERSION}",
            f"Python: {platform.python_version()} ({platform.system()} {platform.release()})",
            f"Theme: {self._theme_name}",
            f"Verbose logging: {self._verbose}",
        ]
        if p is not None:
            lines += [
                "",
                "— Editor page —",
                f"Video file: {p._video.get() or '(none)'}",
                f"Output folder: {p._outdir.get()}",
                f"Mode: {p._mode.get()}",
                f"Voice sensitivity: {p._thresh.get():.3f}",
                f"Game audio (beta): {p._game.get()}",
                f"Running: {p._running}",
            ]
        else:
            lines.append("\n(Editor page failed to load)")
        messagebox.showinfo("Debug — App State", "\n".join(lines))

    def _debug_show_editor_config(self):
        try:
            from video_editor import editor_config as cfg
        except Exception as e:
            messagebox.showerror("Debug — Editor Config", f"Could not import editor_config:\n{e}")
            return
        attrs = [a for a in dir(cfg) if a.isupper()]
        lines = [f"{a} = {getattr(cfg, a)!r}" for a in attrs]
        messagebox.showinfo("Debug — editor_config.py", "\n".join(lines))

    def _debug_show_settings_file(self):
        lines = [f"{k} = {v!r}" for k, v in self.settings.data.items()]
        lines.append(f"\nFile path: {os.path.abspath(self.settings.path)}")
        messagebox.showinfo("Debug — settings.json", "\n".join(lines) if lines else "(empty)")

    def _debug_toggle_verbose(self):
        self._verbose = self._verbose_var.get()
        msg = f"Verbose console logging {'enabled' if self._verbose else 'disabled'}"
        print(f"[DEBUG] {msg}")
        self.set_status(msg, "info")
        if self.page is not None:
            self.page._log_line(msg, "info")

    def _debug_reload_theme(self):
        theme_name = self.settings.get("theme", DEFAULT_THEME)
        self.theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.set_status(f"Reloaded theme '{theme_name}' (restart still needed for full effect)", "info")
        if self.page is not None:
            self.page._log_line(f"[debug] reloaded theme data for '{theme_name}'", "info")

    def _debug_open_output_folder(self):
        folder = self.page._outdir.get().strip() if self.page is not None else ""
        if not folder:
            messagebox.showwarning("Debug — Output Folder", "No output folder set yet.")
            return
        os.makedirs(folder, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as e:
            messagebox.showerror("Debug — Output Folder", f"Could not open folder:\n{e}")

    def _debug_clear_log(self):
        if self.page is not None:
            self.page._clear_log()

    def _debug_force_error(self):
        """Deliberately raise, to exercise the app's error-handling path."""
        if self.page is not None:
            self.page._log_line("[debug] simulating an error…", "warning")
        try:
            raise RuntimeError("This is a simulated debug error — not a real failure.")
        except Exception:
            import traceback
            trace = traceback.format_exc()
            print(trace)
            if self.page is not None:
                self.page._log_line(trace, "error")
            messagebox.showerror("Debug — Forced Error", trace)

    def _render_error(self, message: str):
        t = self.theme
        f = tk.Frame(self._content, bg=t["bg"])
        f.pack(fill="both", expand=True)
        tk.Label(
            f, text="Could not load tool",
            font=("Segoe UI", 15, "bold"),
            fg=t["error"], bg=t["bg"]
        ).pack(pady=(100, 8))
        txt = tk.Text(f, font=("Courier", 9), fg=t["text_muted"],
                      bg=t["panel"], relief="flat", wrap="word",
                      height=12, width=80)
        txt.insert("1.0", message)
        txt.configure(state="disabled")
        txt.pack(pady=4, padx=40)

    # ── theme ─────────────────────────────────────────────────────────────────
    def _on_theme_change(self, name: str):
        self.settings.set("theme", name)
        self.set_status(f"Theme set to '{name}' — restart to apply", "warning")

    # ── public API ────────────────────────────────────────────────────────────
    def set_status(self, text: str, level: str = "info"):
        t = self.theme
        colors = {
            "info":    (t["text_muted"],  t["accent"]),
            "success": (t["success"],     t["success"]),
            "warning": (t["warning"],     t["warning"]),
            "error":   (t["error"],       t["error"]),
        }
        txt_col, dot_col = colors.get(level, colors["info"])
        self._status_lbl.configure(text=text, fg=txt_col)
        self._status_dot.configure(fg=dot_col)

    @property
    def colors(self):
        return self.theme
