"""
Vellum Screen Capture
Reusable UI components

Anything used more than once in the UI, or complex enough to clutter
main_window.py, lives here.
"""

import customtkinter as ctk

from theme import ERROR, NORMAL_FONT, SMALL_FONT


class LabeledCombo(ctk.CTkFrame):
    """A label + combobox pair laid out as one packable/gridable unit.

    Replaces the repeated "label(col, text) + CTkComboBox" boilerplate
    that used to appear three times in main_window.py (FPS, Quality, Format).
    """

    def __init__(self, master, label_text, values, width=100, initial=None, **kwargs):
        super().__init__(master, fg_color="transparent")

        self.label = ctk.CTkLabel(self, text=label_text, font=SMALL_FONT)
        self.label.pack(side="left", padx=(0, 6))

        self.combo = ctk.CTkComboBox(self, values=values, width=width, **kwargs)
        if initial is not None:
            self.combo.set(str(initial))
        self.combo.pack(side="left")

    def get(self):
        return self.combo.get()

    def set(self, value):
        self.combo.set(str(value))


class RecordingOverlay(ctk.CTkToplevel):
    """Small always-on-top badge shown in the corner while recording."""

    def __init__(self, master):
        super().__init__(master)
        self.geometry("160x40+20+20")
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        ctk.CTkLabel(
            self,
            text="● Recording",
            text_color=ERROR,
            font=NORMAL_FONT,
        ).pack(expand=True)
