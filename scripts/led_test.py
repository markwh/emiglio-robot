"""Standalone LED test script. Run on Pi with LEDs connected.

Usage:
    EMIGLIO_HARDWARE_MODE=real uv run python scripts/led_test.py
    # or in mock mode (default):
    uv run python scripts/led_test.py
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emiglio.config import settings

# GPIO pins per connectors.md (JST-XH 6-pin LED harness)
LED_PINS = {
    "right_eye":    24,
    "left_eye":     25,
    "right_panel":   5,
    "left_panel":    6,
}


def main():
    mock = settings.hardware_mode == "mock"

    if mock:
        print("Running in MOCK mode (no real GPIO). Set EMIGLIO_HARDWARE_MODE=real on Pi.")
        leds = {name: None for name in LED_PINS}
    else:
        from gpiozero import LED
        leds = {name: LED(pin) for name, pin in LED_PINS.items()}

    def on(name):
        print(f"  ON:  {name}")
        if not mock:
            leds[name].on()

    def off(name):
        print(f"  OFF: {name}")
        if not mock:
            leds[name].off()

    def all_off():
        for name in leds:
            if not mock:
                leds[name].off()

    try:
        # 1. Each LED on individually
        print("\n--- Individual LED test ---")
        for name in LED_PINS:
            on(name)
            time.sleep(1.0)
            off(name)
            time.sleep(0.3)

        # 2. All on together
        print("\n--- All LEDs on ---")
        for name in LED_PINS:
            on(name)
        time.sleep(2.0)
        all_off()
        time.sleep(0.5)

        # 3. Chase pattern (left eye → right eye → left panel → right panel, repeat 3x)
        print("\n--- Chase pattern (3x) ---")
        chase_order = ["left_eye", "right_eye", "left_panel", "right_panel"]
        for _ in range(3):
            for name in chase_order:
                on(name)
                time.sleep(0.2)
                off(name)
        time.sleep(0.3)

        # 4. Blink all 3x
        print("\n--- Blink all (3x) ---")
        for _ in range(3):
            for name in LED_PINS:
                if not mock:
                    leds[name].on()
            print("  ALL ON")
            time.sleep(0.4)
            all_off()
            print("  ALL OFF")
            time.sleep(0.4)

    except KeyboardInterrupt:
        print("\nInterrupted!")
    finally:
        all_off()
        if not mock:
            for led in leds.values():
                led.close()
        print("Done.")


if __name__ == "__main__":
    main()
