import serial
import time
import lgpio
import threading
from datetime import datetime
import numpy as np
import sounddevice as sd

# Pin definitions (BCM numbering)
VALVE_PIN = 5
IR_PIN = 22
LICK_PIN = 17

# Open a connection to the GPIO chip
h = lgpio.gpiochip_open(0)  # Usually 0 is the main chip

# Set up pins
lgpio.gpio_claim_input(h, IR_PIN)
lgpio.gpio_claim_input(h, LICK_PIN)
lgpio.gpio_claim_output(h, VALVE_PIN)

# Serial setup
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    timeout=0.01  # Change '/dev/ttyUSB0' to your actual port if needed
)

try:
    while True:
        lgpio.gpio_write(h, VALVE_PIN, 1)
        time.sleep(0.02)
        lgpio.gpio_write(h, VALVE_PIN, 0)
        time.sleep(3)
except KeyboardInterrupt:
    print("Exiting gracefully...")
finally:
    lgpio.gpiochip_close(h)
    ser.close()