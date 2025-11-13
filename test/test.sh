source ../setenv.sh

# ***** Run Test script for Google Calendar API
run()
{
    getCredentials
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    python3 test.py
}

# ***** MAIN EXECUTION
run