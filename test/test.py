import subprocess
import json

token = None

def authenticate():
    post_url = "http://localhost:8000/auth/token"
    post_headers = ["-H", "Content-Type: application/json"]
    post_data = ["-d", '{"username": "admin", "password": "secure_password_123"}']

    post_response = subprocess.run(
        ["curl", "-X", "POST", post_url] + post_headers + post_data,
        capture_output=True,
        text=True
    )

    try:
        response_json = json.loads(post_response.stdout)
        access_token = response_json.get("access_token")
        print("POST Status Code:", post_response.returncode)
        print("POST Response Body:", post_response.stdout)
        print("Access Token:", access_token)
    except Exception:
        access_token = None

    return access_token

def test_get_upcoming_events():
    if token:
        print("Authentication successful.")
        get_url = "http://localhost:8000/calendar/events/upcoming"
        get_headers = ["-H", f"Authorization: Bearer {token}"]

        get_response = subprocess.run(
            ["curl", "-X", "GET", get_url] + get_headers,
            capture_output=True,
            text=True
        )

        print("GET Status Code:", get_response.returncode)
        print("GET Response Body:", get_response.stdout)
    else:
        print("Authentication failed.")
            
def main():
    global token
    print("Testing FastAPI Calendar Service Endpoints")
    token = authenticate()
    print("Testing /calendar/events/upcoming endpoint")
    test_get_upcoming_events()
    
if __name__ == "__main__":
    main()