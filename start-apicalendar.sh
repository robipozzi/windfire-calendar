source ./setenv.sh

# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API)
main()
{
    echo ${blu}"################################################################"${end}
    echo ${blu}"############### Windfire Calendar FastAPI server ###############"${end}
    echo ${blu}"################################################################"${end}
    echo This script will run the following steps:
    echo    1. Create a Python Virtual Environment, if does not exist
    echo    2. Activate the Python Virtual Environment
    echo    3. Install Python prerequisites, if not already installed
    echo    4. Run the Windfire Calendar FastAPI server
    echo 
    source ./createPythonVenv.sh
    run $1
}

run()
{
    printSelectEnvironment $1
    echo ${cyn}Running calendar service API in environment : $ENVIRONMENT${end} ${grn}$
    inputKeycloakClientSecret
    ENVIRONMENT=$ENVIRONMENT \
    KEYCLOAK_URL=$KEYCLOAK_URL \
    KEYCLOAK_REALM=$KEYCLOAK_REALM \
    KEYCLOAK_CLIENT_ID=$KEYCLOAK_CLIENT_ID \
    KEYCLOAK_CLIENT_SECRET=$KEYCLOAK_CLIENT_SECRET \
    python3 fastapiCalendarService.py
}

# Function to input KEYCLOAK_CLIENT_SECRET securely
inputKeycloakClientSecret() {
    while true; do
        read -s -p "Enter KEYCLOAK_CLIENT_SECRET: " KEYCLOAK_CLIENT_SECRET
        echo
        if [[ -z "$KEYCLOAK_CLIENT_SECRET" ]]; then
            echo "Error: KEYCLOAK_CLIENT_SECRET cannot be empty. Please try again."
        else
            export KEYCLOAK_CLIENT_SECRET
            break
        fi
    done
}

# ***** MAIN EXECUTION
main $1