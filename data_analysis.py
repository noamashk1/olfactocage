
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats import norm

def calculate_d_prime(hits, fas, misses, crs):
    hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
    fa_rate = fas / (fas + crs) if (fas + crs) > 0 else 0
    hit_rate = min(max(hit_rate, 0.01), 0.99)
    fa_rate = min(max(fa_rate, 0.01), 0.99)
    z_hit = norm.ppf(hit_rate)
    z_fa = norm.ppf(fa_rate)
    return z_hit - z_fa

class DataAnalysis:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Data Viewer")
        self.root.geometry("300x250")
        self.df = None

        self.load_button = tk.Button(root, text="Load txt", command=self.load_txt)
        self.load_button.pack(pady=(20, 10))

        self.mouse_id_label = tk.Label(root, text="Select Mouse ID:")
        self.mouse_id_label.pack()
        self.mouse_id_combobox = ttk.Combobox(root, state="readonly")
        self.mouse_id_combobox.pack()

        # קלטים לחלון ו-overlap
        self.window_size_label = tk.Label(root, text="Window Size:")
        self.window_size_label.pack()
        self.window_size_entry = tk.Entry(root)
        self.window_size_entry.insert(0, "70")
        self.window_size_entry.pack()

        self.overlap_label = tk.Label(root, text="Overlap:")
        self.overlap_label.pack()
        self.overlap_entry = tk.Entry(root)
        self.overlap_entry.insert(0, "30")
        self.overlap_entry.pack()

        self.graph_button = tk.Button(root, text="Graph", command=self.open_graph_window)
        self.graph_button.pack(pady=10)

    def load_txt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        self.df = pd.read_csv(file_path, sep=',')
        self.df['mouse ID'] = self.df['mouse ID'].astype(str).str.strip()
        self.df['score'] = self.df['score'].astype(str).str.upper()

        unique_ids = sorted(self.df['mouse ID'].unique())
        self.mouse_id_combobox['values'] = unique_ids
        if unique_ids:
            self.mouse_id_combobox.set(unique_ids[0])

    def open_graph_window(self):
        if self.df is None:
            return

        selected_id = self.mouse_id_combobox.get().strip()
        if not selected_id:
            return

        try:
            window_size = int(self.window_size_entry.get())
            overlap = int(self.overlap_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid integers for window size and overlap.")
            return

        if window_size <= 0 or overlap < 0:
            messagebox.showerror("Input Error", "Window size must be > 0 and overlap must be ≥ 0.")
            return

        if overlap >= window_size:
            messagebox.showerror("Input Error", "Overlap must be smaller than window size.")
            return

        stride = window_size - overlap

        mouse_data = self.df[self.df['mouse ID'] == selected_id]
        if mouse_data.empty:
            messagebox.showwarning("Warning", f"No data found for Mouse ID: {selected_id}")
            return

        if window_size > len(mouse_data):
            messagebox.showerror("Input Error", f"Window size ({window_size}) is larger than number of trials ({len(mouse_data)}).")
            return

        new_window = tk.Toplevel(self.root)
        new_window.title(f"Graphs for Mouse {selected_id}")

        score_counts = mouse_data['score'].value_counts().reindex(['HIT', 'FA', 'MISS', 'CR'], fill_value=0)

        fig, axs = plt.subplots(2, 1, figsize=(8, 8))
        fig.tight_layout(pad=3.0)

        # גרף עמודות
        axs[0].bar(score_counts.index, score_counts.values, color='skyblue')
        axs[0].set_title(f"Score Distribution for Mouse {selected_id}")
        axs[0].set_ylabel("Count")

        # d-prime
        d_prime_values = []
        trial_indices = []

        for start in range(0, len(mouse_data) - window_size + 1, stride):
            window = mouse_data.iloc[start:start + window_size]
            hits = (window['score'] == 'HIT').sum()
            fas = (window['score'] == 'FA').sum()
            misses = (window['score'] == 'MISS').sum()
            crs = (window['score'] == 'CR').sum()
            d_prime = calculate_d_prime(hits, fas, misses, crs)
            d_prime_values.append(d_prime)
            trial_indices.append(start + window_size)

        axs[1].plot(trial_indices, d_prime_values, marker='o', linestyle='-', color='green')
        axs[1].set_title("d-prime Over Time (overlapping windows)")
        axs[1].set_xlabel("Trial Index")
        axs[1].set_ylabel("d-prime")
        axs[1].set_xticks(trial_indices)

        canvas = FigureCanvasTkAgg(fig, master=new_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MouseDataGUI(root)
    root.mainloop()
# import tkinter as tk
# from tkinter import ttk, filedialog
# import pandas as pd
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import numpy as np
# from scipy.stats import norm
#
# ####################### add this to GIU_sections
#
# # import tkinter as tk
# # from data_analysis import MouseDataGUI
# #
# # def open_data_analysis_window(self):
# #     analysis_root = tk.Toplevel()
# #     MouseDataGUI(analysis_root)
# #
# # self.btnDataAnalysis = tk.Button(self.left_frame_bottom, text="Data Analysis",
# #                                  command=self.open_data_analysis_window)
# # self.btnDataAnalysis.grid(row=0, column=1, padx=10, pady=10)
#
# ##########################
# def calculate_d_prime(hits, fas, misses, crs):
#     hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
#     fa_rate = fas / (fas + crs) if (fas + crs) > 0 else 0
#     hit_rate = min(max(hit_rate, 0.01), 0.99)
#     fa_rate = min(max(fa_rate, 0.01), 0.99)
#     z_hit = norm.ppf(hit_rate)
#     z_fa = norm.ppf(fa_rate)
#     return z_hit - z_fa
#
#
# class MouseDataGUI:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Mouse Data Viewer")
#         self.root.geometry("300x100")
#         self.df = None
#
#         self.load_button = tk.Button(root, text="Load txt", command=self.load_txt)
#         self.load_button.pack()
#
#         self.mouse_id_label = tk.Label(root, text="Select Mouse ID:")
#         self.mouse_id_label.pack()
#         self.mouse_id_combobox = ttk.Combobox(root, state="readonly")
#         self.mouse_id_combobox.pack()
#
#         self.graph_button = tk.Button(root, text="Graph", command=self.open_graph_window)
#         self.graph_button.pack()
#
#     def load_txt(self):
#         file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
#         if not file_path:
#             return
#
#         self.df = pd.read_csv(file_path, sep=',')
#
#         # ניקוי רווחים ומעבר לאותיות גדולות
#         self.df['mouse ID'] = self.df['mouse ID'].astype(str).str.strip()
#         self.df['score'] = self.df['score'].astype(str).str.upper()
#
#         unique_ids = sorted(self.df['mouse ID'].unique())
#         self.mouse_id_combobox['values'] = unique_ids
#         if unique_ids:
#             self.mouse_id_combobox.set(unique_ids[0])
#
#     def open_graph_window(self):
#         if self.df is None:
#             return
#
#         selected_id = self.mouse_id_combobox.get().strip()
#         if not selected_id:
#             return
#
#         # סינון בטוח של העכבר
#         mouse_data = self.df[self.df['mouse ID'] == selected_id]
#         if mouse_data.empty:
#             tk.messagebox.showwarning("Warning", f"No data found for Mouse ID: {selected_id}")
#             return
#
#         new_window = tk.Toplevel(self.root)
#         new_window.title(f"Graphs for Mouse {selected_id}")
#
#         score_counts = mouse_data['score'].value_counts().reindex(['HIT', 'FA', 'MISS', 'CR'], fill_value=0)
#
#         fig, axs = plt.subplots(2, 1, figsize=(8, 8))
#         fig.tight_layout(pad=3.0)
#
#         # גרף עמודות
#         axs[0].bar(score_counts.index, score_counts.values, color='skyblue')
#         axs[0].set_title(f"Score Distribution for Mouse {selected_id}")
#         axs[0].set_ylabel("Count")
#
#         # d-prime
#         window_size = 70
#         stride = 15k
#         d_prime_values = []
#         trial_indices = []
#
#         for start in range(0, len(mouse_data) - window_size + 1, stride):
#             window = mouse_data.iloc[start:start + window_size]
#             hits = (window['score'] == 'HIT').sum()
#             fas = (window['score'] == 'FA').sum()
#             misses = (window['score'] == 'MISS').sum()
#             crs = (window['score'] == 'CR').sum()
#             d_prime = calculate_d_prime(hits, fas, misses, crs)
#             d_prime_values.append(d_prime)
#             trial_indices.append(start + window_size)
#
#         axs[1].plot(trial_indices, d_prime_values, marker='o', linestyle='-', color='green')
#         axs[1].set_title("d-prime Over Time (overlapping windows)")
#         axs[1].set_xlabel("Trial Index")
#         axs[1].set_ylabel("d-prime")
#         axs[1].set_xticks(trial_indices)
#
#         canvas = FigureCanvasTkAgg(fig, master=new_window)
#         canvas.draw()
#         canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
#
#
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = MouseDataGUI(root)
#     root.mainloop()

# import tkinter as tk
# from tkinter import ttk, filedialog
# import pandas as pd
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import numpy as np
# from scipy.stats import norm
# 
# ####################### add this to GIU_sections
# 
# # import tkinter as tk
# # from data_analysis import DataAnalysis
# #
# # def open_data_analysis_window(self):
# #     analysis_root = tk.Toplevel()
# #     DataAnalysis(analysis_root)
# #
# # self.btnDataAnalysis = tk.Button(self.left_frame_bottom, text="Data Analysis",
# #                                  command=self.open_data_analysis_window)
# # self.btnDataAnalysis.grid(row=0, column=1, padx=10, pady=10)
# 
# ##########################
# def calculate_d_prime(hits, fas, misses, crs):
#     hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
#     fa_rate = fas / (fas + crs) if (fas + crs) > 0 else 0
#     hit_rate = min(max(hit_rate, 0.01), 0.99)
#     fa_rate = min(max(fa_rate, 0.01), 0.99)
#     z_hit = norm.ppf(hit_rate)
#     z_fa = norm.ppf(fa_rate)
#     return z_hit - z_fa
# 
# 
# class DataAnalysis:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Mouse Data Viewer")
#         self.root.geometry("300x100")
#         self.df = None
# 
#         self.load_button = tk.Button(root, text="Load txt", command=self.load_txt)
#         self.load_button.pack()
# 
#         self.mouse_id_label = tk.Label(root, text="Select Mouse ID:")
#         self.mouse_id_label.pack()
#         self.mouse_id_combobox = ttk.Combobox(root, state="readonly")
#         self.mouse_id_combobox.pack()
# 
#         self.graph_button = tk.Button(root, text="Graph", command=self.open_graph_window)
#         self.graph_button.pack()
# 
#     def load_txt(self):
#         file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
#         if not file_path:
#             return
# 
#         self.df = pd.read_csv(file_path, sep=',')
# 
#         # ניקוי רווחים ומעבר לאותיות גדולות
#         self.df['mouse ID'] = self.df['mouse ID'].astype(str).str.strip()
#         self.df['score'] = self.df['score'].astype(str).str.upper()
# 
#         unique_ids = sorted(self.df['mouse ID'].unique())
#         self.mouse_id_combobox['values'] = unique_ids
#         if unique_ids:
#             self.mouse_id_combobox.set(unique_ids[0])
# 
#     def open_graph_window(self):
#         if self.df is None:
#             return
# 
#         selected_id = self.mouse_id_combobox.get().strip()
#         if not selected_id:
#             return
# 
#         # סינון בטוח של העכבר
#         mouse_data = self.df[self.df['mouse ID'] == selected_id]
#         if mouse_data.empty:
#             tk.messagebox.showwarning("Warning", f"No data found for Mouse ID: {selected_id}")
#             return
# 
#         new_window = tk.Toplevel(self.root)
#         new_window.title(f"Graphs for Mouse {selected_id}")
# 
#         score_counts = mouse_data['score'].value_counts().reindex(['HIT', 'FA', 'MISS', 'CR'], fill_value=0)
# 
#         fig, axs = plt.subplots(2, 1, figsize=(8, 8))
#         fig.tight_layout(pad=3.0)
# 
#         # גרף עמודות
#         axs[0].bar(score_counts.index, score_counts.values, color='skyblue')
#         axs[0].set_title(f"Score Distribution for Mouse {selected_id}")
#         axs[0].set_ylabel("Count")
# 
#         # d-prime
#         window_size = 20
#         stride = 5
#         d_prime_values = []
#         trial_indices = []
# 
#         for start in range(0, len(mouse_data) - window_size + 1, stride):
#             window = mouse_data.iloc[start:start + window_size]
#             hits = (window['score'] == 'HIT').sum()
#             fas = (window['score'] == 'FA').sum()
#             misses = (window['score'] == 'MISS').sum()
#             crs = (window['score'] == 'CR').sum()
#             d_prime = calculate_d_prime(hits, fas, misses, crs)
#             d_prime_values.append(d_prime)
#             trial_indices.append(start + window_size)
# 
#         axs[1].plot(trial_indices, d_prime_values, marker='o', linestyle='-', color='green')
#         axs[1].set_title("d-prime Over Time (overlapping windows)")
#         axs[1].set_xlabel("Trial Index")
#         axs[1].set_ylabel("d-prime")
#         axs[1].set_xticks(trial_indices)
# 
#         canvas = FigureCanvasTkAgg(fig, master=new_window)
#         canvas.draw()
#         canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
# 
# 
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = DataAnalysis(root)
#     root.mainloop()
# 