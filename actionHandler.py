import dateMgr
import calendarService
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def getDateInput():
  while True:
    day = input("Enter the day: ")
    month = input("Enter the month: ")
    year = input("Enter the year: ")
    try:
      date = dateMgr.getDate(day, month, year)
      return date
    except ValueError:
      print(Fore.RED + "Invalid date. Please enter a valid day, month, and year.")

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
  num_events = calendarService.countCalendarEventsToday(event_title, start_date)
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
  end_date = dateMgr.formatDateTimeEndOfDay(endDate)
  num_events = calendarService.countCalendarEvents(event_title, start_date, end_date)
  print(f"Number of '{event_title}' events from {start_date} to {end_date}: {num_events}")

def getUpcomingEventsHandler():
  events = calendarService.getUpcomingEvents()
  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    print(start, event["summary"])