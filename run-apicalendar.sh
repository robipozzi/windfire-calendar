source ./setEnv.sh

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

# ***** Run FastAPI server for Google Calendar API
run()
{
    printSelectEnvironment
    echo ${cyn}Running calendar service API in environment : $ENVIRONMENT${end} ${grn}$
    inputKeycloakClientSecret
    ENVIRONMENT=$ENVIRONMENT \
    KEYCLOAK_URL=$KEYCLOAK_URL \
    KEYCLOAK_REALM=$KEYCLOAK_REALM \
    KEYCLOAK_CLIENT_ID=$KEYCLOAK_CLIENT_ID \
    KEYCLOAK_CLIENT_SECRET=$KEYCLOAK_CLIENT_SECRET \
    python3 fastapiCalendarService.py
}

# ***** MAIN EXECUTION
run