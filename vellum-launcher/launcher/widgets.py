"""
Reusable widget primitives: dividers, icon badges, pills, buttons, and a
scrollable frame with proper mouse-wheel + touchpad support.
"""

import tkinter as tk
from tkinter import ttk

from .theme import C, FONT, PLAT


def sep(parent, axis="x", pad=0):
    """Thin divider line."""
    if axis == "x":
        tk.Frame(parent, bg=C["card_border"], height=1).pack(fill="x", padx=pad, pady=6)
    else:
        tk.Frame(parent, bg=C["card_border"], width=1).pack(fill="y", side="left", padx=6)


def icon_badge(parent, app, size=40):
    """
    Layered icon badge: outer frame (color) + inner label (glyph).
    Looks like a rounded-square app icon.
    """
    color = app.get("icon_color", C["accent"])
    outer = tk.Frame(parent, bg=color, width=size, height=size)
    outer.pack_propagate(False)
    tk.Label(
        outer,
        text=app.get("icon_char", "?"),
        bg=color, fg=C["white"],
        font=(FONT, max(9, size // 3 - 1), "bold"),
    ).place(relx=0.5, rely=0.5, anchor="center")
    return outer


def pill_label(parent, text, color=None, fg=None):
    """Small status pill."""
    bg = color or C["accent"]
    fg = fg or C["white"]
    return tk.Label(
        parent, text=text,
        bg=bg, fg=fg,
        font=(FONT, 7, "bold"),
        padx=6, pady=2,
    )


class HoverButton(tk.Label):
    """
    A Label styled as a button with hover + press states.
    tkinter's tk.Button is hard to style well cross-platform; this avoids it.
    """
    def __init__(self, parent, text, command,
                 bg=None, fg=None, hover_bg=None,
                 font_size=9, bold=True, padx=16, pady=7, width=None, **kw):
        self._bg      = bg       or C["accent"]
        self._fg      = fg       or C["white"]
        self._hover   = hover_bg or C["accent_dim"]
        self._cmd     = command

        kw.setdefault("cursor", "hand2")
        kw.setdefault("relief", "flat")
        super().__init__(
            parent,
            text=text,
            bg=self._bg, fg=self._fg,
            font=(FONT, font_size, "bold" if bold else "normal"),
            padx=padx, pady=pady,
            **kw,
        )
        if width:
            self.config(width=width)
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, _):   self.config(bg=self._hover)
    def _on_leave(self, _):   self.config(bg=self._bg)
    def _on_press(self, _):   self.config(bg=C["accent_dim"])
    def _on_release(self, e): self.config(bg=self._hover); self._cmd()

    def set_bg(self, bg, hover=None):
        self._bg    = bg
        self._hover = hover or bg
        self.config(bg=bg)


class GhostButton(HoverButton):
    def __init__(self, parent, text, command, **kw):
        kw.setdefault("fg", C["sub"])
        super().__init__(
            parent, text, command,
            bg=C["input"], hover_bg=C["card_hover"],
            **kw,
        )


def scrollable_frame(parent):
    """
    Return (inner_frame, canvas). Pack canvas into parent.

    Mouse-wheel / touchpad scrolling is bound only while the pointer is
    actually over this canvas (bind on <Enter>, unbind on <Leave>), rather
    than globally for the whole app's lifetime. That matters because the
    launcher pre-builds several pages — each with its own scrollable
    canvas — at startup; a permanent bind_all() would leave every page's
    wheel events wired to whichever canvas happened to bind last, instead
    of the one the user is actually looking at.

    Delta handling is platform-specific:
      - Windows: wheel/touchpad deltas arrive in multiples of 120.
      - macOS:   trackpad deltas arrive as small raw line counts.
      - Linux:   no <MouseWheel> event; uses Button-4 / Button-5 instead.
    """
    canvas = tk.Canvas(parent, bg=C["base"], highlightthickness=0, bd=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=C["base"])
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _resize(e): canvas.itemconfig(win_id, width=e.width)
    def _scroll(e): canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.bind("<Configure>", _resize)
    inner.bind("<Configure>", _scroll)
    canvas.configure(yscrollcommand=vsb.set)

    def _on_wheel(e):
        if PLAT == "darwin":
            canvas.yview_scroll(-1 * e.delta, "units")
        else:
            units = int(-1 * (e.delta / 120)) if e.delta else 0
            canvas.yview_scroll(units or (-1 if e.delta > 0 else 1), "units")

    def _on_wheel_up(e):   canvas.yview_scroll(-1, "units")
    def _on_wheel_down(e): canvas.yview_scroll(1, "units")

    def _bind_wheel(_e=None):
        canvas.bind_all("<MouseWheel>", _on_wheel)
        canvas.bind_all("<Button-4>", _on_wheel_up)
        canvas.bind_all("<Button-5>", _on_wheel_down)

    def _unbind_wheel(_e=None):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind_wheel)
    canvas.bind("<Leave>", _unbind_wheel)
    inner.bind("<Enter>", _bind_wheel)

    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return inner, canvas
