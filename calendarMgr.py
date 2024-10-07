from colorama import Fore, Style, init
import actionHandler

# Initialize colorama
init(autoreset=True)

#############################################
##### Menu options management functions #####
#############################################
def printMenu():
    print(Style.BRIGHT + Fore.CYAN + "Menu:")
    print(Fore.CYAN + "1. Count calendar events up to today")
    print(Fore.CYAN + "2. Count calendar events from start to end date")
    print(Fore.CYAN + "3. List upcoming 10 events")
    print(Fore.CYAN + "4. Exit")

def getChoice():
    choice = input(Fore.MAGENTA + "Enter your choice (1-4): ")
    return choice

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
            actionHandler.countCalendarEventsTodayHandler()
            break
        elif choice == '2':
            print(Fore.YELLOW + "You selected Option 2.")
            actionHandler.countCalendarEventsHandler()
            break
        elif choice == '3':
            print(Fore.YELLOW + "You selected Option 3.")
            actionHandler.getUpcomingEventsHandler()
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