source ./setVars.sh

# ***** Create Python Virtual environment
run()
{
    echo ${grn}Creating Python3 Virtual Environment ...${end}
    python3 -m venv $PYTORCH_VIRTUAL_ENV
    echo ${grn}Python3 Virtual Environment created${end}
}

deactivateVenv()
{
    echo ${grn}Deactivating Python3 Virtual Environment ...${end}
    #deactivate
    echo ${grn}Python3 Virtual Environment deactivated${end}
}

# ***** MAIN EXECUTION
run