#!/bin/bash
source ../common.sh

# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API)

# ===== DEFAULT VALUES =====
LOG_LEVEL=
RUN_ENVIRONMENT=
SECURITY_ENV_OPTION=

# ===== MAIN FUNCTION =====
main() {
    # Display header
    echo -e "${BLU}################################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar FastAPI server ###############${RESET}"
    echo -e "${BLU}################################################################${RESET}"
    echo 
    
    # Invoke parseArguments() function to parse and validate arguments
    parseArguments "$@"

    # Select application environment and Windfire Security environment (prompts only for values not given as arguments)
    selectEnvironment "$RUN_ENVIRONMENT"
    selectSecurityEnvironment "$SECURITY_ENV_OPTION"

    # createPythonVenv.sh re-sources ../common.sh, which resets these variables: save them and restore after
    local selectedEnvironment=$ENVIRONMENT
    local selectedSecurityEnvironment=$WINDFIRE_SECURITY_ENVIRONMENT
    local selectedSecurityHost=$WINDFIRE_SECURITY_HOST
    local selectedSecurityPort=$WINDFIRE_SECURITY_PORT

    # Source createPythonVenv.sh script to create and activate Python Virtual Environment
    source ./createPythonVenv.sh "$ENVIRONMENT_SELECTION"

    ENVIRONMENT=$selectedEnvironment
    WINDFIRE_SECURITY_ENVIRONMENT=$selectedSecurityEnvironment
    WINDFIRE_SECURITY_HOST=$selectedSecurityHost
    WINDFIRE_SECURITY_PORT=$selectedSecurityPort

    # Invoke run() function to start the FastAPI server
    run
}

# ===== SERVER RUN FUNCTION =====
run()
{
    echo -e "${YELLOW}Running calendar service API in environment : $ENVIRONMENT${RESET}"
    echo -e "${YELLOW}Authenticating against Windfire Security environment : $WINDFIRE_SECURITY_ENVIRONMENT ($WINDFIRE_SECURITY_HOST:$WINDFIRE_SECURITY_PORT)${RESET}"

    # Run Calendar Service
    echo -e "${YELLOW}Starting server with: LOG_LEVEL=${LOG_LEVEL} ENVIRONMENT=$ENVIRONMENT WINDFIRE_SECURITY_ENVIRONMENT=$WINDFIRE_SECURITY_ENVIRONMENT WINDFIRE_SECURITY_HOST=$WINDFIRE_SECURITY_HOST WINDFIRE_SECURITY_PORT=$WINDFIRE_SECURITY_PORT python3 calendarApiServer.py${RESET}"

    LOG_LEVEL=${LOG_LEVEL} \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    WINDFIRE_SECURITY_ENVIRONMENT=$WINDFIRE_SECURITY_ENVIRONMENT \
    WINDFIRE_SECURITY_HOST=$WINDFIRE_SECURITY_HOST \
    WINDFIRE_SECURITY_PORT=$WINDFIRE_SECURITY_PORT \
    ROOT_CA_PATH=$WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE \
    python3 calendarApiServer.py
}

# ===== ARGUMENT PARSING FUNCTION =====
parseArguments() {
    echo "Parsing arguments..."
    while [[ $# -gt 0 ]]; do
        case $1 in
            1|2|3)
                echo "environment option selected: $1"
                RUN_ENVIRONMENT="$1"
                shift
                ;;
            --LOG_LEVEL)
                if [[ -z "$2" ]]; then
                    echo -e "${RED}Error: --LOG_LEVEL requires a value${RESET}"
                    exit 1
                fi
                echo "Setting LOG_LEVEL to $2"
                LOG_LEVEL="$2"
                shift 2
                ;;
            --SECURITY_ENV)
                case $2 in
                    1|2|3|dev|test|prod)
                        echo "Windfire Security environment option selected: $2"
                        SECURITY_ENV_OPTION="$2"
                        shift 2
                        ;;
                    *)
                        echo -e "${RED}Error: --SECURITY_ENV requires one of dev|test|prod (or 1|2|3)${RESET}"
                        exit 1
                        ;;
                esac
                ;;
            -h|--help)
                printHelp
                exit 0
                ;;
            -v|--version)
                echo "Windfire Calendar API Server v1.0.0"
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

# ===== HELP FUNCTION =====
printHelp() {
    # Display help information
    echo -e "${BOLD}╔═════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║    Windfire Calendar FastAPI Server - Startup Script    ║${RESET}"
    echo -e "${BOLD}╚═════════════════════════════════════════════════════════╝${RESET}"
    echo
    echo -e "${BOLD}DESCRIPTION:${RESET}"
    echo -e "Starts the Windfire Calendar FastAPI server that wraps the Google Calendar API."
    echo -e "The script handles Python virtual environment setup and server initialization."
    echo
    echo -e "The script will run the following steps:"
    echo -e "  1. Create a Python Virtual Environment, if it does not exist"
    echo -e "  2. Activate the Python Virtual Environment"
    echo -e "  3. Install Python prerequisites, if not already installed"
    echo -e "  4. Run the Windfire Calendar FastAPI server"
    echo
    echo -e "${BOLD}USAGE:${RESET}"
    echo -e "    ./run-apicalendar.sh [1|2|3] [--SECURITY_ENV ENV] [--LOG_LEVEL LEVEL]"
    echo
    echo -e "${BOLD}ARGUMENTS:${RESET}"
    echo -e "1|2|3                   Application environment: 1=Development, 2=Test, 3=Production (prompted if omitted)"
    echo
    echo -e "${BOLD}OPTIONS:${RESET}"
    echo -e "-v, --version           Show version information"
    echo
    echo -e "--SECURITY_ENV ENV      Windfire Security environment used for authentication: dev|test|prod (or 1|2|3)"
    echo -e "                        Prompted if omitted (Enter = prod). Host/port are read from WINDFIRE_SECURITY_<ENV>_HOST/PORT in .env"
    echo
    echo -e "--LOG_LEVEL LEVEL       Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    echo
    echo -e "-h, --help              Display this help message and exit"
    echo
    echo -e "${BOLD}EXAMPLES:${RESET}"
    echo -e "./run-apicalendar.sh"
    echo -e "    Prompt for application environment and Windfire Security environment"
    echo
    echo -e "./run-apicalendar.sh 3 --SECURITY_ENV prod"
    echo -e "    Run in Production, authenticating against the Production Windfire Security server"
    echo
    echo -e "./run-apicalendar.sh 1 --SECURITY_ENV dev --LOG_LEVEL DEBUG"
    echo -e "    Run in Development against the Development Windfire Security server, with DEBUG logging"
    echo
    echo -e "./run-apicalendar.sh --help"
    echo -e "    Display this help message"
    echo
    echo -e "${BOLD}WHAT THIS SCRIPT DOES:${RESET}"
    echo -e "1. Create a Python Virtual Environment (if it doesn't exist)"
    echo -e "2. Activate the Python Virtual Environment"
    echo -e "3. Install Python prerequisites (if not already installed)"
    echo -e "4. Run the Windfire Calendar FastAPI server"
    echo
    echo -e "${BOLD}.env KEYS USED:${RESET}"
    echo -e "   WINDFIRE_SECURITY_DEV_HOST / WINDFIRE_SECURITY_DEV_PORT     Development Windfire Security server"
    echo -e "   WINDFIRE_SECURITY_TEST_HOST / WINDFIRE_SECURITY_TEST_PORT   Test Windfire Security server"
    echo -e "   WINDFIRE_SECURITY_PROD_HOST / WINDFIRE_SECURITY_PROD_PORT   Production Windfire Security server"
    echo 
    echo -e "${BOLD}EXIT CODES:${RESET}"
    echo -e "   0   Success"
    echo -e "   1   Invalid arguments"
    echo -e "   2   Missing environment specification"
    echo
    echo -e "${BOLD}NOTES:${RESET}"
    echo -e "   - The script sources '../common.sh' for configuration"
    echo -e "   - Python 3 is required"
}

# ===== EXECUTION =====
main "$@"