source ../setenv.sh

# ***** Create Python Virtual environment
main()
{
    echo ${blu}"#########################################################"${end}
    echo ${blu}"########## Python Virtual Environment creation ##########"${end}
    echo ${blu}"#########################################################"${end}
    # Check if the directory exists
    echo Check if Python virtual environment ${blu}$PYTORCH_VIRTUAL_ENV_TEST${end} exists
    if [ -d "$PYTORCH_VIRTUAL_ENV_TEST" ]; then
        echo "Python virtual environment ${blu}$PYTORCH_VIRTUAL_ENV_TEST${end} exists, activating ..."
        echo
        activate $1
    else
        echo "${mag}Python virtual environment $PYTORCH_VIRTUAL_ENV_TEST does not exist, creating ..."${end}
        echo
        create
        echo
        activate $1
    fi
}

create()
{
    echo Creating Python Virtual Environment ...
    python3 -m venv $PYTORCH_VIRTUAL_ENV_TEST
    echo ${grn}Python Virtual Environment created${end}
}

activate()
{
    source ./activatePythonVenv.sh $1
}

# ***** MAIN EXECUTION
main $1