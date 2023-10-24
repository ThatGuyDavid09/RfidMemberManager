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

from LogWindow import LogWindow

def view_logs(events=None):
    file_path = log_entry.get()

    if os.path.exists(file_path):
        log_window = LogWindow(root, file_path, 20)
    else:
        log_window = ctk.CTkToplevel(root)
        log_window.title("Error")

        start_date_label = ctk.CTkLabel(log_window, text="That log does not exist!")
        start_date_label.pack(padx=10, pady=10)

ctk.set_appearance_mode("light")
root = ctk.CTk()
root.title("Flight Club Login Viewer")
# root.geometry("500x400")

icon = tk.PhotoImage(file="fc_502_logo.png")
root.iconphoto(False, icon)

log_entry_frame = ctk.CTkFrame(root)
log_entry_frame.pack(side=tk.TOP, padx=10, pady=10)

log_entry_label = ctk.CTkLabel(log_entry_frame, text="Log file name")
log_entry_label.pack(side=tk.LEFT, padx=(5, 0))

log_entry = ctk.CTkEntry(log_entry_frame, width=150)
log_entry.pack(side=tk.LEFT, padx=5)

log_entry.bind('<Return>', view_logs)

view_log_button = ctk.CTkButton(root, text="View Log", command=view_logs)
view_log_button.pack(pady=(5, 10))

root.mainloop()