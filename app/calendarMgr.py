from colorama import Fore, Style, init
from handler import actionHandler
import os
# Initialize logger at the top so it's available everywhere
from logger.loggingFactory import logger_factory
logger = logger_factory.get_logger('calendar_api')

# Initialize colorama
init(autoreset=True)

#############################################
##### Menu options management functions #####
#############################################
def printMenu():
    print(Style.BRIGHT + Fore.CYAN + "Menu:")
    print(Fore.CYAN + "1. Count calendar events for a specific year")
    print(Fore.CYAN + "2. Count calendar events from start date up to today")
    print(Fore.CYAN + "3. Count calendar events from start to end date")
    print(Fore.CYAN + "4. List upcoming 10 events")
    print(Fore.CYAN + "5. Exit")

def getChoice():
    choice = input(Fore.MAGENTA + "Enter your choice (1-4): ")
    return choice

#################################
##### Main program function #####
#################################
def main():
    logger.info("Starting calendar manager application")
    logger.debug(f"### Current Environment ###")
    logger.debug(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'prod')}")
    # Menu Options - START
    while True:
        printMenu()
        choice = getChoice()
        if choice == '1':
            print(Fore.YELLOW + "You selected Option 1.")
            actionHandler.countCalendarEventsYearHandler()
            break
        elif choice == '2':
            print(Fore.YELLOW + "You selected Option 2.")
            actionHandler.countCalendarEventsTodayHandler()
            break
        elif choice == '3':
            print(Fore.YELLOW + "You selected Option 3.")
            actionHandler.countCalendarEventsHandler()
            break
        elif choice == '4':
            print(Fore.YELLOW + "You selected Option 4.")
            actionHandler.getUpcomingEventsHandler()
            break
        elif choice == '5':
            print(Fore.RED + "Exiting the program. Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")   

##########################
##### Main Execution #####
##########################
if __name__ == "__main__":
    main()