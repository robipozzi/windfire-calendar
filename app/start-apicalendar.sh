#!/bin/bash

# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API)

source ../setenv.sh
source ../commons.sh

# ===== DEFAULT VALUES =====
LOG_LEVEL=
RUN_ENVIRONMENT=

# ===== MAIN FUNCTION =====
main() {
    # Display header
    echo -e "${BLU}################################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar FastAPI server ###############${RESET}"
    echo -e "${BLU}################################################################${RESET}"
    echo 
    
    # Invoke parseArguments() function to parse and validate arguments
    parseArguments "$@"

    # Source createPythonVenv.sh script to create and activate Python Virtual Environment
    source ./createPythonVenv.sh "$RUN_ENVIRONMENT"

    # Invoke run() function to start the FastAPI server
    run "$RUN_ENVIRONMENT"
}

# ===== SERVER RUN FUNCTION =====
run()
{
    printSelectEnvironment $1
    echo -e "${YELLOW}Running calendar service API in environment : $ENVIRONMENT${RESET}"
    inputKeycloakClientSecret

    # Run Calendar Service
    echo -e "${YELLOW}Starting server with: LOG_LEVEL=${LOG_LEVEL} ENVIRONMENT=$ENVIRONMENT KEYCLOAK_CLIENT_SECRET={***} python3 calendarApiServer.py${RESET}"

    LOG_LEVEL=${LOG_LEVEL} \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    ROOT_CA_PATH=$WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE \
    KEYCLOAK_CLIENT_SECRET=$KEYCLOAK_CLIENT_SECRET \
    python3 calendarApiServer.py
}

# ===== ARGUMENT PARSING FUNCTION =====
parseArguments() {
    echo "Parsing arguments..."
    local arg="$1"

    # Check for help flags
    if [[ "$arg" == "-h" ]] || [[ "$arg" == "--help" ]]; then
        printHelp
        exit 0
    fi

    # Check for version flag
    if [[ "$arg" == "-v" ]] || [[ "$arg" == "--version" ]]; then
        echo "Windfire Calendar API Server v1.0.0"
        exit 0
    fi

    # Check for valid environment
    if [[ "$arg" == "1" ]] || [[ "$arg" == "2" ]] || [[ "$arg" == "3" ]]; then
        echo "environment option selected: $arg"
        RUN_ENVIRONMENT="$arg"
        arg="$2"
        # Check for version flag
        if [[ "$arg" == "--LOG_LEVEL" ]] ; then
            arg="$3"
            echo "Setting LOG_LEVEL to $arg"
            LOG_LEVEL="$arg"
            return 0
        fi
        return
    fi

    # Check for version flag
    if [[ "$arg" == "--LOG_LEVEL" ]] ; then
        arg="$2"
        echo "Setting LOG_LEVEL to $arg"
        LOG_LEVEL="$arg"
        return 0
    fi

    return 0
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
    echo -e "    ./start-apicalendar.sh [OPTIONS] [ENVIRONMENT]"
    echo
    echo -e "${BOLD}OPTIONS:${RESET}"
    echo -e "-v, --version           Show version information"
    echo
    echo -e "--LOG_LEVEL LEVEL       Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    echo
    echo -e "-h, --help              Display this help message and exit"
    echo
    echo -e "${BOLD}EXAMPLES:${RESET}"
    echo -e "./start-apicalendar.sh --LOG_LEVEL ERROR"
    echo -e "    Set logging level to ERROR"
    echo
    echo -e "./start-apicalendar.sh --help"
    echo -e "    Display this help message"
    echo
    echo -e "${BOLD}WHAT THIS SCRIPT DOES:${RESET}"
    echo -e "1. Create a Python Virtual Environment (if it doesn't exist)"
    echo -e "2. Activate the Python Virtual Environment"
    echo -e "3. Install Python prerequisites (if not already installed)"
    echo -e "4. Run the Windfire Calendar FastAPI server"
    echo
    echo -e "${BOLD}ENVIRONMENT VARIABLES REQUIRED:${RESET}"
    echo -e "   KEYCLOAK_CLIENT_SECRET  Keycloak OAuth client secret (prompted if not set)"
    echo 
    echo -e "${BOLD}EXIT CODES:${RESET}"
    echo -e "   0   Success"
    echo -e "   1   Invalid arguments"
    echo -e "   2   Missing environment specification"
    echo
    echo -e "${BOLD}NOTES:${RESET}"
    echo -e "   - The script sources '../setenv.sh' and '../commons.sh' for configuration"
    echo -e "   - Python 3 is required"
}

# ===== EXECUTION =====
main "$@"