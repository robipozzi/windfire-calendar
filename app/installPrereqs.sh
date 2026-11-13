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
    INSTALL_ARGS=$HOME/dev/windfire-security-client
    if [ -n "$ENVIRONMENT_OPTION" ] && [ "$ENVIRONMENT_OPTION" -eq 3 ]; then
        # windfire-security-client wheel synced by the deployment to $HOME/dist: exactly one must be there
        # (this script is sourced, so no shopt nullglob: an unmatched glob stays as the literal pattern)
        local wheels=("$HOME"/dist/windfire_security_client-*.whl)
        if [ ! -e "${wheels[0]}" ]; then
            echo -e "${RED}Error: no windfire_security_client-*.whl found in $HOME/dist${RESET}"
            return 1
        fi
        if [ ${#wheels[@]} -gt 1 ]; then
            echo -e "${RED}Error: more than one windfire_security_client-*.whl found in $HOME/dist, keep exactly one:${RESET}"
            printf '  %s\n' "${wheels[@]##*/}"
            return 1
        fi
        INSTALL_ARGS=${wheels[0]}
        # The package was distributed as "client" up to 1.0.0: remove it so it does not stay in the venv next to the new one
        echo "Uninstall old client distribution, if present"
        pip3 uninstall -y client || return 1
        echo "Install custom module from $INSTALL_ARGS"
        pip3 install "$INSTALL_ARGS"
    else
        echo "Install custom module from $INSTALL_ARGS"
        pip3 install -e "$INSTALL_ARGS"
    fi
}

# ===== EXECUTION =====
main $1