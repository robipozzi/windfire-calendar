source ../common.sh

# ***** Install Python modules prerequisites

# ===== MAIN FUNCTION =====
main()
{
    echo "Installing Python prerequisites..."
    if ! installPythonModules; then
        echo -e "${RED}Error: Python prerequisites installation failed, see pip output above.${RESET}"
        return 1
    fi
    echo "Python prerequisites installation complete."
    echo ""
    echo "Installing custom Python prerequisites..."
    if ! installCustomPythonModules $1; then
        echo -e "${RED}Error: custom Python prerequisites installation failed, see pip output above.${RESET}"
        return 1
    fi
    echo "Custom Python prerequisites installation complete."
}

# ===== Install Python prerequisites for Google Calendar API =====
installPythonModules()
{
    pip3 install -r requirements.txt
}

# ===== Install custom Windfire Security Python modules =====
installCustomPythonModules()
{
    ENVIRONMENT_OPTION=$1
    PIP_CMD="pip3 install"
    INSTALL_ARGS=$HOME/dev/windfire-security-client
    if [ -n "$ENVIRONMENT_OPTION" ] && [ "$ENVIRONMENT_OPTION" -eq 3 ]; then
        # Newest windfire-security-client wheel synced by the deployment, so version bumps need no change here
        INSTALL_ARGS=$(ls -v $HOME/dist/client-*-py3-none-any.whl 2>/dev/null | tail -1)
        if [ -z "$INSTALL_ARGS" ]; then
            echo -e "${RED}Error: no client-*.whl found in $HOME/dist${RESET}"
            return 1
        fi
        PIP_CMD="pip3 install $INSTALL_ARGS"
    else
        PIP_CMD="pip3 install -e $INSTALL_ARGS"
    fi
    echo "Install custom module from $INSTALL_ARGS"
    $PIP_CMD
}

# ===== EXECUTION =====
main $1