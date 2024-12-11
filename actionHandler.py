from datetime import date
import dateMgr
import calendarService
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def getYearInput():
  while True:
    # Get user input for year
    year = int(input("Enter the year (YYYY): "))
    # If input year is in the future, do not proceed and ask to try again
    if(dateMgr.isFuture(year)):
      print(Fore.RED + f"Invalid year input: {year} is in the future")
      print("Please try again.\n")
      continue
    return year

def getDateInput():
  while True:
    try:
      # Get user input for day, month, and year
      day = int(input("Enter the day (1-31): "))
      month = int(input("Enter the month (1-12): "))
      year = int(input("Enter the year (YYYY): "))
      # Attempt to create a date object to validate the input
      input_date = date(year, month, day)
      # If input date is in the future, do not proceed and ask to try again
      if(dateMgr.isFutureDate(input_date)):
        print(Fore.RED + f"Invalid date input: {input_date} is in the future")
        print("Please try again.\n")
        continue
      return input_date
    except ValueError as e:
        # Catch and explain specific validation errors
        print(Fore.RED + "Invalid date input. Please check your values:")
        print(Style.BRIGHT + Fore.RED + f"{e}")
        print("Please try again.\n")

#################################################
##### Calendar management handler functions #####
#################################################
def countCalendarEventsYearHandler():
  #== Date input - START
  year = getYearInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered year: {year}")
  #== Date input - END
  
  # Call Calendar events management service
  event_title = "Palestra"
  num_events = calendarService.countCalendarEventsYear(event_title, year)
  print(f"Number of '{event_title}' events for year {year}: {num_events}")

def countCalendarEventsTodayHandler():
  #== Date input - START
  start_date = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered start date: {date}")
  #== Date input - END
  
  # Call Calendar events management service
  event_title = "Palestra"
  num_events = calendarService.countCalendarEventsToday(event_title, start_date)
  print(f"Number of '{event_title}' events from {start_date} up to today: {num_events}")

def countCalendarEventsHandler():
  #== Date input - START
  print(Style.BRIGHT + Fore.YELLOW + f"Enter start date")
  start_date = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered start date: {start_date}")

  print(Style.BRIGHT + Fore.YELLOW + f"Enter end date")
  end_date = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered end date: {end_date}")
  #== Date input - END
  
  # Call Calendar events management service
  event_title = "Palestra"
  num_events = calendarService.countCalendarEvents(event_title, start_date, end_date)
  print(f"Number of '{event_title}' events from {start_date} to {end_date}: {num_events}")

def getUpcomingEventsHandler():
  events = calendarService.getUpcomingEvents()
  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    print(start, event["summary"])