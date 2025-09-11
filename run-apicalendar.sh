source ./setEnv.sh

# ***** Run FastAPI server for Google Calendar API
run()
{
    printSelectEnvironment
    echo ${cyn}Running calendar service API in environment : $ENVIRONMENT${end} ${grn}$
    ENVIRONMENT=$ENVIRONMENT python3 fastapiCalendarService.py
}

# ***** MAIN EXECUTION
run