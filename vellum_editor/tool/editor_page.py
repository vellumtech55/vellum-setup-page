# tool/editor_page.py — AI Video Editor UI
# Drop-in ToolPage that VellumTool._mount_tool() loads automatically.

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk


class EditorPage(tk.Frame):
    """Main editor UI — file picker, settings, progress, log."""

    def __init__(self, parent, app):
        t = app.colors
        super().__init__(parent, bg=t["bg"])
        self._app   = app
        self._t     = t
        self._video = tk.StringVar()
        self._outdir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Videos", "Vellum"))
        self._mode  = tk.StringVar(value="single")
        self._thresh = tk.DoubleVar(value=0.03)
        self._game  = tk.BooleanVar(value=False)
        self._running = False

        self._build()

    # ─────────────────────────────────────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────────────────────────────────────
    def _build(self):
        t = self._t

        # Two-column layout: left = controls (fixed), right = log (flex)
        self.grid_columnconfigure(0, minsize=340, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── LEFT PANEL ───────────────────────────────────────────────────────
        left = tk.Frame(self, bg=t["bg"], padx=24, pady=24)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        row = 0

        # Section: Input
        self._section(left, row, "Input"); row += 1

        self._field_label(left, row, "Video file"); row += 1
        pick_row = tk.Frame(left, bg=t["bg"])
        pick_row.grid(row=row, column=0, sticky="ew", pady=(0, 12)); row += 1
        pick_row.grid_columnconfigure(0, weight=1)

        self._video_entry = ctk.CTkEntry(
            pick_row, textvariable=self._video,
            placeholder_text="No file selected",
            fg_color=t["panel"], border_color=t["border"],
            text_color=t["text"], placeholder_text_color=t["text_dim"],
            font=("Segoe UI", 10), height=34, corner_radius=6,
        )
        self._video_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            pick_row, text="Browse",
            command=self._browse_video,
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color=t["btn_text"],
            font=("Segoe UI", 10, "bold"), height=34, corner_radius=6, width=80,
        ).grid(row=0, column=1)

        # Output folder
        self._field_label(left, row, "Output folder"); row += 1
        out_row = tk.Frame(left, bg=t["bg"])
        out_row.grid(row=row, column=0, sticky="ew", pady=(0, 20)); row += 1
        out_row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            out_row, textvariable=self._outdir,
            fg_color=t["panel"], border_color=t["border"],
            text_color=t["text"],
            font=("Segoe UI", 10), height=34, corner_radius=6,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            out_row, text="Browse",
            command=self._browse_outdir,
            fg_color=t["panel_alt"], hover_color=t["border"],
            text_color=t["text"],
            font=("Segoe UI", 10), height=34, corner_radius=6, width=80,
        ).grid(row=0, column=1)

        # Divider
        tk.Frame(left, bg=t["border"], height=1).grid(
            row=row, column=0, sticky="ew", pady=(4, 16)); row += 1

        # Section: Settings
        self._section(left, row, "Settings"); row += 1

        # Output mode
        self._field_label(left, row, "Output mode"); row += 1
        mode_row = tk.Frame(left, bg=t["bg"])
        mode_row.grid(row=row, column=0, sticky="ew", pady=(0, 12)); row += 1

        for label, val in [("Single file", "single"), ("Separate clips", "multiple")]:
            rb = tk.Radiobutton(
                mode_row, text=label, variable=self._mode, value=val,
                font=("Segoe UI", 10), fg=t["text"], bg=t["bg"],
                activeforeground=t["accent"], activebackground=t["bg"],
                selectcolor=t["panel_alt"],
                relief="flat", bd=0,
            )
            rb.pack(side="left", padx=(0, 16))

        # Volume threshold
        self._field_label(left, row, "Voice sensitivity"); row += 1
        thresh_row = tk.Frame(left, bg=t["bg"])
        thresh_row.grid(row=row, column=0, sticky="ew", pady=(0, 12)); row += 1
        thresh_row.grid_columnconfigure(0, weight=1)

        self._thresh_lbl = tk.Label(
            thresh_row, text=f"{self._thresh.get():.3f}",
            font=("Segoe UI", 10, "bold"),
            fg=t["accent"], bg=t["bg"], width=5,
        )
        self._thresh_lbl.grid(row=0, column=1, padx=(8, 0))

        ctk.CTkSlider(
            thresh_row,
            from_=0.005, to=0.15,
            variable=self._thresh,
            command=self._on_thresh,
            button_color=t["accent"],
            button_hover_color=t["accent_hover"],
            progress_color=t["accent"],
            fg_color=t["border"],
            height=16,
        ).grid(row=0, column=0, sticky="ew")

        tk.Label(
            left,
            text="Lower = more sensitive (picks up quieter speech)",
            font=("Segoe UI", 8), fg=t["text_dim"], bg=t["bg"],
        ).grid(row=row, column=0, sticky="w", pady=(0, 14)); row += 1

        # Game audio toggle
        game_row = tk.Frame(left, bg=t["bg"])
        game_row.grid(row=row, column=0, sticky="ew", pady=(0, 4)); row += 1

        ctk.CTkCheckBox(
            game_row,
            text="Game audio detection (beta)",
            variable=self._game,
            font=("Segoe UI", 10), text_color=t["text"],
            fg_color=t["accent"], hover_color=t["accent_hover"],
            checkmark_color=t["btn_text"],
            border_color=t["border"],
            corner_radius=4, height=20,
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Highlights moments matching a reference sound",
            font=("Segoe UI", 8), fg=t["text_dim"], bg=t["bg"],
        ).grid(row=row, column=0, sticky="w", pady=(0, 20)); row += 1

        # Divider
        tk.Frame(left, bg=t["border"], height=1).grid(
            row=row, column=0, sticky="ew", pady=(0, 20)); row += 1

        # Run button
        self._run_btn = ctk.CTkButton(
            left,
            text="▶  Process Video",
            command=self._run,
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color=t["btn_text"],
            font=("Segoe UI", 12, "bold"),
            height=44, corner_radius=8,
        )
        self._run_btn.grid(row=row, column=0, sticky="ew"); row += 1

        # Progress bar
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ctk.CTkProgressBar(
            left,
            variable=self._progress_var,
            progress_color=t["accent"],
            fg_color=t["border"],
            corner_radius=4, height=6,
        )
        self._progress.grid(row=row, column=0, sticky="ew", pady=(10, 0)); row += 1
        self._progress.grid_remove()   # hidden until processing

        # ── RIGHT PANEL: Log ─────────────────────────────────────────────────
        right = tk.Frame(self, bg=t["bg"], pady=24)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 24))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Log header
        log_hdr = tk.Frame(right, bg=t["bg"])
        log_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        tk.Label(
            log_hdr, text="Activity Log",
            font=("Segoe UI", 11, "bold"),
            fg=t["text"], bg=t["bg"],
        ).pack(side="left")

        ctk.CTkButton(
            log_hdr, text="Clear",
            command=self._clear_log,
            fg_color=t["panel_alt"], hover_color=t["border"],
            text_color=t["text_muted"],
            font=("Segoe UI", 9), height=26, corner_radius=5, width=54,
        ).pack(side="right")

        # Log box
        log_frame = tk.Frame(right, bg=t["panel"],
                             highlightbackground=t["border"],
                             highlightthickness=1)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self._log = tk.Text(
            log_frame,
            font=("Consolas", 9),
            fg=t["text_muted"], bg=t["panel"],
            relief="flat", wrap="word",
            state="disabled",
            padx=14, pady=10,
        )
        self._log.grid(row=0, column=0, sticky="nsew")

        sb = tk.Scrollbar(log_frame, command=self._log.yview,
                          bg=t["panel_alt"], troughcolor=t["panel"])
        sb.grid(row=0, column=1, sticky="ns")
        self._log["yscrollcommand"] = sb.set

        # Tag colours for log levels
        self._log.tag_configure("info",    foreground=t["text_muted"])
        self._log.tag_configure("success", foreground=t["success"])
        self._log.tag_configure("warning", foreground=t["warning"])
        self._log.tag_configure("error",   foreground=t["error"])
        self._log.tag_configure("bold",    font=("Consolas", 9, "bold"))

        self._log_line("Vellum automatic video editor — ready.", "info")
        self._log_line("Select a video file and click Process Video.", "info")

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _section(self, parent, row, text):
        t = self._t
        tk.Label(
            parent, text=text.upper(),
            font=("Segoe UI", 8, "bold"),
            fg=t["text_dim"], bg=t["bg"],
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=(0, 8))

    def _field_label(self, parent, row, text):
        t = self._t
        tk.Label(
            parent, text=text,
            font=("Segoe UI", 10),
            fg=t["text_muted"], bg=t["bg"],
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=(0, 4))

    def _on_thresh(self, val):
        self._thresh_lbl.configure(text=f"{float(val):.3f}")

    def _browse_video(self):
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.webm *.m4v"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._video.set(path)
            self._log_line(f"Selected: {os.path.basename(path)}", "info")
            self._app.set_status(f"Loaded: {os.path.basename(path)}")

    def _browse_outdir(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self._outdir.set(path)

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _log_line(self, text, level="info"):
        """Thread-safe log append."""
        def _write():
            self._log.configure(state="normal")
            self._log.insert("end", text + "\n", level)
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, _write)

    def _set_progress(self, pct):
        def _upd():
            if pct is None:
                return
            self._progress_var.set(pct / 100.0)
        self.after(0, _upd)

    # ─────────────────────────────────────────────────────────────────────────
    # Processing
    # ─────────────────────────────────────────────────────────────────────────
    def _run(self):
        if self._running:
            return

        video = self._video.get().strip()
        if not video:
            messagebox.showwarning("No file", "Please select a video file first.")
            return
        if not os.path.isfile(video):
            messagebox.showerror("File not found", f"Cannot find:\n{video}")
            return

        self._running = True
        self._run_btn.configure(state="disabled", text="Processing…")
        self._progress.grid()
        self._progress_var.set(0)
        self._log_line("─" * 48, "info")
        self._log_line(f"Starting: {os.path.basename(video)}", "bold")
        self._app.set_status("Processing…", "warning")

        # Run in background thread so UI stays responsive
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _worker(self):
        from video_editor import editor_config as cfg
        from video_editor.editor_core import process_video, check_dependencies

        ok, err = check_dependencies()
        if not ok:
            self._log_line(
                f"Missing dependencies:\n  {err}\n\n"
                "Install with:\n  pip install librosa moviepy",
                "error",
            )
            self._finish(success=False)
            return

        def progress_cb(pct, msg):
            self._log_line(msg, "info")
            if pct is not None:
                self._set_progress(pct)
            self.after(0, lambda: self._app.set_status(msg, "info"))

        try:
            paths = process_video(
                video_path       = self._video.get().strip(),
                mode             = self._mode.get(),
                output_folder    = self._outdir.get().strip() or None,
                volume_threshold = self._thresh.get(),
                progress_cb      = progress_cb,
            )
            # also patch game audio setting
            cfg.USE_GAME_AUDIO = self._game.get()

            self._log_line(f"✓ Exported {len(paths)} file(s):", "success")
            for p in paths:
                self._log_line(f"  {p}", "success")
            self._finish(success=True)

        except Exception as exc:
            import traceback
            self._log_line(traceback.format_exc(), "error")
            self._finish(success=False, msg=str(exc))

    def _finish(self, success: bool, msg: str = ""):
        def _ui():
            self._running = False
            self._run_btn.configure(state="normal", text="▶  Process Video")
            self._progress.grid_remove()
            if success:
                self._app.set_status("Done — output saved.", "success")
            else:
                short = (msg[:80] + "…") if len(msg) > 80 else msg
                self._app.set_status(f"Error: {short}", "error")
        self.after(0, _ui)
