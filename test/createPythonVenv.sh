source ../common.sh

# ***** Create Python Virtual environment

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}#########################################################${RESET}"
    echo -e "${BLU}########## Python Virtual Environment creation ##########${RESET}"
    echo -e "${BLU}#########################################################${RESET}"
    # Check if the directory exists
    echo -e "Check if Python virtual environment ${BLU}$PYTORCH_VIRTUAL_ENV_TEST${RESET} exists"
    if [ -d "$PYTORCH_VIRTUAL_ENV_TEST" ]; then
        echo -e "Python virtual environment ${BLU}$PYTORCH_VIRTUAL_ENV_TEST${RESET} exists, activating ..."
        echo
        activate $1
    else
        echo -e "${MAGENTA}Python virtual environment $PYTORCH_VIRTUAL_ENV_TEST does not exist, creating ...${RESET}"
        echo
        create
        echo
        activate
        echo
        installPrereqs $1
    fi
}

# ===== CREATE PYTHON VIRTUAL ENV FUNCTION =====
create()
{
    echo Creating Python Virtual Environment ...
    python3 -m venv $PYTORCH_VIRTUAL_ENV_TEST
    echo -e "${GREEN}Python Virtual Environment created${RESET}"
}

# ===== ACTIVATE PYTHON VIRTUAL ENV FUNCTION =====
activate()
{
    source ./activatePythonVenv.sh
}

# ===== INSTALL PYTHON PREREQUISITE MODULES FUNCTION =====
installPrereqs()
{
    source ./installPrereqs.sh $1
}

# ***** MAIN EXECUTION
main $1