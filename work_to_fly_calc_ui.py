import string
import tkinter as tk
import tkcalendar
from tkinter import simpledialog
import customtkinter as ctk
from pathlib import Path
from tkinter import ttk
from datetime import date, datetime, timedelta
import pandas as pd

from PIL import Image

from ConfigHandler import ConfigHandler

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
                (datetime(2023, 10, 1, 7), datetime(2023, 10, 1, 10)),
                (datetime(2023, 10, 1, 14), "NTBM")
            )
        }
    )
}
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
  "duration": (dur_hours, adjusted (T/F))
}
"""
def add_member_to_treeview(member_info):
    top_level_id = member_info["name"].lower().replace(" ", "_")
    members_treeview.insert("", "end", top_level_id, text=string.capwords(member_info["name"]))
    total_duration_hours = 0
    for day in member_info["days"]:
        day_id = top_level_id + f"_{day["day"].strftime(r"%d%m%y")}"

        hours_for_day = sum([round((time[1] - time[0]).total_seconds() / 3600) for time in day["times"] if type(time[1]) != str])
        day_text = f"{day["day"].strftime(r"%m/%d/%y")} - {hours_for_day} hours * ${dollars_per_hour} = ${hours_for_day * dollars_per_hour}"

        members_treeview.insert(top_level_id, "end", day_id, text=day_text)
        for start, end in day["times"]:
            time_id = day_id + f"_{start.strftime(r"%H%M%S")}"
            duration = None if type(end) == str else end - start
            duration_hours = None if duration is None else round(duration.total_seconds() / 3600)
            # total_duration_hours += duration_hours if duration_hours else 0
            dur_text = "" if duration is None else f": {duration_hours} hours * ${dollars_per_hour} = ${duration_hours * dollars_per_hour}"
            text = f"{start.strftime(r"%H:%M:%S")} - {"NTBM" if duration is None else end.strftime(r"%H:%M:%S")}" + dur_text
            members_treeview.insert(day_id, "end", time_id, text=text)
    duration_id = top_level_id + "_total_dur"
    total_duration_hours = member_info["duration"][0]
    if member_info["duration"][1]:
        members_treeview.insert(top_level_id, "end", duration_id + "1",
                                text=f"More than max hours! Adjusted")
        members_treeview.insert(top_level_id, "end", duration_id + "2",
                                text=f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}")
    else:
        members_treeview.insert(top_level_id, "end", duration_id,
                                text=f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}")


def process_day_for_member(sorted_logins_df, last_time, member_name_lower):
    logged_times = []
    warnings = []

    day_struct = {
        "day": last_time,
        "times": []
    }
    
    if sorted_logins_df.empty:
        last_time = last_time + timedelta(1)
        return last_time, timedelta(0), day_struct, warnings

    start_time = None
    # member_df_time_sorted.sort_values(by="login_time", ascending=True)
    # print(member_df_time_sorted.login_time.dtype)
    # print(member_df_time_sorted)
    # if not log:
    #     print(f"  Logs on {last_time.date()}")
    # else:
    #     with open(log_file, "a", encoding="utf-8") as f:
    #         f.write(f"  Logs on {last_time.date()}\n")

    for _, row in sorted_logins_df.iterrows():
        if not start_time:
            start_time = row.login_time
        else:
            logged_time = [start_time, row.login_time, row.login_time - start_time]
            logged_times.append(logged_time)
            start_time = None

    if start_time:
        logged_time = [start_time, "NTBM", -1]
        logged_times.append(logged_time)

    # pprint(logged_times)
    duration_this_day = pd.Timedelta(0)
    for time_segment in logged_times:
        duration_this_day += time_segment[2] if time_segment[2] != -1 else pd.Timedelta(0)
        day_struct["times"].append(time_segment[:2])

        # duration_str = f": duration {time_segment[2].to_pytimedelta()}" if time_segment[2] != -1 else ""
        # if not log:
        #     print(f"    {str(time_segment[0]).split()[-1]} - {str(time_segment[1]).split()[-1]}{duration_str}")
        # else:
        #     with open(log_file, "a", encoding="utf-8") as f:
        #         f.write(f"    {str(time_segment[0]).split()[-1]} - {str(time_segment[1]).split()[-1]}{duration_str}\n")
    # total_member_duration += duration_this_day

    duration_this_day = timedelta(hours=round(duration_this_day.total_seconds() / 3600))

    if duration_this_day > timedelta(hours=8):
        warnings.append([member_name_lower, "More than 8 hours in one day"])
    # print(f"    Total duration this day: {duration_this_day.to_pytimedelta()}")

    last_time = last_time + timedelta(1)
    return last_time, duration_this_day, day_struct, warnings


def get_only_current_data(data_df):
    data_df = data_df.loc[
        (data_df["login_time"] >= pd.to_datetime(last_log_time_processed))]
    return data_df


def process_member(member_df, member_name_lower):
    member_structure = {
        "name": member_name_lower,
        "days": [],
        "duration": []
    }

    warnings = []

    last_time = pd.to_datetime(last_log_time_processed)

    total_member_duration = pd.Timedelta(0)

    while last_time < datetime.now():
        member_df_time_sorted = member_df.loc[
            (member_df.login_time > last_time) & (member_df.login_time <= last_time + timedelta(1))]
        member_df_time_sorted = member_df_time_sorted.sort_values(by="login_time", ascending=True)

        last_time, dur_to_add, day_struct, warning_member = process_day_for_member(member_df_time_sorted, last_time, member_name_lower)
        warnings.extend(warning_member)
        if day_struct["times"]:
            member_structure["days"].append(day_struct)
        total_member_duration += dur_to_add

    weeks_duration = ((last_time - timedelta(1)) - last_log_time_processed).to_pytimedelta().days / 7
    max_hours = timedelta(hours=(weeks_duration * max_hrs_7_days) // 1)

    if total_member_duration > max_hours:
        warnings.append([member_name_lower, f"Exceeded max allowed hours for duration, reduced"])
        # print(f"Duration > max, adjusted duration: {max_hours}")
        member_structure["duration"] = [int(max_hours.total_seconds() // 3600), True]
    else:
        member_structure["duration"] = [int(total_member_duration.total_seconds() // 3600), False]
    return member_structure, warnings

    # total_dur_mem_string = f"  Total duration this member: {total_member_duration}"
    # if not log:
    #     print(total_dur_mem_string)
    #
    #     if total_member_duration > max_hours:
    #         warning_members.append([member_name_lower, f"Exceeded max allowed hours for duration, reduced"])
    #         print(f"Duration > max, adjusted duration: {max_hours}")
    #         member_durations.append([member_name_lower, max_hours])
    #     else:
    #         member_durations.append([member_name_lower, total_member_duration])
    # else:
    #     with open(log_file, "a", encoding="utf-8") as f:
    #         f.write(total_dur_mem_string + "\n")
    #         if total_member_duration > max_hours:
    #             total_member_duration = max_hours
    #             f.write(f"Duration > max, adjusted duration: {max_hours}\n")
    #
    #         final_dur = timedelta(0)
    #         for name, dur in member_durations:
    #             if name == member_name_lower:
    #                 final_dur = dur
    #                 if dur != total_member_duration:
    #                     f.write(f"Duration manually adjusted, final {dur}\n")
    #         f.write(f"Credited ${calculate_to_credit(final_dur)}\n")
    #
    # if not log:
    #     print("-" * len(total_dur_mem_string))
    # else:
    #     with open(log_file, "a", encoding="utf-8") as f:
    #         f.write("-" * len(total_dur_mem_string) + "\n")


def check_member_tree_populated():
    if not members_treeview.get_children():
        members_treeview.insert("", "end", text="No logs found for this timeframe!")


def process_data(data_df):
    warnings = []
    all_members = []

    data_df = get_only_current_data(data_df)

    clear_member_tree()

    for member_name_lower in data_df.name_lower.unique():
        member_df = data_df[data_df.name_lower == member_name_lower]
        member_structure, warning_member = process_member(member_df, member_name_lower)
        all_members.append(member_structure)
        warnings.extend(warning_member)
        add_member_to_treeview(member_structure)
    check_member_tree_populated()


def clear_member_tree():
    members_treeview.delete(*members_treeview.get_children())


def preprocess_data(df):
    global preprocessed_data_df

    df.drop(df[df["name_lower"] == "unknown"].index, inplace=True)
    df.drop(df[df["login_reason"] != login_type_tag_to_search].index, inplace=True)
    df["login_time"] = pd.to_datetime(df["login_time"])
    preprocessed_data_df = df
    return df


def fetch_and_process_file():
    file_path = browse_files()
    setup_member_treeview_heading()
    members_df = pd.read_csv(file_path)
    members_df = preprocess_data(members_df)
    process_data(members_df)


def browse_files():
    filename = tk.filedialog.askopenfilename(initialdir="./", title="Select a File",
                                             filetypes=(("CSV Files", "*.csv"),))
    file_path = Path(filename)
    file_button.configure(text=f"Selected file: {file_path.name}")
    return file_path
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

member_search_job_id = None
member_search_last_update = datetime.now()
def filter_by_member_name(name=""):
    if preprocessed_data_df is None:
        fetch_and_process_file()
    
    clear_member_tree()
    name_filtered_df = preprocessed_data_df[preprocessed_data_df["name_lower"].str.contains(name.lower())]
    process_data(name_filtered_df)        


def member_search_name_update(stringvar):
    global member_search_job_id

    if member_search_job_id:
        root.after_cancel(member_search_job_id)
    member_search_job_id = root.after(800, lambda name=stringvar.get(): filter_by_member_name(name))        


def setup_member_treeview_heading():
    members_treeview.heading("#0", text=f"Logs since {last_log_time_processed.strftime(r"%m/%d/%y")}")


class OptionsMenu(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Options Menu")

        tk.Label(self, text="Maximum Hours per Week:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.max_hours_per_week = tk.Entry(self)
        self.max_hours_per_week.insert(0, max_hrs_7_days)
        self.max_hours_per_week.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self, text="Earliest Log to Process:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        # tk.Button(self, text="Select Date", command=self.select_date).grid(row=1, column=1, padx=10, pady=5)
        self.earliest_log_date = tkcalendar.DateEntry(self, selectmode='day', 
                                                      year=last_log_time_processed.year,
                                                      month=last_log_time_processed.month,
                                                      day=last_log_time_processed.day)
        self.earliest_log_date.grid(row=1, column=1, padx=10, pady=5)
        # tk.Entry(self, text="Select Date", date=True)

        tk.Label(self, text="Dollars per Hour:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.dollars_per_hour = tk.Entry(self)
        self.dollars_per_hour.insert(0, dollars_per_hour)
        self.dollars_per_hour.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(self, text="Confirm", command=self.save_changes).grid(row=3, column=0, columnspan=2, pady=10)

    def select_date(self):
        selected_date = simpledialog.askstring("Select Date", "Choose the earliest log date:")
        self.earliest_log_date.set(selected_date)

    def save_changes(self):
        global max_hrs_7_days, last_log_time_processed, dollars_per_hour

        max_hrs_7_days = int(self.max_hours_per_week.get())
        # Needed to allow proper processing by strptime
        date_str = "/".join([i.zfill(2) for i in self.earliest_log_date.get().split("/")])
        last_log_time_processed = datetime.strptime(date_str, r"%m/%d/%y")
        setup_member_treeview_heading()
        dollars_per_hour = int(self.dollars_per_hour.get())

        filter_by_member_name()

        self.destroy()


last_log_time_processed = None
max_hrs_7_days = None
dollars_per_hour = None
login_type_tag_to_search = None
config = init_config()

preprocessed_data_df = None

ctk.set_appearance_mode("light")
root = ctk.CTk()
root.title("Work to Fly Calculator")

button_frame = ctk.CTkFrame(root)
button_frame.pack(side=tk.TOP, padx=10, pady=10)

file_button = ctk.CTkButton(button_frame, text="Select file", command=fetch_and_process_file)
file_button.pack(side=tk.LEFT, padx=(0, 10))

member_search_sv = ctk.StringVar()
member_search_sv.trace("w", lambda name, index, mode, sv=member_search_sv: member_search_name_update(sv))
member_search_entry = ctk.CTkEntry(button_frame, corner_radius=5,
                                   placeholder_text="Search member",
                                   placeholder_text_color="lightgray",
                                   textvariable=member_search_sv)
member_search_entry.pack(side=tk.LEFT, padx=(0, 10))

options_button = ctk.CTkButton(button_frame, text="Options", width=100, command=OptionsMenu)
options_button.pack(side=tk.LEFT, padx=(0, 10))

confirm_button = ctk.CTkButton(button_frame, text="Confirm", width=100)
confirm_button.pack(side=tk.LEFT)

members_treeview = ttk.Treeview(root, height=20)
# members_treeview.heading("log_time", text=f"Logs since {last_log_time_processed.strftime(r"%m/%d/%y")}")
# members_treeview.column("log_time", width=400, stretch=tk.YES)

members_treeview.heading("#0", text="Please select file")
members_treeview.column("#0", width=400, stretch=tk.YES)
# members_treeview.insert('', 'end', '1234', text='Widget Tour')
# members_treeview.insert("widgets", 'end', 'widgets2', text='child')
members_treeview.pack(pady=10)

warnings_treeview = ttk.Treeview(root, height=5)
warnings_treeview.pack(pady=10)

# add_member_to_treeview(example_member)

root.mainloop()
