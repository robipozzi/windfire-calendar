source ../setenv.sh
source ../commons.sh

# ***** Run Windfire Calendar test application

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}##################################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar test application ###############${RESET}"
    echo -e "${BLU}##################################################################${RESET}"
    echo This script will run the following steps:
    echo    1. Create a Python Virtual Environment, if does not exist
    echo    2. Activate the Python Virtual Environment
    echo    3. Install Python prerequisites, if not already installed
    echo    4. Run the Windfire Calendar test application
    echo 
    source ./createPythonVenv.sh
    run
}

# ===== TEST APPLICATION RUN FUNCTION =====
run()
{
    printSelectEnvironment $1
    getCredentials
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    python3 test.py
}

# ===== EXECUTION =====
main