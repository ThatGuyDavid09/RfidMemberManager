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

def view_logs():
    pass

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