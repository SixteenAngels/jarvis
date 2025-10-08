from __future__ import annotations

"""Text-to-Speech with provider fallbacks based on features.yaml.

If ElevenLabs or Azure is configured (via env/keys), call those; otherwise
fall back to gTTS or a placeholder.
"""

from ...utils.config import load_yaml


def synthesize(text: str, voice: str | None = None) -> bytes:
    feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    # TODO: check env vars for ElevenLabs/Azure keys and call providers
    try:
        if feats.get("whisper"):  # reusing flag area; add specific flags if needed
            from gtts import gTTS  # type: ignore

            tts = gTTS(text)
            import io

            buf = io.BytesIO()
            tts.write_to_fp(buf)
            return buf.getvalue()
    except Exception:
        pass
    return b"audio-bytes-placeholder"
