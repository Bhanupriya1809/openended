import requests
import json
import os

# =========================================================================
# 🚨 IMPORTANT: CHANGE ONLY THIS VARIABLE 🚨
# =========================================================================
# 1. Paste the FULL URL of your Jenkins job here (e.g., http://my-jenkins.com:8080/job/Test-Job/)
JOB_URL = os.getenv("JENKINS_URL", "http://localhost:8080/job/SmartHealthReminder-CICD/configure") 
# =========================================================================

def get_build_count_unauthenticated(url):
    """
    Fetches the total number of builds for a specific Jenkins job
    using the unauthenticated Remote API endpoint.
    """
    # Construct the API URL by appending /api/json
    api_url = f"{url.rstrip('/')}/api/json"
    
    print(f"Attempting to connect to: {api_url}")
    
    try:
        # Make the request without providing any authentication headers
        response = requests.get(api_url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract the next build number
            next_build_number = data.get("nextBuildNumber", 1)
            
            # The total count is nextBuildNumber minus 1
            total_builds = max(0, next_build_number - 1)
            
            print(f"--- Jenkins Build Tracker Report ---")
            print(f"✅ SUCCESS: Access Granted (Unauthenticated)")
            print(f"Job Name: {data.get('name', 'N/A')}")
            print(f"Total Completed Builds: {total_builds}")
            print("------------------------------------")
            return total_builds
        
        elif response.status_code in [401, 403]:
            # This is the expected failure if Anonymous Read Access is disabled
            print("❌ FAILURE: Access Denied (Status 401/403)")
            print("Your Jenkins job requires authentication. This script will not work without an API token.")
            print("Request your instructor or admin for read permissions or the required token.")
            
        else:
            # Handle other HTTP errors (e.g., 404 Not Found, 500 Server Error)
            print(f"❌ FAILURE: Received HTTP Status Code {response.status_code}")
            print("Check the JOB_URL to ensure it is correct.")

    except requests.exceptions.RequestException as e:
        print(f"❌ FAILURE: A connection or network error occurred: {e}")
        print("Ensure Jenkins is running and the URL is reachable.")

    return None

if __name__ == "__main__":
    get_build_count_unauthenticated(JOB_URL)