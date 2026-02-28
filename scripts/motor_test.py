"""Standalone motor test script. Run on Pi with motors connected.

Usage:
    EMIGLIO_HARDWARE_MODE=real uv run python scripts/motor_test.py
    # or in mock mode (default):
    uv run python scripts/motor_test.py
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emiglio.locomotion.driver import MotorDriver


def main():
    driver = MotorDriver()
    tests = [
        ("Forward", 0.5, 0.5),
        ("Backward", -0.5, -0.5),
        ("Turn left", -0.5, 0.5),
        ("Turn right", 0.5, -0.5),
        ("Left only", 0.5, 0),
        ("Right only", 0, 0.5),
        ("Full speed", 1.0, 1.0),
    ]

    try:
        for name, left, right in tests:
            print(f"\n--- {name}: L={left}, R={right} ---")
            driver.set_motors(left, right)
            time.sleep(1.5)
            driver.stop()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nInterrupted!")
    finally:
        driver.cleanup()
        print("Done.")


if __name__ == "__main__":
    main()
