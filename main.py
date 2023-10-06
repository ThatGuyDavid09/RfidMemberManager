import functools
import os
import tkinter as tk
from tkinter import ttk
import time
import csv
import pandas as pd


# from breeze import breeze

def get_all_logins():
    return pd.read_csv("data/login_log.csv")


def update_log():
    global sort_option
    log_data = get_all_logins()

    selected_option = sort_option.get()
    filtered_data = []

    if selected_option == "Date Range":
        start_date = start_date_entry.get()
        end_date = end_date_entry.get()
        filtered_data = log_data[start_date <= log_data["entry_time"] <= end_date]
            # .append(entry)
    elif selected_option == "Member Name":
        selected_member = member_name_entry.get()
        filtered_data = log_data[log_data["name"] == selected_member]
    else:
        filtered_data = log_data

    log_listbox.delete(0, tk.END)
    for _, entry in filtered_data.iterrows():
        log_listbox.insert(tk.END, f"Member: {entry['name']}, Login Time: {entry['login_time']}, RFID ID: {entry['rfid_code']}")

def open_log_window():
    # TODO FIXME This is not working. Stuff is not showing up.
    global view_log_window
    view_log_window = tk.Toplevel(root)
    view_log_window.title("Log")

    menu = tk.Menu(view_log_window)
    view_log_window.config(menu=menu)
    log_menu = tk.Menu(menu)
    menu.add_cascade(label="Log", menu=log_menu)

    # Add options to the "Log" menu
    global sort_option
    sort_option = tk.StringVar()
    log_menu.add_radiobutton(label="All Entries", variable=sort_option, value="All Entries", command=update_log)
    log_menu.add_radiobutton(label="Date Range", variable=sort_option, value="Date Range", command=update_log)
    log_menu.add_radiobutton(label="Member Name", variable=sort_option, value="Member Name", command=update_log)

    # Create and pack widgets for date range and member name input
    global start_date_entry
    start_date_label = tk.Label(root, text="Start Date:")
    start_date_label.pack()
    start_date_entry = tk.Entry(root)
    start_date_entry.pack()

    global end_date_entry
    end_date_label = tk.Label(root, text="End Date:")
    end_date_label.pack()
    end_date_entry = tk.Entry(root)
    end_date_entry.pack()

    global member_name_entry
    member_name_label = tk.Label(root, text="Member Name:")
    member_name_label.pack()
    member_name_entry = tk.Entry(root)
    member_name_entry.pack()

    # Create a listbox to display log entries
    global log_listbox
    log_listbox = tk.Listbox(root, width=50, height=15)
    log_listbox.pack()

    # Create a button to apply the selected sorting option
    apply_button = tk.Button(root, text="Apply", command=update_log)
    apply_button.pack()

    # Initialize the sort_option variable
    sort_option.set("All Entries")

    # Initialize the log display with all entries
    update_log()

def init_data_files():
    if not os.path.isfile("data/members_list.csv"):
        with open('data/members_list.csv', 'w', encoding="utf-8") as f:
            f.write('name,rfid_code,member_id\n')

    if not os.path.isfile("data/login_log.csv"):
        with open('data/login_log.csv', 'w', encoding="utf-8") as f:
            f.write('name,rfid_code,member_id,login_time\n')


def save_member(rfid_id, name, member_id):
    global members
    with open("data/members_list.csv", "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, rfid_id, member_id])
    members = pd.read_csv("data/members_list.csv")
    print(members)



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

        member_data = (member_name, current_datetime, rfid_id)
        tree.insert("", 0, values=member_data)
        rfid_entry.delete(0, "end")


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
