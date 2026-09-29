#!/bin/bash
source ../common.sh

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

    # Run test application and propagate its exit code (0 = all tests passed, 1 = failures)
    run
    exit $?
}

# ===== TEST APPLICATION RUN FUNCTION =====
run()
{
    selectEnvironment "$RUN_ENVIRONMENT"
    selectSecurityEnvironment "$RUN_SECURITY_ENVIRONMENT"
    getCredentials

    # Show configuration
    display_config

    echo -e "${YELLOW}Running test application${RESET}"
    
    # Pass PORT only when it was given, otherwise test.py uses its default (8443)
    if [ -n "${PORT}" ]; then
        echo -e "${YELLOW}PORT is set to $PORT${RESET}"
        export PORT
    else
        echo -e "${YELLOW}PORT is not set, test.py will use its default${RESET}"
        unset PORT
    fi

    # Set environment variables and run
    echo -e "${YELLOW}Run test application with: USERNAME=$USERNAME PASSWORD={***} SERVICE=$AUTH_SERVICE_TEST VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS ENVIRONMENT=$ENVIRONMENT SECURITY_ENVIRONMENT=$SECURITY_ENVIRONMENT ${PORT:+PORT=$PORT }python3 test.py${RESET}"
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    SERVICE=$AUTH_SERVICE_TEST \
    VERIFY_SSL_CERTS=$VERIFY_SSL_CERTS \
    ENVIRONMENT=$ENVIRONMENT \
    SECURITY_ENVIRONMENT=$SECURITY_ENVIRONMENT \
    ROOT_CA_PATH=$WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE \
    python3 test.py
}

# ===== WINDFIRE SECURITY ENVIRONMENT SELECTION FUNCTION =====
# Empty answer selects Production; host/port are resolved by test.py from ../app/.env
selectSecurityEnvironment()
{
    local option=$1
    while true; do
        if [[ -z "$option" ]]; then
            echo -e "${BLU}Select Windfire Security environment : ${RESET}"
            echo -e "${BLU}1. Development${RESET}"
            echo -e "${BLU}2. Test${RESET}"
            echo -e "${BLU}3. Production [default]${RESET}"
            read option
            if [[ -z "$option" ]]; then
                option=3
            fi
        fi
        case $option in
            1)  SECURITY_ENVIRONMENT=dev
                break
                ;;
            2)  SECURITY_ENVIRONMENT=test
                break
                ;;
            3)  SECURITY_ENVIRONMENT=prod
                break
                ;;
            *)  echo -e "${RED}No valid Windfire Security environment option selected: $option${RESET}"
                option=
                ;;
        esac
    done
}

# ===== ARGUMENT PARSING FUNCTION =====
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -e|--env)
                case $2 in
                    1|2|3)
                        RUN_ENVIRONMENT="$2"
                        shift 2
                        ;;
                    *)
                        echo -e "${RED}Error: --env requires one of 1|2|3${RESET}"
                        exit 1
                        ;;
                esac
                ;;
            -s|--security-env)
                case $2 in
                    1|2|3)
                        RUN_SECURITY_ENVIRONMENT="$2"
                        shift 2
                        ;;
                    *)
                        echo -e "${RED}Error: --security-env requires one of 1|2|3${RESET}"
                        exit 1
                        ;;
                esac
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
    echo -e "  Windfire Calendar environment:  ${YELLOW}$ENVIRONMENT${RESET}"
    echo -e "  Windfire Security environment:  ${YELLOW}$SECURITY_ENVIRONMENT${RESET}"
    echo -e "  Port:                           ${YELLOW}${PORT:-8443 (default)}${RESET}"
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
    echo -e "    This script runs a test suite against Windfire Calendar APIs"
    echo -e "    It prints a PASS/FAIL/SKIP summary and exits with 0 if all tests pass, 1 otherwise"
    echo
    echo -e "    The script will run the following steps:"
    echo -e "    1. Create a Python Virtual Environment, if does not exist"
    echo -e "    2. Activate the Python Virtual Environment"
    echo -e "    3. Install Python prerequisites, if not already installed"
    echo -e "    4. Run the Windfire Calendar test application"
    echo
    echo -e "${BOLD}USAGE:${RESET}"
    echo -e "    ./run-test.sh [OPTIONS]"
    echo
    echo -e "${BOLD}OPTIONS:${RESET}"
    echo -e "    -p, --port PORT            Specify port on which Windfire Calendar server runs (1-65535)"
    echo -e "                               Default: 8443"
    echo
    echo -e "    -e, --env 1|2|3            Windfire Calendar environment: 1=Development, 2=Test, 3=Production"
    echo -e "                               1/2 -> https://localhost:<PORT>, 3 -> https://raspberry02:<PORT>"
    echo -e "                               Prompted if omitted"
    echo
    echo -e "    -s, --security-env 1|2|3   Windfire Security environment used to authenticate:"
    echo -e "                               1=Development, 2=Test, 3=Production"
    echo -e "                               1/2 -> KEYCLOAK_DEV/TEST_HOST:PORT in ../app/.env (localhost:8444)"
    echo -e "                               3   -> https://raspberry01:8444"
    echo -e "                               Prompted if omitted, empty answer selects Production"
    echo
    echo -e "    -h, --help                 Display this help message and exit"
    echo
    echo -e "${BOLD}EXAMPLES:${RESET}"
    echo -e "    # Run with default settings"
    echo -e "    ./run-test.sh"
    echo
    echo -e "    # Run tests of Windfire Calendar service running on custom port"
    echo -e "    ./run-test.sh -p 9000"
    echo
    echo -e "    # Run tests against the Test environment without prompting for it"
    echo -e "    ./run-test.sh -e 2"
    echo
    echo -e "    # Test the local server, authenticating against the production Windfire Security server"
    echo -e "    ./run-test.sh -e 1 -s 3"
    echo
    echo -e "    # Test production without any environment prompt"
    echo -e "    ./run-test.sh -e 3 -s 3"
    echo
    echo -e "${BOLD}STARTUP STEPS:${RESET}"
    echo -e "    1. Create a Python Virtual Environment, if does not exist"
    echo -e "    2. Activate the Python Virtual Environment"
    echo -e "    3. Install Python prerequisites, if not already installed"
    echo -e "    4. Run the Windfire Calendar test application"
    echo
    echo -e "${BOLD}TROUBLESHOOTING:${RESET}"
    echo -e "    • Permission denied: Run 'chmod +x run-test.sh'"
    echo -e "    • Module not found: Ensure createPythonVenv.sh is in the current directory"
    echo
    echo -e "${BOLD}========================================================${RESET}"
}

# ===== EXECUTION =====
main "$@"