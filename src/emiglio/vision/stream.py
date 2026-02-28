"""MJPEG streaming endpoint for the camera feed."""

import asyncio
import logging

from starlette.responses import StreamingResponse

from emiglio.vision.camera import Camera

logger = logging.getLogger(__name__)

BOUNDARY = "emiglioframe"
FRAME_INTERVAL = 1 / 15  # ~15 FPS cap for the stream


async def mjpeg_generator(camera: Camera):
    """Yields multipart MJPEG frames for streaming response."""
    while True:
        jpeg = await camera.get_jpeg_async()
        if jpeg is not None:
            yield (
                b"--" + BOUNDARY.encode() + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n"
                b"\r\n" + jpeg + b"\r\n"
            )
        await asyncio.sleep(FRAME_INTERVAL)


def stream_response(camera: Camera) -> StreamingResponse:
    """Create an MJPEG StreamingResponse for a camera."""
    return StreamingResponse(
        mjpeg_generator(camera),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
    )
