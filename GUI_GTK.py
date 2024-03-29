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
import traceback
from datetime import date, datetime
from typing import Union, Optional

import gi

from Database import Database
import Uploader

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, config: dict, *args, **kwargs):
        global database
        assert isinstance(database, Database)

        self.config = config
        self.changed = False

        # Creating the window and its properties.

        super(MainWindow, self).__init__(*args, title=config["Window Name"], **kwargs)
        self.connect("delete-event", self.on_destroy)
        self.set_default_size(500, 500)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)
        self.set_icon_from_file('Icon/icon.png')

        # Creating the header bar.

        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = config["Window Name"]
        self.menu = Gio.Menu()

        self.sectionA = Gio.Menu()
        self.sectionA.append_item(Gio.MenuItem().new("Open", "app.open"))
        self.sectionA.append_item(Gio.MenuItem().new("Save", "app.save"))
        self.sectionA.append_item(Gio.MenuItem().new("Upload", "app.upload"))
        self.menu.append_section(None, self.sectionA)

        self.sectionB = Gio.Menu()
        self.sectionB.append_item(Gio.MenuItem().new("Upload All", "app.upload-all"))
        self.menu.append_section(None, self.sectionB)

        self.menuButton = Gtk.MenuButton(menu_model=self.menu)
        self.header.pack_start(self.menuButton)
        self.set_titlebar(self.header)

        self.currentSaveFile = None

        # Creating the table that displays the entries.

        self.listStore = database.genListStore()

        self.tree = Gtk.TreeView(model=self.listStore)

        self.nameColumnRender = Gtk.CellRendererText()
        self.signInColumnRender = Gtk.CellRendererText()
        self.signOutColumnRender = Gtk.CellRendererText()

        self.nameColumnRender.set_property("editable", True)
        self.signInColumnRender.set_property("editable", True)
        self.signOutColumnRender.set_property("editable", True)

        renderer = Gtk.CellRendererText()

        for i, column_title in enumerate(["Name", "Sign In Time", "Sign Out Time", "Total Time"]):
            if column_title == "Name":
                column = Gtk.TreeViewColumn(column_title, self.nameColumnRender, text=i)
            elif column_title == "Sign In Time":
                column = Gtk.TreeViewColumn(column_title, self.signInColumnRender, text=i)
            elif column_title == "Sign Out Time":
                column = Gtk.TreeViewColumn(column_title, self.signOutColumnRender, text=i)
            else:
                column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            # column.set_sort_column_id(i)
            self.tree.append_column(column)

        self.nameColumnRender.connect("edited", self.nameEdited)
        self.signInColumnRender.connect("edited", self.signInEdited)
        self.signOutColumnRender.connect("edited", self.signOutEdited)

        self.box.pack_start(self.tree, True, True, 0)

        # Creating the entry box.

        self.entry = Gtk.Entry()

        # Creating the autofill.

        self.entryCompletionModel = Gtk.ListStore(str)

        self.entryCompletionNames = []

        for i in config["Auto Complete"].split(","):
            self.entryCompletionNames.append(i.strip())

        self.entryCompletionNames.sort()
        for i in self.entryCompletionNames:
            self.entryCompletionModel.append([i.strip()])

        self.entryCompletion = Gtk.EntryCompletion()
        self.entryCompletion.set_text_column(0)
        self.entryCompletion.set_model(self.entryCompletionModel)

        self.entry.set_completion(self.entryCompletion)
        self.entryCompletion.complete()

        # Done creating the autofill.

        self.entry.set_placeholder_text("Enter your name to sign in: ")
        self.entry.connect("activate", self.processEntry)

        self.box.pack_end(self.entry, False, True, 0)

        # Showing all widgets.

        self.show_all()

    def processEntry(self, widget: Gtk.Entry):
        global database
        assert isinstance(database, Database)
        logging.debug("Processing Entry")
        if not database.logInOrOut(widget.get_text()):
            self.updateAutoFill(widget.get_text())

        self.listStore = database.genListStore()
        self.tree.set_model(self.listStore)
        widget.set_text("")
        self.changed = True

    # noinspection PyUnusedLocal
    def nameEdited(self, widget, path, text):
        logging.info("Changing name of entry at " + path + " to \"" + text + "\"")
        global database
        assert isinstance(text, str)
        if text == "" or text.isspace():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Are you sure you want to delete this entry?",
            )
            dialog.format_secondary_text(
                "This can not be undone."
            )
            response = dialog.run()

            dialog.destroy()
            if response == Gtk.ResponseType.YES:
                self.updateAutoFill(database.getEntry(int(path)).name)
                database.removeEntry(int(path))
        else:
            self.updateAutoFill(database.getEntry(int(path)).name)
            database.updateEntry(int(path), name=text.title())
        self.updateEntries()
        self.updateAutoFill(text.title())
        # self.changed = True

    def signInEdited(self, widget, path, text):
        logging.info("Changing sign in time of entry at " + path + " to \"" + text + "\"")
        global database
        assert isinstance(text, str)
        if text == "" or text.isspace():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Are you sure you want to delete this entry?",
            )
            dialog.format_secondary_text(
                "This can not be undone."
            )
            response = dialog.run()

            dialog.destroy()
            if response == Gtk.ResponseType.YES:
                self.updateAutoFill(database.getEntry(int(path)).name)
                database.removeEntry(int(path))
        else:
            try:
                if database.getEntry(int(path)).signout is not None and \
                        database.getEntry(int(path)).signout < datetime.fromisoformat(text):
                    logging.warning("Sign in time came after sign out time while updating the sign in time.")
                    raise Exception("sign in time came after sign out time")
                database.updateEntry(int(path), signin=text)
            except Exception as e:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.CANCEL,
                    text="Invalid Sign In Time",
                )
                dialog.format_secondary_text(
                    "The time you inputted for the sign in time was incorrectly formatted or came after the sign out "
                    "time."
                )
                dialog.run()
                dialog.destroy()
        self.updateEntries()
        # self.changed = True

    def signOutEdited(self, widget, path, text):
        logging.info("Changing sign out time of entry at " + path + " to \"" + text + "\"")
        global database
        assert isinstance(text, str)
        if text == "" or text.isspace():
            database.updateEntry(int(path), signout=None)
        else:
            try:
                if database.getEntry(int(path)).signin > datetime.fromisoformat(text):
                    logging.warning("Sign out time came before sign in time while updating the sign out time.")
                    raise Exception("sign out time came before sign in time")
                database.updateEntry(int(path), signout=text)
            except Exception as e:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.CANCEL,
                    text="Invalid Sign out Time",
                )
                dialog.format_secondary_text(
                    "The time you inputted for the sign out time was incorrectly formatted or came before the sign in "
                    "time."
                )
                dialog.run()
                dialog.destroy()
        self.updateEntries()
        # self.changed = True

    @staticmethod
    def add_filters(dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Record Files")
        filter_text.add_pattern("*.json")
        dialog.add_filter(filter_text)

    # noinspection PyUnusedLocal
    def open(self, *args):
        global database
        assert isinstance(database, Database)
        dialog = Gtk.FileChooserDialog(title="Open", action=Gtk.FileChooserAction.OPEN)
        dialog.set_current_folder("Records")
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        self.add_filters(dialog)

        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            if len(database.data) > 0:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Do you want to replace the current entries?",
                )
                response = dialog.run()
                dialog.destroy()
                if response == Gtk.ResponseType.YES:
                    logging.debug("Reloading Database")
                    database = database.loadFromFile(open(filename, "r"))
                    self.updateEntries()
                    self.changed = False

            else:
                logging.debug("Reloading Database")
                database = database.loadFromFile(open(filename, "r"))
                self.updateEntries()
                self.changed = False

    # noinspection PyUnusedLocal
    def save(self, *args, skipAsking=False) -> bool:
        global database, saveFile
        assert isinstance(database, Database)
        if not skipAsking:

            dialog = Gtk.FileChooserDialog(title="Save", action=Gtk.FileChooserAction.SAVE)
            dialog.set_current_folder("Records")
            dialog.add_buttons(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            )
            dialog.set_do_overwrite_confirmation(True)
            self.add_filters(dialog)
            dialog.set_current_name(str(date.today()) + "_Record.json")

            response = dialog.run()
            filename = dialog.get_filename()
            dialog.destroy()

            if response == Gtk.ResponseType.OK:
                if not database.isAllOut():
                    if self.config["Auto Log Out On Quit"]:
                        database.logAllOut()
                    elif not skipAsking:
                        dialog = Gtk.MessageDialog(
                            transient_for=self,
                            flags=0,
                            message_type=Gtk.MessageType.WARNING,
                            buttons=Gtk.ButtonsType.YES_NO,
                            text="Not everyone has been logged out.",
                        )
                        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
                        dialog.format_secondary_text(
                            "Do you want to log everyone out?"
                        )
                        response = dialog.run()
                        dialog.destroy()
                        if response == Gtk.ResponseType.YES:
                            database.logAllOut()
                        elif response == Gtk.ResponseType.CANCEL:
                            logging.debug("User Canceled Action.")
                database.saveToFile(open(filename, "w"))
                saveFile = filename
                return True
            else:
                return False
        else:
            if self.config["Auto Log Out On Quit"]:
                database.logAllOut()
            elif not skipAsking:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Not everyone has been logged out.",
                )
                dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
                dialog.format_secondary_text(
                    "Do you want to log everyone out?"
                )
                response = dialog.run()
                dialog.destroy()
                if response == Gtk.ResponseType.YES:
                    database.logAllOut()
                elif response == Gtk.ResponseType.CANCEL:
                    logging.debug("User Canceled Action.")
            database.saveToFile(open("Records/" + str(date.today()) + "_Record.json", "w"))
            saveFile = str(date.today()) + "_Record.json"
            return True

    # noinspection PyUnusedLocal
    def upload(self, skipSaving=False, *args):
        if self.changed or database.uploaded:
            if skipSaving or self.save():
                if self.config["UPLOADER"]["Upload Destination"] is not None:
                    Uploader.main(saveFile, self.config["UPLOADER"])

    # noinspection PyUnusedLocal
    def uploadAll(self, *args):
        if self.changed:
            self.save()
        if self.config["UPLOADER"]["Upload Destination"] is not None:
            Uploader.uploadAllNotUploaded(self.config["UPLOADER"])

    # noinspection PyUnusedLocal
    def on_destroy(self, *args) -> bool:
        global database
        assert isinstance(database, Database)
        logging.debug("Running On Destroy")

        if self.changed:
            if self.config["Auto Save On Quit"]:
                self.save(skipAsking=True)
                if self.config["Auto Upload On Quit"]:
                    self.upload(skipSaving=True)
                else:
                    dialog = Gtk.MessageDialog(
                        transient_for=self,
                        flags=0,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text="Do you wish to upload?",
                    )
                    dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
                    response = dialog.run()

                    dialog.destroy()
                    if response == Gtk.ResponseType.YES:
                        self.upload(skipSaving=True)
                    elif response == Gtk.ResponseType.CANCEL:
                        return True
            else:
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Save Changes before closing?",
                )
                dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
                dialog.format_secondary_text(
                    "If you don't save, all records from this session will be permanently lost."
                )
                response = dialog.run()

                dialog.destroy()
                if response == Gtk.ResponseType.YES:
                    return not self.save()
                elif response == Gtk.ResponseType.CANCEL:
                    return True

        self.get_application().on_quit()
        return False

    def exit_window(self):
        global database
        assert isinstance(database, Database)
        logging.debug("exiting window")

        if self.changed:
            if self.config["Auto Save On Quit"]:
                self.save(skipAsking=True)

        self.get_application().on_quit()

    def updateEntries(self):
        global database
        assert isinstance(database, Database)
        logging.debug("Updating Entries")
        self.listStore = database.genListStore()
        self.tree.set_model(self.listStore)
        self.changed = True

    def updateAutoFill(self, name: str):
        name = name.title()
        self.entryCompletionModel = Gtk.ListStore(str)

        if name not in self.entryCompletionNames:
            self.entryCompletionNames.append(name)
        elif name not in self.config["Auto Complete"]:
            self.entryCompletionNames.remove(name)
        self.entryCompletionNames.sort()

        for i in self.entryCompletionNames:
            self.entryCompletionModel.append([i.strip()])

        self.entryCompletion.set_model(self.entryCompletionModel)

        self.entry.set_completion(self.entryCompletion)
        self.entryCompletion.complete()


class Application(Gtk.Application):
    def __init__(self, config: dict, **kwargs):
        super().__init__(application_id="none.none.none", **kwargs)
        self.window: Optional[MainWindow] = None
        self.config = config

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.makeWindow()

        action = Gio.SimpleAction(name="open")
        action.connect("activate", self.window.open)
        self.add_action(action)

        action = Gio.SimpleAction(name="save")
        action.connect("activate", self.window.save)
        self.add_action(action)

        action = Gio.SimpleAction(name="upload")
        action.connect("activate", self.window.upload)
        self.add_action(action)

        action = Gio.SimpleAction(name="update")
        action.connect("activate", self.window.updateEntries)
        self.add_action(action)

        action = Gio.SimpleAction(name="upload-all")
        action.connect("activate", self.window.uploadAll)
        self.add_action(action)

    def makeWindow(self):
        global database
        assert isinstance(database, Database)
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = MainWindow(self.config, application=self)

    def do_activate(self):
        self.window.present()

    # noinspection PyUnusedLocal
    def on_quit(self, *args, **kwargs):
        self.window.destroy()
        self.quit()

    def exit_window(self):
        self.window.exit_window()


def main(config: dict, _database: Database):
    """
    :param config: A dictionary containing the GUI configuration.
    :param _database: The Database for the entries.
    """
    global database, app
    database = _database

    if "Records" not in os.listdir():
        os.mkdir("Records")

    app = Application(config)
    args = sys.argv
    if "no-update" in args:
        args.remove("no-update")
    app.run(args)


database: Union[Database, None] = None
saveFile = ""
app: Optional[Application] = None

if __name__ == "__main__":
    import ConfigManager

    main(ConfigManager.load()["GUI"], Database())
