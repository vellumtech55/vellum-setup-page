from pathlib import Path

SUPPORTED = {
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".aiff",
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv", ".m4v",
}


def is_supported(path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED
