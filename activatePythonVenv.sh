source ./setVars.sh

# ***** Activate Python Virtual environment
activate()
{
    printf "${grn}Activating Python3 Virtual Environment ...${end}\n"
    source windfire-calendar/bin/activate
    printf "${grn}Python3 Virtual Environment activated${end}\n"
}

# ***** MAIN EXECUTION
activate