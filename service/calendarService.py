import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils import dateMgr
from datetime import date
from colorama import Fore, Style, init
from log import loggingFactory

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Global credentials variable
credentials = None

# Initialize colorama
init(autoreset=True)

# Initialize logger at the top so it's available everywhere
logger = loggingFactory.get_logger('calendar_service')

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
            logger.info("Getting credentials from token.json")
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            logger.warning("No valid credentials were found, logging in ...")
            if creds and creds.expired and creds.refresh_token:
                logger.warning("Credentials expired, refreshing ...")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}. Re-authenticating ...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", SCOPES
                    )
                    creds = flow.run_local_server(port=0)
            else:
                logger.info("Authenticating using settings from credentials.json ...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                logger.info("Authenticating using credentials.json and saving credentials to token.json ...")
                token.write(creds.to_json())
                logger.info("Credentials saved to token.json")
            
        credentials = creds
    except HttpError:
       logger.error("HTTP Error")

######################################
##### Calendar inquiry functions #####
######################################
##### Count calendar events for a specific year
"""
Counts events in a Google Calendar for a specific year.
If the year is the current year, the service will return the events up to current day.
If the year is not the current year but a previous one, the service will return all the events for the year.

Args:
  event_title: The title of the events to count.
  year: The year to count events for.

Returns:
  The number of events found.
"""
def countCalendarEventsYear(event_title, year):
  logger.debug(f"====> calendarService.countCalendarEventsYear(event_title, year) called <====")
  start_date = date(year, 1, 1)
  is_current_year = dateMgr.isCurrentYear(year)
  
  # if year is current year, the end date is current day (i.e.: today)
  if(is_current_year):
    logger.info("Year is current year: the end date will be set to current day (i.e.: today)")
    end_date = date.today()
  # if year is not current year, the end date is 31.12.yyyy
  else:
    logger.info("Year is not current year: the end date will be set to 31.12.yyyy")
    end_date = date(year, 12, 31)

  logger.debug(f"****** start_date: {start_date}")
  logger.debug(f"****** end_date: {end_date}")
  return countCalendarEvents(event_title, start_date, end_date)

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
  logger.debug(f"====> calendarService.countCalendarEventsToday(event_title, start_date) called <====")
  end_date = date.today()
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
  logger.debug(f"====> calendarService.countCalendarEvents(event_title, start_date, end_date) called <====")
  global credentials
  try:
    service = build('calendar', 'v3', credentials=credentials)
    
    # Convert start_date and end_date to datetime objects ISO 8601 format
    start_time = dateMgr.getDateTimeIsoFormat(dateMgr.formatDate(start_date, "YYYY-MM-DD"))
    end_time = dateMgr.getDateTimeIsoFormat(dateMgr.formatDateTimeEndOfDay(end_date))
    logger.info(f"Getting '{event_title}' events from {start_time} to {end_time}")

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
    logger.error(f"An error occurred: {error}")

##### List 10 upcoming calendar events
"""
Shows basic usage of the Google Calendar API. 
logger.debugs the start and name of the next 10 events on the user's calendar.

Args:
  None.

Returns:
  The number of events found.
"""
def getUpcomingEvents():
  logger.debug(f"====> calendarService.getUpcomingEvents() called <====")
  global credentials
  try:
    service = build('calendar', 'v3', credentials=credentials)

    # Call the Calendar API
    now = dateMgr.getDateTimeIsoFormat(dateMgr.getTodayDateTime())
    logger.info("Getting the upcoming 10 events")
    events_result = (service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",).execute()
    )
    events = events_result.get("items", [])

    if not events:
      logger.info("No upcoming events found.")
      return
    return events

  except HttpError as error:
    logger.error(f"An error occurred: {error}")

authenticate()