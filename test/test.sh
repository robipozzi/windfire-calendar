source ../setEnv.sh

getCredentials() {
    while true; do
        read -p "Enter username: " USERNAME
        if [[ -z "$USERNAME" ]]; then
            echo "Error: Username cannot be empty."
            continue
        fi
        read -s -p "Enter password: " PASSWORD
        echo
        if [[ -z "$PASSWORD" ]]; then
            echo "Error: Password cannot be empty."
            continue
        fi
        export USERNAME
        export PASSWORD
        break
    done
}

# ***** Run Test script for Google Calendar API
run()
{
    getCredentials
    USERNAME=$USERNAME \
    PASSWORD=$PASSWORD \
    python3 test.py
}

# ***** MAIN EXECUTION
run