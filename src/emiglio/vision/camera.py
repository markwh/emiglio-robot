"""OpenCV USB camera capture with async frame access."""

import asyncio
import glob as globmod
import logging
import threading
import time
from pathlib import Path

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
        self._index: int = settings.camera_index

    @staticmethod
    def list_devices() -> list[dict]:
        """Enumerate available V4L2 video devices.

        Returns a list of dicts: [{"index": 0, "name": "Integrated Webcam"}, ...]
        Only includes devices that OpenCV can actually open (filters out
        metadata-only /dev/video nodes).
        """
        devices = []
        for path in sorted(globmod.glob("/dev/video*")):
            try:
                index = int(path.replace("/dev/video", ""))
            except ValueError:
                continue

            # Read device name from udev or sysfs
            name = f"Video device {index}"
            sysfs_name = Path(f"/sys/class/video4linux/video{index}/name")
            if sysfs_name.exists():
                try:
                    name = sysfs_name.read_text().strip()
                except OSError:
                    pass

            # Probe whether OpenCV can open this device (skip metadata nodes)
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                cap.release()
                devices.append({"index": index, "name": name})
            else:
                cap.release()

        return devices

    @property
    def active_index(self) -> int:
        """Return the currently active camera index."""
        return self._index

    def start(self, index: int | None = None) -> None:
        if self._running:
            return
        if index is not None:
            self._index = index
        self._cap = cv2.VideoCapture(self._index)
        if not self._cap.isOpened():
            logger.error("Failed to open camera %d", self._index)
            self._cap = None
            return
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(
            "Camera started (index=%d, %dx%d)",
            self._index,
            settings.camera_width,
            settings.camera_height,
        )

    def switch(self, index: int) -> None:
        """Hot-switch to a different camera device."""
        logger.info("Switching camera from %d to %d", self._index, index)
        self.stop()
        self._jpeg = None
        self.start(index)

    def _capture_loop(self) -> None:
        consecutive_failures = 0
        while self._running and self._cap is not None:
            ok, frame = self._cap.read()
            if not ok:
                consecutive_failures += 1
                if consecutive_failures > 50:
                    logger.warning("Camera: %d consecutive read failures, retrying open...", consecutive_failures)
                    self._cap.release()
                    time.sleep(1.0)
                    self._cap = cv2.VideoCapture(self._index)
                    consecutive_failures = 0
                else:
                    time.sleep(0.01)
                continue
            consecutive_failures = 0
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
