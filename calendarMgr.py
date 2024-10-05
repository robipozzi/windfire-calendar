import datetime
import dateutil.parser
import os.path
import logging
from colorama import Fore, Style, init
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
# Initialize colorama
init(autoreset=True)

def printMenu():
    print(Fore.CYAN + "Menu:")
    print(Fore.CYAN + "1. Count calendar events up to today")
    print(Fore.CYAN + "2. Count calendar events from start to end date")
    print(Fore.CYAN + "3. List upcoming 10 events")
    print(Fore.CYAN + "4. Exit")

def getChoice():
    choice = input(Fore.MAGENTA + "Enter your choice (1-4): ")
    return choice

###########################################
##### Google Authentication function  #####
###########################################
def authenticate():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
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

  return build('calendar', 'v3', credentials=creds)

#######################################
##### Calendar inquiry functions  #####
#######################################

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
  end_date = datetime.date.today().strftime("%Y-%m-%d")  # Today's date
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
  try:
    service = authenticate()

    # Convert start_date and end_date to datetime objects
    start_datetime = dateutil.parser.parse(start_date)
    end_datetime = dateutil.parser.parse(end_date)

    # Convert datetime objects to ISO 8601 format
    start_time = start_datetime.isoformat('T') + 'Z'
    end_time = end_datetime.isoformat('T') + 'Z'

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

##### Count calendar events from start date up to end date
"""
Shows basic usage of the Google Calendar API. 
Prints the start and name of the next 10 events on the user's calendar.

Args:
  None.

Returns:
  The number of events found.
"""
def getEvents():
  try:
    service = authenticate()

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
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

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")

def getDateInput():
  while True:
    day = input("Enter the day: ")
    month = input("Enter the month: ")
    year = input("Enter the year: ")
    try:
      date = datetime.datetime(int(year), int(month), int(day))
      return date
    except ValueError:
      print("Invalid date. Please enter a valid day, month, and year.")


########################
##### Main Program #####
########################
def main():
  ### Menu Options - START
  while True:
        printMenu()
        choice = getChoice()
        if choice == '1':
            print(Fore.YELLOW + "You selected Option 1.")
            #== Date input - START
            date = getDateInput()
            print("You entered:", date)
            #== Date input - END
            event_title = "Palestra"
            start_date = "2024-09-01"
            num_events = countCalendarEventsToday(event_title, start_date)
            print(f"Number of '{event_title}' events from {start_date} up to today: {num_events}")
            break
        elif choice == '2':
            print(Fore.YELLOW + "You selected Option 2.")
            event_title = "Palestra"
            start_date = "2024-09-01"
            end_date = "2024-10-30"
            num_events = countCalendarEvents(event_title, start_date, end_date)
            print(f"Number of '{event_title}' events from {start_date} to {end_date}: {num_events}")
            print(" ")
            break
        elif choice == '3':
            print(Fore.YELLOW + "You selected Option 3.")
            getEvents()
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
  main()