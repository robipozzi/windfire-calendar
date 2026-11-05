source ../common.sh

# ***** Main function
main()
{
    echo "Installing Python prerequisites..."
    installPythonModules
    echo "Python prerequisites installation complete."
    echo ""
    echo "Installing custom Python prerequisites..."
    installCustomPythonModules $1
    echo "Custom Python prerequisites installation complete."
}

# ***** Install Python prerequisites for Google Calendar API
installPythonModules()
{
    pip3 install -r requirements.txt
}

# ***** Install custom Windfire Security Python modules
installCustomPythonModules()
{
    ENVIRONMENT_OPTION=$1
    PIP_CMD="pip3 install"
    INSTALL_ARGS=$HOME/dev/windfire-security-client
    if [ -n "$ENVIRONMENT_OPTION" ] && [ "$ENVIRONMENT_OPTION" -eq 3 ]; then
        INSTALL_ARGS=$HOME/dist/client-1.0.0-py3-none-any.whl
        PIP_CMD="pip3 install $INSTALL_ARGS"
    else
        PIP_CMD="pip3 install -e $INSTALL_ARGS"
    fi
    echo "Install custom module from $INSTALL_ARGS"
    $PIP_CMD
}

# ***** MAIN EXECUTION
main $1