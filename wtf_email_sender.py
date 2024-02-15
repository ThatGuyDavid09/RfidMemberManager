from email.mime.text import MIMEText
import string
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

import smtplib, ssl

from ConfigHandler import ConfigHandler

last_log_time_processed = None
# Account for differing end of month times
today = datetime.today()
if today.day >= 28: # Task run at the end of the month, need every day since the 15th, inclusive
    last_log_time_processed = today.replace(day=15).date()
else: # Task run on the 15th, need every day since last day of last month, inclusive
    last_log_time_processed = (today.replace(day=1) - timedelta(days=1)).date()

# last_log_time_processed = datetime.today().date() - timedelta(weeks=2)
last_log_time_processed_str = last_log_time_processed.strftime(r"%d/%m/%y")
max_hrs_7_days = None
dollars_per_hour = None
login_type_tag_to_search = None


def check_log_file_size():
    path = r"run_logs/wtf_email_run_log.txt"
    file_size_mb = os.stat(path).st_size  / (1024 * 1024)
    if file_size_mb > 50:
        with open(path, "r") as f:
            f.truncate()


def init_config(config_file):
    """
    Loads configuration variables from file and sets them in global variables.
    """
    global last_log_time_processed, max_hrs_7_days, dollars_per_hour, login_type_tag_to_search

    config = ConfigHandler(config_file)
    max_hrs_7_days = int(config.get_config_element("DEFAULT/MaxHoursPerWeek"))
    dollars_per_hour = int(config.get_config_element("DEFAULT/DollarsPerHour"))
    login_type_tag_to_search = str(config.get_config_element("DEFAULT/LoginSearchTypeTag")).lower()

    print(f"[INFO {str(datetime.now())}] Config initalized")

    return config

def get_only_current_data(data_df, last_login_time):
    """
    Returns a dataframe with all logins before the specified log time processed time removed.
    """
    data_df = data_df.loc[
        (data_df["login_time"] >= pd.to_datetime(last_login_time))]
    return data_df

def preprocess_data(df):
    """
    Removes unknown logins or logins with the wrong reason from provided df, and converts login_time column to 
    a pandas datetime object.
    """
    global preprocessed_data_df

    df.drop(df[df["name_lower"] == "unknown"].index, inplace=True)
    df.drop(df[df["login_reason"] != "work to fly"].index, inplace=True)
    df["login_time"] = pd.to_datetime(df["login_time"])
    preprocessed_data_df = df
    return df

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
    weeks_duration = ((last_time - timedelta(1)).to_pydatetime().date() - last_log_time_processed).days / 7
    max_hours = timedelta(hours=(weeks_duration * max_hrs_7_days) // 1)

    if total_member_duration > max_hours:
        warnings.append([member_name_lower, f"Exceeded max allowed hours for duration, reduced"])
        # We set second element of the list to True to let other methods know we have modified the date
        member_structure["duration"] = [int(max_hours.total_seconds() // 3600), True]
    else:
        member_structure["duration"] = [int(total_member_duration.total_seconds() // 3600), False]
    return member_structure, warnings

def process_data(data_df, last_login_time):
    """
    Processes all members and adds them to UI.
    """
    all_members = []

    data_df = get_only_current_data(data_df, last_login_time)

    for member_name_lower in data_df.name_lower.unique():
        member_df = data_df[data_df.name_lower == member_name_lower]
        member_structure, _ = process_member(member_df, member_name_lower)
        all_members.append(member_structure)
    return all_members


def get_display_text_and_hours(seconds):
    if seconds is None:
        return "NTBM", 0

    hours = round(seconds / 3600)
    if hours > 0:
        return (f"{hours} hour" + ("" if hours == 1 else "s")), hours
    else:
        minutes = round(seconds / 60)
        return (f"{minutes} minute" + ("" if minutes == 1 else "s")), 0


def output_log(all_members):
    """
    Outputs a log file based on all_members.
    """
    os.makedirs('credit_logs', exist_ok=True)
    with open(f"credit_logs/credit_log.txt", "a", encoding="utf-8") as f:
        f.write(f"AUTO Processed \"{login_type_tag_to_search}\" on {datetime.now().strftime(r"%m/%d/%y")}, logs since {last_log_time_processed.strftime(r"%m/%d/%y")}\n")

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

check_log_file_size()
port = 465 
smtp_server = "smtp.gmail.com"
sender_email = "skininthegame@flightclub502.org" 
receiver_email = "liam.cantin@flightclub502.org"
bcc_email = "iman.ghali@flightclub502.org"
password = "Skininthegame#502!"

cfg_file = None
if len(sys.argv) > 1:
    cfg_file = sys.argv[1]
else:
    cfg_file = "config.ini"
init_config(cfg_file)

members_df = pd.read_csv(r"C:\Users\fligh\Documents\RfidMemberManager\data\login_log.csv")
print(f"[INFO {str(datetime.now())}] Data loaded")
members_df = preprocess_data(members_df)
print(f"[INFO {str(datetime.now())}] Data preprocessed")
all_members = process_data(members_df, last_log_time_processed)
print(f"[INFO {str(datetime.now())}] Data processed")

# message = f"Logs since {last_log_time_processed_str}\n"

# message += "To credit by member:\n"
# for member in all_members:
#     duration = member["duration"][0]
#     message += " " * 4 + f"{string.capwords(member["name"])}: {duration} hours * ${dollars_per_hour} = ${duration * dollars_per_hour}\n"

# Too lazy to make more customizable, just same as log file
message = (f"AUTO Processed \"{login_type_tag_to_search}\" on {datetime.now().strftime(r"%m/%d/%y")}, logs since {last_log_time_processed.strftime(r"%m/%d/%y")}\n")

for member in all_members:
    message += (string.capwords(member["name"]) + "\n")
    total_duration_hours = 0
    for day in member["days"]:
        # For display only.
        seconds_for_day = sum(
            [(time[1] - time[0]).total_seconds() for time in day["times"] if
                type(time[1]) != str])
        time_text, hours_for_day = get_display_text_and_hours(seconds_for_day)
        day_text = f"{day["day"].strftime(r"%m/%d/%y")} - {time_text} * ${dollars_per_hour} = ${hours_for_day * dollars_per_hour}"
        message += (" " * 4 + day_text + "\n")

        for start, end in day["times"]:
            duration = None if end == "NTBM" else end - start
            duration_seconds = None if duration is None else duration.total_seconds()
            sub_dur_text, duration_hours = get_display_text_and_hours(duration_seconds)
            dur_text = "" if duration is None else f": {sub_dur_text} * ${dollars_per_hour} = ${duration_hours * dollars_per_hour}"
            time_text = f"{start.strftime(r"%H:%M:%S")} - {"NTBM" if duration is None else end.strftime(r"%H:%M:%S")}" + dur_text
            message += (" " * 8 + time_text + "\n")
    total_duration_hours = member["duration"][0]
    if member["duration"][1]:
        message += (" " * 4 + f"More than max hours! Adjusted\n")
        message += (
            " " * 4 + f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}\n")
    else:
        message += (
            " " * 4 + f"Total: {total_duration_hours} hours * ${dollars_per_hour} = ${total_duration_hours * dollars_per_hour}\n")
message += ("\n")
message += ("To credit by member:\n")
for member in all_members:
    duration = member["duration"][0]
    message += (
        " " * 4 + f"{string.capwords(member["name"])}: {duration} hours * ${dollars_per_hour} = ${duration * dollars_per_hour}\n")
message += ("-" * 60 + "\n\n")

msg = MIMEText(message)
msg['Subject'] = f"Skin in the game logs since {last_log_time_processed_str}"
msg['From'] = sender_email
msg['To'] = receiver_email
if "general" in cfg_file:
    msg['Bcc'] = bcc_email

context = ssl.create_default_context()
with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
print(f"[INFO {str(datetime.now())}] Email sent")
output_log(all_members)
print(f"[INFO {str(datetime.now())}] Log outputted")
print(f"--------------------")
