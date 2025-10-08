from datetime import date
from utils import dateMgr
from service import calendarService
from colorama import Fore, Style, init
from log import loggingFactory

# Initialize colorama
init(autoreset=True)

# Initialize logger at the top so it's available everywhere
logger = loggingFactory.get_logger('calendar_handler')

def getYearInput():
  logger.debug(f"====> actionHandler.getYearInput() called <====")
  # Loop until valid year is provided
  while True:
    try:
      # Get user input for year
      year_input = input(Fore.MAGENTA + "Enter the year (YYYY): ")
      year = int(year_input)
      # If input year is in the future, do not proceed and ask to try again
      if(dateMgr.isFuture(year)):
        print(Fore.RED + f"Invalid year input: {year} is in the future")
        print(Style.BRIGHT + Fore.WHITE + "Please try again.\n")
        continue
    except ValueError:
      print(Fore.RED + "Invalid input. Please enter a valid year (numeric, e.g. 2024).")
      print(Style.BRIGHT + Fore.WHITE + "Please try again.\n")
      continue
    break
  return year

def getDateInput():
  logger.debug(f"====> actionHandler.getDateInput() called <====")
  # Loop until valid date is provided
  while True:
    try:
      # Get user input for day, month, and year
      day = int(input(Fore.MAGENTA + "Enter the day (1-31): "))
      month = int(input(Fore.MAGENTA + "Enter the month (1-12): "))
      year = int(input(Fore.MAGENTA + "Enter the year (YYYY): "))
      # Attempt to create a date object to validate the input
      input_date = date(year, month, day)
      # If input date is in the future, do not proceed and ask to try again
      if(dateMgr.isFutureDate(input_date)):
        print(Fore.RED + f"Invalid date input: {input_date} is in the future")
        print(Style.BRIGHT + Fore.WHITE + "Please try again.\n")
        continue
    except ValueError as e:
        # Catch and explain specific validation errors
        print(Fore.RED + "Invalid date input. Please check your values.")
        print(Style.BRIGHT + Fore.RED + f"{e}")
        print(Style.BRIGHT + Fore.WHITE + "Please try again.\n")
        continue
    break
  return input_date

def getEventInput():
  logger.debug(f"====> actionHandler.getEventInput() called <====")
  # Loop until valid event name is provided
  while True:
    try:
      # Get user input for event name
      event_name = input(Fore.MAGENTA + "Enter the event name: ").strip()
      if not event_name:
        print(Fore.RED + "Event name cannot be empty.")
        print(Style.BRIGHT + Fore.WHITE + "Please try again.\n")
        continue
    except ValueError:
      print(Fore.RED + "Invalid input. Please enter a valid event name.")
      print(Style.BRIGHT + Fore.WHITE + "Please try again.\n")
      continue
    break
  return event_name

#################################################
##### Calendar management handler functions #####
#################################################
def countCalendarEventsYearHandler():
  logger.debug(f"====> actionHandler.countCalendarEventsYearHandler() called <====")
  #== Date input - START
  year = getYearInput()
  event_title = getEventInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered year: {year} and event name: {event_title}")
  #== Date input - END
  # Call Calendar events management service
  num_events = calendarService.countCalendarEventsYear(event_title, year)
  print(Style.NORMAL + Fore.CYAN + f"Number of '{event_title}' events for year {year}: {num_events}")

def countCalendarEventsTodayHandler():
  logger.debug(f"====> actionHandler.countCalendarEventsTodayHandler() called <====")
  #== Date input - START
  start_date = getDateInput()
  event_title = getEventInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered start date: {start_date} and event name: {event_title}")
  #== Date input - END
  # Call Calendar events management service
  num_events = calendarService.countCalendarEventsToday(event_title, start_date)
  print(Style.NORMAL + Fore.CYAN + f"Number of '{event_title}' events from {start_date} up to today: {num_events}")

def countCalendarEventsHandler():
  logger.debug(f"====> actionHandler.countCalendarEventsHandler() called <====")
  #== Date input - START
  # Get start date
  print(Style.BRIGHT + Fore.YELLOW + f"Enter start date")
  start_date = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered start date: {start_date}")
  # Get end date
  print(Style.BRIGHT + Fore.YELLOW + f"Enter end date")
  end_date = getDateInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered end date: {end_date}")
  #== Date input - END
  # Call Calendar events management service
  event_title = getEventInput()
  print(Style.BRIGHT + Fore.GREEN + f"You entered event name: {event_title}")
  # Call Calendar events management service
  num_events = calendarService.countCalendarEvents(event_title, start_date, end_date)
  print(Style.NORMAL + Fore.CYAN + f"Number of '{event_title}' events from {start_date} to {end_date}: {num_events}")

def getUpcomingEventsHandler():
  logger.debug(f"====> actionHandler.getUpcomingEventsHandler() called <====")
  events = calendarService.getUpcomingEvents()
  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    print(Style.NORMAL + Fore.CYAN + start, Style.NORMAL + Fore.CYAN + event["summary"])