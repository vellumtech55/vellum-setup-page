# editor_core.py — AI Video Editor core processing
# Detects speech segments, removes silence, and exports clean clips.

import os
import numpy as np

try:
    import librosa
    from moviepy import VideoFileClip, concatenate_videoclips
    _DEPS_OK = True
    _DEPS_ERROR = None
except ImportError as e:
    _DEPS_OK = False
    _DEPS_ERROR = str(e)

from . import editor_config as config
from .game_audio import load_reference_sound, detect_game_events


def check_dependencies():
    """Return (ok: bool, error_msg: str | None)."""
    return _DEPS_OK, _DEPS_ERROR


# ══════════════════════════════════════════════════════════════════════════════
# Audio helpers
# ══════════════════════════════════════════════════════════════════════════════

def extract_audio(video_path, out_path="temp_audio.wav"):
    video = VideoFileClip(video_path)
    if video.audio is None:
        raise ValueError("Video has no audio track.")
    video.audio.write_audiofile(out_path, logger=None)
    video.close()
    return out_path


def load_audio(audio_path, sr=22050):
    y, sr = librosa.load(audio_path, sr=sr)
    return y, sr


# ══════════════════════════════════════════════════════════════════════════════
# Speech detection
# ══════════════════════════════════════════════════════════════════════════════

def detect_sentences(y, sr):
    """Group continuous speech into (start, end) segments."""
    rms        = librosa.feature.rms(y=y)[0]
    times      = librosa.frames_to_time(range(len(rms)), sr=sr)
    frame_time = float(times[1] - times[0]) if len(times) > 1 else 0.01
    sil_thresh = config.VOLUME_THRESHOLD * config.SILENCE_THRESHOLD_MULT

    sentences    = []
    start        = None
    silence_time = 0.0

    for t, energy in zip(times, rms):
        if energy > sil_thresh:
            silence_time = 0.0
            if start is None:
                start = t
        else:
            silence_time += frame_time
            if start is not None and silence_time >= config.MIN_SILENCE_DURATION:
                s = max(0.0, float(start) - config.SPEECH_PADDING_START)
                e = float(t) + config.SPEECH_PADDING_END
                sentences.append((s, e))
                start = None

    # flush trailing sentence
    if start is not None:
        s = max(0.0, float(start) - config.SPEECH_PADDING_START)
        e = float(times[-1]) + config.SPEECH_PADDING_END
        sentences.append((s, e))

    return sentences


def score_sentences(y, sr, sentences):
    rms   = librosa.feature.rms(y=y)[0]
    times = librosa.frames_to_time(range(len(rms)), sr=sr)

    scored = []
    for start, end in sentences:
        energies   = [rms[i] for i, t in enumerate(times) if start <= t <= end]
        avg_vol    = float(np.mean(energies)) if energies else 0.0
        duration   = end - start
        scored.append({
            "start":      start,
            "end":        end,
            "avg_volume": avg_vol,
            "duration":   duration,
            "keep": (avg_vol >= config.VOLUME_THRESHOLD
                     and duration >= config.MIN_CLIP_LENGTH),
        })
    return scored


def decide_cuts(scored):
    return [{"start": s["start"], "end": s["end"]}
            for s in scored if s["keep"]]


# ══════════════════════════════════════════════════════════════════════════════
# Game-audio helpers
# ══════════════════════════════════════════════════════════════════════════════

def build_cuts_from_events(events, padding=0.4):
    return [
        {"start": max(0, e["time"] - padding),
         "end":   e["time"] + padding,
         "reason": e["type"]}
        for e in events
    ]


def merge_overlapping_cuts(cuts):
    if not cuts:
        return []
    cuts   = sorted(cuts, key=lambda c: c["start"])
    merged = [dict(cuts[0])]
    for c in cuts[1:]:
        if c["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], c["end"])
        else:
            merged.append(dict(c))
    return merged


# ══════════════════════════════════════════════════════════════════════════════
# Export
# ══════════════════════════════════════════════════════════════════════════════

def apply_cuts(video_path, cuts):
    video = VideoFileClip(video_path)
    clips = []
    for cut in cuts:
        s = max(0.0, float(cut["start"]))
        e = min(float(video.duration), float(cut["end"]))
        if e > s:
            clips.append(video.subclipped(s, e))
    return clips


def export_video(clips, mode="single", output_folder=None, progress_cb=None):
    """
    Export clips to disk.
    progress_cb(pct: float, msg: str) is called periodically if provided.
    """
    if not clips:
        raise ValueError("No clips to export — nothing met the threshold.")

    folder = output_folder or os.getcwd()
    os.makedirs(folder, exist_ok=True)

    def _log(msg):
        if progress_cb:
            progress_cb(None, msg)

    if mode == "single":
        out = os.path.join(folder, "output_final.mp4")
        _log(f"Joining {len(clips)} clip(s)…")
        final = concatenate_videoclips(clips)
        final.write_videofile(out, codec="libx264", logger=None)
        _log(f"Saved → {out}")
        return [out]
    else:
        paths = []
        for i, clip in enumerate(clips):
            out = os.path.join(folder, f"output_clip_{i+1:03d}.mp4")
            _log(f"Exporting clip {i+1}/{len(clips)}…")
            clip.write_videofile(out, codec="libx264", logger=None)
            paths.append(out)
        _log(f"Saved {len(paths)} clips → {folder}")
        return paths


# ══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def process_video(
    video_path,
    mode             = None,
    output_folder    = None,
    volume_threshold = None,
    progress_cb      = None,
):
    """
    Full pipeline:  extract → detect speech → (game audio) → merge → export.

    progress_cb(pct: float | None, msg: str) — optional callback for UI updates.
    Returns list of output file paths.
    """
    if not _DEPS_OK:
        raise ImportError(
            f"Required libraries missing: {_DEPS_ERROR}\n\n"
            "Install with:\n  pip install librosa moviepy"
        )

    def log(pct, msg):
        if progress_cb:
            progress_cb(pct, msg)
        else:
            print(f"[{int(pct or 0):3d}%] {msg}")

    # apply overrides
    if mode             is not None: config.OUTPUT_MODE      = mode
    if output_folder    is not None: config.OUTPUT_FOLDER    = output_folder
    if volume_threshold is not None: config.VOLUME_THRESHOLD = volume_threshold

    log(5,  "Extracting audio…")
    audio_path = extract_audio(video_path)

    log(15, "Loading audio…")
    y, sr = load_audio(audio_path)

    log(25, "Detecting speech segments…")
    sentences  = detect_sentences(y, sr)
    scored     = score_sentences(y, sr, sentences)
    speech_cuts = decide_cuts(scored)

    log(45, f"Found {len(speech_cuts)} speech segment(s).")

    # ── Game audio (optional) ────────────────────────────────────────────────
    all_cuts = list(speech_cuts)

    if config.USE_GAME_AUDIO:
        ref_path = config.GAME_AUDIO_REFERENCE if hasattr(config, "GAME_AUDIO_REFERENCE") else None
        if ref_path and os.path.exists(ref_path):
            log(50, "Scanning for game events…")
            ref_features = load_reference_sound(ref_path, sr)
            events       = detect_game_events(y, sr, ref_features)
            game_cuts    = build_cuts_from_events(events)
            all_cuts.extend(game_cuts)
            log(60, f"Found {len(events)} game event(s).")
        else:
            log(60, "Game audio enabled but no reference file set — skipping.")

    log(65, "Merging overlapping cuts…")
    all_cuts = merge_overlapping_cuts(all_cuts)

    log(70, f"Applying {len(all_cuts)} cut(s) to video…")
    clips = apply_cuts(video_path, all_cuts)

    log(80, "Exporting…")
    paths = export_video(
        clips,
        mode          = config.OUTPUT_MODE,
        output_folder = config.OUTPUT_FOLDER,
        progress_cb   = lambda _, m: log(90, m),
    )

    # clean up temp audio
    try:
        os.remove(audio_path)
    except OSError:
        pass

    log(100, "Done!")
    return paths
