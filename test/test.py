import os
import subprocess
import requests # pyright: ignore[reportMissingModuleSource]
from colorama import Fore, Style, init # pyright: ignore[reportMissingModuleSource]
from typing import Optional
from datetime import date
# Import the AuthClient instance from the client package
from client.authClient import authClient

token = None
colorama_init = init(autoreset=True)
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
service = os.getenv("SERVICE")
verify_ssl = os.getenv("VERIFY_SSL_CERTS").lower() == "true"
environment = os.getenv("ENVIRONMENT")
calendarServerPort = "8443"
# If PORT is set in the environment, validate and use it; otherwise keep default
port_env = os.getenv("PORT")
if port_env:
    try:
        # ensure it's an integer-like value, store as string for URL formatting
        calendarServerPort = str(int(port_env))
    except ValueError:
        print(Style.BRIGHT + Fore.YELLOW + f"Invalid PORT value '{port_env}', using default port {calendarServerPort}")

httpsCalendarServerUrl = os.getenv("HTTPS_CALENDAR_SERVER_URL", f"https://localhost:{calendarServerPort}")
if environment == "dev":
    httpsCalendarServerUrl = os.getenv("HTTPS_CALENDAR_SERVER_URL", f"https://localhost:{calendarServerPort}")
elif environment == "test":
    httpsCalendarServerUrl = os.getenv("HTTPS_CALENDAR_SERVER_URL", f"https://localhost:{calendarServerPort}")
elif environment == "prod":
    httpsCalendarServerUrl = os.getenv("HTTPS_CALENDAR_SERVER_URL", f"https://raspberry02:{calendarServerPort}")
print(Style.BRIGHT + f"Environment is {environment}")
print(Style.BRIGHT + f"     --> AuthClient module will use {authClient.url_base} to authenticate")
print(Style.BRIGHT + f"     --> Windfire Calendar server url {httpsCalendarServerUrl}")

def test_health_endpoint():
    apiEndpoint = "/v1/monitor/health"
    print(Style.BRIGHT + Fore.BLUE + "---> Function test_health_endpoint() called <---")
    print(Style.BRIGHT + Fore.BLUE + f"Calling {apiEndpoint} endpoint on Windfire Calendar Server ...")
    print(Style.BRIGHT + Fore.BLUE + "No Authentication required")
    url = httpsCalendarServerUrl + apiEndpoint
    http_headers = {"Content-Type": "application/json"}
    print(Style.BRIGHT + Fore.BLUE + f"Calling {url} ...")
    try:
        response = requests.get(url, headers=http_headers, timeout=5, verify=verify_ssl)
        print(f"GET {url} -> Status Code: {response.status_code}")
        try:
            print("Response JSON:", response.json())
        except ValueError:
            print("Response Body:", response.text)

        if response.ok:
            print(Style.NORMAL + Fore.GREEN + "Health endpoint OK")
        else:
            print(Style.BRIGHT + Fore.LIGHTRED_EX + "Health endpoint returned error")
    except requests.RequestException as e:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + f"Request error: {e}")

def authenticate():
    print(Style.BRIGHT + Fore.BLUE + "---> Function authenticate() called <---")
    print(Style.BRIGHT + Fore.BLUE + "Authenticating with Windfire Security service to obtain access token...")
    print(Style.BRIGHT + Fore.BLUE + "Delegating authentication to authClient module ...")
    print(Style.BRIGHT + Fore.BLUE + "Calling client.authClient.authenticate() ...")
    access_token = authClient.authenticate(username, password, service)
    #print(f"Access Token (from AuthClient): {access_token}\n")
    if not access_token is None:
        print(Style.NORMAL + Fore.GREEN + "Authentication successful")
    else:
        access_token = None
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "Authentication failed")
    return access_token

def test_count_events_by_year() -> Optional[dict]:
    """
    Test the count events by year endpoint
    """
    apiEndpoint = "/v1/calendar/events/count/year"
    print(Style.BRIGHT + Fore.BLUE + "---> Function test_count_events_by_year() called <---")
    print(Style.BRIGHT + Fore.BLUE + f"Calling {apiEndpoint} endpoint on Windfire Calendar Server ...")
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = httpsCalendarServerUrl + apiEndpoint
        http_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        event_title = "Palestra"
        year = 2025
        data = {
            "event_title": event_title,
            "year": year
        }
        print(Style.BRIGHT + Fore.BLUE + f"Calling {url} ...")
        try:
            response = requests.post(url, json=data, headers=http_headers, verify=verify_ssl)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Count events by year successful:")
            print(f"   Event Title: {result['event_title']}")
            print(f"   Count: {result['count']}")
            print(f"   Date Range: {result['start_date']} to {result['end_date']}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Count events by year failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response text: {e.response.text}")
            return None
        
    else:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No valid authentication token available, skipping POST request")

def test_count_events_to_today() -> Optional[dict]:
    """
    Test the count events to today endpoint
    """
    apiEndpoint = "/v1/calendar/events/count/today"
    print(Style.BRIGHT + Fore.BLUE + "---> Function test_count_events_to_today() called <---")
    print(Style.BRIGHT + Fore.BLUE + f"Calling {apiEndpoint} endpoint on Windfire Calendar Server ...")
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = httpsCalendarServerUrl + apiEndpoint
        http_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        event_title = "Palestra"
        current_year = date.today().year
        # Test count events to today
        start_date = date(current_year, 6, 1)
        data = {
            "event_title": event_title,
            "start_date": start_date.isoformat()
        }
        print(Style.BRIGHT + Fore.BLUE + f"Calling {url} ...")
        try:
            response = requests.post(url, json=data, headers=http_headers, verify=verify_ssl)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Count events to today successful:")
            print(f"   Event Title: {result['event_title']}")
            print(f"   Count: {result['count']}")
            print(f"   Date Range: {result['start_date']} to {result['end_date']}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Count events to today failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response text: {e.response.text}")
            return None
    else:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No valid authentication token available, skipping POST request")

def test_count_events_by_range() -> Optional[dict]:
    """
    Test the count events by range endpoint
    """
    apiEndpoint = "/v1/calendar/events/count/range"
    print(Style.BRIGHT + Fore.BLUE + "---> Function test_count_events_by_range() called <---")
    print(Style.BRIGHT + Fore.BLUE + f"Calling {apiEndpoint} endpoint on Windfire Calendar Server ...")
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = httpsCalendarServerUrl + apiEndpoint
        http_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        event_title = "Palestra"
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        data = {
            "event_title": event_title,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        print(Style.BRIGHT + Fore.BLUE + f"Calling {url} ...")
        try:
            response = requests.post(url, json=data, headers=http_headers, verify=verify_ssl)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Count events by range successful:")
            print(f"   Event Title: {result['event_title']}")
            print(f"   Count: {result['count']}")
            print(f"   Date Range: {result['start_date']} to {result['end_date']}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Count events by range failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response text: {e.response.text}")
            return None
        
    else:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No valid authentication token available, skipping POST request")

def test_get_upcoming_events() -> Optional[dict]:
    """
    Test the get upcoming events endpoint
    """
    apiEndpoint = "/v1/calendar/events/upcoming"
    print(Style.BRIGHT + Fore.BLUE + "---> Function test_get_upcoming_events() called <---")
    print(Style.BRIGHT + Fore.BLUE + f"Calling {apiEndpoint} endpoint on Windfire Calendar Server ...")
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = httpsCalendarServerUrl + apiEndpoint
        http_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        print(Style.BRIGHT + Fore.BLUE + f"Calling {url} ...")
        try:
            response = requests.get(url, headers=http_headers, verify=verify_ssl)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Get upcoming events successful:")
            print(f"   Total events: {result['count']}")
            
            if result['events']:
                print("   Events:")
                for i, event in enumerate(result['events'], 1):  # Show first 3 events
                    print(f"     {i}. {event['summary']} (ID: {event['id'][:10]}...)")
            else:
                print("   No upcoming events found")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Get upcoming events failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response text: {e.response.text}")
            return None
    else:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No valid authentication token available, skipping GET request")
        
# NOT USED keeping for reference    
def __test_get_upcoming_events():
    """
    Test the upcoming events endpoint
    """
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with GET request...")
        url = httpsCalendarServerUrl + "/v1/calendar/events/upcoming"
        http_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        headers = ["-H", f"Authorization: Bearer {token}"]
        print(Style.BRIGHT + Fore.BLUE + f"Calling {url} ...")
        get_response = subprocess.run(
            ["curl", "-X", "GET", url] + http_headers,
            capture_output=True,
            text=True
        )

        print("GET Status Code:", get_response.returncode)
        print("GET Response Body:", get_response.stdout)
    else:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No valid authentication token available, skipping GET request")
            
def main():
    global token
    print(Style.BRIGHT + Fore.CYAN +"######################################################")
    print(Style.BRIGHT + Fore.CYAN +"##### Testing FastAPI Calendar Service Endpoints #####")
    print(Style.BRIGHT + Fore.CYAN +"######################################################")
    print("")

    print(Style.BRIGHT + Fore.BLUE + "===> Testing /v1/monitor/health endpoint <===")
    test_health_endpoint()
    print("")

    token = authenticate()
    print("")
    
    print(Style.BRIGHT + Fore.BLUE + "===> Testing /v1/calendar/events/count/year endpoint <===")
    test_count_events_by_year()
    print("")

    print(Style.BRIGHT + Fore.BLUE + "===> Testing /v1/calendar/events/count/today endpoint <===")
    test_count_events_to_today()
    print("")
    
    print(Style.BRIGHT + Fore.BLUE + "===> Testing /v1/calendar/events/count/range endpoint <===")
    test_count_events_by_range()
    print("")
    
    print(Style.BRIGHT + Fore.BLUE + "===> Testing /v1/calendar/events/upcoming endpoint <===")
    test_get_upcoming_events()
    print("")
    
if __name__ == "__main__":
    main()