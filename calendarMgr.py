import os.path
from colorama import Fore, Style, init
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import dateMgr

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

#############################################
##### Menu options management functions #####
#############################################
def printMenu():
    print(Fore.CYAN + "Menu:")
    print(Fore.CYAN + "1. Count calendar events up to today")
    print(Fore.CYAN + "2. Count calendar events from start to end date")
    print(Fore.CYAN + "3. List upcoming 10 events")
    print(Fore.CYAN + "4. Exit")

def getChoice():
    choice = input(Fore.MAGENTA + "Enter your choice (1-4): ")
    return choice

def getDateInput():
  while True:
    day = input("Enter the day: ")
    month = input("Enter the month: ")
    year = input("Enter the year: ")
    try:
      date = dateMgr.getDate(day, month, year)
      return date
    except ValueError:
      print("Invalid date. Please enter a valid day, month, and year.")

#################################################
##### Calendar management handler functions #####
#################################################
def countCalendarEventsTodayHandler():
  #== Date input - START
  date = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered start date: {date}")
  formattedStartDate = dateMgr.formatDate(date, "YYYY-MM-DD")
  #== Date input - END
  
  # Call Calendar events management service
  event_title = "Palestra"
  start_date = formattedStartDate
  num_events = countCalendarEventsToday(event_title, start_date)
  print(f"Number of '{event_title}' events from {start_date} up to today: {num_events}")

def countCalendarEventsHandler():
  #== Date input - START
  print(Style.BRIGHT + Fore.YELLOW + f"Enter start date")
  startDate = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered start date: {startDate}")

  print(Style.BRIGHT + Fore.YELLOW + f"Enter end date")
  endDate = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered end date: {endDate}")
  #== Date input - END

  # Call Calendar events management service
  event_title = "Palestra"
  start_date = dateMgr.formatDate(startDate, "YYYY-MM-DD")
  end_date = dateMgr.formatDate(endDate, "YYYY-MM-DD")
  num_events = countCalendarEvents(event_title, start_date, end_date)
  print(f"Number of '{event_title}' events from {start_date} to {end_date}: {num_events}")

def getUpcomingEventsHandler():
  events = getUpcomingEvents()
  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    print(start, event["summary"])

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
    print(f"An error occurred: {error}")

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
    print(f"An error occurred: {error}")

#################################
##### Main program function #####
#################################
def main():
  ### Menu Options - START
  while True:
        printMenu()
        choice = getChoice()
        if choice == '1':
            print(Fore.YELLOW + "You selected Option 1.")
            countCalendarEventsTodayHandler()
            break
        elif choice == '2':
            print(Fore.YELLOW + "You selected Option 2.")
            countCalendarEventsHandler()
            break
        elif choice == '3':
            print(Fore.YELLOW + "You selected Option 3.")
            getUpcomingEventsHandler()
            break
        elif choice == '4':
            print(Fore.RED + "Exiting the program. Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")


##########################
##### Main Execution #####
##########################
if __name__ == "__main__":
  authenticate()
  main()