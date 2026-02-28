"""Quick audio test. Records from mic, plays it back.

Usage:
    uv run python scripts/audio_test.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emiglio.audio.capture import AudioCapture
from emiglio.audio.playback import AudioPlayback


async def main():
    capture = AudioCapture()
    playback = AudioPlayback()

    print("Recording 3 seconds...")
    wav_bytes = await capture.record_seconds(3.0)
    print(f"Recorded {len(wav_bytes)} bytes")

    print("Playing back...")
    await playback.play_wav(wav_bytes)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
