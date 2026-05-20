import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk  # Make sure to import ttk for the Combobox
import csv  # To handle CSV writing
from tkinter import filedialog  # To open the file dialog for saving files
import os
import pandas as pd
from column_constants import ColumnNames
import General_functions


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
    
    def __init__(self, master, experiment, initial_data=None):
        self.master = master
        self.experiment = experiment
        self._rows_data_by_level = {}
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

        if initial_data is not None and not initial_data.empty:
            self._populate_from_initial_data(initial_data)

    def _resolve_column(self, df, canonical_name):
        if canonical_name in df.columns:
            return canonical_name
        lower = canonical_name.lower()
        for col in df.columns:
            if str(col).strip().lower() == lower:
                return col
        raise KeyError(f"Column '{canonical_name}' not found in levels data")

    def _populate_from_initial_data(self, df):
        level_col = self._resolve_column(df, ColumnNames.LEVEL_NAME)
        odor_col = self._resolve_column(df, ColumnNames.ODOR_NUMBER)
        prob_col = self._resolve_column(df, ColumnNames.PROBABILITY)
        value_col = self._resolve_column(df, ColumnNames.VALUE)
        index_col = self._resolve_column(df, ColumnNames.INDEX)

        for level_name, group in df.groupby(level_col, sort=False):
            level_name = str(level_name).strip()
            self.add_level_with_values(level_name, len(group))
            self._rows_data_by_level[level_name] = [
                {
                    ColumnNames.ODOR_NUMBER: row[odor_col],
                    ColumnNames.PROBABILITY: row[prob_col],
                    ColumnNames.VALUE: row[value_col],
                    ColumnNames.INDEX: row[index_col],
                }
                for _, row in group.iterrows()
            ]

        self.load_levels()

    def add_level_with_values(self, level_name, stimuli_count):
        self.add_level()
        name_entry, count_entry = self.level_entries[-1]
        name_entry.insert(0, level_name)
        count_entry.insert(0, str(stimuli_count))

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
        # If the Save button already exists (after "Build stimuli table"),
        # keep it in sync with the current_row so it doesn't overlap.
        if self.save_button is not None:
            self.save_button.grid(row=self.current_row + 2, column=0, columnspan=2, pady=10)
        
    def header_titles(self):
        # Create header for the stimuli table
        tk.Label(self.stimuli_frame, text=ColumnNames.LEVEL_NAME, font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.ODOR_NUMBER, font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.PROBABILITY, font=("Arial", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.VALUE, font=("Arial", 12, "bold")).grid(row=0, column=3, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text=ColumnNames.INDEX, font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5, pady=5)
            
    
    def _capture_current_stimuli_data(self):
        """Keep filled stimuli values when rebuilding the table (e.g. after adding a level)."""
        self._rows_data_by_level = {}
        for level_name, stimulus_combobox, probability_entry, value_combobox, row_index in self.stimuli_table_content:
            level_name = str(level_name).strip()
            odor = stimulus_combobox.get().strip()
            probability = probability_entry.get().strip()
            value = value_combobox.get().strip()
            self._rows_data_by_level.setdefault(level_name, []).append(
                {
                    ColumnNames.ODOR_NUMBER: odor if odor and odor != "Select" else None,
                    ColumnNames.PROBABILITY: probability if probability else None,
                    ColumnNames.VALUE: value if value and value != "Select" else None,
                    ColumnNames.INDEX: row_index,
                }
            )

    def load_levels(self):
        if self.stimuli_table_content:
            self._capture_current_stimuli_data()

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
                
                rows_data = self._rows_data_by_level.get(level_name)
                self.create_stimuli_rows(level_name, number_of_stimuli, rows_data)

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

        # Table is built -> recenter the main window (its size changes)
        General_functions.center_the_window(self.master)
            
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
                
    def create_stimuli_rows(self, level_name, number_of_stimuli, rows_data=None):
        start_row = len(self.stimuli_frame.grid_slaves()) // 3

        for i in range(number_of_stimuli):
            row_index = len(self.stimuli_table_content) + 1
            row_data = rows_data[i] if rows_data and i < len(rows_data) else None

            if row_data and row_data.get(ColumnNames.INDEX) is not None:
                row_index = row_data[ColumnNames.INDEX]

            tk.Label(self.stimuli_frame, text=level_name).grid(row=start_row + i + 1, column=0, padx=5, pady=2)
            gpio_keys = list(self.experiment.GPIO_dict.keys())
            odor_value = ""
            if row_data and row_data.get(ColumnNames.ODOR_NUMBER) is not None:
                odor_value = str(row_data[ColumnNames.ODOR_NUMBER]).strip()
            combobox_values = list(gpio_keys)
            if odor_value and odor_value not in combobox_values:
                combobox_values = [odor_value] + combobox_values
            stimulus_combobox = ttk.Combobox(
                self.stimuli_frame, values=combobox_values, state="readonly"
            )
            stimulus_combobox.grid(row=start_row + i + 1, column=1, padx=5, pady=2)
            if odor_value:
                stimulus_combobox.set(odor_value)
            else:
                stimulus_combobox.set("Select")

            probability_entry = tk.Entry(self.stimuli_frame)
            probability_entry.grid(row=start_row + i + 1, column=2, padx=5, pady=2)
            if row_data and row_data.get(ColumnNames.PROBABILITY) is not None:
                probability_entry.insert(0, str(row_data[ColumnNames.PROBABILITY]))

            value_options = ["go", "no-go", "catch"]
            value_combobox = ttk.Combobox(self.stimuli_frame, values=value_options)
            value_combobox.grid(row=start_row + i + 1, column=3, padx=5, pady=2)
            if row_data and row_data.get(ColumnNames.VALUE) is not None:
                value = str(row_data[ColumnNames.VALUE]).strip()
                if value and value not in value_options:
                    value_options = [value] + value_options
                    value_combobox["values"] = value_options
                value_combobox.set(value)
            else:
                value_combobox.set("Select")

            index_label = tk.Label(self.stimuli_frame, text=str(row_index))
            index_label.grid(row=start_row + i + 1, column=4, padx=5, pady=2)

            self.stimuli_table_content.append(
                (level_name, stimulus_combobox, probability_entry, value_combobox, row_index)
            )
            
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

