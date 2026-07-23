# editor_config.py — settings for the AI Video Editor

OUTPUT_MODE   = "single"   # "single" or "multiple"
OUTPUT_FOLDER = "videos"

VOLUME_THRESHOLD      = 0.03
MIN_CLIP_LENGTH       = 1.0

SPEECH_PADDING_START  = 0.25   # seconds before speech onset
SPEECH_PADDING_END    = 0.35   # seconds after speech ends

SILENCE_THRESHOLD_MULT = 0.5
MIN_SILENCE_DURATION   = 0.3   # seconds of silence to split a sentence

USE_GAME_AUDIO = False          # beta: game-sound highlight detection
