source ../setenv.sh
source ../commons.sh

# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API) in background
main()
{
    echo ${blu}"################################################################"${end}
    echo ${blu}"############### Windfire Calendar FastAPI server ###############"${end}
    echo ${blu}"################################################################"${end}
    echo This script will run the following steps:
    echo    1. Create a Python Virtual Environment, if does not exist
    echo    2. Activate the Python Virtual Environment
    echo    3. Install Python prerequisites, if not already installed
    echo    4. Run the Windfire Calendar FastAPI server in background
    echo 
    run
}

run()
{
    inputKeycloakClientSecret
    ./start-apicalendar.sh 3 > logs/windfire-calendar.log 2>&1 &
}

# ***** MAIN EXECUTION
main