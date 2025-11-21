source ../setenv.sh
source ../commons.sh

# ***** Run Test script for Google Calendar API
run()
{
    printSelectEnvironment $1
    getCredentials
    installCustomPythonModules
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    python3 test.py
}

# ***** Install custom Windfire Security Python modules
installCustomPythonModules()
{
    pip3 install -e $HOME/dev/windfire-security
}

# ***** MAIN EXECUTION
run