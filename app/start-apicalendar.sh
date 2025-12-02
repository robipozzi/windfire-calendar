source ../setenv.sh
source ../commons.sh

LOG_LEVEL=
RUN_ENVIRONMENT=
# ***** Start FastAPI server for Windfire Calendar API (wraps Google Calendar API)

# ***** MAIN FUNCTION
main() {
    echo ${blu}"################################################################"${end}
    echo ${blu}"############### Windfire Calendar FastAPI server ###############"${end}
    echo ${blu}"################################################################"${end}
    echo ""
    echo "This script will run the following steps:"
    echo "  1. Create a Python Virtual Environment, if it does not exist"
    echo "  2. Activate the Python Virtual Environment"
    echo "  3. Install Python prerequisites, if not already installed"
    echo "  4. Run the Windfire Calendar FastAPI server"
    echo ""
    
    # Invoke parseArguments() function to parse and validate arguments
    parseArguments "$@"

    # Source createPythonVenv.sh script to create and activate Python Virtual Environment
    source ./createPythonVenv.sh "$RUN_ENVIRONMENT"

    # Invoke run() function to start the FastAPI server
    run "$RUN_ENVIRONMENT"
}

run()
{
    printSelectEnvironment $1
    echo ${cyn}Running calendar service API in environment : $ENVIRONMENT${end}
    inputKeycloakClientSecret
    LOG_LEVEL=${LOG_LEVEL} \
    ENVIRONMENT=$ENVIRONMENT \
    KEYCLOAK_CLIENT_SECRET=$KEYCLOAK_CLIENT_SECRET \
    python3 calendarApiServer.py
}

# ***** ARGUMENT PARSING FUNCTION
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

# ***** HELP FUNCTION
printHelp() {
    cat << EOF
╔═════════════════════════════════════════════════════════╗
║    Windfire Calendar FastAPI Server - Startup Script    ║
╚═════════════════════════════════════════════════════════╝

USAGE:
    ./start-apicalendar.sh [OPTION] [ENVIRONMENT]

DESCRIPTION:
    Starts the Windfire Calendar FastAPI server that wraps the Google Calendar API.
    This script handles Python virtual environment setup and server initialization.

OPTIONS:
    -h, --help              Show this help message and exit
    -v, --version           Show version information
    --LOG_LEVEL             Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)

EXAMPLES:
    ./start-apicalendar.sh --LOG_LEVEL ERROR
        Set logging level to ERROR

    ./start-apicalendar.sh --help
        Display this help message

WHAT THIS SCRIPT DOES:
    1. Create a Python Virtual Environment (if it doesn't exist)
    2. Activate the Python Virtual Environment
    3. Install Python prerequisites (if not already installed)
    4. Run the Windfire Calendar FastAPI server

ENVIRONMENT VARIABLES REQUIRED:
    KEYCLOAK_CLIENT_SECRET  Keycloak OAuth client secret (prompted if not set)

EXIT CODES:
    0   Success
    1   Invalid arguments
    2   Missing environment specification

NOTES:
    - The script sources '../setenv.sh' and '../commons.sh' for configuration
    - Python 3 is required
    - Virtual environment created in './venv' directory

EOF
}

# ***** MAIN EXECUTION
main "$@"