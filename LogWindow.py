from datetime import datetime, timedelta
import pandas as pd

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class LogWindow:
    def __init__(self, root, log_file_path, log_tree_height=10):
        self.log_file_path = log_file_path

        log_window = ctk.CTkToplevel(root)
        log_window.title("Log Viewer")

        sort_label = ctk.CTkLabel(log_window, text="Sort by:")
        sort_label.pack()

        self.sort_column = tk.StringVar()
        self.sort_order = tk.StringVar()
        self.sort_column.set("Member Name")
        self.sort_order.set("asc")  # Default to ascending order

        # sort_option = tk.StringVar()
        # sort_option.set("All Entries")

        start_date_label = ctk.CTkLabel(log_window, text="Start Date (mm/dd/yyyy):")
        start_date_label.pack()
        self.start_date_entry = ctk.CTkEntry(log_window)
        self.start_date_entry.pack()

        end_date_label = ctk.CTkLabel(log_window, text="End Date (mm/dd/yyyy):")
        end_date_label.pack()
        self.end_date_entry = ctk.CTkEntry(log_window)
        self.end_date_entry.pack()

        member_name_label = ctk.CTkLabel(log_window, text="Member Name:")
        member_name_label.pack()
        self.member_name_entry = ctk.CTkEntry(log_window)
        self.member_name_entry.pack()

        login_reason_label = ctk.CTkLabel(log_window, text="Login Reason:")
        login_reason_label.pack()
        self.login_reason_entry = ctk.CTkEntry(log_window)
        self.login_reason_entry.pack(pady=(0, 10))


        apply_button = ctk.CTkButton(log_window, text="Apply", command=self.update_log)
        apply_button.pack()

        self.log_tree = ttk.Treeview(log_window, columns=("Member Name", "Login Time", "Login Reason"), show="headings",
                                height=log_tree_height)

   
    # all_entries_radio = tk.Radiobutton(log_window, text="All Entries", variable=sort_option, value="All Entries",
    #                                    command=self.update_log)
    # all_entries_radio.pack()
    #
    # date_range_radio = tk.Radiobutton(log_window, text="Date Range", variable=sort_option, value="Date Range",
    #                                   command=self.update_log)
    # date_range_radio.pack()
    #
    # member_name_radio = tk.Radiobutton(log_window, text="Member Name", variable=sort_option, value="Member Name",
    #                                    command=self.update_log)
    # member_name_radio.pack()

        self.column_sort_data = {
            "Member Name": {"order": "asc", "icon": "↓"},
            "Login Time": {"order": "asc", "icon": "↓"},
            "Login Reason": {"order": "asc", "icon": "↓"},
        }

        for column in self.column_sort_data:
            self.log_tree.heading(column, text=column + " " + self.column_sort_data[column]["icon"],
                            command=lambda c=column: self.toggle_sort_column(c))

        self.log_tree.heading("Member Name", text="Member Name", command=lambda: self.toggle_sort_column("Member Name"))
        self.log_tree.heading("Login Time", text="Login Time", command=lambda: self.toggle_sort_column("Login Time"))
        self.log_tree.column("Login Time", width=210)
        self.log_tree.heading("Login Reason", text="Login Reason", command=lambda: self.toggle_sort_column("Login Reason"))

        self.log_tree.pack(side="left", fill="both", padx=(20, 0), pady=20)

        self.log_tree_scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=self.log_tree_scrollbar.set)
        self.log_tree_scrollbar.pack(side="right", padx=(0, 10), pady=10, fill="y")

        log_window.bind('<Return>', self.update_log)

        self.update_log()

        log_window.attributes('-topmost', True)
        log_window.update()
        log_window.attributes('-topmost', False)
        log_window.focus()

    def update_log(self, events=None):
        log_data = self.get_all_logins()

        # selected_option = sort_option.get()
        filtered_data = log_data

        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        selected_member = self.member_name_entry.get().lower()

        login_reason = self.login_reason_entry.get().lower()

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
        if selected_member:
            filtered_data = filtered_data[filtered_data["name_lower"].str.contains(selected_member)]
        if login_reason:
            filtered_data = filtered_data[filtered_data["login_reason"].str.contains(login_reason)]

        for record in self.log_tree.get_children():
            self.log_tree.delete(record)

        column_mapping = {
            "member name": "name",
            "login time": "login_time",
            "login reason": "login_reason"
        }

        key = column_mapping[self.sort_column.get().lower()]
        ascending = self.sort_order.get() == "asc"
        sorted_data = filtered_data.sort_values(by=key, ascending=ascending)

        for _, entry in sorted_data.iterrows():
            member_name = entry["name"]
            login_time = entry["login_time"]
            login_reason = entry["login_reason"]
            self.log_tree.insert("", "end", values=(member_name, login_time, login_reason.capitalize()))

    def toggle_sort_column(self, col):
        current_column = self.sort_column.get()
        current_order = self.sort_order.get()

        if current_column == col:
            new_order = "asc" if current_order == "desc" else "desc"
            self.sort_order.set(new_order)
        else:
            self.sort_column.set(col)
            self.sort_order.set("asc")

        for column in self.column_sort_data:
            if column == col:
                self.column_sort_data[column]["icon"] = "▲" if self.sort_order.get() == "asc" else "▼"
            else:
                self.column_sort_data[column]["icon"] = ""

        self.update_log()
        self.update_sort_icons()

    def update_sort_icons(self):
        for column in self.column_sort_data:
            heading_text = column + " " + self.column_sort_data[column]["icon"]
            self.log_tree.heading(column, text=heading_text)

    def get_all_logins(self):
        logins = pd.read_csv(self.log_file_path)
        logins["login_time"] = pd.to_datetime(logins["login_time"])
        return logins