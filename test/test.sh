source ../setenv.sh

# ***** Run Test script for Google Calendar API
run()
{
    getCredentials
    installCustomPythonModules
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    python3 test.py
}

# ***** Install custom Windfire Security Python modules
installCustomPythonModules()
{
    pip3 install -e $HOME/dev/windfire-security
}

# ***** MAIN EXECUTION
run