import configparser
import functools
import os
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint
import time
import csv
import pandas as pd

from ConfigHandler import ConfigHandler

def get_all_logins(login_path):
        logins = pd.read_csv(login_path)
        logins["login_time"] = pd.to_datetime(logins["login_time"])
        return logins

def init_config():
    global flight_circle_api_key, last_log_time_processed, max_hrs_7_days, dollars_per_hour

    config = ConfigHandler()
    flight_circle_api_key = int(config.get_config_element("DEFAULT/FlightCircleApiKey"))
    last_log_time_processed = (config.get_config_element("DEFAULT/LastLogTimeProcessed"))
    max_hrs_7_days = int(config.get_config_element("DEFAULT/MaxHoursPerWeek"))
    dollars_per_hour = int(config.get_config_element("DEFAULT/DollarsPerHour"))

    if last_log_time_processed == "-1":
        last_log_time_processed = datetime.today() - timedelta(14)
        last_log_time_processed = datetime(*last_log_time_processed.timetuple()[:3])
    else:
        last_log_time_processed = pd.to_datetime(last_log_time_processed)
    print(last_log_time_processed)
    return config

flight_circle_api_key = None
last_log_time_processed = None
max_hrs_7_days = None
dollars_per_hour = None
config = init_config()

log_file = ""

login_path = input("Enter login log file path (should be data/something): ")
while not os.path.exists(login_path):
    print("That file doesn't exist!")
    login_path = input("Enter login log file path: ")

filtered_data = get_all_logins(login_path)
print(len(filtered_data))
filtered_data.drop(filtered_data[filtered_data["name_lower"] == "unknown"].index)
filtered_data = filtered_data.loc[
    (filtered_data["login_time"] >= pd.to_datetime(last_log_time_processed))]

warning_members = []
member_durations = []

last_log_time_input = input("Enter earliest day to process (mm/dd/yyyy), or enter to use default: ")
if last_log_time_input:
    while True:
        try:
            last_log_time_processed = datetime.strptime(last_log_time_input, r"%m/%d/%Y")
            break
        except ValueError:
            print("Invalid format!")
            last_log_time_input = input("Enter earliest day to process (mm/dd/yyyy), or enter to use default: ")
print(last_log_time_processed)
print(f"Logs since {last_log_time_processed}")

def calculate_to_credit(duration):
    # Round to nearest hour
    return round((duration.total_seconds() / 3600) * dollars_per_hour)


def process_day_for_member(sorted_logins_df, last_time, member_name_lower, log=False):
    if sorted_logins_df.empty:
        last_time = last_time + timedelta(1)
        return last_time, timedelta(0)
    
    logged_times = []

    start_time = None
    # member_df_time_sorted.sort_values(by="login_time", ascending=True)
    # print(member_df_time_sorted.login_time.dtype)
    # print(member_df_time_sorted)
    if not log:
        print(f"  Logs on {last_time.date()}")
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"  Logs on {last_time.date()}\n")

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
        duration_str = f": duration {time_segment[2].to_pytimedelta()}" if time_segment[2] != -1 else ""
        if not log:
            print(f"    {str(time_segment[0]).split()[-1]} - {str(time_segment[1]).split()[-1]}{duration_str}")
        else:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"    {str(time_segment[0]).split()[-1]} - {str(time_segment[1]).split()[-1]}{duration_str}\n")
    # total_member_duration += duration_this_day
    if duration_this_day > timedelta(hours=8) and not log:
        warning_members.append([member_name_lower, "More than 8 hours in one day"])
    # print(f"    Total duration this day: {duration_this_day.to_pytimedelta()}")

    last_time = last_time + timedelta(1)
    return last_time, duration_this_day

def process_member(member_df, member_name_lower, log=False):
    if not log:
        print(f"{member_df.iloc[0]["name"]} logs")
    else: 
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{member_df.iloc[0]["name"]} logs\n")

    last_time = pd.to_datetime(last_log_time_processed)
    
    member_df_time_sorted = member_df.copy()
    total_member_duration = pd.Timedelta(0)

    while last_time < datetime.now():        
        member_df_time_sorted = member_df.loc[(member_df.login_time > last_time) & (member_df.login_time <= last_time + timedelta(1))]
        member_df_time_sorted = member_df_time_sorted.sort_values(by="login_time", ascending=True)

        last_time, dur_to_add = process_day_for_member(member_df_time_sorted, last_time, member_name_lower, log=log)
        total_member_duration += dur_to_add


    weeks_duration = ((last_time - timedelta(1)) - last_log_time_processed).to_pytimedelta().days / 7
    max_hours = timedelta(hours=weeks_duration * max_hrs_7_days)
    total_dur_mem_string = f"  Total duration this member: {total_member_duration}"
    if not log:
        print(total_dur_mem_string)

        if total_member_duration > max_hours:
            warning_members.append([member_name_lower, f"Exceeded max allowed hours for duration, reduced"])
            print(f"Duration > max, adjusted duration: {max_hours}")
            member_durations.append([member_name_lower, max_hours])
        else:
            member_durations.append([member_name_lower, total_member_duration])
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(total_dur_mem_string + "\n")
            if total_member_duration > max_hours:
                total_member_duration = max_hours
                f.write(f"Duration > max, adjusted duration: {max_hours}\n")
            
            final_dur = timedelta(0)
            for name, dur in member_durations:
                if name == member_name_lower:
                    final_dur = dur
                    if dur != total_member_duration:
                        f.write(f"Duration manually adjusted, final {dur}\n")
            f.write(f"Credited {calculate_to_credit(final_dur)}\n")
    
    if not log:
        print("-" * len(total_dur_mem_string))
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("-" * len(total_dur_mem_string) + "\n")


def process_all(log=False):
    for member_name_lower in filtered_data.name_lower.unique():
        member_df = filtered_data[filtered_data.name_lower == member_name_lower]
        process_member(member_df, member_name_lower, log=log)

def print_warnings():
    for member, message in warning_members:
        print(f"WARNING! {member}, {message}")
    print()

def process_commands():
    command = ""
    while command != "confirm":
        command = input("Enter command: ").lower()
        cmd_parts = command.split()

        match cmd_parts[0]:
            case "help":
                help_command = \
                    """
                    help: displays this message.

                    exit: exits without applying hours.

                    confirm: confirms set hours, outputs log, applies credit, ends program.

                    edit [member_name_lowercase] [hours]: edits member specified to have that many hours total.
                        (alias e)
                    
                    query [member_name_lowercase]: returns total set hours and hours to credit for member specified.
                        (alias q)
                    """
                print(help_command)
            case "edit"|"e":
                if len(cmd_parts) < 4:
                    print("Improper number of arguments!")
                    continue
                
                did_set = False
                member_to_search = f"{cmd_parts[1]} {cmd_parts[2]}"

                for index, item in enumerate(member_durations):
                    item_copy = item.copy()
                    if item_copy[0] == member_to_search:
                        item_copy[1] = timedelta(hours=int(cmd_parts[3]))
                        member_durations[index] = item_copy
                        did_set = True
                        print(f"{item_copy[1]} set for {item_copy[0]}")
                        break
                
                if not did_set:
                    print(f"Failed to find member {member_to_search}")
            
            case "query"|"q":
                if len(cmd_parts) < 3:
                    print("Improper number of arguments!")
                    continue
                
                did_set = False
                
                member_to_search = f"{cmd_parts[1]} {cmd_parts[2]}"
                for index, item in enumerate(member_durations):
                    item_copy = item.copy()
                    if item_copy[0] == member_to_search:
                        did_set = True
                        print(f"{item[0]}: duration {item_copy[1]}, will credit ${calculate_to_credit(item_copy[1])}")
                        break
                
                if not did_set:
                    print(f"Failed to find member {member_to_search}")

            case "confirm":
                output_log_file()

                config.config["DEFAULT"]["LastLogTimeProcessed"] = str(datetime.strptime(str(datetime.now()).split()[0], r"%Y-%m-%d"))
                with open('config.ini', 'w') as configfile:
                    config.config.write(configfile)


            case "exit":
                break
            case _:
                print("Unknown command!")

def output_log_file():
    global log_file
    log_file = f"credit_logs/hours_log {str(datetime.now()).split()[0]}.txt"
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\nLogs since {last_log_time_processed}\n")
    process_all(log=True)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\nTo credit:\n")
        for member, dur in member_durations:
            f.write(f"{member}: calculation - {timedelta(hours = round((duration.total_seconds() / 3600))} * ${dollars_per_hour} = ${calculate_to_credit(dur)}\n")

if __name__ == "__main__":
    process_all()
    print_warnings()
    process_commands()
