"""Tests for the vision subsystem."""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from emiglio.vision.camera import Camera
from emiglio.vision.stream import mjpeg_generator, BOUNDARY


def _make_mock_camera() -> Camera:
    """Create a Camera with a fake JPEG frame preloaded."""
    cam = Camera()
    # Simulate a captured JPEG without opening a real camera
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    import cv2
    _, jpeg = cv2.imencode(".jpg", fake_frame)
    cam._jpeg = jpeg.tobytes()
    return cam


def test_camera_get_jpeg_none_before_start():
    cam = Camera()
    assert cam.get_jpeg() is None


def test_camera_get_jpeg_returns_bytes():
    cam = _make_mock_camera()
    jpeg = cam.get_jpeg()
    assert isinstance(jpeg, bytes)
    assert len(jpeg) > 0
    # JPEG magic bytes
    assert jpeg[:2] == b"\xff\xd8"


async def test_camera_get_jpeg_async():
    cam = _make_mock_camera()
    jpeg = await cam.get_jpeg_async()
    assert isinstance(jpeg, bytes)
    assert jpeg[:2] == b"\xff\xd8"


async def test_mjpeg_generator_yields_frames():
    cam = _make_mock_camera()
    gen = mjpeg_generator(cam)
    frame = await gen.__anext__()
    assert BOUNDARY.encode() in frame
    assert b"Content-Type: image/jpeg" in frame


def test_camera_stop_without_start():
    cam = Camera()
    cam.stop()  # should not raise
