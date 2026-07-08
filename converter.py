import subprocess
from pathlib import Path


def auto_rename(path: Path) -> Path:
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def convert_file(input_file, output_folder, fmt, bitrate, sample_rate, channels, overwrite_mode="auto_rename"):
    src = Path(input_file)
    dst = Path(output_folder) / f"{src.stem}.{fmt}"

    if dst.exists():
        if overwrite_mode == "skip":
            return False, "Skipped (file exists)"
        elif overwrite_mode == "auto_rename":
            dst = auto_rename(dst)
        # "overwrite" falls through — ffmpeg -y handles it

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-b:a", f"{bitrate}k",
        "-ar", str(sample_rate),
        "-ac", str(channels),
        str(dst),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, str(dst)
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip().splitlines()[-1] if e.stderr else "ffmpeg error"
