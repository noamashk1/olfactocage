
import serial
import time
import lgpio
import threading
from trial import Trial
from datetime import datetime
import numpy as np
import sounddevice as sd
import shutil
import os
import psutil
import glob

from General_functions import send_email

# Max time to wait for IR to go LOW (mouse left) after trial; then email + skip logic
IR_EXIT_WAIT_MAX_SEC = 1 * 60
IR_PROBLEM_REMINDER_SEC = 3 * 60 * 60

audio_lock = threading.Lock()
valve_pin = 4#23
IR_pin = 27#25
lick_pin = 17#24
exit_odor_valve_pin = 12
h = lgpio.gpiochip_open(0)
# Claim basic input/output pins once
lgpio.gpio_claim_input(h, IR_pin)
lgpio.gpio_claim_input(h, lick_pin)
lgpio.gpio_claim_output(h, valve_pin, 0)
lgpio.gpio_claim_output(h, exit_odor_valve_pin, 0)

ports = glob.glob('/dev/ttyUSB*')
if not ports:
    raise Exception("No USB serial device found!")

port = ports[0] 
ser = serial.Serial(port=port, baudrate=9600, timeout=0.01)
print(f"Connected to {port}")


# ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600,
#                     timeout=0.01)  # timeo1  # Change '/dev/ttyS0' to the detected port
LOG_FILE = "debug_log.txt"
process = psutil.Process(os.getpid())

def log_message(message: str):
    """Write message to log file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_memory_usage(tag=""):
    """Log current memory usage in MB."""
    mem = process.memory_info().rss / (1024 * 1024)  # in MB
    log_message(f"[MEM] {tag} Memory usage: {mem:.2f} MB")

class State:
    def __init__(self, name, fsm):
        self.name = name
        self.fsm = fsm
        if self.fsm.exp.live_w.activate_window:
            self.fsm.exp.live_w.deactivate_states_indicators(name)

    def on_event(self, event):
        pass


class IdleState(State):
    def __init__(self, fsm):
        super().__init__("Idle", fsm)
        ser.flushInput()  # clear the data from the serial
        self.fsm.current_trial.clear_trial()
        if self.fsm.exp.live_w.activate_window:
            self.fsm.exp.live_w.update_last_rfid('')
            self.fsm.exp.live_w.update_level('')
            self.fsm.exp.live_w.update_score('')
            self.fsm.exp.live_w.update_trial_value('')
            self.fsm.exp.live_w.update_stimulus('')

        log_memory_usage("Enter Idle")

        threading.Thread(target=self.wait_for_event, daemon=True).start()
        
    def wait_for_event(self):
        minutes_passed = 0
        last_log_time = time.time()

        while True:
            if self.fsm.skip_ir_exit and lgpio.gpio_read(h, IR_pin) == 0:
                self.fsm.on_ir_exit_recovered()
            elif self.fsm.skip_ir_exit:
                self.fsm.maybe_send_ir_problem_reminder()

            if time.time() - last_log_time > 60:
                minutes_passed += 1
                last_log_time = time.time()
                print(f"[IdleState] Waiting for RFID... {minutes_passed} minutes passed")

                if minutes_passed % 5 == 0: 
                    try:
                        self.fsm.exp.upload_data()

                    except PermissionError:
                        print("PermissionError")
                    except FileNotFoundError:
                        print("FileNotFoundError")
                    except Exception as e:
                        print(f"Exception: {e}")
                 
                if minutes_passed % 5 == 0:
                    log_memory_usage("IdleState periodic check")

            if ser.in_waiting > 0 and not self.fsm.exp.live_w.pause:
                try:
                    mouse_id = ser.readline().decode('utf-8').rstrip()
                except Exception as e:
                    print(f"[IdleState] Error reading RFID: {e}")
                    continue

                if self.recognize_mouse(mouse_id):
                    self.fsm.current_trial.update_current_mouse(self.fsm.exp.mice_dict[mouse_id])
                    print("\nmouse: " + self.fsm.exp.mice_dict[mouse_id].get_id())
                    print("Level: " + self.fsm.exp.mice_dict[mouse_id].get_level())
                    if self.fsm.exp.live_w.activate_window:
                        self.fsm.exp.live_w.update_last_rfid(mouse_id)
                        self.fsm.exp.live_w.update_level(self.fsm.exp.mice_dict[mouse_id].get_level())
                    self.on_event('in_port')
                    break  
            else:
                #ser.flushInput()
                time.sleep(0.05)

    def on_event(self, event):
        if event == 'in_port':
            print("Transitioning from Idle to in_port")
            self.fsm.state = InPortState(self.fsm)

    def recognize_mouse(self, data: str):
        if data in self.fsm.exp.mice_dict:
            return True
        else:
            print("mouse ID: '" + data + "' does not exist in the mouse dictionary.")
            return False


class InPortState(State):
    def __init__(self, fsm):
        super().__init__("port", fsm)
        threading.Thread(target=self.wait_for_event, daemon=True).start()

    def wait_for_event(self):
        timeout_seconds = 15  # timeout
        start_time = time.time()

        while lgpio.gpio_read(h, IR_pin) != 1:
            if time.time() - start_time > timeout_seconds:
                print("Timeout in InPortState: returning to IdleState")
                self.on_event("timeout")
                return
            time.sleep(0.09)
        if self.fsm.exp.live_w.activate_window:
            self.fsm.exp.live_w.toggle_indicator("IR", "on")
            time.sleep(0.1)
            self.fsm.exp.live_w.toggle_indicator("IR", "off")
        else:
            time.sleep(0.1)
        print("The mouse entered!")

        if self.fsm.exp.exp_params["start_trial_time"] is not None:
            time.sleep(int(self.fsm.exp.exp_params["start_trial_time"]))
            print("Sleep before start trial")

        self.on_event('IR_stim')

    def on_event(self, event):
        if event == 'IR_stim':
            print("Transitioning from InPort to Trial")
            self.fsm.state = TrialState(self.fsm)
        elif event == 'timeout':
            print("Transitioning from InPort to Idle due to timeout")
            self.fsm.state = IdleState(self.fsm)

class TrialState(State):
    def __init__(self, fsm):
        super().__init__("trial", fsm)
        self.got_response = None
        self.stop_threads = False
        self.trial_thread = threading.Thread(target=self.run_trial)
        self.trial_thread.start()

    def run_trial(self):
        self.fsm.current_trial.start_time = datetime.now().strftime('%H:%M:%S.%f')  # Get current time
        self.fsm.current_trial.calculate_stim()
        # if self.fsm.exp.live_w.activate_window:
        #    self.fsm.exp.live_w.update_trial_value(self.fsm.current_trial.current_value)
        current_value = self.fsm.current_trial.current_value
        current_stim = str(self.fsm.current_trial.current_stim_number)
        print(f"Trial value: {current_value}, Stimulus: {current_stim}")
        if self.fsm.exp.live_w.activate_window:
           self.fsm.exp.live_w.update_trial_value(current_value)
           self.fsm.exp.live_w.update_stimulus(current_stim)

        stim_thread = threading.Thread(target=self.odor_stim, args=(lambda: self.stop_threads,))
        input_thread = threading.Thread(target=self.receive_input, args=(lambda: self.stop_threads,))
        
        stim_thread.start()
        input_thread.start()

        while stim_thread.is_alive():
            if self.got_response:
                self.stop_threads = True
                break
            time.sleep(0.05)

        stim_thread.join()
        self.stop_threads = True
        input_thread.join()
        if self.fsm.current_trial.score is None:
            self.fsm.current_trial.score = self.evaluate_response()
            print("score: " + self.fsm.current_trial.score)
            if self.fsm.exp.live_w.activate_window:
                self.fsm.exp.live_w.update_score(self.fsm.current_trial.score)

            if self.fsm.current_trial.score == 'hit':
                self.give_reward()
            elif self.fsm.current_trial.score == 'fa':
                self.give_punishment()
        self.on_event('trial_over')

    

    def odor_stim(self, stop):
        stim_number = self.fsm.current_trial.current_stim_number
        stim_duration = float(self.fsm.exp.exp_params["open_odor_duration"])
        odor_gpio = self.fsm.exp.GPIO_dict[stim_number]
        self.valve_on(odor_gpio)
        time.sleep(float(self.fsm.exp.exp_params["load_odor_duration"]))
        try:
            self.valve_on(exit_odor_valve_pin)
            if self.fsm.exp.live_w.activate_window:
                self.fsm.exp.live_w.toggle_indicator("stim", "on")
            start_time = time.time()
            while time.time() - start_time < stim_duration:
                if stop(): # self.got_response
                    print("Early response detected — closing valve early")
                    break
                time.sleep(0.05)  # בדיקה כל 50ms

        finally:
            self.valve_off(exit_odor_valve_pin)
            self.valve_off(odor_gpio)
            if self.fsm.exp.live_w.activate_window:
                self.fsm.exp.live_w.toggle_indicator("stim", "off")
        
        time_to_lick = int(self.fsm.exp.exp_params["time_to_lick_after_stim"])
        print("Valve closed. Waiting post-stim lick window...")

        start_post = time.time()
        while time.time() - start_post < time_to_lick:
            if stop(): #self.got_response
                print("Early response during post-stim window — skipping rest")
                return
            time.sleep(0.05)

    def receive_input(self, stop):
        if self.fsm.exp.exp_params["lick_time_bin_size"] is not None:
            time.sleep(int(self.fsm.exp.exp_params["lick_time_bin_size"]))
        elif self.fsm.exp.exp_params["lick_time"] == "1":
            pass
        elif self.fsm.exp.exp_params["lick_time"] == "2":
            time.sleep(int(self.fsm.exp.exp_params["stimulus_length"]))

        counter = 0
        self.got_response = False
        previous_lick_state = 0  # Track previous state for edge detection
        print('waiting for licks...')
        while not stop():
            current_lick_state = lgpio.gpio_read(h, lick_pin)
            # Only count lick on transition from LOW to HIGH (rising edge)
            if current_lick_state == 1 and previous_lick_state == 0:  # 1 == HIGH, 0 == LOW
                self.fsm.current_trial.add_lick_time()
                counter += 1
                if self.fsm.exp.live_w.activate_window:
                    self.fsm.exp.live_w.toggle_indicator("lick", "on")
                    time.sleep(0.01) #wait for the lick to be visible on the indicator
                    self.fsm.exp.live_w.toggle_indicator("lick", "off")
                print("lick detected")

                if counter >= int(self.fsm.exp.exp_params["lick_threshold"]) and not self.got_response:
                    self.got_response = True
                    print('threshold reached')
                    break
            # Update previous state for next iteration
            previous_lick_state = current_lick_state
            time.sleep(0.01)

        if not self.got_response:
            print('no response')
        print('num of licks: ' + str(counter))

    
    def give_reward(self):
        self.valve_on(valve_pin)
        time.sleep(float(self.fsm.exp.exp_params["open_valve_duration"]))
        self.valve_off(valve_pin)

    def give_punishment(self): #after changing to .npz
        with audio_lock:
            sd.stop()
            try:
                sd.play(self.fsm.noise, samplerate=self.fsm.noise_Fs, blocking=True) 
            finally:
                sd.stop()
                time.sleep(float(self.fsm.exp.exp_params["timeout_punishment"])) #timeout as punishment
            
    def valve_on(self, gpio_number):
        lgpio.gpio_write(h, gpio_number, 1)
        
    def valve_off(self, gpio_number):
        lgpio.gpio_write(h, gpio_number, 0)
    def evaluate_response(self):
        value = self.fsm.current_trial.current_value
        if value == 'go':
            return 'hit' if self.got_response else 'miss'
        elif value == 'no-go':
            return 'fa' if self.got_response else 'cr'
        elif value == 'catch':
            return 'catch - response' if self.got_response else 'catch - no response'

    def on_event(self, event):
        if event == 'trial_over':
            time.sleep(0.5)
            self.fsm.current_trial.write_trial_to_csv(self.fsm.exp.txt_file_path)
            if self.fsm.exp.exp_params['ITI_time'] is None:
                if self.fsm.skip_ir_exit:
                    time.sleep(1)
                    print("[IR] Slept 1 second. Skipping IR exit wait (after IR exit timeout this session).")
                else:
                    loop_start = time.time()
                    while lgpio.gpio_read(h, IR_pin) == 1:  # 1 == HIGH — wait until mouse leaves
                        if time.time() - loop_start >= IR_EXIT_WAIT_MAX_SEC:
                            self.fsm.on_ir_exit_wait_timed_out()
                            break
                        time.sleep(0.09)
                time.sleep(1)  # wait one sec after exit- before pass to the next trial
            else:
                time.sleep(int(self.fsm.exp.exp_params['ITI_time']))
            print("Transitioning from trial to idle")
            self.fsm.state = IdleState(self.fsm)

class FiniteStateMachine:

    def __init__(self, experiment=None):
        self.exp = experiment
        self.current_trial = Trial(self)
        # True after IR exit wait timeout; cleared when IR reads LOW again in Idle (ITI_time is None)
        self.skip_ir_exit = False
        self.last_ir_problem_email_ts = None

        # Prepare all odor GPIO outputs once, before the FSM starts running
        self.init_odor_gpio_outputs()

        # Load white noise for punishment
        try:
            #with np.load('/home/educage/git_educage2/educage2/pythonProject1/stimuli/white_noise.npz', mmap_mode='r') as z:
            with np.load(os.path.join('stimuli', 'white_noise.npz'), mmap_mode='r') as z:
                self.noise = z['noise']
                self.noise_Fs = int(z['Fs'])
        except FileNotFoundError:
            print("Warning: white_noise.npz not found, punishment audio will not work")

        # Start in Idle state after all init is done
        self.state = IdleState(self)

    def init_odor_gpio_outputs(self):
        """
        Claim all GPIO pins used for odor valves (stimulus lines)
        once at startup, based on the experiment's GPIO mapping.
        """
        # Odor GPIOs defined by the experiment mapping
        if hasattr(self.exp, "GPIO_dict") and isinstance(self.exp.GPIO_dict, dict):
            for pin in self.exp.GPIO_dict.values():
                try:
                    lgpio.gpio_claim_output(h, int(pin), 0)
                except Exception as e:
                    print(f"[GPIO init] Failed to claim output for pin {pin}: {e}")

    def on_ir_exit_wait_timed_out(self):
        """
        IR stayed HIGH past IR_EXIT_WAIT_MAX_SEC after trial (mouse "never left" / sensor fault).
        Notify by email, log, and skip IR exit wait on all subsequent trial ends this session.
        """
        exp = self.exp
        body = (
            f"IR sensor stayed HIGH for {IR_EXIT_WAIT_MAX_SEC // 60} minutes while waiting "
            f"for the mouse to leave the port. There may be dirt or debris on the IR sensor and it might need cleaning.\n\n"
            f"Experiment folder / name: {getattr(exp, 'txt_file_name', '?')}\n"
            f"The FSM left the wait loop and will skip the IR-exit wait until IR reads LOW again in Idle.\n"
            f"ITI exit-and-enter wait will resume automatically once the sensor is OK."
        )
        try:
            recipients = getattr(exp, "user_emails", None)
            if not recipients:
                recipients = [getattr(exp, "user_email", "") or ""]
            for to_email in recipients:
                to_email = (to_email or "").strip()
                if not to_email:
                    continue
                send_email(
                    to_email=to_email,
                    subject="Olfactocage: IR exit wait timeout",
                    body=body,
                )
            self.last_ir_problem_email_ts = time.time()
        except Exception as e:
            print(f"[IR] Failed to send warning email: {e}")
        print(
            f"[IR] Exit wait exceeded {IR_EXIT_WAIT_MAX_SEC}s — continuing; "
            "IR exit wait disabled until IR reads LOW in Idle."
        )
        self.skip_ir_exit = True
        self._log_ir_event_to_parameters(
            event_type="IR problem (exit wait timeout)",
            details=(
                f"IR stayed HIGH for {IR_EXIT_WAIT_MAX_SEC // 60} minutes after trial end "
                f"while waiting for the mouse to leave the port. "
                f"Possible sensor fault or debris. "
                f"ITI exit-and-enter wait is disabled until IR reads LOW again in Idle."
            ),
        )

    def maybe_send_ir_problem_reminder(self):
        """While IR issue persists, resend warning email at a fixed interval."""
        now = time.time()
        if self.last_ir_problem_email_ts is not None and (now - self.last_ir_problem_email_ts) < IR_PROBLEM_REMINDER_SEC:
            return

        exp = self.exp
        body = (
            f"Reminder: IR sensor issue is still ongoing.\n\n"
            f"IR sensor stayed HIGH for {IR_EXIT_WAIT_MAX_SEC // 60} minutes while waiting "
            f"for the mouse to leave the port. There may be dirt or debris on the IR sensor and it might need cleaning.\n\n"
            f"Experiment folder / name: {getattr(exp, 'txt_file_name', '?')}\n"
            f"The FSM is still skipping IR-exit wait until IR reads LOW again in Idle."
        )
        try:
            recipients = getattr(exp, "user_emails", None)
            if not recipients:
                recipients = [getattr(exp, "user_email", "") or ""]
            for to_email in recipients:
                to_email = (to_email or "").strip()
                if not to_email:
                    continue
                send_email(
                    to_email=to_email,
                    subject="Olfactocage: IR exit wait timeout",
                    body=body,
                )
            self.last_ir_problem_email_ts = now
            print("[IR] Reminder email sent (issue still ongoing).")
        except Exception as e:
            print(f"[IR] Failed to send reminder email: {e}")

    def on_ir_exit_recovered(self):
        """IR reads LOW again while skip_ir_exit was active — restore normal ITI exit wait."""
        self.skip_ir_exit = False
        self.last_ir_problem_email_ts = None
        print(
            "[IR] Sensor reads LOW in Idle — IR exit wait restored. "
            "ITI exit-and-enter will wait for the mouse to leave again after each trial."
        )
        self._log_ir_event_to_parameters(
            event_type="IR recovered",
            details="IR reads LOW in Idle. ITI exit-and-enter wait restored.",
        )

    def _log_ir_event_to_parameters(self, event_type: str, details: str):
        """Append IR status notes to parameters.txt (same folder as experiment txt file)."""
        exp = self.exp
        if exp is None or not getattr(exp, "txt_file_path", None):
            print("[IR] Cannot log to parameters.txt: experiment path not set.")
            return
        folder_path = os.path.dirname(exp.txt_file_path)
        parameters_file_path = os.path.join(folder_path, "parameters.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(parameters_file_path, "a", encoding="utf-8") as file:
                file.write(f"\n--- IR event {timestamp} ---\n")
                file.write(f"Event: {event_type}\n")
                file.write(f"Details: {details}\n")
                file.write(f"Experiment: {getattr(exp, 'txt_file_name', '?')}\n")
                file.write(f"skip_ir_exit: {self.skip_ir_exit}\n")
                if exp.exp_params is not None:
                    iti_time = exp.exp_params.get("ITI_time")
                    file.write(f"ITI_time: {iti_time}\n")
                file.write("-" * 40 + "\n")
            print(f"[IR] Logged to parameters.txt: {event_type}")
        except Exception as e:
            print(f"[IR] Failed to write to parameters.txt: {e}")

    def on_event(self, event):
        self.state.on_event(event)

    def get_state(self):
        return self.state.name


if __name__ == "__main__":
    fsm = FiniteStateMachine()

