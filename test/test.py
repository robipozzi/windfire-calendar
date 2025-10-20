import subprocess
import requests
from colorama import Fore, Style, init
from typing import Optional
from datetime import date
import os

token = None
colorama_init = init(autoreset=True)

def authenticate():
    print(Style.BRIGHT + Fore.BLUE + "Authenticating to obtain access token...")
    post_url = "http://localhost:8000/auth"
    post_headers = {"Content-Type": "application/json"}
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    try:
        response = requests.post(post_url,
                     json={'username': username, 'password': password},
                     headers=post_headers)
        access_token = response.json()['access_token']
        print(f"Return Code: {response.status_code}\n")
        # ****** START - Uncomment for debug purposes in development ONLY ********
        #print(f"Response Body: {response.__dict__}\n")
        #print(f"Access Token: {access_token}\n")
        # ****** START - Uncomment for debug purposes in development ONLY ********
        if not access_token is None:
            print(Style.NORMAL + Fore.GREEN + "Authentication successful")
    except Exception:
        access_token = None
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "Authentication failed")
        print(f"Response: {response.__dict__} \n")
        print("POST Status Code:", response.status_code)
        
    return access_token

def test_count_events_by_year() -> Optional[dict]:
    """
    Test the count events by year endpoint
    """
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = "http://localhost:8000/calendar/events/count/year"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        event_title = "Palestra"
        year = 2025
        data = {
            "event_title": event_title,
            "year": year
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
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
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No authentication token available, skipping POST request")

def test_count_events_to_today() -> Optional[dict]:
    """
    Test the count events to today endpoint
    """
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = "http://localhost:8000/calendar/events/count/today"
        headers = {
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

        try:
            response = requests.post(url, json=data, headers=headers)
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
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No authentication token available, skipping POST request")

def test_count_events_by_range() -> Optional[dict]:
    """
    Test the count events by range endpoint
    """
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = "http://localhost:8000/calendar/events/count/range"
        headers = {
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

        try:
            response = requests.post(url, json=data, headers=headers)
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
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No authentication token available, skipping POST request")

def test_get_upcoming_events() -> Optional[dict]:
    """
    Test the get upcoming events endpoint
    """
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with POST request...")
        url = "http://localhost:8000/calendar/events/upcoming"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
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
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No authentication token available, skipping GET request")
        
# NOT USED keeping for reference    
def __test_get_upcoming_events():
    """
    Test the upcoming events endpoint
    """
    if token:
        print(Style.NORMAL + Fore.GREEN + "Authentication token is available, proceeding with GET request...")
        url = "http://localhost:8000/calendar/events/upcoming"
        headers = ["-H", f"Authorization: Bearer {token}"]

        get_response = subprocess.run(
            ["curl", "-X", "GET", url] + headers,
            capture_output=True,
            text=True
        )

        print("GET Status Code:", get_response.returncode)
        print("GET Response Body:", get_response.stdout)
    else:
        print(Style.BRIGHT + Fore.LIGHTRED_EX + "No authentication token available, skipping GET request")
            
def main():
    global token
    print(Style.BRIGHT + Fore.CYAN +"######################################################")
    print(Style.BRIGHT + Fore.CYAN +"##### Testing FastAPI Calendar Service Endpoints #####")
    print(Style.BRIGHT + Fore.CYAN +"######################################################")
    print("")
    token = authenticate()
    print("")
    
    print(Style.BRIGHT + Fore.BLUE + "===> Testing /calendar/events/count/year endpoint <===")
    test_count_events_by_year()
    print("")

    print(Style.BRIGHT + Fore.BLUE + "===> Testing /calendar/events/count/today endpoint <===")
    test_count_events_to_today()
    print("")

    print(Style.BRIGHT + Fore.BLUE + "===> Testing /calendar/events/count/range endpoint <===")
    test_count_events_by_range()
    print("")

    print(Style.BRIGHT + Fore.BLUE + "===> Testing /calendar/events/upcoming endpoint <===")
    test_get_upcoming_events()
    print("")
    
if __name__ == "__main__":
    main()