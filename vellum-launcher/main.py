"""
Vellum App Launcher — entry point.

Run:      python main.py
Requires: Python 3.8+ with tkinter
          (built in on Windows/macOS; on Linux: sudo apt install python3-tk)
"""

from launcher.app import Launcher

if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
