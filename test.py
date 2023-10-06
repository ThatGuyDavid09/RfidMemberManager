import tkinter as tk
from tkinter import ttk

# Sample log data
log_data = [
    {"member_name": "John", "login_time": "2023-10-01 08:30:00", "rfid_id": "12345"},
    {"member_name": "Alice", "login_time": "2023-10-02 09:15:00", "rfid_id": "67890"},
    # Add more log entries here
]

# Create a function to update the log display based on user input
def update_log():
    selected_option = sort_option.get()
    filtered_data = []

    if selected_option == "Date Range":
        start_date = start_date_entry.get()
        end_date = end_date_entry.get()
        for entry in log_data:
            entry_time = entry["login_time"]
            if start_date <= entry_time <= end_date:
                filtered_data.append(entry)
    elif selected_option == "Member Name":
        selected_member = member_name_entry.get()
        for entry in log_data:
            if entry["member_name"] == selected_member:
                filtered_data.append(entry)
    else:
        filtered_data = log_data

    log_listbox.delete(0, tk.END)
    for entry in filtered_data:
        log_listbox.insert(tk.END, f"Member: {entry['member_name']}, Login Time: {entry['login_time']}, RFID ID: {entry['rfid_id']}")

# Create the main window
root = tk.Tk()
root.title("Log Viewer")

# Create a menu
menu = tk.Menu(root)
root.config(menu=menu)

# Create a StringVar for the menu option
sort_option = tk.StringVar()
sort_option.set("All Entries")

# Add options to the "Log" menu
log_menu = tk.Menu(menu)
menu.add_cascade(label="Log", menu=log_menu)
log_menu.add_radiobutton(label="All Entries", variable=sort_option, value="All Entries", command=update_log)
log_menu.add_radiobutton(label="Date Range", variable=sort_option, value="Date Range", command=update_log)
log_menu.add_radiobutton(label="Member Name", variable=sort_option, value="Member Name", command=update_log)

# Create and pack widgets for date range and member name input
start_date_label = tk.Label(root, text="Start Date:")
start_date_label.pack()
start_date_entry = tk.Entry(root)
start_date_entry.pack()

end_date_label = tk.Label(root, text="End Date:")
end_date_label.pack()
end_date_entry = tk.Entry(root)
end_date_entry.pack()

member_name_label = tk.Label(root, text="Member Name:")
member_name_label.pack()
member_name_entry = tk.Entry(root)
member_name_entry.pack()

# Create a listbox to display log entries
log_listbox = tk.Listbox(root, width=50, height=15)
log_listbox.pack()

# Create a button to apply the selected sorting option
apply_button = tk.Button(root, text="Apply", command=update_log)
apply_button.pack()

# Initialize the log display with all entries
update_log()

# Start the tkinter main loop
root.mainloop()
