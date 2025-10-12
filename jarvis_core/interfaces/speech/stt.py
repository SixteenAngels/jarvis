from __future__ import annotations

"""Speech-to-Text interface with feature-flagged backends.

Attempts to use OpenAI Whisper (local) if the `features.whisper` flag is set
in configs/features.yaml and the dependency is installed. Falls back to a
placeholder transcription otherwise.
"""

from ..utils import typing as _typing  # noqa: F401  # placeholder to appease linters if needed
from ...utils.config import load_yaml
from ...utils.logging import get_logger


def _whisper_available() -> bool:
    try:
        import whisper  # type: ignore
        _ = whisper
        return True
    except Exception:
        return False


def transcribe(audio_path: str) -> str:
    """Transcribe an audio file to text.

    Args:
        audio_path: Path to an audio file.

    Returns:
        A best-effort transcription string.
    """
    feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    logger = get_logger("stt")
    if feats.get("whisper") and _whisper_available():
        try:
            import whisper  # type: ignore

            model = whisper.load_model("base")
            out = model.transcribe(audio_path)
            return out.get("text", "").strip() or ""
        except Exception:
            logger.warning("whisper_transcribe_failed")
    elif feats.get("whisper"):
        logger.info("whisper_enabled_but_not_installed")
    if feats.get("stt_deepgram"):
        # TODO: integrate Deepgram SDK via env keys
        logger.info("deepgram_enabled_but_not_implemented")
    return "[stt] transcription placeholder"
