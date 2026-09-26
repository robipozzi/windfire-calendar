import os.path
from google.auth.transport.requests import Request # pyright: ignore[reportMissingImports]
from google.oauth2.credentials import Credentials # pyright: ignore[reportMissingImports]
from google_auth_oauthlib.flow import InstalledAppFlow # pyright: ignore[reportMissingImports]
from googleapiclient.discovery import build # pyright: ignore[reportMissingImports]
from googleapiclient.errors import HttpError # pyright: ignore[reportMissingImports]
from utils import dateMgr
from datetime import date
from colorama import init # pyright: ignore[reportMissingModuleSource]
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('calendarService')

from config.settings import settings

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Google OAuth files: configurable via .env, relative paths are resolved against the app directory
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resolvePath(path):
  return path if os.path.isabs(path) else os.path.normpath(os.path.join(APP_DIR, path))

CREDENTIALS_FILE = resolvePath(settings.get('GOOGLE_CREDENTIALS_FILE') or "credentials.json")
TOKEN_FILE = resolvePath(settings.get('GOOGLE_TOKEN_FILE') or "token.json")

CREDENTIALS_HELP = f"""Google OAuth client file not found: {CREDENTIALS_FILE}
To create it:
  1. Google Cloud Console > APIs & Services > Library: enable 'Google Calendar API'
  2. OAuth consent screen: configure it and add your Google account as a Test user
  3. Credentials > Create credentials > OAuth client ID > Application type 'Desktop app'
  4. Download the JSON and save it as {CREDENTIALS_FILE}
     (or set GOOGLE_CREDENTIALS_FILE in .env to its location)"""

# Global credentials variable
credentials = None

# Initialize colorama
init(autoreset=True)

class CalendarService:
  def __init__(self):
    logger.debug(f"====> CalendarService.__init__() called <====")

  ##########################################
  ##### Google Authentication function #####
  ##########################################
  def authenticate(self):
      try:
          # Authenticates the user and sets the global credentials variable.
          global credentials
          creds = None
          # The file token.json stores the user's access and refresh tokens, and is
          # created automatically when the authorization flow completes for the first time.
          if os.path.exists(TOKEN_FILE):
              logger.info(f"Getting credentials for Google from {TOKEN_FILE}")
              creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
          # If there are no (valid) credentials available, let the user log in.
          if not creds or not creds.valid:
              logger.warning("No valid Google credentials were found, logging in ...")
              if creds and creds.expired and creds.refresh_token:
                  logger.warning("Credentials expired, refreshing ...")
                  try:
                      creds.refresh(Request())
                  except Exception as e:
                      logger.error(f"Failed to refresh credentials: {e}. Re-authenticating ...")
                      creds = self._runOAuthFlow()
              else:
                  creds = self._runOAuthFlow()
              # Save the credentials for the next run
              with open(TOKEN_FILE, "w") as token:
                  token.write(creds.to_json())
                  logger.info(f"Credentials saved to {TOKEN_FILE}")

          credentials = creds
      except HttpError:
          logger.error("HTTP Error")

  def _runOAuthFlow(self):
      # Runs the interactive Google OAuth flow using the OAuth client file
      if not os.path.exists(CREDENTIALS_FILE):
          logger.error(f"Google OAuth client file not found: {CREDENTIALS_FILE}")
          raise FileNotFoundError(CREDENTIALS_HELP)
      logger.info(f"Authenticating to Google using settings from {CREDENTIALS_FILE} ...")
      flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
      return flow.run_local_server(port=0)

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
  def countCalendarEventsYear(self, event_title, year):
    logger.debug(f"====> calendarService.countCalendarEventsYear(event_title, year) called <====")
    self.authenticate()
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
    return self.countCalendarEvents(event_title, start_date, end_date)

  ##### Count calendar events from start date up to Today included
  """
  Counts events in a Google Calendar timeframe from start_date up to Today included.

  Args:
    event_title: The title of the events to count.
    start_date: The start date of the timeframe.

  Returns:
    The number of events found.
  """
  def countCalendarEventsToday(self, event_title, start_date):
    logger.debug(f"====> calendarService.countCalendarEventsToday(event_title, start_date) called <====")
    self.authenticate()
    end_date = date.today()
    return self.countCalendarEvents(event_title, start_date, end_date)

  ##### Count calendar events from start date up to end date
  """
  Counts events in a Google Calendar timeframe from start_date up to end_date.

  Args:
    event_title: The title of the events to count.
    start_date: The start date of the timeframe.
    end_date: The end date of the timeframe.

  Returns:
    The number of events found.

  Raises:
    ValueError: If end_date is before start_date.
  """
  def countCalendarEvents(self, event_title, start_date, end_date):
    logger.debug(f"====> calendarService.countCalendarEvents(event_title, start_date, end_date) called <====")
    if end_date < start_date:
      logger.error(f"Invalid date range: end date {end_date} is before start date {start_date}")
      raise ValueError(f"End date {end_date} is before start date {start_date}")
    self.authenticate()
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
  def getUpcomingEvents(self):
    logger.debug(f"====> calendarService.getUpcomingEvents() called <====")
    self.authenticate()
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

################################################
##### Initialize Calendar Service instance #####
################################################
calendarSrv = CalendarService()
#authenticate()