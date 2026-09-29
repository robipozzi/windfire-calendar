#!/bin/bash
cd "$(dirname "$0")" || exit 1
source ../common.sh

# ***** Deploy script for Windfire Calendar component *****

# ===== MAIN FUNCTION =====
main() {
    # Display header
    echo -e "${BOLD}${BLU}##########################################################################${RESET}"
    echo -e "${BOLD}${BLU}############### Windfire Calendar Service deploy procedure ###############${RESET}"
    echo -e "${BOLD}${BLU}##########################################################################${RESET}"
    echo

    # Parse arguments
    parseArgs "$@"

    # Start deployment
    deploy
}

parseArgs()
{
    echo -e "${BOLD}Parsing arguments...${RESET}"
    PLATFORM_OPTION=
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                printHelp
                exit 0
                ;;
            -*)
                echo -e "${RED}Error: Unknown option '$1'${RESET}"
                echo "Use --help for usage information"
                exit 1
                ;;
            *)
                PLATFORM_OPTION=$1
                shift
                ;;
        esac
    done
    selectDeploymentPlatform
    echo -e "${BOLD}Selected platform: ${DEPLOY_PLATFORM}${RESET}"
}

deploy()
{
    setFunction
    $DEPLOY_FUNCTION
}

setFunction()
{
    while true; do
        case $DEPLOY_PLATFORM in
            raspberry) DEPLOY_FUNCTION="deployToRaspberry"
                return
                ;;
            *)  echo -e "${RED}No valid option selected${RESET}"
                PLATFORM_OPTION=""
                PLATFORM_SELECTED=false
                selectDeploymentPlatform || exit 1
                ;;
        esac
    done
}

deployToRaspberry()
{
    ## Deploy Windfire Calendar component to remote Raspberry box
    echo -e "${BLU}Deploy Windfire Calendar component to Raspberry Pi ...${RESET}"
    echo
    checkPrerequisites
    checkRootCA
    checkSSLCertificates
    checkSecurityClientWheel
    checkAppConfig
    collectSecrets
    runPlaybook raspberry/windfire-calendar-deploy.yaml
}

# ===== PRE-FLIGHT FUNCTIONS =====
printBanner()
{
    local title="***** $1 *****"
    local line
    line=$(printf '%*s' "${#title}" '' | tr ' ' '*')
    echo -e "${BLU}${line}${RESET}"
    echo -e "${BLU}${title}${RESET}"
    echo -e "${BLU}${line}${RESET}"
}

checkPrerequisites()
{
    printBanner "Check deployment prerequisites"
    if ! command -v ansible-playbook >/dev/null 2>&1; then
        echo -e "${RED}Error: ansible-playbook not found on PATH. Install Ansible first (e.g. brew install ansible)${RESET}"
        exit 1
    fi
    echo -e "${GREEN}ansible-playbook found: $(command -v ansible-playbook)${RESET}"
    if [ ! -f "$ANSIBLE_SSH_KEY" ]; then
        echo -e "${RED}Error: Ansible SSH key $ANSIBLE_SSH_KEY not found${RESET}"
        exit 1
    fi
    echo -e "${GREEN}Ansible SSH key found: $ANSIBLE_SSH_KEY${RESET}"
    echo
}

checkRootCA()
{
    printBanner "Check Windfire Root CA"
    if [ ! -f "$WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE" ]; then
        echo -e "${RED}Error: Windfire Root CA $WINDFIRE_DEFAULT_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE not found${RESET}"
        echo -e "${RED}Create it with windfire-security/ssl/createRootCA.sh first${RESET}"
        exit 1
    fi
    echo -e "${GREEN}Windfire Root CA found in $WINDFIRE_DEFAULT_TRUSTSTORE_DIR${RESET}"
    echo
}

checkSSLCertificates()
{
    printBanner "Check SSL certificates for Raspberry"
    if [ ! -f "$WINDFIRE_DEFAULT_CERTS_PROD_DIR/$WINDFIRE_SERVER_CERTIFICATE" ] || [ ! -f "$WINDFIRE_DEFAULT_CERTS_PROD_DIR/$WINDFIRE_SERVER_KEY" ]; then
        echo -e "${YELLOW}SSL certificate/key not found for raspberry environment. Generating...${RESET}"
        echo -e "${YELLOW}When prompted, select option 3 (Production)${RESET}"
        echo
        (cd ../app/ssl && ./generateServerCert.sh)
        if [ ! -f "$WINDFIRE_DEFAULT_CERTS_PROD_DIR/$WINDFIRE_SERVER_CERTIFICATE" ] || [ ! -f "$WINDFIRE_DEFAULT_CERTS_PROD_DIR/$WINDFIRE_SERVER_KEY" ]; then
            echo -e "${RED}Error: SSL certificate/key still missing in $WINDFIRE_DEFAULT_CERTS_PROD_DIR (was Production selected?)${RESET}"
            exit 1
        fi
    fi
    echo -e "${GREEN}SSL certificate and key found in $WINDFIRE_DEFAULT_CERTS_PROD_DIR${RESET}"
    echo
}

checkSecurityClientWheel()
{
    printBanner "Check windfire-security-client wheel"
    local wheels=("$SECURITY_CLIENT_DIST_DIR"/client-*.whl)
    if [ ! -f "${wheels[0]}" ]; then
        echo -e "${RED}Error: no client-*.whl found in $SECURITY_CLIENT_DIST_DIR${RESET}"
        echo -e "${RED}Build it with ./createModule.sh in the windfire-security-client repository${RESET}"
        exit 1
    fi
    echo -e "${GREEN}windfire-security-client wheel found: ${wheels[*]##*/}${RESET}"
    echo
}

checkAppConfig()
{
    printBanner "Check Google Calendar API credentials"
    local missing=false
    for file in credentials.json token.json; do
        if [ ! -f "../app/$file" ]; then
            echo -e "${RED}Error: app/$file not found${RESET}"
            missing=true
        fi
    done
    if [ "$missing" == true ]; then
        echo -e "${RED}Download credentials.json from Google Cloud Console into app/, then run the app locally once${RESET}"
        echo -e "${RED}(e.g. cd app && ./run-calendar.sh) to complete the OAuth consent and create token.json${RESET}"
        exit 1
    fi
    echo -e "${GREEN}app/credentials.json and app/token.json found${RESET}"
    echo
}

# ===== SECRETS COLLECTION FUNCTIONS =====
inputWithDefault()
{
    local label=$1
    local default=$2
    local value=
    while [[ -z "$value" ]]; do
        read -r -p "${CYAN}Input $label [${default}]: ${END}" value
        value=${value:-$default}
        if [[ -z "$value" ]]; then
            echo -e "${RED}$label cannot be blank${RESET}" >&2
        fi
    done
    echo "$value"
}

collectSecrets()
{
    printBanner "Collect Keycloak configuration and secrets"
    local envFile=../app/.env
    KEYCLOAK_SERVER_HOST=$(inputWithDefault "Keycloak server host" "$(getEnvFileValue $envFile KEYCLOAK_PROD_HOST)")
    KEYCLOAK_SERVER_PORT=$(inputWithDefault "Keycloak server port" "$(getEnvFileValue $envFile KEYCLOAK_PROD_PORT)")
    KEYCLOAK_SERVICE=$(inputWithDefault "Keycloak service" "$(getEnvFileValue $envFile KEYCLOAK_SERVICE)")
    AUTH_SERVICE_TEST=$KEYCLOAK_SERVICE
    inputKeycloakClientSecret
    export KEYCLOAK_SERVER_HOST KEYCLOAK_SERVER_PORT KEYCLOAK_SERVICE KEYCLOAK_CLIENT_SECRET
    echo
}

# ===== ANSIBLE FUNCTIONS =====
runPlaybook()
{
    local playbook=$1
    printBanner "Run Ansible playbook $playbook"
    eval "$(ssh-agent -s)" >/dev/null
    trap 'ssh-agent -k >/dev/null' EXIT
    ssh-add "$ANSIBLE_SSH_KEY" || { echo -e "${RED}Error: ssh-add $ANSIBLE_SSH_KEY failed${RESET}"; exit 1; }
    export ANSIBLE_CONFIG=$PWD/raspberry/ansible.cfg
    if ansible-playbook "$playbook"; then
        echo -e "${GREEN}Windfire Calendar deployed and running on Raspberry Pi${RESET}"
        echo
    else
        echo -e "${RED}Deployment failed: see Ansible output above${RESET}"
        exit 1
    fi
}

# ===== HELP FUNCTION =====
printHelp() {
    echo -e "${BOLD}╔═════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║    Windfire Calendar Service - Deploy Script            ║${RESET}"
    echo -e "${BOLD}╚═════════════════════════════════════════════════════════╝${RESET}"
    echo
    echo -e "${BOLD}DESCRIPTION:${RESET}"
    echo -e "Deploys the Windfire Calendar API to the calendar_service Ansible host group"
    echo -e "and runs it as the windfire-calendar systemd service."
    echo
    echo -e "${BOLD}USAGE:${RESET}"
    echo -e "    ./deploy.sh [1]"
    echo
    echo -e "${BOLD}ARGUMENTS:${RESET}"
    echo -e "1                       Deployment platform: 1=Raspberry (prompted if omitted)"
    echo
    echo -e "${BOLD}OPTIONS:${RESET}"
    echo -e "-h, --help              Display this help message and exit"
    echo
    echo -e "${BOLD}WHAT THIS SCRIPT DOES:${RESET}"
    echo -e "1. Check that ansible-playbook and the Ansible SSH key are available"
    echo -e "2. Check that the Windfire Root CA exists"
    echo -e "3. Check the production server certificate and key (generated if missing)"
    echo -e "4. Check that the windfire-security-client wheel has been built"
    echo -e "5. Check app/credentials.json and app/token.json"
    echo -e "6. Ask for the Keycloak host, port, service and client secret"
    echo -e "7. Run the Ansible playbook: deploy, start the systemd service and health-check it"
    echo
    echo -e "${BOLD}ENVIRONMENT VARIABLES:${RESET}"
    echo -e "   KEYCLOAK_CLIENT_SECRET  Keycloak OAuth client secret (prompted if not set)"
    echo
    echo -e "${BOLD}EXIT CODES:${RESET}"
    echo -e "   0   Success"
    echo -e "   1   Invalid arguments, failed pre-flight check or failed deployment"
}

# ===== EXECUTION =====
main "$@"
