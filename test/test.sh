source ../setenv.sh
source ../commons.sh

# ***** Run Windfire Calendar test application

# ===== MAIN FUNCTION =====
main()
{
    echo ${blu}"##################################################################"${end}
    echo ${blu}"############### Windfire Calendar test application ###############"${end}
    echo ${blu}"##################################################################"${end}
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
    installCustomPythonModules
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    python3 test.py
}

# ===== INSTALL CUSTOM Windfire Security PYTHON MODULES PREREQUISITES FUNCTION =====
installCustomPythonModules()
{
    pip3 install -e $HOME/dev/windfire-security
}

# ===== EXECUTION =====
main