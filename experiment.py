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

###  use those commands on terminal to push changes to git

# cd /home/educage/git_educage2/educage2/pythonProject1
# git add .
# git commit -m ""
# git push
# 
# corrupted size vs. prev_size while consolidating
# 
# Process ended with exit code -6.
###
class Experiment:
    def __init__(self,exp_name, mice_dict: dict[str, Mouse] = None, levels_df = None):
        
        
        self.exp_params = None#ExpParameters(self)
        self.fsm = None
        self.live_w = None
        self.levels_df = levels_df
        self.mice_dict = mice_dict#self.create_mice(mice_dict)
        self.results = []
        self.stim_length = 2  ########## maybe need to make it for the user choosing
        self.txt_file_name = exp_name
        self.txt_file_path = None
        self.new_txt_file(self.txt_file_name)
        self.root = tk.Tk()
        self.GUI = GUI_sections.TkinterApp(self.root, self, exp_name = self.txt_file_name)
        self.run_experiment()
        self.root.mainloop()
        self.root.destroy()
        

    def set_parameters(self, parameters):
        """This method is called by App when the OK button is pressed."""
        self.exp_params = parameters
        print("Parameters set in Experiment:", self.exp_params)

    def set_mice_dict(self, mice_dict):
        """This method is called by App when the OK button is pressed."""
        self.mice_dict = mice_dict

    def set_levels_df(self, levels_df):
        """This method is called by App when the OK button is pressed."""
        self.levels_df = levels_df
        

    def new_txt_file(self, filename):
        # Build the path: ./experiments/filename/
        folder_path = os.path.join(os.getcwd(), "experiments", filename)
        os.makedirs(folder_path, exist_ok=True)  # Ensure the folder exists

        self.txt_file_path = os.path.join(folder_path,filename+".txt")  

        with open(self.txt_file_path, 'w') as file:
            pass

    def run_experiment(self):
        # Check periodically if parameters have been set
        if self.exp_params is None:
            self.root.after(100,lambda: self.run_experiment())  # Check again after 100ms
        else:
            print("Parameters received.")
            # Proceed with the experiment once parameters are set
            # Start experiment in a separate thread to keep the GUI responsive
            threading.Thread(target=self.start_experiment).start()

    def start_experiment(self):
        # This method runs the actual experiment (on a separate thread)
        fsm = FiniteStateMachine(self)
        self.fsm = fsm
        print("FSM created:", self.fsm)
        
    def run_live_window(self):
        self.root.after(0, self.open_live_window)
        
    def open_live_window(self):
        if self.live_w is None:
            self.live_w = live_window.LiveWindow()#self.GUI

    def change_mouse_level(self, mouse: Mouse, new_level: Level):
        mouse.update_level(new_level)

    def save_results(self, filename: str):
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=4)

if __name__ == "__main__":
    
    created_folder_name = None

    def create_experiment_folder():
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

    # Create the GUI window
    root = tk.Tk()
    root.title("Experiment Setup")
    root.geometry("300x120")

    tk.Label(root, text="Enter Experiment Name:").pack(pady=10)

    entry = tk.Entry(root, width=30)
    entry.insert(0, "exp")  # Set default text
    entry.pack()

    tk.Button(root, text="Create Folder", command=create_experiment_folder).pack(pady=10)

    root.mainloop()

#     # Create an experiment
    experiment = Experiment(exp_name = created_folder_name)#, mice_dict={mouse_1.get_id():mouse_1, mouse_2.get_id():mouse_2}, levels_df={1: level_1, 2: level_2})

