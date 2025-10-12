"""
Example: Voice pipeline demo using STT (Whisper if available) and TTS (gTTS/ElevenLabs/Azure fallbacks).

Usage:
  python examples/voice_demo.py --audio /path/to/audio.wav --reply "Hello there!"
"""
from __future__ import annotations

import argparse
from jarvis_core.interfaces.speech.stt import transcribe
from jarvis_core.interfaces.speech.tts import synthesize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--reply", default="This is Jarvis Core speaking.")
    args = parser.parse_args()

    text = transcribe(args.audio)
    print({"transcription": text})
    audio_bytes = synthesize(args.reply)
    out = "reply.mp3"
    with open(out, "wb") as f:
        f.write(audio_bytes)
    print({"tts_output": out})


if __name__ == "__main__":
    main()
