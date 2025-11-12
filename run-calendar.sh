source ./setenv.sh

# ***** Run Windfire Calendar application (wraps Google Calendar API)
main()
{
    echo ${blu}"#############################################################"${end}
    echo ${blu}"############### Windfire Calendar application ###############"${end}
    echo ${blu}"#############################################################"${end}
    echo This script will run the following steps:
    echo    1. Create a Python Virtual Environment, if does not exist
    echo    2. Activate the Python Virtual Environment
    echo    3. Install Python prerequisites, if not already installed
    echo    4. Run the Windfire Calendar application
    echo 
    source ./createPythonVenv.sh
    run $1
}

run()
{
    printSelectEnvironment $1
    echo ${cyn}Running calendar manager in environment : $ENVIRONMENT${end} ${grn}$
    ENVIRONMENT=$ENVIRONMENT python3 calendarMgr.py
}

# ***** MAIN EXECUTION
main $1