import configparser
import logging
import os
import re
import sys
from typing import Dict, Any


def __generateConfig__():
    """
    Generates a configuration file for the program.
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config["MAIN"] = {"Window Name": "Sign In Program",
                      "# Separate names with commas.": None,
                      "Auto Complete": "",
                      "Auto Log Out On Quit": True,
                      "Auto Save On Quit": True,
                      "Auto Upload On Quit": False,
                      "# Formatted in 24 hour time as HH:MM:SS, put \"None\" to disable auto quitting.": None,
                      "Auto Quit Time": "none"}
    config["UPLOADER"] = {
        "Credentials File Name": "credentials.json",
        "# URL to the google sheet.": None,
        "Upload Destination": ""
    }
    with open("SignIn.conf", "w") as cf:
        config.write(cf)


def load() -> Dict[str, Any]:
    """
    Loads a configuration file and creates one if needed.
    :return: Dictionary of configurations.
    """
    logging.info("Loading Config")
    if "SignIn.conf" not in os.listdir():
        __generateConfig__()

    config = configparser.ConfigParser()
    config.read_dict({
        "MAIN": {
            "Window Name": "Sign In Program",
            "Auto Complete": "[]",
            "Auto Log Out On Quit": True,
            "Auto Save On Quit": True,
            "Auto Upload On Quit": False,
            "Auto Quit Time": "none"
        },
        "UPLOADER": {
            "Credentials File Name": "credentials.json",
            "Uploading Methods": "Google Sheet",
            "Upload Destination": ""
        }
    })
    config.read("SignIn.conf")

    out = {
        "GUI": {
            "Window Name": config["MAIN"]["Window Name"],
            "Auto Complete": config["MAIN"]["Auto Complete"],
            "Auto Log Out On Quit": config["MAIN"].getboolean("Auto Log Out On Quit"),
            "Auto Save On Quit": config["MAIN"].getboolean("Auto Save On Quit"),
            "Auto Upload On Quit": config["MAIN"].getboolean("Auto Upload On Quit"),
            "Auto Quit Time": config["MAIN"]["Auto Quit Time"],
            "UPLOADER": Any
        },
        "UPLOADER": {
            "Credentials File Name": config["UPLOADER"]["Credentials File Name"],
            "Uploading Methods": config["UPLOADER"]["Uploading Methods"],
            "Upload Destination": None if config["UPLOADER"]["Upload Destination"] == "" else
            googleSheetURLPattern.match(config["UPLOADER"]["Upload Destination"])[3]
        }
    }

    out['GUI'].update(UPLOADER=out['UPLOADER'])
    # noinspection PyTypeChecker
    if out["GUI"]["UPLOADER"]["Upload Destination"] is None:
        logging.warning("No upload destination set in config file.")

    return out


googleSheetURLPattern = re.compile("(\S*)docs.google.com/spreadsheets/(d|u/0)/(\S+)/(\S*)")

if __name__ == "__main__":
    if "generate" in sys.argv:
        __generateConfig__()
    else:
        print(load())
