##### Terminal Colors - START
red=$'\e[1;31m'
grn=$'\e[1;32m'
yel=$'\e[1;33m'
blu=$'\e[1;34m'
mag=$'\e[1;35m'
cyn=$'\e[1;36m'
end=$'\e[0m'
coffee=$'\xE2\x98\x95'
coffee3="${coffee} ${coffee} ${coffee}"
##### Terminal Colors - END

###### Variable section - START
PYTORCH_VIRTUAL_ENV=google-calendar
ENVIRONMENT=
KEYCLOAK_URL="http://raspberry01:8080"
KEYCLOAK_REALM="windfire"
KEYCLOAK_CLIENT_ID="windfire-calendar"
KEYCLOAK_CLIENT_SECRET=
###### Variable section - END

###### Function section - START
printSelectEnvironment()
{
    ENVIRONMENT_SELECTION=$1
    if [[ -n "${ENVIRONMENT_SELECTION}" ]]; then
        echo 
    else
        echo ${blu}Select environment : ${end}
        echo "${blu}1. Development${end}"
        echo "${blu}2. Test${end}"
        echo "${blu}3. Production${end}"
        read ENVIRONMENT_SELECTION
    fi
	setEnvironment
}

setEnvironment()
{
	case $ENVIRONMENT_SELECTION in
		1)  ENVIRONMENT=dev
			;;
		2)  ENVIRONMENT=test
			;;
        3)  ENVIRONMENT=prod
            ;;
		*) 	printf "\n${red}No valid option selected${end}\n"
			printSelectEnvironment
			;;
	esac
}
###### Function section - END