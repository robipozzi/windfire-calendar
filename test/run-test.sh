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
    selectTestSecurityEnvironment "$RUN_SECURITY_ENVIRONMENT"
    getCredentials

    # Show configuration
    display_config

    # Start local Windfire Security / Windfire Calendar servers when needed; cleanup() stops them on exit
    trap cleanup EXIT
    trap 'exit 130' INT TERM
    startServers || exit 1

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

# ===== LOCAL SERVERS START/STOP FUNCTIONS =====
SERVER_START_TIMEOUT=120
STARTED_SECURITY=false
STARTED_CALENDAR=false

# Succeeds if the health endpoint at URL answers 200
isHealthy()
{
    [[ "$(curl -sk --max-time 3 -o /dev/null -w '%{http_code}' "$1")" == "200" ]]
}

# Waits until the health endpoint answers (first start may create a venv and install prerequisites)
waitHealthy()
{
    local name=$1 url=$2 logFile=$3 elapsed=0
    echo -e "${YELLOW}Waiting for $name to answer on $url (up to ${SERVER_START_TIMEOUT}s) ...${RESET}"
    while (( elapsed < SERVER_START_TIMEOUT )); do
        if isHealthy "$url"; then
            echo -e "${GREEN}$name is up${RESET}"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo -e "${RED}$name did not answer within ${SERVER_START_TIMEOUT}s, last lines of $logFile:${RESET}"
    tail -n 30 "$logFile" 2>/dev/null
    return 1
}

# Starts the Windfire Security server when the selected Security environment points to localhost
startSecurityServer()
{
    local envFile=$WINDFIRE_CALENDAR_HOME/app/.env
    local prefix host port url
    prefix=$(echo "$SECURITY_ENVIRONMENT" | tr '[:lower:]' '[:upper:]')
    host=$(getEnvFileValue "$envFile" "WINDFIRE_SECURITY_${prefix}_HOST")
    port=$(getEnvFileValue "$envFile" "WINDFIRE_SECURITY_${prefix}_PORT")
    if [[ "$host" != "localhost" && "$host" != "127.0.0.1" ]]; then
        echo -e "${CYAN}Windfire Security server is remote (${host:-unknown}), not starting it${RESET}"
        return 0
    fi
    port=${port:-8444}
    url="https://localhost:$port/v1/monitor/health"
    if isHealthy "$url"; then
        echo -e "${CYAN}Windfire Security server already running on port $port, reusing it (it will be left running)${RESET}"
        return 0
    fi
    if [[ ! -x "$WINDFIRE_SECURITY_HOME/server/start-auth-server-background.sh" ]]; then
        echo -e "${RED}Error: $WINDFIRE_SECURITY_HOME/server/start-auth-server-background.sh not found, cannot start the local Windfire Security server${RESET}"
        return 1
    fi
    echo -e "${YELLOW}Starting Windfire Security server in background on port $port${RESET}"
    "$WINDFIRE_SECURITY_HOME/server/start-auth-server-background.sh" -p "$port" || return 1
    STARTED_SECURITY=true
    waitHealthy "Windfire Security server" "$url" "$WINDFIRE_SECURITY_HOME/server/logs/windfire-security.log"
}

# Starts the Windfire Calendar server when the selected Calendar environment is local (dev/test)
startCalendarServer()
{
    local appDir=$WINDFIRE_CALENDAR_HOME/app
    local serverPort port url
    if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "test" ]]; then
        echo -e "${CYAN}Windfire Calendar server is remote ($ENVIRONMENT), not starting it${RESET}"
        return 0
    fi
    serverPort=$(getEnvFileValue "$appDir/.env" API_PORT_SECURE)
    serverPort=${serverPort:-8443}
    port=${PORT:-8443}
    url="https://localhost:$port/v1/monitor/health"
    if isHealthy "$url"; then
        echo -e "${CYAN}Windfire Calendar server already running on port $port, reusing it (it will be left running)${RESET}"
        return 0
    fi
    if [[ "$port" != "$serverPort" ]]; then
        echo -e "${YELLOW}Warning: port $port differs from API_PORT_SECURE ($serverPort) in app/.env, not starting Windfire Calendar server: it must already be running on port $port${RESET}"
        return 0
    fi
    echo -e "${YELLOW}Starting Windfire Calendar server in background on port $serverPort${RESET}"
    (cd "$appDir" && ./start-apicalendar-background.sh "$ENVIRONMENT_SELECTION" --SECURITY_ENV "$SECURITY_ENVIRONMENT") || return 1
    STARTED_CALENDAR=true
    waitHealthy "Windfire Calendar server" "$url" "$appDir/logs/windfire-calendar.log"
}

startServers()
{
    startSecurityServer || return 1
    startCalendarServer || return 1
    echo
}

# Stops only the servers this script started, keeping the test exit code
cleanup()
{
    local rc=$?
    trap - EXIT INT TERM
    if [[ "$STARTED_CALENDAR" == true ]]; then
        echo -e "${YELLOW}Stopping Windfire Calendar server${RESET}"
        (cd "$WINDFIRE_CALENDAR_HOME/app" && ./stop-apicalendar.sh)
    fi
    if [[ "$STARTED_SECURITY" == true ]]; then
        echo -e "${YELLOW}Stopping Windfire Security server${RESET}"
        (cd "$WINDFIRE_SECURITY_HOME/server" && ./stop-auth-server.sh)
    fi
    exit $rc
}

# ===== WINDFIRE SECURITY ENVIRONMENT SELECTION FUNCTION =====
# Empty answer selects Production; host/port are resolved by test.py from ../app/.env
selectTestSecurityEnvironment()
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
    echo -e "    4. Ask for the Windfire Calendar and Windfire Security environments and credentials (unless given as options)"
    echo -e "    5. Start local Windfire Security / Windfire Calendar servers in background, if needed"
    echo -e "    6. Run the Windfire Calendar test application"
    echo -e "    7. Stop the servers started in step 5"
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
    echo -e "                               1/2 -> WINDFIRE_SECURITY_DEV/TEST_HOST:PORT in ../app/.env (localhost:8444)"
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
    echo -e "    4. Ask for the Windfire Calendar and Windfire Security environments and credentials (unless given as options)"
    echo -e "    5. Start local Windfire Security / Windfire Calendar servers in background, if needed"
    echo -e "    6. Run the Windfire Calendar test application"
    echo -e "    7. Stop the servers started in step 5"
    echo
    echo -e "${BOLD}LOCAL SERVERS:${RESET}"
    echo -e "    • Security env 1/2 with a localhost host in ../app/.env: the Windfire Security server is started"
    echo -e "      from ../../windfire-security/server (log: server/logs/windfire-security.log)"
    echo -e "    • Calendar env 1/2: the Windfire Calendar server is started from ../app (log: app/logs/windfire-calendar.log)"
    echo -e "    • A server already answering on its port is reused and left running"
    echo -e "    • Only servers started by this script are stopped, also on failure or Ctrl-C"
    echo -e "    • With -p different from API_PORT_SECURE in ../app/.env the Calendar server is not started"
    echo -e "    • Production servers (raspberry01/raspberry02) are never started"
    echo
    echo -e "${BOLD}TROUBLESHOOTING:${RESET}"
    echo -e "    • Permission denied: Run 'chmod +x run-test.sh'"
    echo -e "    • Module not found: Ensure createPythonVenv.sh is in the current directory"
    echo
    echo -e "${BOLD}========================================================${RESET}"
}

# ===== EXECUTION =====
main "$@"