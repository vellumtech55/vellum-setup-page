"""
Audio Converter Pro
Main application
"""

import threading
from tkinter import filedialog, ttk

import customtkinter as ctk

from converter import convert_file
from queue_manager import QueueManager
from settings_manager import load_settings, save_settings
from settings_tab import SettingsTab
from utils import is_supported

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#00BFFF"
BACKGROUND = "#08192D"


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Audio Converter Pro")
        self.geometry("1100x720")
        self.resizable(True, True)

        self.settings = load_settings()
        self.queue = QueueManager()
        self.output_folder = ""

        self._build_ui()

    # ----------------------------
    # UI
    # ----------------------------
    def _build_ui(self):
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_converter_tab(tabs.add("Converter"))

        settings_frame = tabs.add("Settings")
        self.settings_tab = SettingsTab(
            settings_frame, self.settings, on_save=self._save_settings, accent_color=ACCENT
        )
        self.settings_tab.pack(fill="both", expand=True)

    def _build_converter_tab(self, parent):
        # Toolbar
        toolbar = ctk.CTkFrame(parent, fg_color=BACKGROUND)
        toolbar.pack(fill="x", padx=8, pady=8)

        for text, cmd in [
            ("Add Files", self._add_files),
            ("Output Folder", self._select_output),
            ("Convert", self._start_conversion),
            ("Clear Queue", self._clear_queue),
        ]:
            ctk.CTkButton(toolbar, text=text, fg_color=ACCENT, width=120, command=cmd).pack(
                side="left", padx=4, pady=6
            )

        self.file_count_label = ctk.CTkLabel(toolbar, text="Queue: 0 files")
        self.file_count_label.pack(side="right", padx=16)

        self.folder_label = ctk.CTkLabel(toolbar, text="No output folder selected", text_color="gray")
        self.folder_label.pack(side="right", padx=8)

        # Queue table
        self.queue_table = ttk.Treeview(parent, columns=("file", "status"), show="headings", height=16)
        self.queue_table.heading("file", text="File")
        self.queue_table.heading("status", text="Status")
        self.queue_table.column("file", width=820)
        self.queue_table.column("status", width=160, anchor="center")
        self.queue_table.pack(fill="both", expand=True, padx=8, pady=4)

        # Progress + log
        self.progress = ttk.Progressbar(parent, mode="determinate")
        self.progress.pack(fill="x", padx=8, pady=4)

        self.log = ctk.CTkTextbox(parent, height=130, state="disabled")
        self.log.pack(fill="x", padx=8, pady=6)

    # ----------------------------
    # Actions
    # ----------------------------
    def _add_files(self):
        paths = filedialog.askopenfilenames()
        added = 0

        for p in paths:
            if not self.queue.contains(p) and is_supported(p):
                self.queue.add(p)
                self.queue_table.insert("", "end", iid=p, values=(p, "Waiting"))
                added += 1

        self._update_count()

        if added:
            self._log(f"Added {added} file(s).")

    def _select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.folder_label.configure(text=folder, text_color="white")
            self._log(f"Output → {folder}")

    def _clear_queue(self):
        self.queue.clear()
        for row in self.queue_table.get_children():
            self.queue_table.delete(row)
        self.progress["value"] = 0
        self._update_count()

    def _save_settings(self, values):
        self.settings = values
        save_settings(self.settings)
        self._log("Settings saved.")

    def _start_conversion(self):
        if not len(self.queue):
            self._log("No files in queue.")
            return
        if not self.output_folder:
            self._log("Please select an output folder first.")
            return
        threading.Thread(target=self._run_conversion, daemon=True).start()

    def _run_conversion(self):
        items = list(self.queue)
        total = len(items)
        s = self.settings

        for i, item in enumerate(items):
            success, result = convert_file(
                item["path"],
                self.output_folder,
                s["output_format"],
                s["bitrate"],
                s["sample_rate"],
                s["channels"],
                s["overwrite_mode"],
            )
            status = "✓ Done" if success else "✗ Failed"
            self.queue.set_status(item["path"], status)
            self.queue_table.item(item["path"], values=(item["path"], status))
            self._log(result)
            self.progress["value"] = (i + 1) / total * 100
            self.update_idletasks()

    # ----------------------------
    # Helpers
    # ----------------------------
    def _log(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg.strip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _update_count(self):
        self.file_count_label.configure(text=f"Queue: {len(self.queue)} files")


if __name__ == "__main__":
    App().mainloop()
