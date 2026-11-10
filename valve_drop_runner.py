import argparse
import time
import lgpio

# import RPi.GPIO as GPIO
#import lgpio


# Match finite_state_machine.py
VALVE_PIN = 4

# Match default in parameters_GUI.py (time_open_valve_entry.insert(0, "0.015"))
DEFAULT_OPEN_VALVE_DURATION_SEC = 0.015
DEFAULT_DROPS = 100
DEFAULT_INTER_DROP_DELAY_SEC = 0.12


def release_drops(
    drops: int,
    open_valve_duration_sec: float,
    inter_drop_delay_sec: float,
) -> None:
    if drops <= 0:
        raise ValueError("drops must be > 0")
    if open_valve_duration_sec <= 0:
        raise ValueError("open_valve_duration_sec must be > 0")
    if inter_drop_delay_sec < 0:
        raise ValueError("inter_drop_delay_sec must be >= 0")

    # GPIO.setwarnings(False)
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(VALVE_PIN, GPIO.OUT)
    # GPIO.output(VALVE_PIN, GPIO.LOW)
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(h, VALVE_PIN, 0)

    print(
        f"Starting valve run: drops={drops}, "
        f"open={open_valve_duration_sec:.4f}s, "
        f"gap={inter_drop_delay_sec:.4f}s, pin={VALVE_PIN}"
    )

    try:
        for i in range(1, drops + 1):
            # GPIO.output(VALVE_PIN, GPIO.HIGH)
            lgpio.gpio_write(h, VALVE_PIN, 1)
            time.sleep(open_valve_duration_sec)
            # GPIO.output(VALVE_PIN, GPIO.LOW)
            lgpio.gpio_write(h, VALVE_PIN, 0)

            if i < drops and inter_drop_delay_sec > 0:
                time.sleep(inter_drop_delay_sec)

            if i % 10 == 0 or i == drops:
                print(f"Released {i}/{drops} drops")
    finally:
        # GPIO.output(VALVE_PIN, GPIO.LOW)
        # GPIO.cleanup(VALVE_PIN)
        lgpio.gpio_write(h, VALVE_PIN, 0)
        lgpio.gpio_free(h, VALVE_PIN)
        lgpio.gpiochip_close(h)
        print("Done. Valve pin cleaned up.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Release a selected number of drops by opening/closing the valve. "
            "Default open time matches parameters_GUI.py."
        )
    )
    parser.add_argument(
        "--drops",
        type=int,
        default=DEFAULT_DROPS,
        help=f"Number of drops to release (default: {DEFAULT_DROPS})",
    )
    parser.add_argument(
        "--open-valve-duration",
        type=float,
        default=DEFAULT_OPEN_VALVE_DURATION_SEC,
        help=(
            "Valve open time in seconds per drop "
            f"(default: {DEFAULT_OPEN_VALVE_DURATION_SEC})"
        ),
    )
    parser.add_argument(
        "--inter-drop-delay",
        type=float,
        default=DEFAULT_INTER_DROP_DELAY_SEC,
        help=(
            "Delay between drops in seconds (default: "
            f"{DEFAULT_INTER_DROP_DELAY_SEC})"
        ),
    )
    args = parser.parse_args()

    release_drops(
        drops=args.drops,
        open_valve_duration_sec=args.open_valve_duration,
        inter_drop_delay_sec=args.inter_drop_delay,
    )


if __name__ == "__main__":
    main()
