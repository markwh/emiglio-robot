"""Quick camera test. Opens webcam, shows a frame, saves a snapshot.

Usage:
    uv run python scripts/camera_test.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import cv2


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera 0")
        sys.exit(1)

    print("Camera opened. Capturing frame...")
    ok, frame = cap.read()
    if not ok:
        print("ERROR: Failed to read frame")
        cap.release()
        sys.exit(1)

    h, w = frame.shape[:2]
    print(f"Frame captured: {w}x{h}")

    out_path = "camera_test_snapshot.jpg"
    cv2.imwrite(out_path, frame)
    print(f"Snapshot saved to {out_path}")

    cap.release()
    print("Done.")


if __name__ == "__main__":
    main()
