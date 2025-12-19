import os

try:
    # Load from .env if present
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=False)
except Exception:
    # dotenv is optional; skip if not installed
    pass

def get_livekit_url() -> str:
    return os.getenv("LIVEKIT_URL", "wss://assisagtbnt-k43m2kkg.livekit.cloud")

def get_livekit_api_key() -> str:
    return os.getenv("LIVEKIT_API_KEY", "APIflTpySn3dTWk")

def get_livekit_api_secret() -> str:
    return os.getenv("LIVEKIT_API_SECRET", "piHOhghWOerftpTgnoEoLKKXOhCztBvgX1T5YGDCF1y")


def get_gemini_api_key() -> str:
    """Return Gemini API key from env or the provided default."""
    return os.getenv("GEMINI_API_KEY", "AIzaSyDhMe-HN-BzEyP632i14GQa0u3LN-qMFNo")


def get_stt_engine() -> str:
    """Return Speech-to-Text engine preference."""
    return os.getenv("STT_ENGINE", "google")


def get_wake_word_enabled() -> bool:
    """Return whether wake word detection is enabled."""
    return os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"


def get_listening_timeout() -> int:
    """Return listening timeout in seconds."""
    return int(os.getenv("LISTENING_TIMEOUT", "6"))


def get_phrase_time_limit() -> int:
    """Return phrase time limit in seconds."""
    return int(os.getenv("PHRASE_TIME_LIMIT", "8"))


