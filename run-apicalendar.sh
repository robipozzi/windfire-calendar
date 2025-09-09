source ./setVars.sh

# ***** Run FastAPI server for Google Calendar API
run()
{
    python3 fastapiCalendarService.py
}

# ***** MAIN EXECUTION
run