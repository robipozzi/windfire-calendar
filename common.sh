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
# Repository root (resolved from this file, so it works whatever the caller's working directory is)
WINDFIRE_CALENDAR_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINDFIRE_SERVER_CERTIFICATE=windfire-calendar.crt
WINDFIRE_SERVER_KEY=windfire-calendar.key
SECURITY_CLIENT_DIST_DIR=$WINDFIRE_CALENDAR_HOME/../windfire-security-client/dist
ANSIBLE_SSH_KEY=$HOME/.ssh/ansible_rsa

# ===== PYTHON VIRTUAL ENVIRONMENTS VARIABLES =====
PYTHON_VIRTUAL_ENV=windfire-calendar
PYTHON_VIRTUAL_ENV_TEST=windfire-calendar-test

# ===== APPLICATION CONFIGURATION VARIABLES =====
ENVIRONMENT=
DEFAULT_USERNAME=windfire
DEFAULT_AUTH_SERVICE_TEST=windfire-calendar-srv
VERIFY_SSL_CERTS=true
AUTH_SERVICE_TEST=$DEFAULT_AUTH_SERVICE_TEST

# ===== WINDFIRE SECURITY CONFIGURATION VARIABLES =====
WINDFIRE_SECURITY_ENVIRONMENT=
WINDFIRE_SECURITY_HOST=
WINDFIRE_SECURITY_PORT=

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

# Function to read a single KEY=value from an env file (.env can't be sourced: values with spaces, inline comments)
getEnvFileValue()
{
    local file=$1
    local key=$2
    local value
    value=$(grep -E "^${key}=" "$file" 2>/dev/null | tail -n 1)
    value=${value#*=}
    value=${value%%#*}
    value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    value=${value#[\"\']}
    value=${value%[\"\']}
    echo "$value"
}

# Function to select Windfire Security environment used for authentication and resolve its host/port from ./.env
selectSecurityEnvironment()
{
    local option=$1
    while true; do
        if [[ -z "$option" ]]; then
            echo -e "${BLU}Select Windfire Security environment for authentication : ${RESET}"
            echo -e "${BLU}1. Development${RESET}"
            echo -e "${BLU}2. Test${RESET}"
            echo -e "${BLU}3. Production [default]${RESET}"
            read option
            if [[ -z "$option" ]]; then
                option=3
            fi
        fi
        case $option in
            1|dev)   WINDFIRE_SECURITY_ENVIRONMENT=dev
                     break
                     ;;
            2|test)  WINDFIRE_SECURITY_ENVIRONMENT=test
                     break
                     ;;
            3|prod)  WINDFIRE_SECURITY_ENVIRONMENT=prod
                     break
                     ;;
            *)       echo -e "${RED}No valid Windfire Security environment option selected: $option${RESET}"
                     option=
                     ;;
        esac
    done

    local envPrefix
    envPrefix=$(echo "$WINDFIRE_SECURITY_ENVIRONMENT" | tr '[:lower:]' '[:upper:]')
    WINDFIRE_SECURITY_HOST=$(getEnvFileValue ./.env "WINDFIRE_SECURITY_${envPrefix}_HOST")
    WINDFIRE_SECURITY_PORT=$(getEnvFileValue ./.env "WINDFIRE_SECURITY_${envPrefix}_PORT")
    if [[ -z "$WINDFIRE_SECURITY_HOST" || -z "$WINDFIRE_SECURITY_PORT" ]]; then
        echo -e "${RED}Error: WINDFIRE_SECURITY_${envPrefix}_HOST and WINDFIRE_SECURITY_${envPrefix}_PORT must be set in ./.env${RESET}"
        exit 1
    fi
    echo -e "${CYAN}Windfire Security environment : $WINDFIRE_SECURITY_ENVIRONMENT ($WINDFIRE_SECURITY_HOST:$WINDFIRE_SECURITY_PORT)${RESET}"
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

# Functions to select and set deployment platform
selectDeploymentPlatform()
{
    if [[ $PLATFORM_OPTION == "" && $PLATFORM_SELECTED == false ]]; then
        echo -e "${BLU}No platform option provided - Select deployment platform :${RESET}"
        echo -e "${GREEN}1. Raspberry${RESET}"
        if ! read PLATFORM_OPTION; then
            echo -e "${RED}No input available to select deployment platform${RESET}"
            exit 1
        fi
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