#!/bin/bash
source ../common.sh

# ***** Run Windfire Calendar application (wraps Google Calendar API)

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}#############################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar application ###############${RESET}"
    echo -e "${BLU}#############################################################${RESET}"
    echo
    echo This script will run the following steps:
    echo    1. Create a Python Virtual Environment, if does not exist
    echo    2. Activate the Python Virtual Environment
    echo    3. Install Python prerequisites, if not already installed
    echo    4. Run the Windfire Calendar application
    echo 

    # Source createPythonVenv.sh script to create and activate Python Virtual Environment
    source ./createPythonVenv.sh

    # Invoke run() function to run the Calendar Management application
    run $1
}

# ===== TERMINAL APPLICATION RUN FUNCTION =====
run()
{
    selectEnvironment $1
    echo -e "${CYAN}Running calendar manager in environment : $ENVIRONMENT${RESET}"
    ENVIRONMENT=$ENVIRONMENT python3 calendarMgr.py
}

# ===== EXECUTION =====
main $1