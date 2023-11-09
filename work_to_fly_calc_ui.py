import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from tkinter import ttk
from datetime import datetime, timedelta
import pandas as pd

from PIL import Image

from ConfigHandler import ConfigHandler

def browse_files():
    filename = tk.filedialog.askopenfilename(initialdir = "./", title = "Select a File", filetypes = (("CSV Files","*.csv"),))
    file_path = Path(filename)
    file_button.configure(text=f"Selected file: {file_path.name}")
    # print(filename)

def init_config():
    global flight_circle_api_key, last_log_time_processed, max_hrs_7_days, dollars_per_hour, login_type_tag_to_search

    config = ConfigHandler()
    last_log_time_processed = (config.get_config_element("DEFAULT/LastLogTimeProcessed"))
    max_hrs_7_days = int(config.get_config_element("DEFAULT/MaxHoursPerWeek"))
    dollars_per_hour = int(config.get_config_element("DEFAULT/DollarsPerHour"))
    login_type_tag_to_search = str(config.get_config_element("DEFAULT/LoginSearchTypeTag")).lower()

    if last_log_time_processed == "-1":
        last_log_time_processed = datetime.today() - timedelta(14)
        last_log_time_processed = datetime(*last_log_time_processed.timetuple()[:3])
    else:
        last_log_time_processed = pd.to_datetime(last_log_time_processed)
    # print(last_log_time_processed)
    return config

last_log_time_processed = None
max_hrs_7_days = None
dollars_per_hour = None
login_type_tag_to_search = None
config = init_config()

ctk.set_appearance_mode("light")
root = ctk.CTk()
root.title("Work to Fly Calculator")

button_frame = ctk.CTkFrame(root)
button_frame.pack(side=tk.TOP, padx=10, pady=10)

file_button = ctk.CTkButton(button_frame, text="Select file", command=browse_files)
file_button.pack(side=tk.LEFT, padx=(0, 10))

member_search_entry = ctk.CTkEntry(button_frame, corner_radius=5, 
                                   placeholder_text="Search member", 
                                   placeholder_text_color="lightgray")
member_search_entry.pack(side=tk.LEFT, padx=(0, 10))

options_button = ctk.CTkButton(button_frame, text="Options", width=100)
options_button.pack(side=tk.LEFT, padx=(0,10))

confirm_button = ctk.CTkButton(button_frame, text="Confirm", width=100)
confirm_button.pack(side=tk.LEFT)

members_treeview = ttk.Treeview(root, height=20, columns=("log_time"), show="headings")
members_treeview.heading("log_time", text=f"Logs since {last_log_time_processed.strftime(r"%m/%d/%y")}")
# members_treeview.insert('', 'end', 'widgets', text='Widget Tour')
# members_treeview.insert("widgets", 'end', 'widgets2', text='child')
members_treeview.pack(pady=10)

warnings_treeview = ttk.Treeview(root, height=5)
warnings_treeview.pack(pady=10)

root.mainloop()