import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk  # Make sure to import ttk for the Combobox
import csv  # To handle CSV writing
from tkinter import filedialog  # To open the file dialog for saving files
import os
from column_constants import ColumnNames


def _raise_tk_window(win):
    """Lift window to front; helps when running inside Thonny/IDE (dialogs behind IDE)."""
    try:
        win.lift()
        win.attributes("-topmost", True)
        win.update_idletasks()
        win.attributes("-topmost", False)
        win.focus_force()
    except tk.TclError:
        pass


class LevelDefinitionApp:
    
    def __init__(self, master, experiment):
        self.master = master
        self.experiment = experiment
        self.master.title("Experiment Level Definition")
        self.frame = tk.Frame(self.master)
        self.frame.pack(padx=10, pady=10)
        
        # Instruction line: clarify the two-step flow
        instruction = "Step 1: Add levels (name + number of stimuli).\nStep 2: Step 2: Build the stimuli table, set its parameters, then Save."
        tk.Label(self.frame, text=instruction, font=("Arial", 9), wraplength=500, justify=tk.LEFT).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Initialize the save_button attribute
        self.save_button = None  # Initially set to None, to be defined later
        
        # Create header row for the first table
        tk.Label(self.frame, text=ColumnNames.LEVEL_NAME, font=("Arial", 12, "bold")).grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.frame, text=ColumnNames.NUMBER_OF_STIMULI, font=("Arial", 12, "bold")).grid(row=1, column=1, padx=5, pady=5)

        # Current row index for the first table
        self.current_row = 2

        # Button to add a new level row
        self.add_button = tk.Button(self.frame, text="Add level row", command=self.add_level)
        self.add_button.grid(row=self.current_row, column=0, columnspan=2, pady=10)

        # Button to build the stimuli table (second step)
        self.load_button = tk.Button(self.frame, text="Build stimuli table", command=self.load_levels)
        self.load_button.grid(row=self.current_row + 1, column=0, columnspan=2, pady=10)

        self.level_entries = []  # Store level name and stimulus counts
        self.stimuli_table_content = []
        self.stimuli_frame = None  # Frame for the stimuli table
        self.stimuli_container = None  # Container for scrollable content
        self.canvas = None  # Canvas for scrolling
        self.scrollbar = None  # Scrollbar
        self.scrollable_frame = None  # Scrollable frame
        self.save_path = None

    def add_level(self):
        level_name_entry = tk.Entry(self.frame)
        level_name_entry.grid(row=self.current_row, column=0, padx=5, pady=5)

        stimuli_count_entry = tk.Entry(self.frame, width=5)  # Make the entry shorter
        stimuli_count_entry.grid(row=self.current_row, column=1, padx=5, pady=5)

        self.level_entries.append((level_name_entry, stimuli_count_entry))  # Save entries to access later

        # Update the current row and reposition buttons
        self.current_row += 1
        self.update_buttons()

    def update_buttons(self):
        # Update the positions of the Add and Load buttons
        self.add_button.grid(row=self.current_row, column=0, columnspan=2, pady=10)
        self.load_button.grid(row=self.current_row + 1, column=0, columnspan=2, pady=10)
        
    def header_titles(self):
        # Create header for the stimuli table
        tk.Label(self.stimuli_frame, text=ColumnNames.LEVEL_NAME, font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.ODOR_NUMBER, font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.PROBABILITY, font=("Arial", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.VALUE, font=("Arial", 12, "bold")).grid(row=0, column=3, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.INDEX, font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5, pady=5)
            
    
    def load_levels(self):
        # if self.stimuli_frame is not None:
        #     for widget in self.stimuli_frame.winfo_children():
        #         widget.destroy()
        #     self.header_titles()
        # else:
        #     # Create stimuli frame if it doesn't exist
        #     self.stimuli_frame = tk.Frame(self.master)
        #     self.stimuli_frame.pack(side="left", padx=10, pady=10)
        #     self.header_titles()
        # Clear previous stimuli frame if it exists
        if self.stimuli_container is not None:
            self.stimuli_container.destroy()
            
        # Clear the stimuli table content list
        self.stimuli_table_content = []
            
        # Create main container for scrollable content
        self.stimuli_container = tk.Frame(self.master)
        self.stimuli_container.pack(side="left", padx=10, pady=10, fill="both", expand=True)
        
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(self.stimuli_container, width=800, height=400)
        self.scrollbar = tk.Scrollbar(self.stimuli_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Set stimuli_frame to be the scrollable frame
        self.stimuli_frame = self.scrollable_frame
        self.header_titles()


        # Attempt to build the second table based on user input
        for level_entry, count_entry in self.level_entries:
            level_name = level_entry.get().strip()
            try:
                number_of_stimuli = int(count_entry.get().strip())
                
                if number_of_stimuli < 1:
                    messagebox.showwarning(
                        "Input Error",
                        "Number of stimuli must be at least 1.",
                        parent=self.master,
                    )
                    return
                
                # Create rows for each stimulus
                self.create_stimuli_rows(level_name, number_of_stimuli)

                # Enable the Save button if it's not already created
                if self.save_button is None:
                    self.save_button = tk.Button(self.frame, text="Save", command=self.save_stimuli_table)
                    self.save_button.grid(row=self.current_row + 2, column=0, columnspan=2, pady=10)
                self.save_button.config(state=tk.NORMAL)  # Enable button

            except ValueError:
                messagebox.showwarning(
                    "Input Error",
                    "Please enter a valid number for the stimuli.",
                    parent=self.master,
                )
            
    def save_stimuli_table(self):
        # Gather the data from the stimuli table
        data_to_save = []
        all_filled = True  # Flag to check if all fields are filled

        # Loop through all level entries to pull their contents
        for level_name, stimulus_combobox, probability_entry, value_combobox, row_index in self.stimuli_table_content:
            
            odor_number = stimulus_combobox.get().strip()
            probability = probability_entry.get().strip()
            value = value_combobox.get().strip()
            index = str(row_index)  # INDEX is auto-filled (read-only)

            # Check if each required field is filled
            if not odor_number or not probability or value == "Select":
                all_filled = False
                break

            # Prepare a row to be saved
            data_to_save.append([level_name, odor_number,probability,value,index])#[stimulus_name, filename_label.cget("text"), probability_selection])

        if all_filled:


            levels_dir = os.path.join(os.getcwd(), "Levels")
            os.makedirs(levels_dir, exist_ok=True)  # Create it if it doesn't exist

            # Open the file dialog in the "Levels" folder
            _raise_tk_window(self.master)
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=levels_dir,  # Set default directory
                title="Save Levels File",
                parent=self.master,
            )

            if file_path:  # If valid path is provided
                # Write to CSV
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(ColumnNames.get_csv_headers())  # Writing headers
                    writer.writerows(data_to_save)  # Writing data rows
                    print(data_to_save)
            
                # Optionally, close the window after saving
                self.save_path = file_path
                self.master.destroy()
        else:
            messagebox.showwarning(
                "Input Error",
                "Please complete all the parameters.",
                parent=self.master,
            )
                
    def create_stimuli_rows(self, level_name, number_of_stimuli):
    # Add rows for each stimulus
        start_row = len(self.stimuli_frame.grid_slaves()) // 3  # Start from the next row based on the number of stimuli shown

        for i in range(number_of_stimuli):
            # Global row index (1-based): same as number of rows so far + 1
            row_index = len(self.stimuli_table_content) + 1

            # Add Level Name label
            tk.Label(self.stimuli_frame, text=level_name).grid(row=start_row + i + 1, column=0, padx=5, pady=2)
            gpio_keys = list(self.experiment.GPIO_dict.keys())  # נניח שיש לך self.experiment
            stimulus_combobox = ttk.Combobox(self.stimuli_frame, values=gpio_keys, state="readonly")
            stimulus_combobox.grid(row=start_row + i + 1, column=1, padx=5, pady=2)
            stimulus_combobox.set("Select")  # Placeholder


            # Create the Probability entry field
            probability_entry = tk.Entry(self.stimuli_frame)
            probability_entry.grid(row=start_row + i + 1, column=2, padx=5, pady=2)

            # Create a Combobox for the value column
            value_combobox = ttk.Combobox(self.stimuli_frame, values=["go", "no-go", "catch"])
            value_combobox.grid(row=start_row + i + 1, column=3, padx=5, pady=2)
            value_combobox.set("Select")  # Set a default placeholder in the combobox
            
            # INDEX: read-only label with row number (1, 2, 3, ...)
            index_label = tk.Label(self.stimuli_frame, text=str(row_index))
            index_label.grid(row=start_row + i + 1, column=4, padx=5, pady=2)
            
            self.stimuli_table_content.append((level_name, stimulus_combobox, probability_entry, value_combobox, row_index))
            
                # Draw a line separator after the last row of stimuli for this level
        separator = tk.Frame(self.stimuli_frame, height=1, bg="gray")  # Create a frame for the line
        separator.grid(row=start_row + number_of_stimuli + 1, column=0, columnspan=5, sticky="ew", padx=5, pady=5) #columnspan - the length of the line- num of columns
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if self.canvas:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
            

# Application Execution
if __name__ == "__main__":
    root = tk.Tk()
    app = LevelDefinitionApp(root, None)
    root.mainloop()

