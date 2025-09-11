source ./setEnv.sh

# ***** Run Python program
run()
{
    printSelectEnvironment
    echo ${cyn}Running calendar manager in environment : $ENVIRONMENT${end} ${grn}$
    ENVIRONMENT=$ENVIRONMENT python3 calendarMgr.py
}

# ***** MAIN EXECUTION
run