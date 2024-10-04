source ./setVars.sh

# ***** Create Python Virtual environment
run()
{
    printf "${grn}Creating Python3 Virtual Environment ...${end}\n"
    python3 -m venv google-calendar
    printf "${grn}Python3 Virtual Environment created${end}\n"
}

deactivateVenv()
{
    printf "${grn}Deactivating Python3 Virtual Environment ...${end}\n"
    #deactivate
    printf "${grn}Python3 Virtual Environment deactivated${end}\n"
}

# ***** MAIN EXECUTION
run