source ../common.sh

# ***** Activate Python Virtual environment

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}###########################################################${RESET}"
    echo -e "${BLU}########## Python Virtual Environment activation ##########${RESET}"
    echo -e "${BLU}###########################################################${RESET}"
    # Ensure the environment variable is set
    if [ -z "$PYTHON_VIRTUAL_ENV" ]; then
        echo -e "${MAGENTA}PYTHON_VIRTUAL_ENV${RESET} is not set"
        exit 1
    fi

    # Verify $PYTHON_VIRTUAL_ENV directory exists (check parent and current dir)
    if [ -d $PYTHON_VIRTUAL_ENV ]; then
        echo -e "${BLU}Found $PYTHON_VIRTUAL_ENV at${RESET} ${BLU}$PYTHON_VIRTUAL_ENV${RESET}"
        # Activate the virtual environment
        echo -e "${BLU}PYTHON_VIRTUAL_ENV${RESET} is set to ${BLU}$PYTHON_VIRTUAL_ENV${RESET}, proceeding to activate ..."
        echo -e "Activating Python Virtual Environment with command ${BLU}source $PYTHON_VIRTUAL_ENV/bin/activate${RESET}..."
        source "$PYTHON_VIRTUAL_ENV/bin/activate"
        echo -e "${GREEN}Python Virtual Environment activated${RESET}"
        echo
    else
        echo -e "${MAGENTA}Directory specified by PYTHON_VIRTUAL_ENV not found:${RESET} ${MAGENTA}$PYTHON_VIRTUAL_ENV${RESET}"
        echo -e "${MAGENTA}Exiting ...${RESET}"
        exit 1
    fi
}

# ===== EXECUTION =====
main $1