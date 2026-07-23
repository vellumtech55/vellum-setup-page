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

    Performance note: this used to call librosa.feature.mfcc() once per
    RMS frame (tens of thousands of calls on a long video). MFCC extraction
    is computed once over the *entire* track here instead, then compared
    against the reference in a single vectorized cosine_similarity call.
    Same detections, orders of magnitude fewer librosa/sklearn calls.
    """
    _require_deps()
    rms   = librosa.feature.rms(y=y)[0]
    times = librosa.frames_to_time(range(len(rms)), sr=sr)

    # One MFCC pass over the whole signal, frame-aligned with rms/times
    # (librosa.feature.rms and librosa.feature.mfcc share the default
    # hop_length, so frame i in mfcc lines up with frame i in rms/times).
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)   # shape (13, n_frames)
    n = min(len(times), mfcc.shape[1])
    frame_features = mfcc[:, :n].T                        # shape (n_frames, 13)

    # One similarity call for every frame at once instead of one per frame
    sims = cosine_similarity(frame_features, reference_features).ravel()

    events = []
    for i in range(n):
        if rms[i] <= 0.02:          # skip silence
            continue
        if sims[i] >= threshold:
            events.append({"time": float(times[i]), "type": "game_event",
                            "confidence": float(sims[i])})

    return events
