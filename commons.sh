source ../setenv.sh

###### Function section - START
AUTH_SERVICE_TEST=$DEFAULT_AUTH_SERVICE_TEST
# Function to select environment where program should run
printSelectEnvironment()
{
    ENVIRONMENT_SELECTION=$1
    if [[ -n "${ENVIRONMENT_SELECTION}" ]]; then
        echo 
    else
        echo -e "${BLU}Select environment : ${RESET}"
        echo -e "${BLU}1. Development${RESET}"
        echo -e "${BLU}2. Test${RESET}"
        echo -e "${BLU}3. Production${RESET}"
        read ENVIRONMENT_SELECTION
    fi
	setEnvironment
}

setEnvironment()
{
	case $ENVIRONMENT_SELECTION in
		1)  ENVIRONMENT=dev
			;;
		2)  ENVIRONMENT=test
			;;
        3)  ENVIRONMENT=prod
            ;;
		*) 	echo -e "${RED}No valid option selected${RESET}"
			printSelectEnvironment
			;;
	esac
}

# Function to input credentials securely
getCredentials() {
    while true; do
        read -r -p "Enter username [${DEFAULT_USERNAME}]: " INPUT_USER
        if [[ -z "$INPUT_USER" ]]; then
            USERNAME="$DEFAULT_USERNAME"
        else
            USERNAME="$INPUT_USER"
        fi

        read -s -r -p "Enter password: " PASSWORD
        echo
        if [[ -z "$PASSWORD" ]]; then
            echo "Error: Password cannot be empty."
            continue
        fi

        read -r -p "Enter service [${DEFAULT_AUTH_SERVICE_TEST}]: " INPUT_SERVICE
        if [[ -z "$INPUT_SERVICE" ]]; then
            AUTH_SERVICE_TEST="$DEFAULT_AUTH_SERVICE_TEST"
        else
            AUTH_SERVICE_TEST="$INPUT_SERVICE"
        fi

        export USERNAME PASSWORD AUTH_SERVICE_TEST
        break
    done
}

# Function to input KEYCLOAK_CLIENT_SECRET securely
inputKeycloakClientSecret() {
    if [ -n "$KEYCLOAK_CLIENT_SECRET" ]; then
        echo "KEYCLOAK_CLIENT_SECRET set"
    else
        while true; do
            read -s -p "${BLU}Enter Keycloak Client Secret for $AUTH_SERVICE_TEST service: ${END}" KEYCLOAK_CLIENT_SECRET
            echo
            if [[ -z "$KEYCLOAK_CLIENT_SECRET" ]]; then
                echo -e "${RED}Error: KEYCLOAK_CLIENT_SECRET cannot be empty. Please try again.${RESET}"
            else
                export KEYCLOAK_CLIENT_SECRET
                break
            fi
        done
    fi
}
###### Function section - END