import datetime
import json
# from builtins import function
import logging
from typing import Optional, TextIO, Any

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class Entry:

    def __init__(self, name: str, ID: int):
        """
        :param name: The name of the entry.
        :param ID: the ID of the person.
        """
        self.name: str = name
        self.ID: int = ID
        self.signin: datetime.datetime = datetime.datetime.now()
        self.signin.replace(microsecond=0)
        self.signout: Optional[datetime.datetime] = None
        self.signtotal: Optional[datetime.timedelta] = None

    def update(self, **kwargs):
        updateTotal: bool = False
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "ID" in kwargs:
            self.ID = kwargs["ID"]
        if "signin" in kwargs:
            self.signin = datetime.datetime.fromisoformat(kwargs["signin"])
            updateTotal = True
        if "signout" in kwargs:
            self.signout = datetime.datetime.fromisoformat(kwargs["signout"])
            updateTotal = True

        if self.signout is not None and updateTotal:
            self.signtotal = self.signout - self.signin
        elif self.signout is None:
            self.signtotal = None

    def logout(self):
        self.update(signout=datetime.datetime.now().isoformat())


class Database(list):
    """
    A class containing all the entry logs from the Sign in program.
    """

    def __init__(self):
        super().__init__()
        self.uploaded: bool = False

    def updateEntry(self, ID: int, **kwargs):
        """
        Updates a person's entry.

        :param ID: The ID of the entry to update.
        """
        for i in self:
            if i.ID == ID:
                i.update(**kwargs)
                return
        logging.warning("Could not find entry with an ID of " + str(ID) + " of type " + str(type(ID)))
        print("Could not find entry with an ID of", ID, "of type", type(ID))

    def getEntry(self, ID: int) -> Optional[Entry]:
        for i in self:
            if i.ID == ID:
                return i
        logging.warning("Could not find entry with an ID of " + str(ID))

    def removeEntry(self, ID: int):
        """
        Removes a person's entry.
        :param ID: The ID of the entry to remove.
        """
        for i in self:
            if i.ID == ID:
                self.remove(i)
                for j in range(len(self)):
                    self[j].update(ID=j)
                break

    def logInOrOut(self, name: str) -> bool:
        """
        Logs a person in or out of the database.
        :param name: Name of the person to login or logout.
        :return: If the person was logged out.
        """
        name = name.title()
        logging.info("Log in or out " + name)
        for i in self:
            if i.name == name and i.signout is None:
                i.logout()
                return True

        self.append(Entry(name, len(self)))
        return False

    def genListStore(self) -> Gtk.ListStore:
        """
        Returns a ListStore containing all the entries for display.
        :return: The ListScore containing all the entries for display.
        """
        store = Gtk.ListStore(str, str, str, str)
        for i in self:
            assert isinstance(i, Entry)
            if i.signout is None:
                store.append([i.name, i.signin.isoformat(" ", "seconds"), "", ""])
            else:
                store.append([i.name, i.signin.isoformat(" ", "seconds"), i.signout.isoformat(" ", "seconds"),
                              str(i.signtotal).partition(".")[0]])

        return store

    def logAllOut(self):
        for i in self:
            if i.signout is None:
                i.logout()

    def isAllOut(self):
        for i in self:
            if i.signout is None:
                return False
        return True

    class DatabaseEncoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            if isinstance(o, Database):
                array = []
                array.extend(o)
                return {
                    "Database": {
                        "Uploaded": o.uploaded,
                        "Entries": array
                    }
                }
            if isinstance(o, Entry):
                return {
                        "Entry": {
                            "Name": o.name,
                            "Sign In": o.signin,
                            "Sign Out": o.signout,
                            "ID": o.ID
                        }
                    }
            if isinstance(o, datetime.datetime):
                return o.isoformat(sep=" ", timespec="seconds")
            return json.JSONEncoder().default(o)

    @staticmethod
    def databaseDecoder(dct: dict):
        if "Database" in dct:
            database = Database()
            database.uploaded = dct["Database"]["Uploaded"]
            database.extend(Database.databaseDecoder(dct["Database"]["Entries"]))
            return database
        if "Entry" in dct:
            i = dct["Entry"]
            entry = Entry(i["Name"], i["ID"])
            entry.signin = datetime.datetime.fromisoformat(i["Sign In"])
            if i["Sign Out"] is None:
                entry.signout = None
                entry.signtotal = None
            else:
                entry.update(signout=i["Sign Out"])
            return entry
        return dct

    @staticmethod
    def loadFromFile(file: TextIO):
        db = Database()
        load = json.load(file, object_hook=Database.databaseDecoder)
        if "Uploaded" in load:
            db.uploaded = load["Uploaded"]
            for i in load["Entries"]:
                db.append(i)
        else:
            for i in load:
                db.append(i)
        return db

    def saveToFile(self, file: TextIO):
        json.dump(self, file, cls=self.DatabaseEncoder, indent=2)
