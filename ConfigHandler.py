import configparser
import os
from typing import Any


class ConfigHandler:
    def __init__(self):
        if not os.path.exists("config.ini"):
            with open('config.ini', "w", encoding="utf-8") as f:
                f.writelines([
                    "[DEFAULT]\n",
                    "AdminRfidCode = -1\n",
                    "FlightCircleApiKey = -1\n",
                    "LastLogTimeProcessed = -1\n",
                    "MaxHoursPerWeek = 12\n",
                    "DollarsPerHour = 16\n",
                    "LoginSearchTypeTag = work to fly\n"
                ])

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
    
    # Note that path should be segmented by a /, so "DEFAULT/Whatever"
    def get_config_element(self, path):
        paths = path.split("/")
        
        requested = self.config
        for elem in paths:
            requested = requested[elem]
        
        return requested
