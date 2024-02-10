#  SignInProgram - Record attendance logs and upload to a Google Sheet.
#  Copyright (C) 2024 LinuxMaster393
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os
import sys
import threading
import traceback
from typing import Optional

args = sys.argv
timer: Optional[threading.Timer] = None


def main():
    global timer
    from datetime import date, datetime, time, timedelta
    from json import JSONDecodeError

    import ConfigManager
    import GUI_GTK as GUI
    import Uploader
    from Database import Database

    def stop(*args, **kwargs):
        GUI.app.exit_window()

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

    if config["GUI"]["Auto Quit Time"] != "none":
        if datetime.now().time() > time.fromisoformat(config["GUI"]["Auto Quit Time"]):
            timeTill = datetime.combine(date.today() + timedelta(days=1),
                                        time.fromisoformat(config["GUI"]["Auto Quit Time"])) - datetime.now()
        else:
            timeTill = datetime.combine(date.today(), time.fromisoformat(config["GUI"]["Auto Quit Time"])) - datetime.now()
        logging.debug("Auto Quitting at: " + str(timeTill))
        timer = threading.Timer(timeTill.total_seconds(), stop)
        timer.start()

    GUI.main(config["GUI"], database)

    if timer is not None:
        timer.cancel()

    if config["UPLOADER"]["Upload Destination"] is not None and \
            config["GUI"]["Auto Upload On Quit"] and \
            GUI.saveFile != "":
        if config["UPLOADER"]["Auto Log Out On Quit"]:
            database.logAllOut()
        Uploader.main(GUI.saveFile, config["UPLOADER"])


if __name__ == '__main__':
    logging.basicConfig(filename='SignInProgram.log',
                        level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s: %(module)s.%(funcName)s():%(lineno)d : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    try:
        if "mark-all-uploaded" in args:
            import Uploader
            Uploader.markAllUploaded()
        elif "upload-all" in args:
            import Uploader
            import ConfigManager
            Uploader.uploadAllNotUploaded(ConfigManager.load())
        else:
            main()
    except BaseException as e:
        logging.error("".join(traceback.format_exception(type(e), e, e.__traceback__)).rstrip("\n"))
        raise e

    if timer is not None:
        timer.cancel()
    if "no-update" not in args:
        os.execlp("bash", "bash", "Updater.sh")
