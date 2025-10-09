from __future__ import annotations

"""Text-to-Speech with provider fallbacks based on features.yaml.

If ElevenLabs or Azure is configured (via env/keys), call those; otherwise
fall back to gTTS or a placeholder.
"""

import os
from ...utils.config import load_yaml


def synthesize(text: str, voice: str | None = None) -> bytes:
    feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    # ElevenLabs
    if feats.get("tts_elevenlabs") and os.getenv("ELEVENLABS_API_KEY"):
        try:
            from elevenlabs import ElevenLabs  # type: ignore

            client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
            audio = client.generate(text=text, voice=voice or "Rachel", model="eleven_monolingual_v1")
            return b"".join(audio) if isinstance(audio, list) else audio
        except Exception:
            pass
    # Azure TTS (placeholder; requires azure-cognitiveservices-speech setup)
    if feats.get("tts_azure") and os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION"):
        try:
            import azure.cognitiveservices.speech as speechsdk  # type: ignore

            speech_config = speechsdk.SpeechConfig(subscription=os.getenv("AZURE_SPEECH_KEY"), region=os.getenv("AZURE_SPEECH_REGION"))
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            result = synthesizer.speak_text_async(text).get()
            # SDK writes to device; without a file sink we return placeholder
        except Exception:
            pass
    # gTTS fallback
    try:
        from gtts import gTTS  # type: ignore
        import io

        tts = gTTS(text)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return b"audio-bytes-placeholder"
