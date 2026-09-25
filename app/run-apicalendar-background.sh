#!/bin/bash
source ../common.sh

# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API) in background

# ===== DEFAULT VALUES =====
LOG_LEVEL=
RUN_ENVIRONMENT=
KEYCLOAK_ENV_OPTION=

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}################################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar FastAPI server ###############${RESET}"
    echo -e "${BLU}################################################################${RESET}"
    echo 
    echo This script will run the following steps:
    echo    1. Select the application environment, if not provided as argument
    echo    2. Select the Keycloak environment used for authentication, if not provided as argument
    echo    3. Input the Keycloak client secret, if KEYCLOAK_CLIENT_SECRET is not set
    echo    4. Create a Python Virtual Environment, if does not exist
    echo    5. Activate the Python Virtual Environment
    echo    6. Install Python prerequisites, if not already installed
    echo    7. Run the Windfire Calendar FastAPI server in background
    echo 

    # Invoke parseArguments() function to parse and validate arguments
    parseArguments "$@"

    # Invoke run() function to start the FastAPI server
    run
}

# ===== SERVER RUN FUNCTION =====
run()
{
    # Prompt for everything up front: once in background, output goes to the log file and no prompt is possible
    selectEnvironment "$RUN_ENVIRONMENT"
    selectKeycloakEnvironment "$KEYCLOAK_ENV_OPTION"
    inputKeycloakClientSecret

    local runArgs=("$ENVIRONMENT_SELECTION" --KEYCLOAK_ENV "$KEYCLOAK_ENVIRONMENT")
    if [[ -n "$LOG_LEVEL" ]]; then
        runArgs+=(--LOG_LEVEL "$LOG_LEVEL")
    fi

    echo -e "${YELLOW}Starting in background: ./run-apicalendar.sh ${runArgs[*]} > logs/windfire-calendar.log 2>&1 &${RESET}"
    ./run-apicalendar.sh "${runArgs[@]}" > logs/windfire-calendar.log 2>&1 &
}

# ===== ARGUMENT PARSING FUNCTION =====
parseArguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            1|2|3)
                RUN_ENVIRONMENT="$1"
                shift
                ;;
            --LOG_LEVEL)
                if [[ -z "$2" ]]; then
                    echo -e "${RED}Error: --LOG_LEVEL requires a value${RESET}"
                    exit 1
                fi
                LOG_LEVEL="$2"
                shift 2
                ;;
            --KEYCLOAK_ENV)
                case $2 in
                    1|2|3|dev|test|prod)
                        KEYCLOAK_ENV_OPTION="$2"
                        shift 2
                        ;;
                    *)
                        echo -e "${RED}Error: --KEYCLOAK_ENV requires one of dev|test|prod (or 1|2|3)${RESET}"
                        exit 1
                        ;;
                esac
                ;;
            -h|--help)
                echo "Usage: ./run-apicalendar-background.sh [1|2|3] [--KEYCLOAK_ENV dev|test|prod] [--LOG_LEVEL LEVEL]"
                echo "Same arguments as ./run-apicalendar.sh (see ./run-apicalendar.sh --help); output goes to logs/windfire-calendar.log"
                exit 0
                ;;
            *)
                echo -e "${RED}Error: Unknown option '$1'${RESET}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# ===== EXECUTION =====
main "$@"
