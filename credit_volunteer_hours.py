import configparser
import functools
import os
from datetime import datetime, timedelta
from pprint import pprint
import time
import csv
import pandas as pd

def get_all_logins(login_path):
        logins = pd.read_csv(login_path)
        logins["login_time"] = pd.to_datetime(logins["login_time"])
        return logins

def init_config_file():
    global flight_circle_api_key, last_log_time_processed

    if not os.path.exists("config.ini"):
        with open('config.ini', "w", encoding="utf-8") as f:
            f.writelines([
                "[DEFAULT]\n",
                "AdminRfidCode = -1\n",
                "FlightCircleApiKey = -1\n",
                "LastLogTimeProcessed = -1\n"
            ])

    config = configparser.ConfigParser()
    config.read("config.ini")
    flight_circle_api_key = int(config["DEFAULT"]["FlightCircleApiKey"])
    last_log_time_processed = int(config["DEFAULT"]["LastLogTimeProcessed"])

    if last_log_time_processed == -1:
        last_log_time_processed = datetime.today() - timedelta(30)
        last_log_time_processed = datetime(*last_log_time_processed.timetuple()[:3])

flight_circle_api_key = None
last_log_time_processed = None
init_config_file()

login_path = "data/login_log.csv" # input("Enter login path: ")
while not os.path.exists(login_path):
    print("That file doesn't exist!")
    login_path = input("Enter login path: ")

filtered_data = get_all_logins(login_path)
filtered_data.drop(filtered_data[filtered_data["name_lower"] == "unknown"].index)
filtered_data = filtered_data.loc[
    (filtered_data["login_time"] >= pd.to_datetime(last_log_time_processed))]

warning_members = []
member_durations = []
print(f"Logs since {last_log_time_processed}")
for member_name_lower in filtered_data.name_lower.unique():
    member_df = filtered_data[filtered_data.name_lower == member_name_lower]
    print(f"{member_df.iloc[0]["name"]} logs")

    last_time = pd.to_datetime(last_log_time_processed)
    
    member_df_time_sorted = member_df.copy()
    total_member_duration = pd.Timedelta(0)

    while last_time < datetime.now():
        member_df_time_sorted = member_df.loc[(member_df.login_time > last_time) & (member_df.login_time <= last_time + timedelta(1))]
        member_df_time_sorted = member_df_time_sorted.sort_values(by="login_time", ascending=True)

        logged_times = []

        start_time = None
        if not member_df_time_sorted.empty:
            # member_df_time_sorted.sort_values(by="login_time", ascending=True)
            # print(member_df_time_sorted.login_time.dtype)
            # print(member_df_time_sorted)
            print(f"  Logs on {last_time.date()}")

            for index, row in member_df_time_sorted.iterrows():
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
                print(f"    {str(time_segment[0]).split()[-1]} - {str(time_segment[1]).split()[-1]}{duration_str}")
            total_member_duration += duration_this_day
            if duration_this_day > timedelta(hours=8):
                warning_members.append([member_name_lower, "More than 8 hours in one day"])
            # print(f"    Total duration this day: {duration_this_day.to_pytimedelta()}")

        last_time = last_time + timedelta(1)

    member_durations.append([member_name_lower, total_member_duration])
    total_dur_mem_string = f"  Total duration this member: {total_member_duration}"
    print(total_dur_mem_string)
    print("-" * len(total_dur_mem_string))

for member, message in warning_members:
    print(f"WARNING! {member}, {message}")
print()
