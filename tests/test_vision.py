"""Tests for the vision subsystem."""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from emiglio.config import settings
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


def test_camera_list_devices_returns_list():
    devices = Camera.list_devices()
    assert isinstance(devices, list)
    for dev in devices:
        assert "index" in dev
        assert "name" in dev
        assert isinstance(dev["index"], int)
        assert isinstance(dev["name"], str)


def test_camera_active_index_default():
    cam = Camera()
    assert cam.active_index == settings.camera_index


@patch("emiglio.vision.camera.cv2.VideoCapture")
def test_camera_switch_stop_start_cycle(mock_vc):
    """switch() should stop the old capture and start a new one."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_vc.return_value = mock_cap

    cam = Camera()
    cam.start(0)
    assert cam._running

    cam.switch(4)
    assert cam._index == 4
    assert cam._running
    # Should have created captures for both index 0 and 4
    assert mock_vc.call_count >= 2
    cam.stop()
