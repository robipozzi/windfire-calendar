source ./setVars.sh

# ***** Run FastAPI server for Google Calendar API
run()
{
    python3 fastapi_calendar_service.py
}

# ***** MAIN EXECUTION
run