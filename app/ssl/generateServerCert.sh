source ../../setenv.sh

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

# ===== MAIN FUNCTION =====
main()
{
    # Select environment
    selectEnvironment
    echo -e "Environment selected is ${BOLD}$ENVIRONMENT${RESET}"
    case "$ENVIRONMENT" in
        dev|staging)
            OPENSSL_CONFIG_FILE="openssl_config_localhost.ext"
            CERTS_DIR="."
            ;;
        prod)
            OPENSSL_CONFIG_FILE="openssl_config_raspberry.ext"
            CERTS_DIR=$WINDFIRE_DEFAULT_CERTS_PROD_DIR
            # Check if Certs directory exists, in case it does not exist, create it
            if [ ! -d "$CERTS_DIR" ]; then
                mkdir -p "$CERTS_DIR" || { echo -e "${RED}Error: failed to create directory: $CERTS_DIR${RED}" >&2; exit 1; }
            fi
            ;;
        *)
            echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${RESET}"
            echo "Valid options: dev, staging, prod"
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
    
    # 3) Sign server certificate
    signServerCertificate

    # 4) Delete server CSR
    deleteServerCsr
}

# ===== CREATE SERVER PRIVATE KEY FUNCTION =====
createServerPrivateKey()
{
    echo "Generating server private key ..."
    openssl genrsa -out $CERTS_DIR/$WINDFIRE_SERVER_PRIVATE_KEY 2048
    echo "Server private key generated"
    echo 
}

# ===== SERVER CSR CREATE FUNCTION =====
createServerCsr()
{
    echo "Creating Server CSR ..."
    openssl req -new -key $CERTS_DIR/$WINDFIRE_SERVER_PRIVATE_KEY -out $WINDFIRE_SERVER_CSR -subj "${SUBJECT}"
    echo "Server CSR created"
    echo 
}

# ===== SERVER CERTIFICATE SIGNING FUNCTION =====
signServerCertificate()
{
    echo "Signing Server Certificate ..."
    echo "  --> Create Server Certificate in $CERTS_DIR directory ..."
    echo "  --> Using $OPENSSL_CONFIG_FILE openssl configuration file ..."
    openssl x509 -req -in $WINDFIRE_SERVER_CSR -CA $WINDFIRE_ROOT_CA_CERTIFICATE -CAkey $WINDFIRE_ROOT_CA_KEY -CAcreateserial \
                -out $CERTS_DIR/$WINDFIRE_SERVER_CERTIFICATE -days $DAYS_VALID -sha256 \
                -extfile $OPENSSL_CONFIG_FILE
    echo "Server Certificate signed"
    echo 
}

# ===== SERVER CSR DELETE FUNCTION =====
deleteServerCsr()
{
    echo "Deleting Server CSR ..."
    rm $WINDFIRE_SERVER_CSR
    echo "Server CSR deleted"
}

# ===== CERTIFICATE AUTHORITY SELECTION FUNCTION =====
getCAs() {
   while true; do
        # Enter Root Certificate Authority certificate path
        read -r -p "Enter path for Certificate Authority truststore [${WINDFIRE_DEFAULT_TRUSTSTORE_DIR}]: " WINDFIRE_TRUSTSTORE_DIR
        if [[ -z "$WINDFIRE_TRUSTSTORE_DIR" ]]; then
            WINDFIRE_TRUSTSTORE_DIR=$WINDFIRE_DEFAULT_TRUSTSTORE_DIR
        fi
        WINDFIRE_ROOT_CA_CERTIFICATE=$WINDFIRE_TRUSTSTORE_DIR/$WINDFIRE_ROOT_CA_CERTIFICATE
        
        # Enter Root Certificate Authority key path
        read -r -p "Enter path for Certificate Authority keystore [${WINDFIRE_DEFAULT_KEYSTORE_DIR}]: " WINDFIRE_KEYSTORE_DIR
        if [[ -z "$WINDFIRE_KEYSTORE_DIR" ]]; then
            WINDFIRE_KEYSTORE_DIR=$WINDFIRE_DEFAULT_KEYSTORE_DIR
        fi
        WINDFIRE_ROOT_CA_KEY=$WINDFIRE_KEYSTORE_DIR/$WINDFIRE_ROOT_CA_KEY
        break
    done
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

# ===== SERVER COMMON NAME SETTING FUNCTION =====
selectEnvironment()
{
    while true; do
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

        case $ENVIRONMENT_SELECTION in
            1)  ENVIRONMENT=dev
                ;;
            2)  ENVIRONMENT=test
                ;;
            3)  ENVIRONMENT=prod
                ;;
            *) 	echo -e "${RED}No valid option selected${RESET}"
                getEnvironment
                ;;
        esac
        break
    done
}

# ===== EXECUTION =====
main