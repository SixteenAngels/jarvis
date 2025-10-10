from __future__ import annotations

"""Voice Router

Provides a thin orchestration layer for speech interactions:
- Transcribe incoming audio (STT)
- Generate spoken reply (TTS)

This module centralizes voice session hooks so the app can swap STT/TTS
providers via features.yaml and environment variables without changing
business logic.
"""

from typing import Dict, Any
from .stt import transcribe
from .tts import synthesize
from ...utils.logging import get_logger


def handle_session(audio_in_path: str, reply_text: str, voice: str | None = None, context: Dict[str, Any] | None = None) -> bytes:
    """Process a single voice interaction.

    Args:
        audio_in_path: Path to the recorded user audio.
        reply_text: Text to synthesize in response.
        voice: Optional voice id/name for provider selection.
        context: Optional dict to thread additional metadata.

    Returns:
        Audio bytes of synthesized reply.
    """
    logger = get_logger("voice_router")
    try:
        user_text = transcribe(audio_in_path)
        logger.info(f"stt_text_len={len(user_text)}")
    except Exception:
        logger.warning("stt_failed")
    # Synthesize reply
    try:
        return synthesize(reply_text, voice=voice)
    except Exception:
        logger.warning("tts_failed")
        return b""
