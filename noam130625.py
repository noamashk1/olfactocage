import serial
import time
import RPi.GPIO as GPIO
import threading

from datetime import datetime
import numpy as np
import sounddevice as sd

valve_pin = 5#23
IR_pin = 22#25
lick_pin = 17#24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_pin, GPIO.IN)
GPIO.setup(lick_pin, GPIO.IN)
GPIO.setup(valve_pin, GPIO.OUT)

GPIO.setwarnings(False)

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600,
                    timeout=0.01)  # timeout=1  # Change '/dev/ttyS0' to the detected port

while True:
    GPIO.output(valve_pin, GPIO.HIGH)
    time.sleep(0.02)
    GPIO.output(valve_pin, GPIO.LOW)
    time.sleep(3)
