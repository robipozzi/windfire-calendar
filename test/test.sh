#!/bin/bash
source ../setenv.sh

# ***** Run Windfire Calendar test application

# ===== MAIN FUNCTION =====
main()
{
    echo -e "${BLU}##################################################################${RESET}"
    echo -e "${BLU}############### Windfire Calendar test application ###############${RESET}"
    echo -e "${BLU}##################################################################${RESET}"
    echo 

    # Parse command-line arguments
    parse_args "$@"
    
    # Create and activate virtual environment
    source ./createPythonVenv.sh

    # Run test application
    run
}

# ===== TEST APPLICATION RUN FUNCTION =====
run()
{
    printSelectEnvironment $1
    getCredentials

    # Show configuration
    display_config

    echo -e "${YELLOW}Running test application${RESET}"
    
    # Build Python command with optional flags
    local python_cmd="python3 test.py"

    if [ -z "${PORT}" ]; then
        echo -e "${YELLOW}PORT is not set or is empty, running with default${RESET}"
        python_cmd="python3 test.py"
    else 
        echo -e "${YELLOW}PORT is set to $PORT${RESET}"
        python_cmd=" PORT=$PORT python3 test.py"
    fi

    # Set environment variables and run 
    echo -e "${YELLOW}Run test application with: USERNAME=$USERNAME PASSWORD={***} SERVICE=$AUTH_SERVICE_TEST VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS ENVIRONMENT=$ENVIRONMENT $python_cmd${RESET}"
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    ROOT_CA_PATH=$WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE \
    eval $python_cmd
}

# ===== ARGUMENT PARSING FUNCTION =====
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -h|--help)
                print_help
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

# ===== CONFIGURATION DISPLAY FUNCTION =====
display_config() {
    echo -e "${BOLD}${GREEN}Configuration Summary:${RESET}"
    echo -e "  Port:           ${YELLOW}$PORT${RESET}"
    echo
}

# ===== HELP FUNCTION =====
print_help() {
    # Display help information
    echo -e "${BOLD}==================================${RESET}"
    echo -e "${BOLD}Windfire Calendar test application${RESET}"
    echo -e "${BOLD}==================================${RESET}"
    echo
    echo -e "${BOLD}DESCRIPTION:${RESET}"
    echo -e "    This script runs an application that tests Windfire Calendar APIs"
    echo
    echo -e "    The script will run the following steps:"
    echo -e "    1. Create a Python Virtual Environment, if does not exist"
    echo -e "    2. Activate the Python Virtual Environment"
    echo -e "    3. Install Python prerequisites, if not already installed"
    echo -e "    4. Run the Windfire Calendar test application"
    echo
    echo -e "${BOLD}USAGE:${RESET}"
    echo -e "    ./test.sh [OPTIONS]"
    echo
    echo -e "${BOLD}OPTIONS:${RESET}"
    echo -e "    -p, --port PORT            Specify port on which Windfire Calendar server runs (1-65535)"
    echo -e "                               Default: 8000 (for HTTP) / 8443 (for HTTPS)"
    echo
    echo -e "    -h, --help                 Display this help message and exit"
    echo
    echo -e "${BOLD}EXAMPLES:${RESET}"
    echo -e "    # Run with default settings"
    echo -e "    ./test.sh"
    echo
    echo -e "    # Run tests of Windfire Calendar service running on custom port"
    echo -e "    ./test.sh -p 9000"
    echo
    echo -e "${BOLD}STARTUP STEPS:${RESET}"
    echo -e "    1. Create a Python Virtual Environment, if does not exist"
    echo -e "    2. Activate the Python Virtual Environment"
    echo -e "    3. Install Python prerequisites, if not already installed"
    echo -e "    4. Run the Windfire Calendar test application"
    echo
    echo -e "${BOLD}TROUBLESHOOTING:${RESET}"
    echo -e "    • Permission denied: Run 'chmod +x start-auth-server.sh'"
    echo -e "    • Module not found: Ensure createPythonVenv.sh is in the current directory"
    echo
    echo -e "${BOLD}========================================================${RESET}"
}

# ===== EXECUTION =====
main "$@"