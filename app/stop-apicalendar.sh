#!/bin/bash
source ../common.sh

# ***** Stop Windfire Calendar FastAPI server

PROCESS_TO_KILL=calendarApiServer.py
PID=

# ***** Stop FastAPI server for Authentication Service

# ===== MAIN FUNCTION =====
main()
{
    getPid
    if [ -z "$PID" ]; then
        echo -e "${BLU}No running process found for $PROCESS_TO_KILL, so far so good, exiting ...${RESET}"
        return 0
    else
        echo -e "${BLU}PID = $PID, stop it${RESET}"
        kill -TERM $PID
        # Wait up to 10 seconds for a clean shutdown, then force it
        for i in {1..10}; do
            pgrep -f $PROCESS_TO_KILL > /dev/null || break
            sleep 1
        done
        if pgrep -f $PROCESS_TO_KILL > /dev/null; then
            echo -e "${BLU}Process still running, force kill${RESET}"
            kill -9 $(pgrep -f $PROCESS_TO_KILL)
        fi
        echo -e "${BLU}Check if process has been stopped${RESET}"
        getPid
    fi
}

# ===== FUNCTION TO GET PID OF RUNNING PROCESS =====
getPid()
{
    echo -e "${BLU}Getting PID for $PROCESS_TO_KILL ...${RESET}"
    ps aux | grep $PROCESS_TO_KILL
    PID=$(pgrep -f $PROCESS_TO_KILL)
}

# ===== EXECUTION =====
main