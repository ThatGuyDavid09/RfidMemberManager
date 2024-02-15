import os
import string
import sys
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

def get_display_text_and_hours(seconds):
    if seconds is None:
        return "NTBM", 0

    hours = round(seconds / 3600)
    if hours > 0:
        return (f"{hours} hour" + ("" if hours == 1 else "s")), hours
    else:
        minutes = round(seconds / 60)
        return (f"{minutes} minute" + ("" if minutes == 1 else "s")), 0

def add_member_to_treeview(member_info):
    """
    Takes a member_info object, in the format described below, and adds it into the members_treeview.

    Takes the following format as member_info
    {
    "name": "John Cena",
    "days": (
        {
        "day": date,
        "times": (
            (start, end)|(start, "NTBM"),
            ...
        ),...
        }
    ),...
    "duration": (dur_hours, is_adjusted)
    }
    """
    # IDs are for setting children in treeview
    top_level_id = member_info["name"].lower().replace(" ", "_")
    members_treeview.insert("", "end", top_level_id, text=string.capwords(member_info["name"]))
    total_duration_hours = 0

    for day in member_info["days"]:
        day_id = top_level_id + f"_{day["day"].strftime(r"%d%m%y")}"

        # This is for display only, and reads 0 if less than 30 mins of work was performed that day. Actual duration is
        # only rounded at the very end of processing
        seconds_for_day = sum(
            [(time[1] - time[0]).total_seconds() for time in day["times"] if time[1] != "NTBM"])
        time_text, hours = get_display_text_and_hours(seconds_for_day)
        # Format example: 11/12/23 - 3 hours * $16 = $48 
        day_text = f"{day["day"].strftime(r"%m/%d/%y")} - {time_text} * ${dollars_per_hour} = ${hours * dollars_per_hour}"

        members_treeview.insert(top_level_id, "end", day_id, text=day_text)
        for start, end in day["times"]:
            time_id = day_id + f"_{start.strftime(r"%H%M%S")}"
            duration = None if end == "NTBM" else end - start
            duration_seconds = None if duration is None else duration.total_seconds()
            time_text, duration_hours = get_display_text_and_hours(duration_seconds)
            dur_text = "" if duration is None else f" | {time_text} * ${dollars_per_hour} = ${duration_hours * dollars_per_hour}"
            
            # Format example: 10:23:12 - 11:52:53: 2 hours * $16 = $32
            # If NTBM: 10:23:12 - NTBM
            text = f"{start.strftime(r"%H:%M:%S")} - {"NTBM" if duration is None else end.strftime(r"%H:%M:%S")}" + dur_text
            members_treeview.insert(day_id, "end", time_id, text=text)
    
    duration_id = top_level_id + "_total_dur"
    total_duration_hours = member_info["duration"][0]
    # Whether the duration was adjusted b/c of max hours is set in the member object, so we don't have to compute it here
    if member_info["duration"][1]:
        members_treeview.insert(top_level_id, "end", duration_id + "1",
                                text=f"More than max hours! Adjusted")
        # Format example: Total: 3 hours * $16 = $48
        members_treeview.insert(top_level_id, "end", duration_id + "2",
                                text=f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}")
    else:
        members_treeview.insert(top_level_id, "end", duration_id,
                                text=f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}")


def process_day_for_member(sorted_logins_df, last_time, member_name_lower):
    """
    Given a date and member name, processes all logins for that member on that date
    sorted_logins_df: The dataframe of logins, already sorted by login_time
    last_time: The time to start searching from. This method will search 1 day from last_time
    member_name_lower: The member to search for, all lowercase. (Ex: john cena)
    """
    logged_times = []
    warnings = []

    day_struct = {
        "day": last_time,
        "times": []
    }

    if sorted_logins_df.empty:
        return timedelta(0), day_struct, warnings

    start_time = None

    for _, row in sorted_logins_df.iterrows():
        if not start_time:
            start_time = row.login_time
        else:
            logged_time = [start_time, row.login_time, row.login_time - start_time]
            logged_times.append(logged_time)
            # Reset to none so we know it was matched with an end time
            start_time = None

    # If we have a leftover login that was not matched with an ending time
    if start_time:
        logged_time = [start_time, "NTBM", -1]
        logged_times.append(logged_time)

    duration_this_day = pd.Timedelta(0)
    for time_segment in logged_times:
        duration_this_day += time_segment[2] if time_segment[2] != -1 else pd.Timedelta(0)
        day_struct["times"].append(time_segment[:2])

    # This is for warning calculation only. Actual duration is only tallied at the end of processing
    duration_this_day = timedelta(hours=round(duration_this_day.total_seconds() / 3600))

    if duration_this_day > timedelta(hours=8):
        warnings.append([member_name_lower, f"{last_time.strftime("%m/%d/%y")} - More than 8 hours in one day"])

    return duration_this_day, day_struct, warnings


def get_only_current_data(data_df):
    """
    Returns a dataframe with all logins before the specified log time processed time removed.
    """
    data_df = data_df.loc[
        (data_df["login_time"] >= pd.to_datetime(last_log_time_processed))]
    return data_df


def process_member(member_df, member_name_lower):
    """
    Processes all logs in the provided dataframe on the given member.
    member_df: The dataframe to search in. Not required to be sorted.
    member_name_lower: The member to process, all lowercase. (Ex: john cena)
    """
    member_structure = {
        "name": member_name_lower,
        "days": [],
        "duration": []
    }

    warnings = []
    last_time = pd.to_datetime(last_log_time_processed)
    total_member_duration = pd.Timedelta(0)

    while last_time < datetime.now():
        # Get all logins withinone day from last_time
        member_df_time_sorted = member_df.loc[
            (member_df.login_time > last_time) & (member_df.login_time <= last_time + timedelta(1))]
        member_df_time_sorted = member_df_time_sorted.sort_values(by="login_time", ascending=True)

        dur_to_add, day_struct, warning_member = process_day_for_member(member_df_time_sorted, last_time,
                                                                                   member_name_lower)
        last_time += timedelta(1)
        warnings.extend(warning_member)

        # Do not add day if no logins were found
        if day_struct["times"]:
            member_structure["days"].append(day_struct)
        total_member_duration += dur_to_add

    # Calculate weeks since last_log_time_processed to low (we use last_time since it rounds to the day) and
    # calculate max_hours based on user setting of max hours per week
    weeks_duration = ((last_time - timedelta(1)) - last_log_time_processed).to_pytimedelta().days / 7
    max_hours = timedelta(hours=(weeks_duration * max_hrs_7_days) // 1)

    if total_member_duration > max_hours:
        warnings.append([member_name_lower, f"Exceeded max allowed hours for duration, reduced"])
        # We set second element of the list to True to let other methods know we have modified the date
        member_structure["duration"] = [int(max_hours.total_seconds() // 3600), True]
    else:
        member_structure["duration"] = [int(total_member_duration.total_seconds() // 3600), False]
    return member_structure, warnings


def check_member_tree_populated():
    """
    Checks whether the members tree is populated, and if not, adds an entry saying no logs found.
    """
    if not members_treeview.get_children():
        members_treeview.insert("", "end", text="No logs found for this timeframe!")


def populate_warnings_tree(warnings):
    """
    Adds all provided warnings into the warning treeview.
    """
    for warning in warnings:
        # Format example: WARNING: Member 1 had more than 8 hours
        warnings_treeview.insert("", "end", text=f"{string.capwords(warning[0])}: {warning[1]}")


def process_all(data_df):
    """
    Clears UI, processes all data, and makes sure UI is correctly populated.
    """
    global all_members

    clear_tree(members_treeview)
    clear_tree(warnings_treeview)
    warnings, members = process_data(data_df)
    check_member_tree_populated()
    populate_warnings_tree(warnings)

    all_members = members


def process_data(data_df):
    """
    Processes all members and adds them to UI.
    """
    warnings = []
    all_members = []

    data_df = get_only_current_data(data_df)

    for member_name_lower in data_df.name_lower.unique():
        member_df = data_df[data_df.name_lower == member_name_lower]
        member_structure, warning_member = process_member(member_df, member_name_lower)
        all_members.append(member_structure)
        warnings.extend(warning_member)
        add_member_to_treeview(member_structure)
    return warnings, all_members


def clear_tree(tree):
    """
    Removes all elements in a given treeview.
    """
    tree.delete(*tree.get_children())


def preprocess_data(df):
    """
    Removes unknown logins or logins with the wrong reason from provided df, and converts login_time column to 
    a pandas datetime object.
    """
    global preprocessed_data_df

    df.drop(df[df["name_lower"] == "unknown"].index, inplace=True)
    df.drop(df[df["login_reason"] != login_type_tag_to_search].index, inplace=True)
    df["login_time"] = pd.to_datetime(df["login_time"])
    preprocessed_data_df = df
    return df


def fetch_and_process_file():
    """
    Prompts the user to select a file, sets up UI based on selection, reads data from file, and processes it.
    """
    file_path = browse_files()
    process_file(file_path)


def process_file(file_path):
    # If user does not select a file, this prevents an error
    try:
        members_df = pd.read_csv(file_path)
    except PermissionError:
        return

    setup_member_treeview_heading()
    members_df = preprocess_data(members_df)
    process_all(members_df)


def browse_files():
    """
    Opens a file dialog allowing the user to select a CSV file they want, and returns a path object pointing to that file.
    """
    filename = tk.filedialog.askopenfilename(initialdir="./", title="Select a File",
                                             filetypes=(("CSV Files", "*.csv"),))
    file_path = Path(filename)
    file_button.configure(text=f"Selected file: {file_path.name}")
    return file_path
    # print(filename)


def init_config():
    """
    Loads configuration variables from file and sets them in global variables.
    """
    global flight_circle_api_key, last_log_time_processed, max_hrs_7_days, dollars_per_hour, login_type_tag_to_search

    config = ConfigHandler()
    last_log_time_processed = (config.get_config_element("DEFAULT/LastLogTimeProcessed"))
    max_hrs_7_days = int(config.get_config_element("DEFAULT/MaxHoursPerWeek"))
    dollars_per_hour = int(config.get_config_element("DEFAULT/DollarsPerHour"))
    login_type_tag_to_search = str(config.get_config_element("DEFAULT/LoginSearchTypeTag")).lower()

    # If last log time is unspecified, sets it to two weeks ago.
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
    """
    Filters and reprocesses already loaded data by provided name. Loads data if not present.
    """
    if preprocessed_data_df is None:
        fetch_and_process_file()

    name_filtered_df = preprocessed_data_df[preprocessed_data_df["name_lower"].str.contains(name.lower())]
    process_all(name_filtered_df)


def member_search_name_update(stringvar):
    """
    Callback for name entry field. Schedules name filtering job for future, and cancels already existing one.
    """
    global member_search_job_id

    if member_search_job_id:
        # We cancel the previous job so we don't constantly reprocess as the user is typing. We will only
        # do the name filtering after .8 seconds of no activity in the name entry field.
        root.after_cancel(member_search_job_id)
    member_search_job_id = root.after(800, lambda name=stringvar.get(): filter_by_member_name(name))


def setup_member_treeview_heading():
    """
    Sets heading of members_treeview based on last log time.
    """
    # Format example: Logs since 11/12/23
    members_treeview.heading("#0", text=f"Logs since {last_log_time_processed.strftime(r"%m/%d/%y")}")


def output_log():
    """
    Outputs a log file based on all_members.
    """
    os.makedirs('credit_logs', exist_ok=True)
    with open(f"credit_logs/credit_log.txt", "a", encoding="utf-8") as f:
        f.write(f"MANUAL Processed \"{login_type_tag_to_search}\" on {datetime.now().strftime(r"%m/%d/%y")}, logs since {last_log_time_processed.strftime(r"%m/%d/%y")}\n")

        for member in all_members:
            f.write(string.capwords(member["name"]) + "\n")
            total_duration_hours = 0
            for day in member["days"]:
                # For display only.
                seconds_for_day = sum(
                    [(time[1] - time[0]).total_seconds() for time in day["times"] if
                     type(time[1]) != str])
                time_text, hours_for_day = get_display_text_and_hours(seconds_for_day)
                day_text = f"{day["day"].strftime(r"%m/%d/%y")} - {time_text} * ${dollars_per_hour} = ${hours_for_day * dollars_per_hour}"
                f.write(" " * 4 + day_text + "\n")

                for start, end in day["times"]:
                    duration = None if end == "NTBM" else end - start
                    duration_seconds = None if duration is None else duration.total_seconds()
                    sub_dur_text, duration_hours = get_display_text_and_hours(duration_seconds)
                    dur_text = "" if duration is None else f": {sub_dur_text} * ${dollars_per_hour} = ${duration_hours * dollars_per_hour}"
                    time_text = f"{start.strftime(r"%H:%M:%S")} - {"NTBM" if duration is None else end.strftime(r"%H:%M:%S")}" + dur_text
                    f.write(" " * 8 + time_text + "\n")
            total_duration_hours = member["duration"][0]
            if member["duration"][1]:
                f.write(" " * 4 + f"More than max hours! Adjusted\n")
                f.write(
                    " " * 4 + f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}\n")
            else:
                f.write(
                    " " * 4 + f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}\n")
        f.write("\n")
        f.write("To credit by member:\n")
        for member in all_members:
            duration = member["duration"][0]
            f.write(
                " " * 4 + f"{string.capwords(member["name"])}: {duration} hours * ${dollars_per_hour} = ${duration * dollars_per_hour}\n")
        f.write("-" * 60 + "\n\n")


def save_last_log():
    # Saves last login time to the config file
    latest_date = pd.to_datetime(preprocessed_data_df["login_time"].max().strftime(r"%m/%d/%y"))
    config.config["DEFAULT"]["LastLogTimeProcessed"] = str(latest_date)
    config.config.write(open("config.ini", "w"))


def open_confirm_window():
    """
    Opens the window with all the hours to credit.
    """
    def close_confirm_window():
        confirm_window.destroy()
        root.destroy()
        sys.exit()

    confirm_window = ctk.CTkToplevel(root)
    confirm_window.title("Confirm")

    ctk.CTkLabel(confirm_window, text="Hours confirmed, log outputted to credit_logs/credit_log.txt").pack(padx=10, pady=10)

    confirm_treevew = ttk.Treeview(confirm_window, height=20)
    confirm_treevew.heading("#0", text="Member payment summary")
    confirm_treevew.column("#0", width=400, stretch=tk.YES)
    confirm_treevew.pack(pady=10, padx=10)

    for member in all_members:
        duration = member["duration"][0]
        confirm_treevew.insert("", "end", text=f"{string.capwords(member["name"])}: {duration} hours * ${dollars_per_hour} = ${duration * dollars_per_hour}")

    ctk.CTkButton(confirm_window, text="OK", width=100, command=close_confirm_window).pack(pady=10)

    confirm_window.protocol("WM_DELETE_WINDOW", close_confirm_window)
    confirm_window.attributes('-topmost', True)
    confirm_window.update()
    confirm_window.attributes('-topmost', False)
    confirm_window.focus()


def confirm():
    """
    Callback for the confirm button. Outputs log, saves time to config, and opens the confirm window.
    """
    output_log()
    save_last_log()
    open_confirm_window()


class OptionsMenu(tk.Tk):
    """
    Allows the user to edit various options without modifying config file.
    """
    def __init__(self):
        super().__init__()

        self.title("Options Menu")

        tk.Label(self, text="Maximum Hours per Week:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.max_hours_per_week = tk.Entry(self)
        self.max_hours_per_week.insert(0, max_hrs_7_days)
        self.max_hours_per_week.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self, text="Earliest Log to Process:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
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


    def save_changes(self):
        """
        Retrieve user settings from the associated entries at set into global variables. Also reprocesses data.
        """
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
all_members = []

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

confirm_button = ctk.CTkButton(button_frame, text="Confirm", width=100, command=confirm)
confirm_button.pack(side=tk.LEFT)

members_treeview = ttk.Treeview(root, height=20)

members_treeview.heading("#0", text="Please select file")
members_treeview.column("#0", width=400, stretch=tk.YES)
members_treeview.pack(pady=10)

warnings_treeview = ttk.Treeview(root, height=5)
warnings_treeview.heading("#0", text="Warnings")
warnings_treeview.column("#0", width=400, stretch=tk.YES)
warnings_treeview.pack(pady=10)

# By default, select login_log
process_file("data/login_log.csv")
file_button.configure(text=f"Selected file: login_log.csv")

root.mainloop()
