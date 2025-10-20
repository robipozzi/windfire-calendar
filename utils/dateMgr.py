from datetime import date, datetime, time
import dateutil.parser
from colorama import Fore, init
from log import loggingFactory

# Initialize colorama
init(autoreset=True)

# Initialize logger at the top so it's available everywhere
logger = loggingFactory.get_logger('date_manager')

"""
  Formats a date object into a string in the "YYYY-MM-DD" format.

  Args:
    date: An object with 'day', 'month', and 'year' attributes (typically a datetime.date or similar).
    format: Unused parameter, included for compatibility.

  Returns:
    str: The formatted date string in "YYYY-MM-DD" format.
"""
def formatDate(date, format):
  logger.debug(f"====> dateMgr.formatDate(date, format) called <====")
  # Ensure day, month, and year are integers
  day = int(date.day)
  month = int(date.month)
  year = int(date.year)
  # Format to "YYYY-MM-DD"
  formattedDate = f"{year:04d}-{month:02d}-{day:02d}"
  logger.debug(f"Formatted Date: {formattedDate}")
  return formattedDate

"""
  Formats a date object into a string representing the end of that day ("YYYY-MM-DD 23:59:59").

  Args:
    date: An object with 'day', 'month', and 'year' attributes (typically a datetime.date or similar).

  Returns:
    str: The formatted date string in "YYYY-MM-DD 23:59:59" format.
"""
def formatDateTimeEndOfDay(date):
  logger.debug(f"====> dateMgr.formatDateTimeEndOfDay(date) called <====")
  # Ensure day, month, and year are integers
  day = int(date.day)
  month = int(date.month)
  year = int(date.year)
  # Format to "YYYY-MM-DD HH:MM:SS"
  formattedDate = f"{year:04d}-{month:02d}-{day:02d} 23:59:59"
  return formattedDate

def getDate(day, month, year):
  return datetime.datetime(int(year), int(month), int(day))

def getDateTime(date):
  logger.debug(f"====> dateMgr.getDateTime(date) called <====")
  # Parse the date string into a datetime object
  return dateutil.parser.parse(date)

def getDateTimeIsoFormat(date):
  logger.debug(f"====> dateMgr.getDateTimeIsoFormat(date) called <====")
  # Convert start_date and end_date to datetime objects
  datetime = getDateTime(date)
  logger.debug(f"datetime = {datetime}")
  # Convert datetime objects to ISO 8601 format
  time = datetime.isoformat('T') + 'Z'
  return time

"""
  Returns today's date with the time set to 23:59:59 as a string in 'YYYY-MM-DD HH:MM:SS' format.
"""
def getTodayDateTime():
  today = datetime.today()
  end_of_day = datetime.combine(today.date(), time(23, 59, 59))
  return end_of_day.strftime("%Y-%m-%d %H:%M:%S")
  ##today = datetime.today()
  ##return datetime.combine(today, datetime.time(23, 59, 59)).strftime("%Y-%m-%d %H:%M:%S")

def isCurrentYear(year):
  logger.debug(f"====> dateMgr.isCurrentYear(year) called <====")
  is_not_future_year = True

  # Extract year from current date (today)
  today = date.today()
  today_year = today.year
  logger.debug(f"****** Today year: {today_year}")

  # Check whether year is before current year
  logger.debug(f"****** Year: {year}")
  if(year < today_year):
     is_not_future_year = False
  
  logger.debug(f"****** is_not_future_year: {is_not_future_year}")
  return is_not_future_year

def isFuture(year):
  logger.debug(f"====> dateMgr.isFuture(year) called <====")
  is_future = False
  # Extract year from current date (today)
  today = date.today()
  today_year = today.year
  logger.debug(f"****** Today year: {today_year}")
  # Check whether year is before current year
  logger.debug(f"****** Year: {year}")
  if(year > today_year):
     print(Fore.RED + f"This year {year} is in the future.")
     is_future = True
  
  logger.debug(f"****** is_future: {is_future}") 
  return is_future

def isFutureDate(user_date):
  logger.debug(f"====> dateMgr.isFutureDate(user_date) called <====")
  is_future = False
  # Extract year from current date (today)
  today = date.today()
  if user_date > today:
    print(Fore.RED + f"This date {user_date} is in the future.")
    is_future = True
    
  return is_future