import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import dateMgr
from colorama import Fore, Style, init

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
# Global credentials variable
credentials = None
# Initialize colorama
init(autoreset=True)

##########################################
##### Google Authentication function #####
##########################################
def authenticate():
    try:
        # Authenticates the user and sets the global credentials variable.
        global credentials
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            print("Credentials got from token.json")
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            print("Credentials not found, logging in ...")
            if creds and creds.expired and creds.refresh_token:
                print("Credentials expired, refreshing ...")
                creds.refresh(Request())
            else:
                print("Authenticating using settings from credentials.json ...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                print("Authenticating using credentials.json and saving credentials to token.json ...")
                token.write(creds.to_json())
                print("Credentials saved to token.json")
            
        credentials = creds
    except HttpError:
       print(Fore.RED + "HTTP Error")

######################################
##### Calendar inquiry functions #####
######################################
##### Count calendar events from start date up to Today included
"""
Counts events in a Google Calendar timeframe from start_date up to Today included.

Args:
  event_title: The title of the events to count.
  start_date: The start date of the timeframe.

Returns:
  The number of events found.
"""
def countCalendarEventsToday(event_title, start_date):
  end_date = dateMgr.getTodayDate()
  return countCalendarEvents(event_title, start_date, end_date)

##### Count calendar events from start date up to end date
"""
Counts events in a Google Calendar timeframe from start_date up to end_date.

Args:
  event_title: The title of the events to count.
  start_date: The start date of the timeframe.
  end_date: The end date of the timeframe.

Returns:
  The number of events found.
"""
def countCalendarEvents(event_title, start_date, end_date):
  global credentials
  try:
    service = build('calendar', 'v3', credentials=credentials)
    
    # Convert start_date and end_date to datetime objects ISO 8601 format
    start_time = dateMgr.getDateTimeIsoFormat(start_date)
    end_time = dateMgr.getDateTimeIsoFormat(end_date)

    print(f"Getting '{event_title}' events from {start_date} to {end_date}")

    events_result = service.events().list(
        calendarId='primary',
        q=event_title,
        timeMin=start_time,
        timeMax=end_time,
        maxResults=1000,
        singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    return len(events)
  
  except HttpError as error:
    print(Fore.RED + f"An error occurred: {error}")

##### List 10 upcoming calendar events
"""
Shows basic usage of the Google Calendar API. 
Prints the start and name of the next 10 events on the user's calendar.

Args:
  None.

Returns:
  The number of events found.
"""
def getUpcomingEvents():
  global credentials
  try:
    service = build('calendar', 'v3', credentials=credentials)

    # Call the Calendar API
    now = dateMgr.getDateTimeIsoFormat(dateMgr.getTodayDate())
    print("Getting the upcoming 10 events")
    events_result = (service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",).execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return
    return events

  except HttpError as error:
    print(Fore.RED + f"An error occurred: {error}")

authenticate()