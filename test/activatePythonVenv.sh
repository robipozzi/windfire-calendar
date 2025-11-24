source ../setenv.sh

# ***** Activate Python Virtual environment
main()
{
    echo ${blu}"###########################################################"${end}
    echo ${blu}"########## Python Virtual Environment activation ##########"${end}
    echo ${blu}"###########################################################"${end}
    # Ensure the environment variable is set
    if [ -z "$PYTORCH_VIRTUAL_ENV_TEST" ]; then
        echo "${mag}PYTORCH_VIRTUAL_ENV_TEST${end} is not set"
        exit 1
    fi

    # Verify $PYTORCH_VIRTUAL_ENV_TEST directory exists (check parent and current dir)
    if [ -d $PYTORCH_VIRTUAL_ENV_TEST ]; then
        echo "${blu}Found $PYTORCH_VIRTUAL_ENV_TEST at${end} ${blu}$PYTORCH_VIRTUAL_ENV_TEST${end}"
        # Activate the virtual environment
        echo "${blu}PYTORCH_VIRTUAL_ENV_TEST${end} is set to ${blu}$PYTORCH_VIRTUAL_ENV_TEST${end}, proceeding to activate ..."
        echo Activating Python Virtual Environment with command ${blu}source $PYTORCH_VIRTUAL_ENV_TEST/bin/activate${end}...
        source "$PYTORCH_VIRTUAL_ENV_TEST/bin/activate"
        echo ${grn}Python Virtual Environment activated${end}
        echo 
        source ./installPrereqs.sh $1
    else
        echo "${mag}Directory specified by PYTORCH_VIRTUAL_ENV_TEST not found:${end} ${mag}$PYTORCH_VIRTUAL_ENV_TEST${end}"
        echo "${mag}Exiting ...${end}"
        exit 1
    fi
}

# ***** MAIN EXECUTION
main $1