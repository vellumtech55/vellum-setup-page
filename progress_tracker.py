import tkinter as tk
from tkinter import ttk

# ── Default black / gray / blue palette ──────────────────────────────────────
# Used as a fallback for any key the host app's `app.colors` dict doesn't
# already define, so this file keeps working whether it's dropped into an
# existing app or run standalone.
COLORS = {
    "bg":            "#121212",  # window / page background (near-black)
    "panel":         "#1c1c1f",  # card / row background (dark gray)
    "surface":       "#242427",  # inputs, hover surfaces (lighter gray)
    "border":        "#2f2f33",  # hairline borders
    "text":          "#e8e8ea",  # primary text
    "text_muted":    "#9a9aa2",  # secondary / caption text
    "accent":        "#3b82f6",  # blue accent
    "accent_hover":  "#2f6fe0",  # blue, hover state
    "accent_pressed":"#265dc0",  # blue, pressed state
    "success":       "#22c55e",
}


def _merged_colors(app):
    """Combine the host app's palette (if any) with the black/gray/blue
    defaults, so any keys the app doesn't set still get a sensible value."""
    colors = dict(COLORS)
    supplied = getattr(app, "colors", None) or {}
    colors.update(supplied)
    return colors


def _configure_styles(colors):
    """Configure ttk styles for the widgets this page uses. ttk widgets
    (Progressbar, Button, Frame, Label) ignore plain bg=/fg=, so they need
    to go through ttk.Style instead."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass  # "clam" isn't available on some platforms; fall back silently

    # Frames
    style.configure("TFrame", background=colors["bg"])
    style.configure("Card.TFrame", background=colors["panel"])

    # Labels
    style.configure("TLabel", background=colors["bg"], foreground=colors["text"])
    style.configure("Card.TLabel", background=colors["panel"], foreground=colors["text"])
    style.configure("Muted.TLabel", background=colors["panel"], foreground=colors["text_muted"])

    # Progress bar
    style.configure(
        "Vellum.Horizontal.TProgressbar",
        troughcolor=colors["surface"],
        bordercolor=colors["border"],
        background=colors["accent"],
        lightcolor=colors["accent"],
        darkcolor=colors["accent"],
        thickness=14,
    )

    # Secondary buttons (+10% / -10% / Reset)
    style.configure(
        "TButton",
        background=colors["surface"],
        foreground=colors["text"],
        bordercolor=colors["border"],
        focuscolor=colors["surface"],
        padding=6,
    )
    style.map(
        "TButton",
        background=[("active", colors["border"]), ("pressed", colors["border"])],
        foreground=[("disabled", colors["text_muted"])],
    )

    # Primary button (Add Task) — blue accent
    style.configure(
        "Accent.TButton",
        background=colors["accent"],
        foreground="#ffffff",
        bordercolor=colors["accent"],
        focuscolor=colors["accent"],
        padding=7,
    )
    style.map(
        "Accent.TButton",
        background=[("active", colors["accent_hover"]), ("pressed", colors["accent_pressed"])],
    )

    return style


def _style_entry(entry, colors, width=None):
    """Apply black/gray/blue styling to a plain tk.Entry (ttk.Entry's
    theming is more limited, so these stay as tk.Entry with manual colors)."""
    entry.configure(
        bg=colors["surface"],
        fg=colors["text"],
        insertbackground=colors["accent"],   # cursor color
        relief="flat",
        highlightthickness=1,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],     # border color on focus
        bd=0,
    )
    if width:
        entry.configure(width=width)


class SubTaskRow(ttk.Frame):
    def __init__(self, parent, title, weight, update_callback, colors=None):
        self.colors = colors or COLORS
        super().__init__(parent, style="Card.TFrame")

        self.weight = float(weight)
        self.value = tk.DoubleVar(value=0)
        self.update_callback = update_callback

        ttk.Label(
            self,
            text=f"{title} ({self.weight * 100:.0f}% impact)",
            style="Card.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=(10, 8), pady=8)

        ttk.Progressbar(
            self,
            orient="horizontal",
            maximum=100,
            variable=self.value,
            length=250,
            style="Vellum.Horizontal.TProgressbar"
        ).grid(row=0, column=1, sticky="ew", pady=8)

        self.text_var = tk.StringVar(value="0%")

        ttk.Label(
            self,
            textvariable=self.text_var,
            style="Muted.TLabel"
        ).grid(row=0, column=2, padx=(8, 10), pady=8)

        self.columnconfigure(1, weight=1)

        self.value.trace_add("write", self._changed)

    def _changed(self, *args):
        self.text_var.set(f"{self.value.get():.0f}%")
        self.update_callback()

    def get_weighted_progress(self):
        return self.value.get() * self.weight / 100

    def set_progress(self, value):
        self.value.set(max(0, min(100, value)))

    def adjust(self, amount):
        self.set_progress(self.value.get() + amount)


class ToolPage(tk.Frame):
    def __init__(self, parent, app):
        self.colors = _merged_colors(app)
        _configure_styles(self.colors)

        super().__init__(parent, bg=self.colors["bg"])

        self.app = app
        self.subtasks = []

        self.main_progress = tk.DoubleVar(value=0)
        self.main_text = tk.StringVar(value="Overall Progress: 0%")

        self._build_header()
        self._build_tasks()
        self._build_form()

        self.add_subtask("Download Files", 0.3)
        self.add_subtask("Process Data", 0.4)
        self.add_subtask("Write Report", 0.3)

    def _build_header(self):
        colors = self.colors

        tk.Label(
            self,
            text="Work Tracker",
            font=("Segoe UI", 20, "bold"),
            fg=colors["text"],
            bg=colors["bg"]
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.main_bar = ttk.Progressbar(
            self,
            maximum=100,
            variable=self.main_progress,
            style="Vellum.Horizontal.TProgressbar"
        )
        self.main_bar.pack(fill="x", padx=20)

        tk.Label(
            self,
            textvariable=self.main_text,
            fg=colors["accent"],
            bg=colors["bg"],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=20, pady=(8, 20))

    def _build_tasks(self):
        self.tasks_frame = tk.Frame(
            self,
            bg=self.colors["bg"]
        )
        self.tasks_frame.pack(
            fill="both",
            expand=True,
            padx=20
        )

    def _build_form(self):
        colors = self.colors

        form = tk.Frame(
            self,
            bg=colors["bg"]
        )
        form.pack(fill="x", padx=20, pady=(10, 20))

        self.title_var = tk.StringVar()

        tk.Label(
            form,
            text="Title",
            fg=colors["text_muted"],
            bg=colors["bg"]
        ).pack(side="left")

        title_entry = tk.Entry(form, textvariable=self.title_var)
        _style_entry(title_entry, colors)
        title_entry.pack(side="left", padx=5, ipady=3)

        self.weight_var = tk.DoubleVar(value=0.1)

        tk.Label(
            form,
            text="Impact",
            fg=colors["text_muted"],
            bg=colors["bg"]
        ).pack(side="left", padx=(15, 0))

        weight_entry = tk.Entry(form, textvariable=self.weight_var)
        _style_entry(weight_entry, colors, width=8)
        weight_entry.pack(side="left", padx=5, ipady=3)

        ttk.Button(
            form,
            text="Add Task",
            command=self._add_clicked,
            style="Accent.TButton"
        ).pack(side="left", padx=10)

    def _add_clicked(self):
        title = self.title_var.get().strip() or "Untitled"
        weight = self.weight_var.get()

        self.add_subtask(title, weight)

        self.title_var.set("")
        self.weight_var.set(0.1)

        self.app.set_status(
            f"Added task '{title}'",
            "success"
        )

    def add_subtask(self, title, weight):
        colors = self.colors

        row_frame = tk.Frame(
            self.tasks_frame,
            bg=colors["panel"],
            highlightthickness=1,
            highlightbackground=colors["border"]
        )
        row_frame.pack(fill="x", pady=4)

        row = SubTaskRow(
            row_frame,
            title,
            weight,
            self.update_progress,
            colors=colors
        )
        row.pack(side="left", fill="x", expand=True)

        ttk.Button(
            row_frame,
            text="+10%",
            command=lambda: row.adjust(10),
            style="TButton"
        ).pack(side="left", padx=(2, 2), pady=6)

        ttk.Button(
            row_frame,
            text="-10%",
            command=lambda: row.adjust(-10),
            style="TButton"
        ).pack(side="left", padx=2, pady=6)

        ttk.Button(
            row_frame,
            text="Reset",
            command=lambda: row.set_progress(0),
            style="TButton"
        ).pack(side="left", padx=(2, 10), pady=6)

        self.subtasks.append({
            "frame": row_frame,
            "row": row
        })

        self.update_progress()

    def update_progress(self):

        total = sum(
            item["row"].get_weighted_progress()
            for item in self.subtasks
        )

        self.main_progress.set(total)
        self.main_text.set(
            f"Overall Progress: {total:.0f}%"
        )

        if total >= 100:
            self.app.set_status(
                "All tasks complete!",
                "success"
            )


# ── Standalone preview ────────────────────────────────────────────────────
# Lets you run this file directly to see the black/gray/blue theme without
# wiring it into the full app. Not used when ToolPage is imported normally.
if __name__ == "__main__":

    class _DemoApp:
        """Minimal stand-in for the real app object, just enough to satisfy
        what ToolPage expects (a .colors dict and a .set_status method)."""
        def __init__(self, root):
            self.root = root
            self.colors = COLORS
            self.status_var = tk.StringVar(value="Ready")

        def set_status(self, message, kind="info"):
            self.status_var.set(message)
            print(f"[status:{kind}] {message}")

    root = tk.Tk()
    root.title("Progress Tracker — preview")
    root.geometry("560x480")
    root.configure(bg=COLORS["bg"])

    demo_app = _DemoApp(root)
    page = ToolPage(root, demo_app)
    page.pack(fill="both", expand=True)

    status_bar = tk.Label(
        root,
        textvariable=demo_app.status_var,
        bg=COLORS["panel"],
        fg=COLORS["text_muted"],
        anchor="w",
        padx=12,
        pady=6
    )
    status_bar.pack(fill="x", side="bottom")

    root.mainloop()
