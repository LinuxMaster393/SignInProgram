import datetime
import json
# from builtins import function
import logging
from typing import Optional, TextIO, Any, List, overload

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class Entry:

    def __init__(self, name: str, ID: int):
        """
        :param name: The name of the entry.
        :param ID: the ID of the person.
        """
        self.upload: bool = True
        self.name: str = name
        self.ID: int = ID
        self.signin: datetime.datetime = datetime.datetime.now()
        self.signin.replace(microsecond=0)
        self.signout: Optional[datetime.datetime] = None
        self.signtotal: Optional[datetime.timedelta] = None

    def update(self, **kwargs):
        updateTotal: bool = False
        if "name" in kwargs:
            if self.name != kwargs["name"]:
                self.name = kwargs["name"]
                self.upload = True
        if "ID" in kwargs:
            if self.ID != kwargs["ID"]:
                self.ID = kwargs["ID"]
                self.upload = True
        if "signin" in kwargs:
            if self.signin != datetime.datetime.fromisoformat(kwargs["signin"]):
                self.signin = datetime.datetime.fromisoformat(kwargs["signin"])
                self.upload = True
                updateTotal = True
        if "signout" in kwargs:
            if self.signout != datetime.datetime.fromisoformat(kwargs["signout"]):
                self.signout = datetime.datetime.fromisoformat(kwargs["signout"])
                self.upload = True
                updateTotal = True

        if self.signout is not None and updateTotal:
            self.signtotal = self.signout - self.signin
        elif self.signout is None:
            self.signtotal = None

    def logout(self):
        self.update(signout=datetime.datetime.now().isoformat())


class Database:
    """
    A class containing all the entry logs from the Sign in program.
    """

    def __init__(self):
        super().__init__()
        self.uploaded: bool = False
        self.data: List[Entry] = []

    def updateEntry(self, ID: int, **kwargs):
        """
        Updates a person's entry.

        :param ID: The ID of the entry to update.
        """
        for i in self.data:
            if i.ID == ID:
                i.update(**kwargs)
                if i.upload:
                    self.uploaded = False
                return
        logging.warning("Could not find entry with an ID of " + str(ID) + " of type " + str(type(ID)))
        print("Could not find entry with an ID of", ID, "of type", type(ID))

    def getEntry(self, ID: int) -> Optional[Entry]:
        for i in self.data:
            if i.ID == ID:
                return i
        logging.warning("Could not find entry with an ID of " + str(ID))

    def removeEntry(self, ID: int):
        """
        Removes a person's entry.
        :param ID: The ID of the entry to remove.
        """
        for i in self.data:
            if i.ID == ID:
                self.data.remove(i)
                for j in range(len(self.data)):
                    self.data[j].update(ID=j)
                break

    def logInOrOut(self, name: str) -> bool:
        """
        Logs a person in or out of the database.
        :param name: Name of the person to login or logout.
        :return: If the person was logged out.
        """
        name = name.title()
        logging.info("Log in or out " + name)
        for i in self.data:
            if i.name == name and i.signout is None:
                i.logout()
                if i.upload:
                    self.uploaded = False
                return True

        self.data.append(Entry(name, len(self.data)))
        return False

    def genListStore(self) -> Gtk.ListStore:
        """
        Returns a ListStore containing all the entries for display.
        :return: The ListScore containing all the entries for display.
        """
        store = Gtk.ListStore(str, str, str, str)
        for i in self.data:
            assert isinstance(i, Entry)
            if i.signout is None:
                store.append([i.name, i.signin.isoformat(" ", "seconds"), "", ""])
            else:
                store.append([i.name, i.signin.isoformat(" ", "seconds"), i.signout.isoformat(" ", "seconds"),
                              str(i.signtotal).partition(".")[0]])

        return store

    def logAllOut(self):
        for i in self.data:
            if i.signout is None:
                i.logout()
                if i.upload:
                    self.uploaded = False

    def isAllOut(self):
        for i in self.data:
            if i.signout is None:
                return False
        return True

    class DatabaseEncoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            if isinstance(o, Database):
                return {
                    "Database": {
                        "Uploaded": o.uploaded,
                        "Entries": o.data
                    }
                }
            if isinstance(o, Entry):
                return {
                        "Entry": {
                            "Name": o.name,
                            "Sign In": o.signin,
                            "Sign Out": o.signout,
                            "ID": o.ID,
                            "Changed": o.upload
                        }
                    }
            if isinstance(o, datetime.datetime):
                return o.isoformat(sep=" ", timespec="seconds")
            return json.JSONEncoder().default(o)

    @staticmethod
    def databaseDecoder(dct: dict):
        if "Database" in dct:
            database = Database()
            if "Uploaded" in dct["Database"]:
                database.uploaded = dct["Database"]["Uploaded"]
            database.data.extend(Database.databaseDecoder(dct["Database"]["Entries"]))
            return database
        if "Entry" in dct:
            i = dct["Entry"]
            entry = Entry(i["Name"], i["ID"])
            entry.signin = datetime.datetime.fromisoformat(i["Sign In"])
            if i["Sign Out"] is None:
                entry.signout = None
                entry.signtotal = None
            else:
                entry.signout = datetime.datetime.fromisoformat(i["Sign Out"])
                entry.signtotal = entry.signout - entry.signin
            if "Changed" in i:
                entry.upload = i["Changed"]
            return entry
        return dct

    @staticmethod
    def loadFromFile(file: TextIO):
        db = json.load(file, object_hook=Database.databaseDecoder)
        return db

    def saveToFile(self, file: TextIO):
        json.dump(self, file, cls=self.DatabaseEncoder, indent=2)
