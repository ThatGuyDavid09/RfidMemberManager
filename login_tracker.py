import functools
import os
import sys
import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import ttk
import time
import csv
import pandas as pd
import pynput as pynput

from ConfigHandler import ConfigHandler

from LogWindow import LogWindow


# from breeze import breeze

def open_log_window():
    log_window = LogWindow(root, "data/login_log.csv")


def init_data_files():
    if not os.path.exists("data/"):
        os.makedirs("data/")

    if not os.path.exists("data/members_list.csv"):
        with open('data/members_list.csv', 'w', encoding="utf-8") as f:
            f.write('name,rfid_code,member_id\n')

    if not os.path.exists("data/login_log.csv"):
        with open('data/login_log.csv', 'w', encoding="utf-8") as f:
            f.write('name,name_lower,rfid_code,member_id,login_time,login_reason\n')


def init_config():
    global flight_circle_api_key, admin_rfid_id

    config = ConfigHandler()

    admin_rfid_id = int(config.get_config_element("DEFAULT/AdminRfidCode"))
    flight_circle_api_key = int(config.get_config_element("DEFAULT/FlightCircleApiKey"))


def save_member(rfid_id, name, member_id):
    global members
    with open("data/members_list.csv", "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, rfid_id, member_id])
    members = pd.read_csv("data/members_list.csv")


def close_add_member_window():
    selection_index = search_results.curselection()
    if not selection_index:
        return
    name = search_results.get(selection_index)

    rfid_id = rfid_member_entry.get()
    if len(rfid_id) < 2 or not rfid_id.isdigit():
        return

    save_member(rfid_id, name, -1)
    add_member_window.destroy()


def search_for_member():
    first_name = first_name_entry.get()
    last_name = last_name_entry.get()

    search_results.delete(0, tk.END)  # Clear previous results
    search_results.insert(tk.END, f"{first_name} {last_name}")
    # search_results.insert(tk.END, "Result 2")
    # search_results.insert(tk.END, "Result 3")


def open_add_member_window():
    global add_member_window
    add_member_window = ctk.CTkToplevel(root)
    add_member_window.title("Add Member")

    global first_name_entry
    first_name_label = ctk.CTkLabel(add_member_window, text="First Name:")
    first_name_label.pack()
    first_name_entry = ctk.CTkEntry(add_member_window)
    first_name_entry.pack()

    global last_name_entry
    last_name_label = ctk.CTkLabel(add_member_window, text="Last Name:")
    last_name_label.pack()
    last_name_entry = ctk.CTkEntry(add_member_window)
    last_name_entry.pack()

    search_button = ctk.CTkButton(add_member_window, text="Search for Member", command=search_for_member)
    search_button.pack(pady=10)

    global search_results
    search_results = tk.Listbox(add_member_window, height=5, width=30)
    search_results.pack(padx=10)

    global rfid_member_entry
    rfid_label = ctk.CTkLabel(add_member_window, text="Scan RFID Tag:")
    rfid_label.pack()
    rfid_member_entry = ctk.CTkEntry(add_member_window)
    rfid_member_entry.pack()

    add_member_button = ctk.CTkButton(add_member_window, text="Add Member", command=close_add_member_window)
    add_member_button.pack(pady=10)

    # add_member_window.after(1000, add_member_window.lift())
    add_member_window.attributes('-topmost', True)
    add_member_window.update()
    add_member_window.attributes('-topmost', False)
    add_member_window.focus()


def open_empty_member_log_window(rfid_id):
    def save_empty_member_entry(event=None):
        name = unknown_member_name_entry.get()

        # open_request_reason_window(rfid_id, name if name else "unknown", -1)
        save_entry(rfid_id, name if name else "unknown", reason="general")

        # save_entry(rfid_id, name if name else None)
        empty_member_window.destroy()

    empty_member_window = ctk.CTkToplevel(root)
    empty_member_window.title("Unknown member")

    instruction_label = ctk.CTkLabel(empty_member_window, text="ID not recognized. Please enter name manually.")
    instruction_label.pack(padx=20, pady=10)

    name_label = ctk.CTkLabel(empty_member_window, text="Name (leave empty for unknown):")
    name_label.pack(pady=(10, 0))
    unknown_member_name_entry = ctk.CTkEntry(empty_member_window)
    unknown_member_name_entry.pack()
    unknown_member_name_entry.bind("<Return>", save_empty_member_entry)

    log_button = ctk.CTkButton(empty_member_window, text="Save", command=save_empty_member_entry)
    log_button.pack(pady=10)

    empty_member_window.protocol("WM_DELETE_WINDOW", save_empty_member_entry)
    empty_member_window.attributes('-topmost', True)
    empty_member_window.update()
    empty_member_window.attributes('-topmost', False)
    empty_member_window.focus()


def open_request_reason_window(rfid_id, member_name, member_id):
    def save_entry_with_reason():
        selection_index = reason_option.curselection()
        reason = ""
        if not selection_index:
            reason = "unknown"
        else:
            reason = reason_option.get(selection_index).lower()
        save_entry(rfid_id, member_name, member_id, reason)
        reason_request_window.destroy()

    reason_request_window = ctk.CTkToplevel(root)
    reason_request_window.title("Input reason")

    instruction_label = ctk.CTkLabel(reason_request_window, text="Please select reason for login:")
    instruction_label.pack(padx=20, pady=10)

    reasons = [
        "Work to fly",
        "Volunteering - general",
        "Flight lessons/study",
        "CFI",
        "Genral clubhouse use - nonflying",
        "Ground school",
        "Hangar talk/Monthy meeting",
        "Visitor",
        "Event",
        "Other"
    ]

    reason_option = tk.Listbox(reason_request_window, height=len(reasons), width=30)
    reason_option.pack(padx=10)

    reason_option.delete(0, tk.END)  # Clear previous results
    for reason in reasons:
        reason_option.insert(tk.END, reason)

    reason_option.bind("<Return>", save_entry_with_reason)

    log_button = ctk.CTkButton(reason_request_window, text="Save", command=save_entry_with_reason)
    log_button.pack(pady=10)

    reason_request_window.protocol("WM_DELETE_WINDOW", save_entry_with_reason)
    reason_request_window.attributes('-topmost', True)
    reason_request_window.update()
    reason_request_window.attributes('-topmost', False)
    reason_request_window.focus()


def log_entry(event=None, rfid_id=None):
    # if rfid_id is None:
    #     rfid_id = rfid_entry.get()
    if len(rfid_id) >= 2 and rfid_id.isdigit():
        member = members.loc[members["rfid_code"] == int(rfid_id)]

        if member.empty or int(rfid_id) == admin_rfid_id:
            open_empty_member_log_window(rfid_id)
        else:
            member_name = member["name"].iloc[0]
            member_id = member["member_id"].iloc[0]

            if "(work)" in member_name:
                member_name = member_name.replace(" (work)", "")
                save_entry(rfid_id, member_name, reason="work to fly")
            else:
                save_entry(rfid_id, member_name, reason="general")
                # open_request_reason_window(rfid_id, member_name, member_id)


def save_entry(rfid_id, member_name=None, member_id=-1, reason="unknown"):
    if member_name is None:
        member_name = "UNKNOWN"

    current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")

    member_data = (member_name, current_datetime, reason)
    recent_entries_tree.insert("", 0, values=member_data)
    # rfid_entry.delete(0, "end")
    with open("data/login_log.csv", "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([member_name, member_name.lower(), rfid_id, member_id, current_datetime, reason.lower()])


currently_pressed_keys = ""
# TODO verify this is the length of rfid codes

rfid_code_length = 10

def on_key_press(key):
    global currently_pressed_keys

    try:
        key = key.char

        if key.isalpha():
            currently_pressed_keys = ""

        if not key.isdigit():
            return
        currently_pressed_keys += key
        if len(currently_pressed_keys) > rfid_code_length:
            currently_pressed_keys = currently_pressed_keys[1:]
        # print(currently_pressed_keys)
    except AttributeError:
        if key == pynput.keyboard.Key.enter and len(currently_pressed_keys) == rfid_code_length:
            log_entry(rfid_id=currently_pressed_keys)
            currently_pressed_keys = ""


listener = pynput.keyboard.Listener(on_press=on_key_press)
listener.start()

admin_rfid_id = None
flight_circle_api_key = None

init_data_files()
init_config()

members = pd.read_csv("data/members_list.csv")

ctk.set_appearance_mode("light")
root = ctk.CTk()
root.title("Flight Club Sign In")
# root.protocol("WM_DELETE_WINDOW", close_main_window)
# root.geometry("500x400")

icon = tk.PhotoImage(file="fc_502_logo.png")
root.iconphoto(False, icon)

# rfid_frame = ctk.CTkFrame(root)
# rfid_frame.pack(side=tk.TOP, padx=10, pady=10)
#
# rfid_label = ctk.CTkLabel(rfid_frame, text="RFID ID")
# rfid_label.pack(side=tk.LEFT, padx=(5, 0))
#
# rfid_entry = ctk.CTkEntry(rfid_frame, width=150)
# rfid_entry.pack(side=tk.LEFT, padx=5)
#
# rfid_entry.bind('<Return>', log_entry)
#
# enter_button = ctk.CTkButton(rfid_frame, text="Enter", width=40, command=log_entry)
# enter_button.pack(side=tk.LEFT)

view_log_button = ctk.CTkButton(root, text="View Log", command=open_log_window)
view_log_button.pack(pady=10)

table_frame = ctk.CTkFrame(root)
table_frame.pack(padx=10, pady=10)

style = ttk.Style()
# style.theme_use('clam')
style.configure("Treeview.Heading", font=(None, 16))
# style.configure("Treeview.Entry", font=(None, 16))
style.configure("Treeview", font=(None, 16), rowheight=30)

columns = ("Member name", "Login time", "Login reason")
recent_entries_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

for col in columns:
    recent_entries_tree.heading(col, text=col)
    recent_entries_tree.column(col, width=500)

recent_entries_tree.pack()

add_member_button = ctk.CTkButton(root, text="Add Member", command=open_add_member_window)
add_member_button.pack(pady=10)

root.mainloop()

# while not exit_flag:
#     print("test")
#     if exit_flag:
#         break

# root.update_idletasks()
# root.update()
