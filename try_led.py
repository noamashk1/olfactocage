import lgpio
import time
import serial

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600,
                    timeout=0.01)  # timeout=1  # Change '/dev/ttyS0' to the detected port

# while True:
# 
#     if ser.in_waiting > 0:
#         try:
#             mouse_id = ser.readline().decode('utf-8').rstrip()
#             print(mouse_id)
#         except Exception as e:
#             print(f"[IdleState] Error reading RFID: {e}")

h = lgpio.gpiochip_open(0)
# PIN = 17
# lgpio.gpio_claim_output(h, PIN, 0)
# lgpio.gpio_write(h, PIN, 1)
# time.sleep(1.000)
# lgpio.gpio_write(h, PIN, 0)
# lgpio.gpiochip_close(h)
valve_pin = 4
IR_pin = 27

lgpio.gpio_claim_input(h,IR_pin)
while True:
    level = lgpio.gpio_read(h, IR_pin)
    print(f"Pin level: {level}")
    time.sleep(1.000)

# lgpio.gpio_claim_output(h, valve_pin, 0)
# while True:
#     lgpio.gpio_write(h, valve_pin, 1)
#     time.sleep(1.000)
#     lgpio.gpio_write(h, valve_pin, 0)
#     time.sleep(1.000)
