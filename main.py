import functools
import os
import tkinter as tk
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
    log_window = tk.Toplevel(root)
    log_window.title("Log Viewer")

    # # Create and pack label for sorting options
    sort_label = tk.Label(log_window, text="Sort by:")
    sort_label.pack()

    sort_column = tk.StringVar()
    sort_order = tk.StringVar()
    sort_column.set("Member Name")
    sort_order.set("asc")  # Default to ascending order

    #
    # # Create a StringVar for the menu option
    # sort_option = tk.StringVar()
    # sort_option.set("All Entries")

    def update_log(events=None):
        log_data = get_all_logins()

        # selected_option = sort_option.get()
        filtered_data = log_data

        start_date = (start_date_entry.get())
        end_date = (end_date_entry.get())

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

            filtered_data = filtered_data.loc[(filtered_data["login_time"] >= start_date) & (filtered_data["login_time"] <= end_date)]
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

    # Create and pack widgets for date range and member name input in the log window
    start_date_label = tk.Label(log_window, text="Start Date (mm/dd/yyyy):")
    start_date_label.pack()
    start_date_entry = tk.Entry(log_window)
    start_date_entry.pack()

    end_date_label = tk.Label(log_window, text="End Date (mm/dd/yyyy):")
    end_date_label.pack()
    end_date_entry = tk.Entry(log_window)
    end_date_entry.pack()

    member_name_label = tk.Label(log_window, text="Member Name:")
    member_name_label.pack()
    member_name_entry = tk.Entry(log_window)
    member_name_entry.pack(pady=(0, 10))

    # Create a button to apply the selected sorting option in the log window
    apply_button = tk.Button(log_window, text="Apply", command=update_log)
    apply_button.pack()

    log_tree = ttk.Treeview(log_window, columns=("Member Name", "Login Time", "RFID Code"), show="headings")

    # Create a dictionary to map column names to sort orders and icons
    column_sort_data = {
        "Member Name": {"order": "asc", "icon": "↓"},
        "Login Time": {"order": "asc", "icon": "↓"},
        "RFID Code": {"order": "asc", "icon": "↓"},
    }

    # Function to toggle sorting column and order when a column heading is clicked
    def toggle_sort_column(col):
        current_column = sort_column.get()
        current_order = sort_order.get()

        # Toggle the sorting order for the current column
        if current_column == col:
            new_order = "asc" if current_order == "desc" else "desc"
            sort_order.set(new_order)
        else:
            # Set the new column as the sorting column and reset its order to ascending
            sort_column.set(col)
            sort_order.set("asc")

        # Update the sort icons for all columns
        for column in column_sort_data:
            if column == col:
                # Set the sort icon for the current column
                column_sort_data[column]["icon"] = "▲" if sort_order.get() == "asc" else "▼"
            else:
                # Reset the sort icon for other columns
                column_sort_data[column]["icon"] = ""

        update_log()
        update_sort_icons()

    def update_sort_icons():
        # Update the sort icons in the column headings
        for column in column_sort_data:
            heading_text = column + " " + column_sort_data[column]["icon"]
            log_tree.heading(column, text=heading_text)

    for column in column_sort_data:
        log_tree.heading(column, text=column + " " + column_sort_data[column]["icon"],
                         command=lambda c=column: toggle_sort_column(c))

    log_tree.heading("Member Name", text="Member Name", command=lambda: toggle_sort_column("Member Name"))
    log_tree.heading("Login Time", text="Login Time", command=lambda: toggle_sort_column("Login Time"))
    log_tree.heading("RFID Code", text="RFID Code", command=lambda: toggle_sort_column("RFID Code"))

    log_tree.pack(side="left", fill="both", padx=(10, 0), pady=10)

    log_tree_scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=log_tree.yview)
    log_tree.configure(yscrollcommand=log_tree_scrollbar.set)
    log_tree_scrollbar.pack(side="right", padx=(0, 10), pady=10, fill="y")

    log_window.bind('<Return>', update_log)

    update_log()


def init_data_files():
    if not os.path.isfile("data/members_list.csv"):
        with open('data/members_list.csv', 'w', encoding="utf-8") as f:
            f.write('name,rfid_code,member_id\n')

    if not os.path.isfile("data/login_log.csv"):
        with open('data/login_log.csv', 'w', encoding="utf-8") as f:
            f.write('name,name_lower,rfid_code,member_id,login_time\n')


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
    if len(rfid_id) < 10 or not rfid_id.isdigit():
        return

    save_member(rfid_id, name, -1)
    add_member_window.destroy()


# Function to handle the "search for member" button click
def search_for_member():
    # Get the values from the first name and last name entry fields
    first_name = first_name_entry.get()
    last_name = last_name_entry.get()

    # Perform some action with the search results (you can modify this part)
    search_results.delete(0, tk.END)  # Clear previous results
    # Populate the listbox with search results (replace this with your actual search results)
    search_results.insert(tk.END, f"{first_name} {last_name}")
    # search_results.insert(tk.END, "Result 2")
    # search_results.insert(tk.END, "Result 3")


def open_add_member_window():
    global add_member_window
    add_member_window = tk.Toplevel(root)
    add_member_window.title("Add Member")

    # Create entry fields for first name and last name
    global first_name_entry
    first_name_label = tk.Label(add_member_window, text="First Name:")
    first_name_label.pack()
    first_name_entry = tk.Entry(add_member_window)
    first_name_entry.pack()

    global last_name_entry
    last_name_label = tk.Label(add_member_window, text="Last Name:")
    last_name_label.pack()
    last_name_entry = tk.Entry(add_member_window)
    last_name_entry.pack()

    # Button to search for a member
    search_button = tk.Button(add_member_window, text="Search for Member", command=search_for_member)
    search_button.pack(pady=10)

    # Listbox to display search results
    global search_results  # Declare search_results as global
    search_results = tk.Listbox(add_member_window, height=5, width=30)
    search_results.pack(padx=10)

    # Entry field for scanning RFID tag
    global rfid_member_entry
    rfid_label = tk.Label(add_member_window, text="Scan RFID Tag:")
    rfid_label.pack()
    rfid_member_entry = tk.Entry(add_member_window)
    rfid_member_entry.pack()

    # Button to add a member and close the window
    add_member_button = tk.Button(add_member_window, text="Add Member", command=close_add_member_window)
    add_member_button.pack(pady=10)


def log_entry(event=None):
    rfid_id = rfid_entry.get()
    if len(rfid_id) >= 10 and rfid_id.isdigit():  # Validate RFID ID length
        current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")  # Get the current date and time
        member = members.loc[members["rfid_code"] == int(rfid_id)]
        member_name = "UNKNOWN" if member.empty else member["name"].iloc[0]
        member_id = -1 if member.empty else member["member_id"].iloc[0]

        member_data = (member_name, current_datetime, rfid_id)
        tree.insert("", 0, values=member_data)
        rfid_entry.delete(0, "end")

        with open("data/login_log.csv", "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([member_name, member_name.lower(), rfid_id, member_id, current_datetime])


#
# breeze_api = breeze.BreezeApi(
#     breeze_url="https://flightclub502.breezechms.com",
#     api_key="MISSING, WAITING ON IT"
# )


init_data_files()

members = pd.read_csv("data/members_list.csv")

# Create the main window
root = tk.Tk()
root.title("Flight Club Sign In")
root.geometry("500x400")  # Set the initial size of the window

# Create a frame for the RFID ID entry and Enter button
rfid_frame = tk.Frame(root)
rfid_frame.pack(side=tk.TOP, padx=10, pady=10)

# Create and place RFID ID label and entry widget
rfid_label = tk.Label(rfid_frame, text="RFID ID")
rfid_label.pack(side=tk.LEFT)

rfid_entry = tk.Entry(rfid_frame, width=15)  # Set the width of the entry field
rfid_entry.pack(side=tk.LEFT)

# Bind the Enter key to the RFID entry field
rfid_entry.bind('<Return>', log_entry)

# Create and place Enter button
enter_button = tk.Button(rfid_frame, text="Enter", command=log_entry)
enter_button.pack(side=tk.LEFT)

# Create and place View Log button
view_log_button = tk.Button(root, text="View Log", command=open_log_window)
view_log_button.pack(pady=10)

# Create a frame for the table
table_frame = tk.Frame(root)
table_frame.pack(padx=10, pady=10)

# Create and configure the treeview widget for the table
columns = ("Member", "Time", "ID")
tree = ttk.Treeview(table_frame, columns=columns, show="headings")

# Set the width of the columns
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=150)  # Set the width of the columns

tree.pack()

# Create and place Add Member button
add_member_button = tk.Button(root, text="Add Member", command=open_add_member_window)
add_member_button.pack(pady=10)

root.mainloop()
