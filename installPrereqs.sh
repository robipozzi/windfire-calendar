source ./setVars.sh

# ***** Install Python prerequisites for Google Calendar API
installPythonModules()
{
    pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dateutil
}

# ***** MAIN EXECUTION
installPythonModules