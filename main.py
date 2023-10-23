import configparser
import functools
import os
import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import ttk
import time
import csv
import pandas as pd


# from breeze import breeze

def get_all_logins():
    logins = pd.read_csv("data/login_log.csv")
    logins["login_time"] = pd.to_datetime(logins["login_time"])
    return logins


def open_log_window():
    log_window = ctk.CTkToplevel(root)
    log_window.title("Log Viewer")

    sort_label = ctk.CTkLabel(log_window, text="Sort by:")
    sort_label.pack()

    sort_column = tk.StringVar()
    sort_order = tk.StringVar()
    sort_column.set("Member Name")
    sort_order.set("asc")  # Default to ascending order

    # sort_option = tk.StringVar()
    # sort_option.set("All Entries")

    def update_log(events=None):
        log_data = get_all_logins()

        # selected_option = sort_option.get()
        filtered_data = log_data

        start_date = start_date_entry.get()
        end_date = end_date_entry.get()

        selected_member = member_name_entry.get()

        if start_date or end_date:
            if not start_date:
                start_date = pd.to_datetime(0, unit="s")
            else:
                start_date = pd.to_datetime(start_date)

            if not end_date:
                tomorrow_timestamp = int((datetime.now() + timedelta(days=1)).timestamp())
                end_date = pd.to_datetime(tomorrow_timestamp, unit="s")
            else:
                end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)

            filtered_data = filtered_data.loc[
                (filtered_data["login_time"] >= start_date) & (filtered_data["login_time"] <= end_date)]
        elif selected_member:
            filtered_data = filtered_data[filtered_data["name_lower"].str.contains(selected_member.lower())]

        for record in log_tree.get_children():
            log_tree.delete(record)

        column_mapping = {
            "member name": "name",
            "login time": "login_time",
            "rfid code": "rfid_code"
        }

        key = column_mapping[sort_column.get().lower()]
        ascending = sort_order.get() == "asc"
        sorted_data = filtered_data.sort_values(by=key, ascending=ascending)

        for _, entry in sorted_data.iterrows():
            member_name = entry["name"]
            login_time = entry["login_time"]
            rfid_id = entry["rfid_code"]
            log_tree.insert("", "end", values=(member_name, login_time, rfid_id))

    # all_entries_radio = tk.Radiobutton(log_window, text="All Entries", variable=sort_option, value="All Entries",
    #                                    command=update_log)
    # all_entries_radio.pack()
    #
    # date_range_radio = tk.Radiobutton(log_window, text="Date Range", variable=sort_option, value="Date Range",
    #                                   command=update_log)
    # date_range_radio.pack()
    #
    # member_name_radio = tk.Radiobutton(log_window, text="Member Name", variable=sort_option, value="Member Name",
    #                                    command=update_log)
    # member_name_radio.pack()

    start_date_label = ctk.CTkLabel(log_window, text="Start Date (mm/dd/yyyy):")
    start_date_label.pack()
    start_date_entry = ctk.CTkEntry(log_window)
    start_date_entry.pack()

    end_date_label = ctk.CTkLabel(log_window, text="End Date (mm/dd/yyyy):")
    end_date_label.pack()
    end_date_entry = ctk.CTkEntry(log_window)
    end_date_entry.pack()

    member_name_label = ctk.CTkLabel(log_window, text="Member Name:")
    member_name_label.pack()
    member_name_entry = ctk.CTkEntry(log_window)
    member_name_entry.pack(pady=(0, 10))

    apply_button = ctk.CTkButton(log_window, text="Apply", command=update_log)
    apply_button.pack()

    log_tree = ttk.Treeview(log_window, columns=("Member Name", "Login Time", "RFID Code"), show="headings",
                            height=20)

    column_sort_data = {
        "Member Name": {"order": "asc", "icon": "↓"},
        "Login Time": {"order": "asc", "icon": "↓"},
        "RFID Code": {"order": "asc", "icon": "↓"},
    }

    def toggle_sort_column(col):
        current_column = sort_column.get()
        current_order = sort_order.get()

        if current_column == col:
            new_order = "asc" if current_order == "desc" else "desc"
            sort_order.set(new_order)
        else:
            sort_column.set(col)
            sort_order.set("asc")

        for column in column_sort_data:
            if column == col:
                column_sort_data[column]["icon"] = "▲" if sort_order.get() == "asc" else "▼"
            else:
                column_sort_data[column]["icon"] = ""

        update_log()
        update_sort_icons()

    def update_sort_icons():
        for column in column_sort_data:
            heading_text = column + " " + column_sort_data[column]["icon"]
            log_tree.heading(column, text=heading_text)

    for column in column_sort_data:
        log_tree.heading(column, text=column + " " + column_sort_data[column]["icon"],
                         command=lambda c=column: toggle_sort_column(c))

    log_tree.heading("Member Name", text="Member Name", command=lambda: toggle_sort_column("Member Name"))
    log_tree.heading("Login Time", text="Login Time", command=lambda: toggle_sort_column("Login Time"))
    log_tree.column("Login Time", width=210)
    log_tree.heading("RFID Code", text="RFID Code", command=lambda: toggle_sort_column("RFID Code"))

    log_tree.pack(side="left", fill="both", padx=(20, 0), pady=20)

    log_tree_scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=log_tree.yview)
    log_tree.configure(yscrollcommand=log_tree_scrollbar.set)
    log_tree_scrollbar.pack(side="right", padx=(0, 10), pady=10, fill="y")

    log_window.bind('<Return>', update_log)

    update_log()

    log_window.attributes('-topmost', True)
    log_window.update()
    log_window.attributes('-topmost', False)
    log_window.focus()


def init_data_files():
    if not os.path.exists("data/"):
        os.makedirs("data/")

    if not os.path.exists("data/members_list.csv"):
        with open('data/members_list.csv', 'w', encoding="utf-8") as f:
            f.write('name,rfid_code,member_id\n')

    if not os.path.exists("data/login_log.csv"):
        with open('data/login_log.csv', 'w', encoding="utf-8") as f:
            f.write('name,name_lower,rfid_code,member_id,login_time\n')


def init_config_file():
    global breeze_api_key, admin_rfid_id

    if not os.path.exists("config.ini"):
        with open('config.ini', "w", encoding="utf-8") as f:
            f.writelines([
                "[DEFAULT]\n",
                "AdminRfidCode = -1\n",
                "BreezeApiKey = -1\n"
            ])

    config = configparser.ConfigParser()
    config.read("config.ini")
    admin_rfid_id = int(config["DEFAULT"]["AdminRfidCode"])
    breeze_api_key = int(config["DEFAULT"]["BreezeApiKey"])


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

    global search_results  # Declare search_results as global
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
    def save_empty_member_entry():
        name = unknown_member_name_entry.get()
        save_entry(rfid_id, name if name else None)
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
    app.attributes('-topmost', True).attributes('-topmost', True)
    app.update().update()
    app.attributes('-topmost', False).attributes('-topmost', False)
    empty_member_window.focus()


def log_entry(event=None):
    rfid_id = rfid_entry.get()
    if len(rfid_id) >= 2 and rfid_id.isdigit():
        member = members.loc[members["rfid_code"] == int(rfid_id)]

        if member.empty or int(rfid_id) == admin_rfid_id:
            open_empty_member_log_window(rfid_id)
        else:
            member_name = member["name"].iloc[0]
            member_id = member["member_id"].iloc[0]

            save_entry(rfid_id, member_name, member_id)


def save_entry(rfid_id, member_name=None, member_id=-1):
    if member_name is None:
        member_name = "UNKNOWN"

    current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")

    member_data = (member_name, current_datetime)
    recent_entries_tree.insert("", 0, values=member_data)
    rfid_entry.delete(0, "end")
    with open("data/login_log.csv", "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([member_name, member_name.lower(), rfid_id, member_id, current_datetime])


#
# breeze_api = breeze.BreezeApi(
#     breeze_url="https://flightclub502.breezechms.com",
#     api_key="MISSING, WAITING ON IT"
# )

breeze_api_key = None
admin_rfid_id = None

init_data_files()
init_config_file()

members = pd.read_csv("data/members_list.csv")

ctk.set_appearance_mode("light")
root = ctk.CTk()
root.title("Flight Club Sign In")
# root.geometry("500x400")

icon = tk.PhotoImage(file="fc_502_logo.png")
root.iconphoto(False, icon)

rfid_frame = ctk.CTkFrame(root)
rfid_frame.pack(side=tk.TOP, padx=10, pady=10)

rfid_label = ctk.CTkLabel(rfid_frame, text="RFID ID")
rfid_label.pack(side=tk.LEFT, padx=(5, 0))

rfid_entry = ctk.CTkEntry(rfid_frame, width=150)
rfid_entry.pack(side=tk.LEFT, padx=5)

rfid_entry.bind('<Return>', log_entry)

enter_button = ctk.CTkButton(rfid_frame, text="Enter", width=40, command=log_entry)
enter_button.pack(side=tk.LEFT)

view_log_button = ctk.CTkButton(root, text="View Log", command=open_log_window)
view_log_button.pack(pady=10)

table_frame = ctk.CTkFrame(root)
table_frame.pack(padx=10, pady=10)

style = ttk.Style()
# style.theme_use('clam')
style.configure("Treeview.Heading", font=(None, 16))
# style.configure("Treeview.Entry", font=(None, 16))
style.configure("Treeview", font=(None, 16), rowheight=30)

columns = ("Member name", "Login time")
recent_entries_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

for col in columns:
    recent_entries_tree.heading(col, text=col)
    recent_entries_tree.column(col, width=500)

recent_entries_tree.pack()

add_member_button = ctk.CTkButton(root, text="Add Member", command=open_add_member_window)
add_member_button.pack(pady=10)

root.mainloop()
