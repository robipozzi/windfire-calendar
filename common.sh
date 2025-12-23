##### TERMINAL COLORS - START
# ===== COLOR CODES =====
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED=$'\e[1;31m'
MAGENTA=$'\e[1;35m'
BLU=$'\e[1;34m'
CYAN=$'\e[1;36m'
RESET='\033[0m'
END=$'\e[0m'
BOLD='\033[1m'
# ===== EMOJI =====
coffee=$'\xE2\x98\x95'
coffee3="${coffee} ${coffee} ${coffee}"
##### TERMINAL COLORS - END

###### Variable section - START
# ===== DEPLOYMENT / UNDEPLOYMENT VARIABLES =====
PLATFORM_OPTION=$1
PLATFORM_SELECTED=false
DEPLOY_PLATFORM=
DEPLOY_FUNCTION=

# ===== PYTHON VIRTUAL ENVIRONMENTS VARIABLES =====
PYTHON_VIRTUAL_ENV=windfire-calendar
PYTHON_VIRTUAL_ENV_TEST=windfire-calendar-test

# ===== APPLICATION CONFIGURATION VARIABLES =====
ENVIRONMENT=
DEFAULT_USERNAME=windfire
DEFAULT_AUTH_SERVICE_TEST=windfire-calendar-srv
VERIFY_SSL_CERTS=true
AUTH_SERVICE_TEST=$DEFAULT_AUTH_SERVICE_TEST

# ===== ROOT CA VARIABLES =====
WINDFIRE_ROOT_CA_KEY="WindfireRootCA.key"
WINDFIRE_ROOT_CA_CERTIFICATE="WindfireRootCA.crt"
WINDFIRE_DEFAULT_KEYSTORE_DIR=$HOME/opt/windfire/ssl/keystore
WINDFIRE_DEFAULT_TRUSTSTORE_DIR=$HOME/opt/windfire/ssl/truststore
WINDFIRE_DEFAULT_CERTS_PROD_DIR=$HOME/opt/windfire/ssl/certs/raspberry
###### Variable section - END

###### Function section - START
# Function to select and set programs run environment
selectEnvironment()
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
			selectEnvironment
			;;
	esac
}

# Function to securely input credentials
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

# Function to securely input KEYCLOAK_CLIENT_SECRET
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

# Functions to select and set deployment platform
selectDeploymentPlatform()
{
    if [[ $PLATFORM_OPTION == "" && $PLATFORM_SELECTED == false ]]; then
        echo -e "${BLU}No platform option provided - Select deployment platform :${RESET}"
        echo -e "${GREEN}1. Raspberry${RESET}"
        read PLATFORM_OPTION
        setDeploymentPlatform
    else
        echo -e "${CYAN}Platform option provided as argument: $PLATFORM_OPTION${RESET}"
        setDeploymentPlatform
    fi
}

setDeploymentPlatform()
{
    case $PLATFORM_OPTION in
        1)  DEPLOY_PLATFORM="raspberry"
            PLATFORM_SELECTED=true
            DEPLOY_PLATFORM="raspberry"
            ;;
        *)  echo -e "${RED}No valid option selected${RESET}"
            PLATFORM_OPTION=""
            PLATFORM_SELECTED=false
            selectDeploymentPlatform
            ;;
    esac
}
###### Function section - END