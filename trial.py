from datetime import datetime
import csv
import random
import os
class Trial:
    def __init__(self,fsm):
        self.fsm = fsm
        self.current_mouse = None
        self.current_stim = None
        self.current_value = None #go\no-go\catch
        self.current_stim_number = None
        self.current_exp_parameters = None
        self.score = None
        self.start_time = None
        self.current_stim_index = None
        self.licks_time = []

    def update_current_mouse(self, new_mouse: 'Mouse'):
        self.current_mouse = new_mouse

    def save_trial(self):
        pass

    def update_score(self, score): # hit\miss\fa\cr
        self.score = score

    def calculate_stim(self): #determine if the trial is go\nogo\catch using random
        level_name = self.current_mouse.get_level()
        level_rows = self.fsm.exp.levels_df.loc[self.fsm.exp.levels_df['Level Name'] == level_name]
        probabilities = level_rows["Probability"].tolist()
        indices = level_rows["Index"].tolist()
        total_probability = sum(probabilities)
        normalized_probabilities = [p / total_probability for p in probabilities]
        chosen_index = random.choices(indices, weights=normalized_probabilities, k=1)[0]
        self.current_stim_df = self.fsm.exp.levels_df.loc[(self.fsm.exp.levels_df['Level Name'] == level_name)&(self.fsm.exp.levels_df['Index'] == chosen_index)]
        self.current_value = self.current_stim_df.iloc[0]['Value']
        self.current_stim_number = self.current_stim_df.iloc[0]['Odor Number']
        self.current_stim_index = self.current_stim_df.iloc[0]['Index']

    def end_trial(self): # the trial is over - go to save it
        pass
    
    def clear_trial(self):
        self.current_mouse = None
        self.current_exp_parameters = None
        self.score = None
        self.current_stim = None
        self.current_value = None  # go\no-go\catch
        self.current_stim_number = None
        self.start_time = None
        self.current_stim_index = None
        self.licks_time = []

    def add_lick_time(self):
        current_datetime = datetime.now()
        self.licks_time.append(current_datetime.strftime('%H:%M:%S.%f'))
# Function to write trial results
    def write_trial_to_csv(self, txt_file_name):
        header = ['date', 'start time', 'end time', 'mouse ID', 'level', r'go\no-go','stim index', 'stim name','score', 'licks_time'] # Define the header if the file does not exist yet
        current_datetime = datetime.now()
        date = current_datetime.strftime('%Y-%m-%d')  # Get current date
        end_time = current_datetime.strftime('%H:%M:%S.%f')  # Get current time
        stim_name = self.current_stim_number
        trial_data = [date, self.start_time, end_time, self.current_mouse.id, self.current_mouse.level, self.current_value,self.current_stim_index,stim_name, self.score , self.licks_time]
        with open(txt_file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Check if the file is empty to write the header
            if file.tell() == 0:  # Check if the file is empty
                writer.writerow(header)  # Write the header
            writer.writerow(trial_data)



