import numpy as np
import sounddevice as sd
import os

def scary_with_ultrasonic(duration=3.0, sample_rate=192000, click_rate=10, save_path: str | None = None):
    """
    מוסיף גם רכיב על-קולי בתדרים שהעכברים שומעים (אנחנו לא).
    חשוב להשתמש בכרטיס קול שיכול לנגן עד 192kHz!
    """
    t = np.linspace(0, duration, int(sample_rate*duration), endpoint=False)

    # --- תדרים צורמים בתוך טווח השמיעה שלנו ---
    f1, f2, f3 = 15000, 15500, 16000
    tone_audible = (
        0.25 * np.sin(2 * np.pi * f1 * t) +
        0.25 * np.sin(2 * np.pi * f2 * t) +
        0.25 * np.sin(2 * np.pi * f3 * t)
    )

    # --- רכיב על-קולי (עכברים בלבד) ---
    f4, f5 = 25000, 35000  # 25–35 kHz
    tone_ultra = (
        0.25 * np.sin(2 * np.pi * f4 * t) +
        0.25 * np.sin(2 * np.pi * f5 * t)
    )

    # --- רעש לבן ---
    noise = 0.3 * np.random.normal(0, 1, len(t))

    # --- נקישות ---
    click_signal = np.zeros_like(t)
    click_interval = int(sample_rate / click_rate)
    click_len = int(0.002 * sample_rate)  # 2ms
    for i in range(0, len(t), click_interval):
        click_signal[i:i+click_len] = 1.0

    # שילוב הכל
    signal = tone_audible + tone_ultra + noise + click_signal
    signal = signal / np.max(np.abs(signal))

    # השמעה
    sd.play(signal, samplerate=sample_rate)
    sd.wait()

    # שמירה כ-NPZ (בדומה ל-General_functions.generate_white_noise_npz)
    if save_path:
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # נשמור גם במפתחות כפולים לתאימות ('noise','Fs') וגם ('data','rate')
            np.savez(save_path, data=signal, Fs=sample_rate)
        except Exception as e:
            print(f"[save npz] failed to save '{save_path}': {e}")

# שים לב: דורש כרטיס קול ורמקולים/טוויטרים שתומכים ב-192kHz כדי לשמוע עד 40kHz!
scary_with_ultrasonic(2, click_rate=15)

# import numpy as np
# import sounddevice as sd

def scary_with_clicks(duration=3.0, sample_rate=44100, click_rate=10, save_path: str | None = None):
    t = np.linspace(0, duration, int(sample_rate*duration), endpoint=False)

    # --- בסיס: תדרים צורמים ---
    f1, f2, f3 = 15000, 15500, 16000
    tone = (
        0.3 * np.sin(2 * np.pi * f1 * t) +
        0.3 * np.sin(2 * np.pi * f2 * t) +
        0.3 * np.sin(2 * np.pi * f3 * t)
    )

    # --- הוספת רעש לבן ---
    noise = 0.2 * np.random.normal(0, 1, len(t))

    # --- יצירת נקישות ---
    click_signal = np.zeros_like(t)
    click_interval = int(sample_rate / click_rate)  # כל כמה דגימות נקישה
    click_len = int(0.002 * sample_rate)  # נקישה של 2ms
    for i in range(0, len(t), click_interval):
        click_signal[i:i+click_len] = 1.0  # פולס קצר

    # שילוב הכל
    signal = tone + noise + click_signal

    # נרמול
    signal = signal / np.max(np.abs(signal))

    # השמעה
    sd.play(signal, samplerate=sample_rate)
    sd.wait()

    # שמירה כ-NPZ (בדומה ל-General_functions.generate_white_noise_npz)
    if save_path:
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            np.savez(save_path, data=signal, Fs=sample_rate)
        except Exception as e:
            print(f"[save npz] failed to save '{save_path}': {e}")

#scary_with_clicks(duration=2, click_rate=12) 

# import lgpio
# import time
# import serial

# ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600,
#                     timeout=0.01)  # timeout=1  # Change '/dev/ttyS0' to the detected port

# # while True:
# # 
# #     if ser.in_waiting > 0:
# #         try:
# #             mouse_id = ser.readline().decode('utf-8').rstrip()
# #             print(mouse_id)
# #         except Exception as e:
# #             print(f"[IdleState] Error reading RFID: {e}")

# h = lgpio.gpiochip_open(0)
# # PIN = 17
# # lgpio.gpio_claim_output(h, PIN, 0)
# # lgpio.gpio_write(h, PIN, 1)
# # time.sleep(1.000)
# # lgpio.gpio_write(h, PIN, 0)
# # lgpio.gpiochip_close(h)
# valve_pin = 4
# IR_pin = 27

# lgpio.gpio_claim_input(h,IR_pin)
# while True:
#     level = lgpio.gpio_read(h, IR_pin)
#     print(f"Pin level: {level}")
#     time.sleep(1.000)

# # lgpio.gpio_claim_output(h, valve_pin, 0)
# # while True:
# #     lgpio.gpio_write(h, valve_pin, 1)
# #     time.sleep(1.000)
# #     lgpio.gpio_write(h, valve_pin, 0)
# #     time.sleep(1.000)
