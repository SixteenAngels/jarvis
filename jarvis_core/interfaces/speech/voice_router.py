from __future__ import annotations

from .stt import transcribe
from .tts import synthesize


def handle_session(audio_in_path: str, reply_text: str) -> bytes:
    _ = transcribe(audio_in_path)
    return synthesize(reply_text)
