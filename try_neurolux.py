import lgpio
import time

PIN = 21  # GPIO BCM

# פותח חיבור ל-LGPIO daemon
chip = lgpio.gpiochip_open(0)  # בדרך כלל chip 0 הוא הראשי

try:
    # מגדיר את הפין כ-output
    lgpio.gpio_claim_output(chip, PIN)

    while True:
        lgpio.gpio_write(chip, PIN, 1)  # HIGH
        time.sleep(1)
        print("on")
        lgpio.gpio_write(chip, PIN, 0)  # LOW
        time.sleep(1)

finally:
    # שחרור משאבים
    lgpio.gpio_release(chip, PIN)
    lgpio.gpiochip_close(chip)
