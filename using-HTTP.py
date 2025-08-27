#!/usr/bin/env python3
"""
PTZOptics HTTP-CGI API Controller Example

This example demonstrates how to control PTZOptics cameras using HTTP-CGI commands.
Commands are sent automatically every 5 seconds in a cycle.

Usage:
    python using-HTTP.py

Requirements:
    - Python 3.6+
    - requests library (pip install requests)
    - PTZOptics camera on network
    - Camera IP address or hostname configured below
"""

import requests
import time
import threading
import signal
import sys
from urllib.parse import urljoin
from requests.auth import HTTPDigestAuth

# Configuration Constants
CAMERA_IP = "192.168.15.164"
CAMERA_USERNAME = "admin"
CAMERA_PASSWORD = "admin1"

class PTZOpticsHTTPController:
    def __init__(self, host="ptzoptics.local", username="admin", password="admin"):
        self.host = host
        self.base_url = f"http://{host}"
        self.username = username
        self.password = password
        self.running = False
        self.command_index = 0
        self.timer_thread = None
        self.session = requests.Session()
        
        # Set up digest authentication if credentials provided
        if username and password:
            self.session.auth = HTTPDigestAuth(username, password)
        
        # HTTP-CGI Command List - Add or modify commands here
        self.cgi_commands = [
            # Pan Left (medium speed: pan=12, tilt=10)
            {
                "url": "/cgi-bin/ptzctrl.cgi?ptzcmd&left&12&10",
                "params": {},
                "method": "GET"
            },
            
            # Stop Pan/Tilt
            {
                "url": "/cgi-bin/ptzctrl.cgi?ptzcmd&ptzstop&0&0",
                "params": {},
                "method": "GET"
            },
            # Pan Left (medium speed: pan=12, tilt=10)
            {
                "url": "/cgi-bin/ptzctrl.cgi?ptzcmd&right&12&10",
                "params": {},
                "method": "GET"
            },
        ]
        
        # Command descriptions for logging
        self.command_descriptions = [
            "Pan Left (Speed 12/10)",
            "Stop Pan/Tilt"
            "Pan Right (Speed 12/10)",
        ]
    
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
            # Build the full URL
            url = urljoin(self.base_url, command["url"])
            
            # Display the URL being sent
            print(f"   URL: {command['url']}")
            
            # Send the request
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
    
    def send_next_command(self):
        """Send the next command in the cycle"""
        if not self.cgi_commands:
            print("⚠️ No commands in command list")
            return
        
        command = self.cgi_commands[self.command_index]
        description = (self.command_descriptions[self.command_index] 
                      if self.command_index < len(self.command_descriptions) 
                      else f"Command {self.command_index + 1}")
        
        print(f"\n📤 Sending: {description}")
        self.send_command(command)
        
        # Move to next command (cycle through the list)
        self.command_index = (self.command_index + 1) % len(self.cgi_commands)
    
    def command_timer(self):
        """Timer function that sends commands every 5 seconds"""
        while self.running:
            if self.running:  # Double-check we're still running
                self.send_next_command()
            time.sleep(5)  # 5 second interval
    
    def start(self):
        """Start the controller"""
        if self.test_connection():
            self.running = True
            self.timer_thread = threading.Thread(target=self.command_timer, daemon=True)
            self.timer_thread.start()
            print("🕒 Started command timer (5 second intervals)")
            return True
        return False
    
    def stop(self):
        """Stop the controller"""
        self.running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=1)
        print("⏹️ Controller stopped")
    
    def send_single_command(self, index):
        """Send a single command by index"""
        if 0 <= index < len(self.cgi_commands):
            command = self.cgi_commands[index]
            description = (self.command_descriptions[index] 
                          if index < len(self.command_descriptions) 
                          else f"Command {index + 1}")
            
            print(f"\n📤 Manual send: {description}")
            self.send_command(command)
        else:
            print(f"❌ Invalid command index: {index}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Stopping PTZ Controller...")
    controller.stop()
    sys.exit(0)

def main():
    global controller
    
    # Create controller instance
    controller = PTZOpticsHTTPController(
        host=CAMERA_IP,
        username=CAMERA_USERNAME,
        password=CAMERA_PASSWORD
    )
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("PTZOptics HTTP-CGI Controller Example")
    print("=" * 40)
    print(f"Connecting to camera at: {controller.host}")
    print("Commands will be sent every 5 seconds")
    print("Press Ctrl+C to stop\n")
    
    # Start the controller
    if controller.start():
        try:
            # Keep the program running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
    else:
        print("Failed to start controller")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
HOW TO ADD MORE COMMANDS:

1. Add command dictionaries to the 'cgi_commands' list
2. Add corresponding descriptions to 'command_descriptions' list

Example commands from the PTZOptics HTTP-CGI documentation:

Pan/Tilt Commands:
- Pan Right:     {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "right", "12": "", "10": ""}, "method": "GET"}
- Tilt Up:       {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "up", "12": "", "10": ""}, "method": "GET"}
- Tilt Down:     {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "down", "12": "", "10": ""}, "method": "GET"}
- Up-Left:       {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "leftup", "12": "", "10": ""}, "method": "GET"}
- Up-Right:      {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "rightup", "12": "", "10": ""}, "method": "GET"}
- Down-Left:     {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "leftdown", "12": "", "10": ""}, "method": "GET"}
- Down-Right:    {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "rightdown", "12": "", "10": ""}, "method": "GET"}

Zoom Commands:
- Zoom In:       {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "zoomin"}, "method": "GET"}
- Zoom Out:      {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "zoomout"}, "method": "GET"}
- Zoom Stop:     {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "zoomstop", "0": ""}, "method": "GET"}

Focus Commands:
- Focus In:      {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "focusin"}, "method": "GET"}
- Focus Out:     {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "focusout"}, "method": "GET"}
- Focus Stop:    {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "focusstop", "0": ""}, "method": "GET"}

Preset Commands:
- Call Home:     {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "home"}, "method": "GET"}
- Set Preset 1:  {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "posset", "1": ""}, "method": "GET"}
- Call Preset 1: {"url": "/cgi-bin/ptzctrl.cgi", "params": {"ptzcmd": "poscall", "1": ""}, "method": "GET"}

Speed Parameters (for pan/tilt):
- Pan speed: 1 (slowest) to 24 (fastest)
- Tilt speed: 1 (slowest) to 20 (fastest)
- Medium speeds: Pan=12, Tilt=10

Installation:
- Install requests: pip install requests
- Update camera credentials in main() function
- Modify the 5-second interval in command_timer() if needed

Note: Some commands may require POST method with Content-Length header.
See the HTTP-CGI documentation for POST request formatting requirements.
"""
