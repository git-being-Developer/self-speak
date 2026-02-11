"""
Test script for Selfspeak API authentication and endpoints
This helps you test the backend without needing the frontend
"""

import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# ANSI color codes for pretty printing
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def test_health_check():
    """Test basic health check endpoint"""
    print_header("Test 1: Health Check (No Auth Required)")

    try:
        response = requests.get(f"{API_BASE_URL}/")

        if response.status_code == 200:
            print_success("Server is running!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running?")
        print_info("Start server with: cd backend && python main.py")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_without_auth():
    """Test endpoint without authentication (should fail)"""
    print_header("Test 2: Access Protected Endpoint Without Auth")

    try:
        response = requests.get(f"{API_BASE_URL}/journal/today")

        if response.status_code == 401:
            print_success("Correctly rejected! (401 Unauthorized)")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print_warning(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def get_test_token():
    """
    Get a test JWT token.

    IMPORTANT: In production, this token comes from Supabase after Google OAuth.
    For testing, you need to provide a REAL token from your Supabase instance.
    """
    print_header("Getting JWT Token")

    print_warning("You need a REAL JWT token from Supabase to continue.")
    print_info("\nHow to get a token:\n")
    print("Option 1: Via Frontend Login")
    print("  1. Start frontend: python -m http.server 3000")
    print("  2. Go to http://localhost:3000/login.html")
    print("  3. Login with Google")
    print("  4. Open browser console (F12)")
    print("  5. Type: localStorage.getItem('sb-access-token')")
    print("  6. Copy the token\n")

    print("Option 2: Via Supabase Dashboard")
    print("  1. Go to Supabase Dashboard → Authentication → Users")
    print("  2. Click on a user")
    print("  3. Copy the JWT token\n")

    print("Option 3: Manual Sign In (Temporary)")
    print("  1. Use the helper function below")
    print("  2. Enter your Supabase credentials\n")

    token = input(f"{Colors.YELLOW}Enter JWT token (or press Enter to skip): {Colors.END}").strip()

    if token:
        print_success("Token received!")
        return token
    else:
        print_warning("No token provided. Skipping authenticated tests.")
        return None


def test_with_auth(token):
    """Test endpoints with authentication"""
    if not token:
        print_warning("No token available. Skipping authenticated tests.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Test 1: Get Today's Journal
    print_header("Test 3: Get Today's Journal (With Auth)")
    try:
        response = requests.get(f"{API_BASE_URL}/journal/today", headers=headers)

        if response.status_code == 200:
            print_success("Successfully retrieved today's data!")
            data = response.json()
            print(f"\nResponse:\n{json.dumps(data, indent=2)}")

            # Parse results
            if data.get('journal_entry'):
                print_success("Journal entry found")
            else:
                print_info("No journal entry for today yet")

            if data.get('analysis'):
                print_success("Analysis found")
            else:
                print_info("No analysis for today yet")

            usage = data.get('usage', {})
            print_info(f"Weekly usage: {usage.get('analyses_used', 0)}/{usage.get('weekly_limit', 2)}")

        elif response.status_code == 401:
            print_error("Authentication failed. Token might be invalid or expired.")
            print(f"Response: {response.json()}")
            return False
        else:
            print_error(f"Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

    # Test 2: Save Journal Entry
    print_header("Test 4: Save Journal Entry")
    journal_content = f"Test journal entry at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. I'm feeling grateful and focused. Working on building something meaningful."

    try:
        response = requests.post(
            f"{API_BASE_URL}/journal/save",
            headers=headers,
            json={"content": journal_content}
        )

        if response.status_code == 200:
            print_success("Journal saved successfully!")
            print(f"\nResponse:\n{json.dumps(response.json(), indent=2)}")
        else:
            print_error(f"Save failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

    # Test 3: Analyze Journal
    print_header("Test 5: Analyze Journal")

    try:
        response = requests.post(
            f"{API_BASE_URL}/journal/analyze",
            headers=headers
        )

        if response.status_code == 200:
            print_success("Analysis completed successfully!")
            data = response.json()
            print(f"\nAnalysis Results:\n{json.dumps(data, indent=2)}")

            print(f"\n{Colors.BOLD}Mental Shape Scores:{Colors.END}")
            print(f"  Confidence: {data.get('confidence_score')}/100")
            print(f"  Abundance: {data.get('abundance_score')}/100")
            print(f"  Clarity: {data.get('clarity_score')}/100")
            print(f"  Gratitude: {data.get('gratitude_score')}/100")
            print(f"  Resistance: {data.get('resistance_score')}/100")

            print(f"\n{Colors.BOLD}Insights:{Colors.END}")
            print(f"  Dominant Emotion: {data.get('dominant_emotion')}")
            print(f"  Overall Tone: {data.get('overall_tone')}")
            print(f"  Goal Present: {data.get('goal_present')}")
            print(f"  Self-Doubt Present: {data.get('self_doubt_present')}")

        elif response.status_code == 403:
            print_warning("Weekly limit reached!")
            print(f"Response: {response.json()}")
        else:
            print_error(f"Analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

    return True


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{'*' * 60}")
    print("Selfspeak API Testing Suite")
    print(f"{'*' * 60}{Colors.END}\n")

    print_info(f"Testing API at: {API_BASE_URL}")
    print_info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run tests
    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health_check()))

    if not results[0][1]:
        print_error("\n❌ Server is not running. Please start it first.")
        print_info("Command: cd backend && python main.py")
        return

    # Test 2: No auth
    results.append(("No Auth Test", test_without_auth()))

    # Test 3-5: With auth
    token = get_test_token()
    if token:
        auth_result = test_with_auth(token)
        results.append(("Authenticated Tests", auth_result))

    # Summary
    print_header("Test Summary")
    for test_name, passed in results:
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print("1. If you don't have a token, set up the frontend to test Google login")
    print("2. Check the TESTING_GUIDE.md for detailed instructions")
    print("3. View API documentation at http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    main()
