"""Emiglio robot entry point. Wires subsystems and starts the web server."""

import os
import sys

# Guard: if the venv Python was created while conda was active, its RPATH
# pulls in conda's outdated libstdc++, breaking system libs like libjack.
# Detect this and warn early, before native imports fail silently.
_python_real = os.path.realpath(sys.executable)
if "miniconda" in _python_real or "anaconda" in _python_real:
    print(
        f"WARNING: This virtualenv uses conda's Python ({_python_real}).\n"
        "Native libraries (audio, etc.) may fail due to conda's bundled libstdc++.\n"
        "Fix: deactivate conda, delete .venv, and run 'uv sync' to recreate it.\n",
        file=sys.stderr,
    )

import logging
import signal

import uvicorn

from emiglio.brain import BrainClient
from emiglio.config import settings
from emiglio.event_bus import EventBus
from emiglio.locomotion.controller import LocomotionController
from emiglio.stt import STTClient
from emiglio.tts import TTSClient
from emiglio.vision.camera import Camera
from emiglio.conversation import ConversationManager
from emiglio.web.server import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("emiglio")

BANNER = r"""
  _____ __  __ ___ ____ _     ___ ___
 | ____|  \/  |_ _/ ___| |   |_ _/ _ \
 |  _| | |\/| || | |  _| |    | | | | |
 | |___| |  | || | |_| | |___ | | |_| |
 |_____|_|  |_|___\____|_____|___\___/
"""


def main() -> None:
    print(BANNER)
    logger.info("Starting Emiglio v0.1.0 (hardware_mode=%s)", settings.hardware_mode)

    # -- Core --
    bus = EventBus()
    locomotion = LocomotionController(bus)

    # -- Camera (optional) --
    camera = Camera()
    camera.start()
    if camera._cap is None:
        logger.warning("Camera unavailable — running without video")

    # -- Audio (optional) --
    audio_capture = None
    audio_playback = None
    try:
        from emiglio.audio.capture import AudioCapture
        from emiglio.audio.playback import AudioPlayback
        audio_capture = AudioCapture()
        audio_playback = AudioPlayback()
        logger.info("Audio subsystem initialized")
    except OSError as e:
        logger.warning("Audio subsystem unavailable: %s", e)

    # -- STT --
    stt = STTClient(mode=settings.stt_mode, model=settings.stt_model)

    # -- TTS --
    tts = TTSClient(
        mode=settings.tts_mode,
        voice_id=settings.tts_voice_id,
        model_id=settings.tts_model_id,
    )

    # -- Brain --
    brain = BrainClient(mode=settings.brain_mode, model=settings.brain_model)

    # -- Conversation --
    conversation = ConversationManager(
        bus=bus,
        camera=camera,
        audio_capture=audio_capture,
        audio_playback=audio_playback,
        brain=brain,
        stt=stt,
        tts=tts,
    )

    # -- Web app --
    app = create_app(bus, locomotion, camera=camera, conversation=conversation)

    # -- Shutdown --
    cleanup_done = False

    def shutdown(sig, frame):
        nonlocal cleanup_done
        if cleanup_done:
            return
        cleanup_done = True
        logger.info("Shutting down...")
        camera.stop()
        locomotion.cleanup()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # -- Startup summary --
    subsystems = []
    subsystems.append("motors (mock)" if settings.hardware_mode == "mock" else "motors (GPIO)")
    subsystems.append("camera" if camera._cap is not None else "camera (off)")
    subsystems.append("audio" if audio_capture else "audio (off)")
    subsystems.append(f"stt ({settings.stt_mode})" if stt.available else "stt (off)")
    subsystems.append(f"tts ({settings.tts_mode})" if tts.available else "tts (off)")
    subsystems.append(f"brain ({settings.brain_mode})" if brain.available else "brain (off)")
    logger.info("Subsystems: %s", ", ".join(subsystems))
    logger.info("Web UI: http://%s:%d", settings.web_host, settings.web_port)

    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
