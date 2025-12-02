source ../setenv.sh

# ***** Activate Python Virtual environment

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}###########################################################${RESET}"
    echo -e "${BLU}########## Python Virtual Environment activation ##########${RESET}"
    echo -e "${BLU}###########################################################${RESET}"
    # Ensure the environment variable is set
    if [ -z "$PYTORCH_VIRTUAL_ENV_TEST" ]; then
        echo -e "${MAGENTA}PYTORCH_VIRTUAL_ENV_TEST${RESET} is not set"
        exit 1
    fi

    # Verify $PYTORCH_VIRTUAL_ENV_TEST directory exists (check parent and current dir)
    if [ -d $PYTORCH_VIRTUAL_ENV_TEST ]; then
        echo -e "${BLU}Found $PYTORCH_VIRTUAL_ENV_TEST at${RESET} ${BLU}$PYTORCH_VIRTUAL_ENV_TEST${RESET}"
        # Activate the virtual environment
        echo -e "${BLU}PYTORCH_VIRTUAL_ENV_TEST${RESET} is set to ${BLU}$PYTORCH_VIRTUAL_ENV_TEST${RESET}, proceeding to activate ..."
        echo -e "Activating Python Virtual Environment with command ${BLU}source $PYTORCH_VIRTUAL_ENV_TEST/bin/activate${RESET}..."
        source "$PYTORCH_VIRTUAL_ENV_TEST/bin/activate"
        echo -e "${GREEN}Python Virtual Environment activated${RESET}"
        echo 
    else
        echo -e "${MAGENTA}Directory specified by PYTORCH_VIRTUAL_ENV_TEST not found:${RESET} ${MAGENTA}$PYTORCH_VIRTUAL_ENV_TEST${RESET}"
        echo -e "${MAGENTA}Exiting ...${RESET}"
        exit 1
    fi
}

# ===== EXECUTION =====
main $1