import logging
import traceback
import os
import sys

# TODO Add SignInProgram.desktop

args = sys.argv


def main():

    from datetime import date
    from json import JSONDecodeError

    import ConfigManager
    import GUI_GTK as GUI
    import Uploader
    from Database import Database

    config = ConfigManager.load()

    database: Database

    try:
        with open("Records/" + str(date.today()) + "_Record.json", "r") as file:
            database = Database.loadFromFile(file)
            GUI.saveFile = str(date.today()) + "_Record.json"

    except OSError:
        database = Database()
    except JSONDecodeError:
        database = Database()

    GUI.main(config["GUI"], database)
    if config["GUI"]["UPLOADER"]["Upload Destination"] is not None and \
            config["GUI"]["Auto Upload On Quit"] and \
            GUI.saveFile != "":
        if config["GUI"]["UPLOADER"]["Auto Log Out On Quit"]:
            database.logAllOut()
        Uploader.main(GUI.saveFile, config["GUI"]["UPLOADER"])


if __name__ == '__main__':
    logging.basicConfig(filename='SignInProgram.log',
                        level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s: %(module)s.%(funcName)s():%(lineno)d : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    try:
        main()
    except BaseException as e:
        logging.error("".join(traceback.format_exception(type(e), e, e.__traceback__)).rstrip("\n"))
        raise e

    if "no-update" not in args:
        os.execlp("bash", "bash", "Updater.sh")
