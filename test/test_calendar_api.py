import requests
from datetime import date
from typing import Optional

class CalendarAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def authenticate(self, username: str = "admin", password: str = "secure_password_123") -> bool:
        """
        Authenticate with the API and store the JWT token
        """
        auth_url = f"{self.base_url}/auth/token"
        auth_data = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            print(f"✅ Authentication successful. Token: {self.token[:20]}...")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def test_health_check(self):
        """
        Test the health check endpoint
        """
        print("\n🏥 Testing health check endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Health check passed: {result}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check failed: {e}")
            return None
    
    def count_events_by_year(self, event_title: str, year: int) -> Optional[dict]:
        """
        Test the count events by year endpoint
        """
        print(f"\n📅 Testing count events by year: '{event_title}' for year {year}...")
        
        if not self.token:
            print("❌ Not authenticated. Please call authenticate() first.")
            return None
        
        url = f"{self.base_url}/calendar/events/count/year"
        data = {
            "event_title": event_title,
            "year": year
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
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
    
    def count_events_to_today(self, event_title: str, start_date: date) -> Optional[dict]:
        """
        Test the count events to today endpoint
        """
        print(f"\n📅 Testing count events to today: '{event_title}' from {start_date}...")
        
        if not self.token:
            print("❌ Not authenticated. Please call authenticate() first.")
            return None
        
        url = f"{self.base_url}/calendar/events/count/today"
        data = {
            "event_title": event_title,
            "start_date": start_date.isoformat()
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
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
    
    def count_events_by_range(self, event_title: str, start_date: date, end_date: date) -> Optional[dict]:
        """
        Test the count events by range endpoint
        """
        print(f"\n📅 Testing count events by range: '{event_title}' from {start_date} to {end_date}...")
        
        if not self.token:
            print("❌ Not authenticated. Please call authenticate() first.")
            return None
        
        url = f"{self.base_url}/calendar/events/count/range"
        data = {
            "event_title": event_title,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
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
    
    def get_upcoming_events(self) -> Optional[dict]:
        """
        Test the get upcoming events endpoint
        """
        print(f"\n📅 Testing get upcoming events...")
        
        if not self.token:
            print("❌ Not authenticated. Please call authenticate() first.")
            return None
        
        url = f"{self.base_url}/calendar/events/upcoming"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Get upcoming events successful:")
            print(f"   Total events: {result['count']}")
            
            if result['events']:
                print("   Events:")
                for i, event in enumerate(result['events'][:3], 1):  # Show first 3 events
                    print(f"     {i}. {event['summary']} (ID: {event['id'][:10]}...)")
                if len(result['events']) > 3:
                    print(f"     ... and {len(result['events']) - 3} more events")
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


def main():
    """
    Main function to demonstrate API testing
    """
    print("🚀 Starting Calendar API Tests")
    print("=" * 50)
    
    # Initialize tester
    tester = CalendarAPITester()
    
    # Test health check
    tester.test_health_check()
    
    # Authenticate
    if not tester.authenticate():
        print("❌ Cannot proceed without authentication")
        return
    
    # Test count events by year (main focus as requested)
    current_year = date.today().year
    tester.count_events_by_year("Meeting", current_year)
    tester.count_events_by_year("Appointment", 2024)
    
    # Test other endpoints
    from datetime import datetime, timedelta
    
    # Test count events to today
    start_date = date(current_year, 1, 1)
    tester.count_events_to_today("Meeting", start_date)
    
    # Test count events by range
    end_date = date.today()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    tester.count_events_by_range("Meeting", start_date, end_date)
    
    # Test get upcoming events
    tester.get_upcoming_events()
    
    print("\n" + "=" * 50)
    print("🏁 API Tests Completed")


# Example usage functions for specific testing scenarios
def test_year_endpoint_only():
    """
    Test only the year endpoint as requested
    """
    print("🎯 Testing Year Endpoint Only")
    print("=" * 30)
    
    tester = CalendarAPITester()
    
    if tester.authenticate():
        # Test current year
        tester.count_events_by_year("Meeting", 2025)
        # Test previous year
        tester.count_events_by_year("Appointment", 2024)
        # Test specific event
        tester.count_events_by_year("Doctor", 2025)


def test_with_custom_server():
    """
    Test with custom server configuration
    """
    # Example for different server URL
    custom_tester = CalendarAPITester(base_url="http://your-server.com:8000")
    
    if custom_tester.authenticate("your_username", "your_password"):
        custom_tester.count_events_by_year("Custom Event", 2025)


if __name__ == "__main__":
    # Run the main test suite
    main()
    
    # Uncomment below to run only year endpoint tests
    # test_year_endpoint_only()
