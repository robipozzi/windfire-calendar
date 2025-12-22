#!/bin/bash
source ../setenv.sh

# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API) in background

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}################################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar FastAPI server ###############${RESET}"
    echo -e "${BLU}################################################################${RESET}"
    echo 
    echo This script will run the following steps:
    echo    1. Create a Python Virtual Environment, if does not exist
    echo    2. Activate the Python Virtual Environment
    echo    3. Install Python prerequisites, if not already installed
    echo    4. Run the Windfire Calendar FastAPI server in background
    echo 

    # Invoke run() function to start the FastAPI server
    run
}

# ===== SERVER RUN FUNCTION =====
run()
{
    inputKeycloakClientSecret
    ./start-apicalendar.sh 3 > logs/windfire-calendar.log 2>&1 &
}

# ===== EXECUTION =====
main