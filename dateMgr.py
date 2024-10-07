import datetime
import dateutil.parser
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def formatDate(date, format):
  # Ensure day, month, and year are integers
  day = int(date.day)
  month = int(date.month)
  year = int(date.year)
  # Format to "YYYY-MM-DD"
  formattedDate = f"{year:04d}-{month:02d}-{day:02d}"
  print(f"Formatted Date: {formattedDate}")
  return formattedDate

def formatDateTimeEndOfDay(date):
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
  return dateutil.parser.parse(date)

def getDateTimeIsoFormat(date):
  # Convert start_date and end_date to datetime objects
  datetime = getDateTime(date)
  print(f"datetime = {datetime}")
  # Convert datetime objects to ISO 8601 format
  time = datetime.isoformat('T') + 'Z'
  return time

def getTodayDateTime():
  today = datetime.date.today()
  return datetime.datetime.combine(today, datetime.time(23, 59, 59)).strftime("%Y-%m-%d %H:%M:%S")