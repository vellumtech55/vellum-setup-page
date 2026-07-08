# game_audio.py — optional game-sound highlight detection (beta)
import numpy as np

try:
    import librosa
    from sklearn.metrics.pairwise import cosine_similarity
    _DEPS_OK = True
except ImportError:
    _DEPS_OK = False


def _require_deps():
    if not _DEPS_OK:
        raise ImportError(
            "game_audio requires librosa and scikit-learn.\n"
            "Install with:  pip install librosa scikit-learn"
        )


def extract_features(y, sr):
    _require_deps()
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfcc, axis=1).reshape(1, -1)


def load_reference_sound(path, sr):
    _require_deps()
    y, _ = librosa.load(path, sr=sr)
    return extract_features(y, sr)


def detect_game_events(y, sr, reference_features, threshold=0.85):
    """
    Slide a window over the audio and flag moments whose MFCC fingerprint
    is similar to the reference sound (e.g. a gunshot).
    Returns a list of dicts: {time, type, confidence}
    """
    _require_deps()
    rms   = librosa.feature.rms(y=y)[0]
    times = librosa.frames_to_time(range(len(rms)), sr=sr)

    events = []
    for i, t in enumerate(times):
        if rms[i] <= 0.02:          # skip silence
            continue

        start = int(t * sr)
        end   = start + int(0.2 * sr)
        chunk = y[start:end]
        if len(chunk) < sr * 0.1:
            continue

        sim = cosine_similarity(
            extract_features(chunk, sr), reference_features
        )[0][0]

        if sim >= threshold:
            events.append({"time": t, "type": "game_event", "confidence": float(sim)})

    return events
