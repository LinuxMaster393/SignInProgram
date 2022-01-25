import datetime
import json
import logging
import os
import traceback
from typing import List, Any

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class Entry:
    def __init__(self, _name: str, signIn, signOut, ID):
        self.name = _name
        self.signIn = signIn
        if signOut is not None:
            self.signOutTime = signOut
            self.totalTime = signOut - signIn
        else:
            self.signOutTime = None
            self.totalTime = None
        self.id = ID

    def sign_out(self):
        self.signOutTime = datetime.datetime.today()
        self.totalTime = (self.signOutTime - self.signIn)

    class EntryEncoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            if isinstance(o, Entry):
                return {
                        "Entry": {
                            "Name": o.name,
                            "Sign In": o.signIn,
                            "Sign Out": o.signOutTime,
                            "ID": o.id
                        }
                    }
            if isinstance(o, datetime.datetime):
                return o.isoformat(sep=" ", timespec="seconds")
            return json.JSONEncoder().default(o)


class SaveFile:
    def __init__(self, file):
        """
        :type file: str
        """
        if not os.listdir("./").__contains__("Records"):
            os.mkdir("Records")
        self.dir_fd = os.open('Records', os.O_RDONLY)
        self.saveFile = open(file, "r", opener=self.opener)
        self.saveFileWrite = file

    def opener(self, path, flags):
        return os.open(path, flags, dir_fd=self.dir_fd)

    def markUploaded(self, entries: List[Entry]):
        json.dump({
                    "Database": {
                        "Uploaded": True,
                        "Entries": entries
                    }
                }, open(self.saveFileWrite, "w", opener=self.opener), cls=Entry.EntryEncoder, indent=2)


def EntryDecoder(dct):
    if "Database" in dct:
        exit(0)
    if "Entry" in dct:
        if dct["Entry"]["Sign Out"] is None:
            return Entry(dct["Entry"]["Name"], datetime.datetime.fromisoformat(dct["Entry"]["Sign In"]),
                         None, dct["Entry"]["ID"])
        else:
            return Entry(dct["Entry"]["Name"], datetime.datetime.fromisoformat(dct["Entry"]["Sign In"]),
                         datetime.datetime.fromisoformat(dct["Entry"]["Sign Out"]), dct["Entry"]["ID"])

    return dct


def gSheet(file: str, config: dict):
    """
    Upload file to a Google sheet.
    :param file: The file to upload
    :param config: A dictionary containing the Upload configuration.
    """

    # Google Sheets API Setup
    logging.debug("Uploading gSheet")

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of a sample spreadsheet.
    # SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    # SAMPLE_RANGE_NAME = 'Class Data!A2:E'

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config["Credentials File Name"], SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    spreadsheet_id: str = config["Upload Destination"]

    # End Google Sheets API Setup

    logging.info("Fetching from Json...")
    saveFile = SaveFile(file)
    entries = json.load(saveFile.saveFile, object_hook=EntryDecoder)
    if not isinstance(entries, list):
        raise TypeError("Incompatible or broken record file.")
    for i in entries:
        if not isinstance(i, Entry):
            raise TypeError("Incompatible or broken record file.")
    logging.info("Fetch from Json Complete.")

    values = []

    for i in entries:
        if i.signOutTime is not None:
            values.append(
                [
                    i.name,
                    i.signIn.isoformat(sep=" ", timespec="seconds"),
                    i.signOutTime.isoformat(sep=" ", timespec="seconds"),
                ]
            )
        else:
            values.append(
                [

                    i.name,
                    i.signIn.isoformat(sep=" ", timespec="seconds"),
                    ""

                ]
            )

    body = {
        # A list of updates to apply to the spreadsheet.
        # Requests will be applied in the order they are specified.
        # If any request is not valid, no requests will be applied.
        'values': values
    }

    request = sheet.values().append(
        spreadsheetId=spreadsheet_id, range='Logs!A2:C',
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS", body=body
    )
    response = request.execute()

    print(response)
    logging.debug(response)
    print("\n\n")

    saveFile.markUploaded(entries)
    saveFile.saveFile.close()


def main(file: str, config: dict):
    """methodsFromConfig = config["Uploader Methods"].split(",")
    methods = []

    for i in methodsFromConfig:
        methods.append(i.strip())

    if "Google Sheet" in methods:
        gSheet(file, config)"""
    logging.debug("Running Main")
    gSheet(file, config)


if __name__ == '__main__':
    import ConfigManager

    logging.basicConfig(filename='SignInProgramUpload.log',
                        level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s: %(module)s.%(funcName)s():%(lineno)d : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    main("Records/" + str(datetime.date.today()) + "_Record.json", ConfigManager.load()["GUI"]["UPLOADER"])
