#!/bin/bash
source ../../common.sh

# ***** Generate Windfire Calendar Server Certificate signed by Windfire Root CA

# ===== VARIABLES =====
COUNTRY="IT"
REGION="Lombardia"
LOCALITY="Milano"
ORGANIZATION="Windfire"
ORGANIZATIONAL_UNIT="Windfire Calendar"
COMMON_NAME="Windfire Calendar API Server"
EMAIL="r.robipozzi@gmail.com"
DAYS_VALID=365
SUBJECT=""
WINDFIRE_SERVER_PRIVATE_KEY="windfire-calendar.key"
WINDFIRE_SERVER_CERTIFICATE="windfire-calendar.crt"
WINDFIRE_SERVER_CSR="windfire-calendar.csr"
OPENSSL_CONFIG_FILE=""
ROOT_CA_CERTIFICATE_PATH=""
ROOT_CA_KEY_PATH=""

# ===== MAIN FUNCTION =====
main()
{
    # Select environment
    selectEnvironment
    echo -e "Environment selected is ${BOLD}$ENVIRONMENT${RESET}"
    case "$ENVIRONMENT" in
        dev|test)
            OPENSSL_CONFIG_FILE="openssl_config_localhost.ext"
            CERTS_DIR="."
            ;;
        prod)
            OPENSSL_CONFIG_FILE="openssl_config_raspberry.ext"
            CERTS_DIR=$WINDFIRE_DEFAULT_CERTS_PROD_DIR
            # Check if Certs directory exists, in case it does not exist, create it
            if [ ! -d "$CERTS_DIR" ]; then
                mkdir -p "$CERTS_DIR" || { echo -e "${RED}Error: failed to create directory: $CERTS_DIR${RESET}" >&2; exit 1; }
            fi
            ;;
        *)
            echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${RESET}"
            echo "Valid options: dev, test, prod"
            exit 1
            ;;
    esac
    echo -e "Openssl config file set to ${BOLD}$OPENSSL_CONFIG_FILE${RESET}"

    # Enter keystore and truststore where CA root key and certificate are stored
    getCAs

    # Enter server Common Name (CN) [e.g.: localhost]
    getCN
    SUBJECT="/C=${COUNTRY}/ST=${REGION}/L=${LOCALITY}/O=${ORGANIZATION}/OU=${ORGANIZATIONAL_UNIT}/CN=${COMMON_NAME}/emailAddress=${EMAIL}"
    echo "Subject: ${SUBJECT}"

    # 1) Create server private key
    createServerPrivateKey

    # 2) Create server CSR (Common Name must match host, or use SANs)
    createServerCsr

    # 3) Sign server certificate with Windfire Root CA
    signServerCertificate

    # 4) Delete server CSR
    deleteServerCsr

    # 5) Verify server certificate chains to Windfire Root CA
    verifyServerCertificate
}

# ===== CREATE SERVER PRIVATE KEY FUNCTION =====
createServerPrivateKey()
{
    echo "Generating server private key in $CERTS_DIR directory ..."
    openssl genrsa -out $CERTS_DIR/$WINDFIRE_SERVER_PRIVATE_KEY 2048 \
        || { echo -e "${RED}Error: failed to generate server private key${RESET}" >&2; exit 1; }
    echo "Server private key generated"
    echo
}

# ===== SERVER CSR CREATE FUNCTION =====
createServerCsr()
{
    echo "Creating Server CSR ..."
    openssl req -new -key $CERTS_DIR/$WINDFIRE_SERVER_PRIVATE_KEY -out $WINDFIRE_SERVER_CSR -subj "${SUBJECT}" \
        || { echo -e "${RED}Error: failed to create server CSR${RESET}" >&2; exit 1; }
    echo "Server CSR created"
    echo
}

# ===== SERVER CERTIFICATE SIGNING FUNCTION =====
signServerCertificate()
{
    echo "Signing Server Certificate with Windfire Root CA ..."
    echo "  --> Create Server Certificate in $CERTS_DIR directory ..."
    echo "  --> Using $OPENSSL_CONFIG_FILE openssl configuration file ..."
    if ! openssl x509 -req -in $WINDFIRE_SERVER_CSR -CA "$ROOT_CA_CERTIFICATE_PATH" -CAkey "$ROOT_CA_KEY_PATH" -CAcreateserial \
                -out $CERTS_DIR/$WINDFIRE_SERVER_CERTIFICATE -days $DAYS_VALID -sha256 \
                -extfile $OPENSSL_CONFIG_FILE; then
        echo -e "${RED}Error: failed to sign server certificate${RESET}" >&2
        rm -f "$CERTS_DIR/$WINDFIRE_SERVER_CERTIFICATE" $WINDFIRE_SERVER_CSR
        exit 1
    fi
    echo "Server Certificate signed"
    echo
}

# ===== SERVER CSR DELETE FUNCTION =====
deleteServerCsr()
{
    echo "Deleting Server CSR ..."
    rm -f $WINDFIRE_SERVER_CSR
    echo "Server CSR deleted"
    echo
}

# ===== SERVER CERTIFICATE VERIFICATION FUNCTION =====
verifyServerCertificate()
{
    echo "Verifying Server Certificate against Windfire Root CA ..."
    openssl verify -CAfile "$ROOT_CA_CERTIFICATE_PATH" "$CERTS_DIR/$WINDFIRE_SERVER_CERTIFICATE" \
        || { echo -e "${RED}Error: server certificate is not signed by Windfire Root CA ${BLU}$ROOT_CA_CERTIFICATE_PATH${RESET}" >&2; exit 1; }
    openssl x509 -in "$CERTS_DIR/$WINDFIRE_SERVER_CERTIFICATE" -noout -issuer -ext subjectAltName -enddate
    echo -e "Server Certificate ${BLU}$CERTS_DIR/$WINDFIRE_SERVER_CERTIFICATE${RESET} verified"
    echo
}

# ===== CERTIFICATE AUTHORITY SELECTION FUNCTION =====
getCAs() {
    # Enter Root Certificate Authority certificate path
    read -r -p "Enter path for Certificate Authority truststore [${WINDFIRE_DEFAULT_TRUSTSTORE_DIR}]: " WINDFIRE_TRUSTSTORE_DIR
    if [[ -z "$WINDFIRE_TRUSTSTORE_DIR" ]]; then
        WINDFIRE_TRUSTSTORE_DIR=$WINDFIRE_DEFAULT_TRUSTSTORE_DIR
    fi
    ROOT_CA_CERTIFICATE_PATH=$WINDFIRE_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE

    # Enter Root Certificate Authority key path
    read -r -p "Enter path for Certificate Authority keystore [${WINDFIRE_DEFAULT_KEYSTORE_DIR}]: " WINDFIRE_KEYSTORE_DIR
    if [[ -z "$WINDFIRE_KEYSTORE_DIR" ]]; then
        WINDFIRE_KEYSTORE_DIR=$WINDFIRE_DEFAULT_KEYSTORE_DIR
    fi
    ROOT_CA_KEY_PATH=$WINDFIRE_KEYSTORE_DIR/$WINDFIRE_ROOT_CA_KEY

    # Windfire Root CA is created by createRootCA.sh in windfire-security repository
    if [ ! -f "$ROOT_CA_CERTIFICATE_PATH" ] || [ ! -f "$ROOT_CA_KEY_PATH" ]; then
        echo -e "${RED}Error: Windfire Root CA not found (expected ${BLU}$ROOT_CA_CERTIFICATE_PATH${RED} and ${BLU}$ROOT_CA_KEY_PATH${RED}).${RESET}" >&2
        echo -e "${RED}Run createRootCA.sh in windfire-security repository first.${RESET}" >&2
        exit 1
    fi
    echo -e "Using Windfire Root CA ${BLU}$ROOT_CA_CERTIFICATE_PATH${RESET}"
}

# ===== SERVER COMMON NAME SETTING FUNCTION =====
getCN() {
    while true; do
        read -r -p "Enter server Common Name (CN) [$COMMON_NAME]: " CN
        if [[ -z "$CN" ]]; then
            echo -e "${BOLD}Common Name (CN) not input, going with default ${BLU}$COMMON_NAME${RESET}${RESET}"
            break
        fi
        COMMON_NAME=$CN
        break
    done
}

# ===== EXECUTION =====
main
