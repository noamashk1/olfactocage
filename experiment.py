import json
from typing import List, Dict, Any
import trial
from level import Level
from mouse import Mouse
from finite_state_machine import FiniteStateMachine
import tkinter as tk
from tkinter import simpledialog
import threading
import GUI_sections
import live_window
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import numpy as np

###  use those commands on terminal to push changes to git

# cd /home/educage/Projects/olfactocage
# git add .
# git commit -m ""
# git push
# 
# corrupted size vs. prev_size while consolidating
# 
# Process ended with exit code -6.
###
# experiment.py
# This file manages the main experiment logic, including GUI setup, experiment folder creation, and experiment execution.
# It uses tkinter for GUI, manages experiment parameters, and handles experiment data storage.
class Experiment:
    def __init__(self,exp_name, mice_dict: dict[str, Mouse] = None, levels_df = None):
        """
        Initialize the Experiment object.
        - exp_name: Name of the experiment (used for folder and file naming)
        - mice_dict: Dictionary of Mouse objects (optional)
        - levels_df: DataFrame or dict of levels (optional)
        """
        self.exp_params = None#ExpParameters(self)  # Experiment parameters (set later by GUI)
        self.fsm = None  # Finite State Machine for experiment logic
        self.live_w = None  # Live window for real-time display (set later)
        self.levels_df = levels_df  # Levels data
        self.mice_dict = mice_dict#self.create_mice(mice_dict)  # Mice data
        self.results = []  # List to store experiment results
        self.stim_length = 2  ########## maybe need to make it for the user choosing
        self.txt_file_name = exp_name  # Name for the experiment text file
        self.txt_file_path = None  # Path to the experiment text file
        self.exp_folder_path =None
        self.remote_folder = "/mnt/labfolder/Noam/results"
        self.new_txt_file(self.txt_file_name)  # Create a new text file for results
        self.GPIO_dict = {
                1: 5,
                2: 6,
                3: 13,
                4: 19,
                5: 26,
                6: 21,
                7: 20,
                8: 16
            }
        self.root = tk.Tk()  # Main tkinter root window
        self.GUI = GUI_sections.TkinterApp(self.root, self, exp_name = self.txt_file_name)  # Main GUI app
        # Preload punishment noise once
        self.white_noise = None
        self.white_noise_fs = None
        self.preload_white_noise()
        self.run_experiment()  # Start experiment logic
        self.root.mainloop()  # Start the GUI event loop
        self.root.destroy()  # Destroy the root window after closing
        

    def set_parameters(self, parameters):
        """
        Set experiment parameters (called by GUI when user confirms parameters).
        """
        self.exp_params = parameters
        print("Parameters set in Experiment:", self.exp_params)

    def set_mice_dict(self, mice_dict):
        """
        Set the mice dictionary (called by GUI when user confirms mice selection).
        """
        self.mice_dict = mice_dict

    def set_levels_df(self, levels_df):
        """
        Set the levels DataFrame or dictionary (called by GUI when user confirms levels).
        """
        self.levels_df = levels_df
        
    def preload_white_noise(self):
        """Load white noise once into memory (noise array and sampling rate)."""
        path = '/home/educage/Projects/olfactocage/stimuli/white_noise.npz'
        data = np.load(path)
        noise = data['data']
        fs = int(data['Fs'])
        self.white_noise = noise
        self.white_noise_fs = fs


    def new_txt_file(self, filename):
        """
        Create a new text file for experiment results in a dedicated folder under ./experiments/filename/.
        If the file already exists, do nothing.
        """
        # Build the path: ./experiments/filename/
        folder_path = os.path.join(os.getcwd(), "experiments", filename)
        self.exp_folder_path = folder_path
        os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists

        self.txt_file_path = os.path.join(folder_path, filename + ".txt")  

        # Only create the file if it doesn't exist
        if not os.path.exists(self.txt_file_path):
            with open(self.txt_file_path, 'w') as file:
                pass
    # def new_txt_file(self, filename):
    #     """
    #     Create a new text file for experiment results in a dedicated folder under ./experiments/filename/.
    #     """
    #     # Build the path: ./experiments/filename/
    #     folder_path = os.path.join(os.getcwd(), "experiments", filename)
    #     os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists

    #     self.txt_file_path = os.path.join(folder_path,filename+".txt")  

    #     with open(self.txt_file_path, 'w') as file:
    #         pass

    def run_experiment(self):
        """
        Wait until experiment parameters are set, then start the experiment in a separate thread.
        This keeps the GUI responsive while the experiment runs.
        """
        # Check periodically if parameters have been set
        if self.exp_params is None:
            self.root.after(100,lambda: self.run_experiment())  # Check again after 100ms
        else:
            print("Parameters received.")
            # Proceed with the experiment once parameters are set
            # Start experiment in a separate thread to keep the GUI responsive
            threading.Thread(target=self.start_experiment).start()

    def start_experiment(self):
        """
        Start the main experiment logic by creating the Finite State Machine (FSM).
        Runs in a separate thread.
        """
        fsm = FiniteStateMachine(self)
        self.fsm = fsm
        print("FSM created:", self.fsm)
        
    def run_live_window(self):
        """
        Schedule opening the live window (real-time display) in the main GUI thread.
        """
        self.root.after(0, self.open_live_window)
        
    def open_live_window(self):
        """
        Open the live window if it hasn't been opened yet.
        """
        if self.live_w is None:
            self.live_w = live_window.LiveWindow()#self.GUI

    def change_mouse_level(self, mouse: Mouse, new_level: Level):
        """
        Change the level of a given mouse.
        """
        mouse.update_level(new_level)

    def save_results(self, filename: str):
        """
        Save the experiment results to a JSON file.
        """
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=4)

    def create_GPIO_dict(self):

        def save_and_close():
            temp_dict = {}
            for idx, entry in enumerate(gpio_entries):
                index = idx + 1
                gpio_val = entry.get().strip()
                if not gpio_val.isdigit():
                    messagebox.showerror("Input Error", f"GPIO value at row {index} must be a number.")
                    return
                temp_dict[index] = int(gpio_val)
            self.GPIO_dict = temp_dict
            print(self.GPIO_dict)
            top.destroy()

        def add_row():
            row_idx = len(gpio_entries)
            if row_idx >= 32:
                messagebox.showwarning("Limit", "Maximum 32 rows allowed.")
                return
            idx_label = tk.Label(table_frame, text=str(row_idx + 1), width=10)
            idx_label.grid(row=row_idx + 1, column=0, padx=5, pady=2)
            gpio_entry = tk.Entry(table_frame, width=10)
            gpio_entry.grid(row=row_idx + 1, column=1, padx=5, pady=2)
            gpio_entry.insert(0, "")
            gpio_entries.append(gpio_entry)

        # Create the popup window
        top = tk.Toplevel(self.root)
        top.title("Set GPIO Mapping")
        top.geometry("250x350")
        table_frame = tk.Frame(top)
        table_frame.pack(padx=10, pady=10)

        # Table headers
        tk.Label(table_frame, text="Index", font=("Arial", 10, "bold"), width=10).grid(row=0, column=0, padx=5, pady=2)
        tk.Label(table_frame, text="GPIO Number", font=("Arial", 10, "bold"), width=10).grid(row=0, column=1, padx=5, pady=2)

        gpio_entries = []
        # Fill with current values from self.GPIO_dict (sorted by index)
        for i, idx in enumerate(sorted(self.GPIO_dict.keys())):
            gpio_num = self.GPIO_dict[idx]
            idx_label = tk.Label(table_frame, text=str(idx), width=10)
            idx_label.grid(row=i + 1, column=0, padx=5, pady=2)
            gpio_entry = tk.Entry(table_frame, width=10)
            gpio_entry.grid(row=i + 1, column=1, padx=5, pady=2)
            gpio_entry.insert(0, str(gpio_num))
            gpio_entries.append(gpio_entry)

        # Add row button
        add_btn = tk.Button(top, text="Add Row", command=add_row)
        add_btn.pack(pady=5)

        # Save button
        save_btn = tk.Button(top, text="Save", command=save_and_close)
        save_btn.pack(pady=5)

# --- Main script for running experiment setup and execution ---
if __name__ == "__main__":r
    # Variable to store the created experiment folder name
    created_folder_name = None
    def create_experiment_folder():
        """
        Create a new experiment folder with the current date appended.
        If the folder exists, ask the user if they want to use it.
        Sets the global variable 'created_folder_name' and closes the setup window on success.
        """
        global created_folder_name

        exp_name = entry.get().strip()
        if not exp_name:
            messagebox.showwarning("Input Error", "Please enter a valid experiment name.")
            return

        date_str = datetime.now().strftime("%d_%m_%Y")
        base_dir = "experiments"
        os.makedirs(base_dir, exist_ok=True)

        folder_name = f"{exp_name}_{date_str}"
        full_path = os.path.join(base_dir, folder_name)

        if os.path.exists(full_path):
            # Ask user if they want to override
            answer = messagebox.askyesno("Folder Exists", f"The folder '{folder_name}' already exists.\nDo you want to use it?")
            if not answer:
                return  # Do nothing, let user change the name or cancel
        else:
            os.makedirs(full_path)

        created_folder_name = folder_name
        #messagebox.showinfo("Success", f"Folder ready:\n{full_path}")
        root.destroy()

    # Create the GUI window for experiment setup
    root = tk.Tk()
    root.title("Experiment Setup")
    root.geometry("300x120")

    tk.Label(root, text="Enter Experiment Name:").pack(pady=10)

    entry = tk.Entry(root, width=30)
    entry.insert(0, "exp")  # Set default text
    entry.pack()

    tk.Button(root, text="Create Folder", command=create_experiment_folder).pack(pady=10)

    root.mainloop()

    # After the setup window closes, create the Experiment object
    experiment = Experiment(exp_name = created_folder_name)#, mice_dict={mouse_1.get_id():mouse_1, mouse_2.get_id():mouse_2}, levels_df={1: level_1, 2: level_2})

