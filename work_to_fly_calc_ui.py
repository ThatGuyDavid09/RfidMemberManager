import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from tkinter import ttk
from datetime import date, datetime, timedelta
import pandas as pd

from PIL import Image

from ConfigHandler import ConfigHandler

"""
Takes the following format as member_info
{
  "name": "John Cena",
  "days": (
    {
      "day": date,
      "times": (
        (start, end),
        (start, "NTBM")
      ),...
    }
  ),...
}
"""
example_member = {
    "name": "John Cena",
    "days": (
        {
            "day": date(2023, 10, 1),
            "times": (
                (datetime(2023, 10, 1, 8), datetime(2023, 10, 1, 10)),
                (datetime(2023, 10, 1, 12), "NTBM")
            )
        },
        {
            "day": date(2023, 10, 2),
            "times": (
                (datetime(2023, 10, 1, 7), datetime(2023, 10, 1, 9)),
                (datetime(2023, 10, 1, 14), "NTBM")
            )
        }
    )
}
def add_member_to_treeview(member_info):
    top_level_id = member_info["name"].lower().replace(" ", "_")
    members_treeview.insert("", "end", top_level_id, values=[member_info["name"]])
    for day in member_info["days"]:
        day_id = top_level_id + f"_{day["day"].strftime(r"%d%m%y")}"
        members_treeview.insert(top_level_id, "end", day_id, values=[day["day"].strftime(r"%m/%d/%y")])
        for start, end in day["times"]:
            time_id = day_id + f"_{start.strftime(r"%H%M%S")}"
            duration = None if type(end) == str else end - start
            duration_hours = None if duration is None else round(duration.total_seconds() / 3600)
            dur_text = "" if duration is None else f": {duration_hours} hours * ${dollars_per_hour} = ${duration_hours * dollars_per_hour}"
            text = f"{start.strftime(r"%H:%M:%S")} - {"NTBM" if duration is None else end.strftime(r"%H:%M:%S")}" + dur_text
            members_treeview.insert(day_id, "end", time_id, values=[text])

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

# TODO fix this, indentation no worky
style = ttk.Style()
style.configure("Treeview",  indent=100)

members_treeview = ttk.Treeview(root, height=20, columns=("log_time"))
members_treeview.heading("log_time", text=f"Logs since {last_log_time_processed.strftime(r"%m/%d/%y")}")
members_treeview.column("log_time", width=400, stretch=tk.YES)
# members_treeview.insert('', 'end', '1234', text='Widget Tour')
# members_treeview.insert("widgets", 'end', 'widgets2', text='child')
members_treeview.pack(pady=10)

warnings_treeview = ttk.Treeview(root, height=5)
warnings_treeview.pack(pady=10)

add_member_to_treeview(example_member)

root.mainloop()