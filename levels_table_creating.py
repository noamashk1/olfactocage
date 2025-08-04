import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk  # Make sure to import ttk for the Combobox
import csv  # To handle CSV writing
from tkinter import filedialog  # To open the file dialog for saving files
import os


class LevelDefinitionApp:
    
    def __init__(self, master):
        self.master = master
        self.master.title("Experiment Level Definition")
        self.frame = tk.Frame(self.master)
        self.frame.pack(padx=10, pady=10)
        
        # Initialize the save_button attribute
        self.save_button = None  # Initially set to None, to be defined later
        
        # Create header row for the first table
        tk.Label(self.frame, text="Level Name", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.frame, text="Number of Stimuli", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)

        # Current row index for the first table
        self.current_row = 1

        # Button to add a new level
        self.add_button = tk.Button(self.frame, text="Add Level", command=self.add_level)
        self.add_button.grid(row=self.current_row, column=0, columnspan=2, pady=10)

        # Load button to create the second table
        self.load_button = tk.Button(self.frame, text="Load", command=self.load_levels)
        self.load_button.grid(row=self.current_row + 1, column=0, columnspan=2, pady=10)

        self.level_entries = []  # Store level name and stimulus counts
        self.stimuli_table_content = []
        self.stimuli_frame = None  # Frame for the stimuli table
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
        tk.Label(self.stimuli_frame, text="Level Name", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text="Stimuli path", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text="Probability", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text="value", font=("Arial", 12, "bold")).grid(row=0, column=3, padx=5, pady=5)
        tk.Label(self.stimuli_frame, text="index", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5, pady=5)
            
    
    def load_levels(self):
        # Clear previous stimuli frame if it exists
        if self.stimuli_frame is not None:
            for widget in self.stimuli_frame.winfo_children():
                widget.destroy()
            self.header_titles()
        else:
            # Create stimuli frame if it doesn't exist
            self.stimuli_frame = tk.Frame(self.master)
            self.stimuli_frame.pack(side="left", padx=10, pady=10)
            self.header_titles()


        # Attempt to build the second table based on user input
        for level_entry, count_entry in self.level_entries:
            level_name = level_entry.get().strip()
            try:
                number_of_stimuli = int(count_entry.get().strip())
                
                if number_of_stimuli < 1:
                    messagebox.showwarning("Input Error", "Number of stimuli must be at least 1.")
                    return
                
                # Create rows for each stimulus
                self.create_stimuli_rows(level_name, number_of_stimuli)

                # Enable the Save button if it's not already created
                if self.save_button is None:
                    self.save_button = tk.Button(self.frame, text="Save", command=self.save_stimuli_table)
                    self.save_button.grid(row=self.current_row + 2, column=0, columnspan=2, pady=10)
                self.save_button.config(state=tk.NORMAL)  # Enable button

            except ValueError:
                messagebox.showwarning("Input Error", "Please enter a valid number for the stimuli.")
            
    def save_stimuli_table(self):
        # Gather the data from the stimuli table
        data_to_save = []
        all_filled = True  # Flag to check if all fields are filled

        # Loop through all level entries to pull their contents
        for level_name, stimulus_entry, probability_entry, value_combobox, index_entry in self.stimuli_table_content:
            
            #level_name = level_name_row.get().strip()
            stimulus_path = stimulus_entry.get().strip()
            probability = probability_entry.get().strip()
            value = value_combobox.get().strip()
            index = index_entry.get().strip()

            # Check if each required field is filled
            if not stimulus_path or not probability or not index or value == "Select":
                all_filled = False
                break

            # Prepare a row to be saved
            data_to_save.append([level_name, stimulus_path,probability,value,index])#[stimulus_name, filename_label.cget("text"), probability_selection])

        if all_filled:
#             # Prompt user to choose location to save the CSV file
#             file_path = filedialog.asksaveasfilename(defaultextension=".csv", 
#                                                        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])

            levels_dir = os.path.join(os.getcwd(), "Levels")
            os.makedirs(levels_dir, exist_ok=True)  # Create it if it doesn't exist

            # Open the file dialog in the "Levels" folder
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=levels_dir,  # Set default directory
                title="Save Levels File"
            )

            if file_path:  # If valid path is provided
                # Write to CSV
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Level Name","Stimulus Path", "Probability", "Value", "Index"])  # Writing headers
                    writer.writerows(data_to_save)  # Writing data rows
                    print(data_to_save)
            
                # Optionally, close the window after saving
                self.save_path = file_path
                self.master.destroy()
        else:
            messagebox.showwarning("Input Error", "Please complete all the parameters.")
                
    def create_stimuli_rows(self, level_name, number_of_stimuli):
    # Add rows for each stimulus
        start_row = len(self.stimuli_frame.grid_slaves()) // 3  # Start from the next row based on the number of stimuli shown

        for i in range(number_of_stimuli):
            # Add Level Name label
            tk.Label(self.stimuli_frame, text=level_name).grid(row=start_row + i + 1, column=0, padx=5, pady=2)
            
            # Create a frame to hold the entry and label
            stimuli_frame = tk.Frame(self.stimuli_frame)
            stimuli_frame.grid(row=start_row + i + 1, column=1, padx=5, pady=2)

            # Create the Stimuli entry field
            stimulus_entry = tk.Entry(stimuli_frame)
            stimulus_entry.pack(side=tk.TOP)  # Pack Entry at the top

            # Create a label to display the filename
            filename_label = tk.Label(stimuli_frame, text="", fg="gray")  # Gray text for the filename
            filename_label.pack(side=tk.TOP)  # Pack Label below the Entry

            # Bind the click event for the entry
            stimulus_entry.bind("<Button-1>", lambda event, entry=stimulus_entry, label=filename_label: self.load_stimulus_file(entry, label))


            # Create the Probability entry field
            probability_entry = tk.Entry(self.stimuli_frame)
            probability_entry.grid(row=start_row + i + 1, column=2, padx=5, pady=2)

            # Create a Combobox for the value column
            value_combobox = ttk.Combobox(self.stimuli_frame, values=["go", "no-go", "catch"])
            value_combobox.grid(row=start_row + i + 1, column=3, padx=5, pady=2)
            value_combobox.set("Select")  # Set a default placeholder in the combobox
            
            # Create the index entry field
            index_entry = tk.Entry(self.stimuli_frame)
            index_entry.grid(row=start_row + i + 1, column=4, padx=5, pady=2) 
            
            self.stimuli_table_content.append((level_name, stimulus_entry,probability_entry,value_combobox,index_entry))
            
            # Draw a line separator after the last row of stimuli for this level
        separator = tk.Frame(self.stimuli_frame, height=1, bg="gray")  # Create a frame for the line
        separator.grid(row=start_row + number_of_stimuli + 1, column=0, columnspan=5, sticky="ew", padx=5, pady=5) #columnspan - the length of the line- num of columns
        
    def load_stimulus_file(self, entry, label):
        # Open file dialog to select a stimulus file
        stimuli_dir = os.path.join(os.getcwd(), "stimuli")
        default_dir = stimuli_dir if os.path.exists(stimuli_dir) else os.getcwd()
        file_path = filedialog.askopenfilename(
        filetypes=(("All Files", "*.*"),),
        initialdir=default_dir,
        title="Select Stimulus File"
    )
#          file_path = filedialog.askopenfilename(title="Select Stimulus File",
#                                                  filetypes=(("All Files", "*.*"),))
        if file_path:  # If a file was selected
            entry.delete(0, tk.END)  # Clear the current entry
            entry.insert(0, file_path)  # Insert the selected file path
            
            # Update the label to show only the filename
            filename = file_path.split("/")[-1]  # Get the filename from the path
            label.config(text=filename)  # Update the label with just the filename
            
        

# Application Execution
if __name__ == "__main__":
    root = tk.Tk()
    app = LevelDefinitionApp(root)
    root.mainloop()

