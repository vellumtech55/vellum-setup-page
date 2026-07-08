import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from core.settings import Settings
from core.theme import THEMES, DEFAULT_THEME

APP_NAME    = "Vellum"
APP_VERSION = "2.0"


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
        except Exception as e:
            import traceback
            self._render_error(traceback.format_exc())

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
