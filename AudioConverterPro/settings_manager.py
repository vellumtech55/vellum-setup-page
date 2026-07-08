import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

DEFAULTS = {
    "output_format": "mp3",
    "bitrate": "320",
    "sample_rate": "44100",
    "channels": "2",
    "overwrite_mode": "auto_rename",
}


def load_settings() -> dict:
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text())}
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULTS.copy()


def save_settings(settings: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(settings, indent=4))
