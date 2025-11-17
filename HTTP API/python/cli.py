#!/usr/bin/env python3
"""
PTZOptics HTTP-CGI API CLI Example

This example demonstrates how to build a command-line interface for controlling
a PTZOptics camera using HTTP-CGI commands.

Usage:
    python cli.py

Requirements:
    - Python 3.6+
    - requests library (pip install requests)
    - PTZOptics camera on network
    - Camera IP address and credentials configured in the script
"""

import requests
import signal
import sys
from urllib.parse import urljoin
from requests.auth import HTTPDigestAuth

# Configuration Constants
CAMERA_HOST = "192.168.1.100"  # Change to your camera's IP address or hostname
CAMERA_USERNAME = "admin"
CAMERA_PASSWORD = "admin"

class PTZOpticsHTTPController:
    def __init__(self, host="ptzoptics.local", username="admin", password="admin"):
        self.host = host
        self.base_url = f"http://{host}"
        self.username = username
        self.password = password
        self.running = False
        self.session = requests.Session()

        # Set up digest authentication if credentials provided
        if username and password:
            self.session.auth = HTTPDigestAuth(username, password)
            
    def test_connection(self):
        """Test connection to the PTZ camera"""
        try:
            # Test with a simple ptzctrl stop command
            test_url = urljoin(self.base_url, "/cgi-bin/ptzctrl.cgi?ptzcmd&ptzstop&0&0")
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                print(f"✓ Connected to PTZ camera at {self.host}")
                return True
            elif response.status_code == 401:
                print(f"❌ Authentication failed - check username/password")
                return False
            else:
                print(f"❌ Connection failed - HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def send_command(self, command):
        """Send an HTTP-CGI command to the camera"""
        try:
            # Handle both string URL and dictionary command formats
            if isinstance(command, str):
                # Simple string URL from cgi_commands dictionary
                url = urljoin(self.base_url, command)
                print(f"   URL: {command}")
                response = self.session.get(url, timeout=10)
            else:
                # Dictionary format with url, method, params
                url = urljoin(self.base_url, command["url"])
                print(f"   URL: {command['url']}")

                if command["method"].upper() == "POST":
                    response = self.session.post(url, data=command["params"], timeout=10)
                else:
                    response = self.session.get(url, params=command["params"] if command["params"] else None, timeout=10)

            # Check response
            if response.status_code == 200:
                print(f"   ✅ Command successful (HTTP {response.status_code})")
                if response.text.strip():
                    # Show first line of response if available
                    first_line = response.text.strip().split('\n')[0][:100]
                    print(f"   Response: {first_line}...")
                return True
            else:
                print(f"   ❌ Command failed (HTTP {response.status_code})")
                if response.text:
                    print(f"   Error: {response.text[:200]}...")
                return False

        except requests.RequestException as e:
            print(f"   ❌ Request error: {e}")
            return False
    
    def prompt(self):
        """Prompt user for command input and execute the command"""
        try:
            user_choice = input("What command would you like to execute? [move, recall]: ").lower().strip()
            if user_choice == "move":
                user_input = input(f"Which direction and speed? [up, down, left, right, leftup, rightup, leftdown, rightdown, stop] [pan: 1-24, tilt: 1-20] (ex. left 5 or stop): ")

                # Handle stop command separately (no speed needed)
                if user_input.strip().lower() == "stop":
                    command_url = "/cgi-bin/ptzctrl.cgi?ptzcmd&ptzstop&0&0"
                else:
                    direction, speed = user_input.split(' ')
                    speed_value = int(speed)
                    # Build command URL with user's speed input
                    command_url = f"/cgi-bin/ptzctrl.cgi?ptzcmd&{direction}&{speed_value}&{speed_value}"

                self.send_command(command_url)
            elif user_choice == "recall":
                preset_number_str = input("Which preset number?: ")
                preset_num = int(preset_number_str)
                # Build command URL with user's preset number
                command_url = f"/cgi-bin/ptzctrl.cgi?ptzcmd&poscall&{preset_num}"
                self.send_command(command_url)
            else:
                print("Please choose from the command list.\n\n")
        except Exception as e:
            print(e)
            
    def start(self):
        """Start the controller"""
        if self.test_connection():
            self.running = True
            return True
        return False
    
    def stop(self):
        """Stop the controller"""
        self.running = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Stopping PTZ Controller...")
    controller.stop()
    sys.exit(0)

def main():
    global controller
    
    # Create controller instance
    controller = PTZOpticsHTTPController(
        host=CAMERA_HOST,
        username=CAMERA_USERNAME,
        password=CAMERA_PASSWORD
    )

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    print("PTZOptics HTTP-CGI Controller CLI")
    print("=" * 40)
    print(f"Connecting to camera at: {controller.host}")
    print("Press Ctrl+C to stop\n")
    
    # Start the controller
    if controller.start():
        try:
            # Keep the program running
            while True:
                controller.prompt()
        except KeyboardInterrupt:
            signal_handler(None, None)
    else:
        print("Failed to start controller")
        sys.exit(1)

if __name__ == "__main__":
    main()
