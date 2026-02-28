"""OpenCV USB camera capture with async frame access."""

import asyncio
import logging
import threading
import time

import cv2
import numpy as np

from emiglio.config import settings

logger = logging.getLogger(__name__)


class Camera:
    """Captures frames from a USB camera in a background thread.

    Frames are grabbed continuously in a dedicated thread so the async
    event loop is never blocked by camera I/O.  Consumers call
    ``get_frame()`` to get the latest JPEG-encoded frame.
    """

    def __init__(self) -> None:
        self._cap: cv2.VideoCapture | None = None
        self._frame: np.ndarray | None = None
        self._jpeg: bytes | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._cap = cv2.VideoCapture(settings.camera_index)
        if not self._cap.isOpened():
            logger.error("Failed to open camera %d", settings.camera_index)
            self._cap = None
            return
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(
            "Camera started (index=%d, %dx%d)",
            settings.camera_index,
            settings.camera_width,
            settings.camera_height,
        )

    def _capture_loop(self) -> None:
        while self._running and self._cap is not None:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            with self._lock:
                self._frame = frame
                self._jpeg = jpeg.tobytes()

    def get_jpeg(self) -> bytes | None:
        """Return the latest JPEG-encoded frame, or None if no frame yet."""
        with self._lock:
            return self._jpeg

    async def get_jpeg_async(self) -> bytes | None:
        """Async wrapper — runs the lock acquisition in a thread executor."""
        return await asyncio.to_thread(self.get_jpeg)

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("Camera stopped")
