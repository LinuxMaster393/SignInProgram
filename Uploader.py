import datetime
import json
import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from Database import Database, Entry


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

    def markUploaded(self, database: Database):
        database.uploaded = True
        database.saveToFile(open(self.saveFileWrite, "w", opener=self.opener))


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
    database = json.load(saveFile.saveFile, object_hook=Database.databaseDecoder)
    if not isinstance(database, Database):
        raise TypeError("Incompatible or broken record file.")
    for i in database.data:
        if not isinstance(i, Entry):
            raise TypeError("Incompatible or broken record file.")
    logging.info("Fetch from Json Complete.")

    if database.uploaded:
        logging.warning("File already marked as uploaded. Skipping.")
        return

    values = []

    for i in database.data:
        if i.upload:
            if i.signout is not None:
                values.append(
                    [
                        i.name,
                        i.signin.isoformat(sep=" ", timespec="seconds"),
                        i.signout.isoformat(sep=" ", timespec="seconds"),
                    ]
                )
            else:
                values.append(
                    [

                        i.name,
                        i.signin.isoformat(sep=" ", timespec="seconds"),
                        ""
                    ]
                )
            i.upload = False

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

    saveFile.markUploaded(database)
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


def uploadAllNotUploaded(config: dict):
    records = os.scandir("Records")
    for i in records:
        assert(isinstance(i, os.DirEntry))
        if i.is_file() and i.name.endswith(".json"):
            file = open(i.path, "r")
            if file.readlines(3)[2].strip() == '"Uploaded": false,':
                main(i.name, config)


def markAllUploaded():
    records = os.scandir("Records")
    for i in records:
        assert (isinstance(i, os.DirEntry))
        if i.is_file() and i.name.endswith(".json"):
            logging.info("Fetching from Json...")
            saveFile = SaveFile(i.name)
            database = json.load(saveFile.saveFile, object_hook=Database.databaseDecoder)
            if not isinstance(database, Database):
                raise TypeError("Incompatible or broken record file.")
            for j in database.data:
                if not isinstance(j, Entry):
                    raise TypeError("Incompatible or broken record file.")
                j.upload = False
            logging.info("Fetch from Json Complete. Marking as Uploaded.")
            saveFile.markUploaded(database)


if __name__ == '__main__':
    import ConfigManager

    logging.basicConfig(filename='SignInProgramUpload.log',
                        level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s: %(module)s.%(funcName)s():%(lineno)d : %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    main("Records/" + str(datetime.date.today()) + "_Record.json", ConfigManager.load()["GUI"]["UPLOADER"])
