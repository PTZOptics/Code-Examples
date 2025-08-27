#!/usr/bin/env python3
"""
PTZOptics VISCA over IP Controller Example

This example demonstrates how to control PTZOptics cameras using VISCA commands
over IP. Commands are sent automatically every 5 seconds in a cycle.

Usage:
    python ptz_visca_example.py

Requirements:
    - Python 3.6+
    - PTZOptics camera on network
    - Camera IP address or hostname configured below
"""

import socket
import time
import threading
import signal
import sys

# Configuration
CAMERA_HOST = "192.168.1.100"  # Replace with your camera's IP address
CAMERA_PORT = 5678

class PTZOpticsVISCAController:
    def __init__(self, host="ptzoptics.local", port=5678):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.command_index = 0
        self.timer_thread = None
        
        # VISCA Command List - Add or modify commands here
        self.visca_commands = [
            # Pan Left (medium speed: pan=0x08, tilt=0x08)
            [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x01, 0x03, 0xFF],
            
            # Stop Pan/Tilt
            [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x03, 0xFF],
        ]
        
        # Command descriptions for logging
        self.command_descriptions = [
            "Pan Left",
            "Stop Pan/Tilt"
        ]
    
    def connect(self):
        """Establish TCP connection to the PTZ camera"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            self.socket.connect((self.host, self.port))
            print(f"✓ Connected to PTZ camera at {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close the connection"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Connection closed")
    
    def send_command(self, command):
        """Send a VISCA command and wait for response"""
        if not self.socket:
            print("❌ No connection available")
            return False
        
        try:
            # Convert command to bytes and send
            command_bytes = bytes(command)
            hex_string = " ".join([f"{b:02X}" for b in command_bytes])
            print(f"   Hex: {hex_string}")
            
            self.socket.send(command_bytes)
            
            # Wait for response
            response = self.socket.recv(16)
            if response:
                response_hex = " ".join([f"{b:02X}" for b in response])
                print(f"   Response: {response_hex}")
                self.interpret_response(response)
            
            return True
            
        except socket.error as e:
            print(f"❌ Send error: {e}")
            return False
    
    def interpret_response(self, response):
        """Interpret VISCA response codes"""
        if len(response) < 3:
            return
        
        if response[0] == 0x90:
            if response[1] == 0x41:  # ACK (camera address 1)
                print("   ✓ Command acknowledged")
            elif response[1] == 0x51:  # Completion (camera address 1)
                print("   ✅ Command completed")
            elif response[1] == 0x60:
                error_code = response[2]
                error_messages = {
                    0x02: "Syntax error",
                    0x03: "Command buffer full",
                    0x04: "Command cancelled",
                    0x05: "No socket",
                    0x41: "Command not executable"
                }
                error_msg = error_messages.get(error_code, f"Unknown error: {error_code:02X}")
                print(f"   ❌ {error_msg}")
            else:
                print("   ⚠️ Unknown response type")
    
    def send_next_command(self):
        """Send the next command in the cycle"""
        if not self.visca_commands:
            print("⚠️ No commands in command list")
            return
        
        command = self.visca_commands[self.command_index]
        description = (self.command_descriptions[self.command_index] 
                      if self.command_index < len(self.command_descriptions) 
                      else f"Command {self.command_index + 1}")
        
        print(f"\n📤 Sending: {description}")
        self.send_command(command)
        
        # Move to next command (cycle through the list)
        self.command_index = (self.command_index + 1) % len(self.visca_commands)
    
    def command_timer(self):
        """Timer function that sends commands every 5 seconds"""
        while self.running:
            if self.socket:
                self.send_next_command()
            time.sleep(5)  # 5 second interval
    
    def start(self):
        """Start the controller"""
        if self.connect():
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
        self.disconnect()
        print("⏹️ Controller stopped")
    
    def send_single_command(self, index):
        """Send a single command by index"""
        if 0 <= index < len(self.visca_commands):
            command = self.visca_commands[index]
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
    controller = PTZOpticsVISCAController(host=CAMERA_HOST, port=CAMERA_PORT)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("PTZOptics VISCA Controller Example")
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

1. Add command byte arrays to the 'visca_commands' list
2. Add corresponding descriptions to 'command_descriptions' list

Example commands from the PTZOptics VISCA documentation:

Pan/Tilt Commands:
- Pan Right:     [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x03, 0xFF]
- Tilt Up:       [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x01, 0xFF]
- Tilt Down:     [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x02, 0xFF]
- Up-Left:       [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x01, 0x01, 0xFF]
- Up-Right:      [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x01, 0xFF]
- Down-Left:     [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x01, 0x02, 0xFF]
- Down-Right:    [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x02, 0xFF]
- Home Position: [0x81, 0x01, 0x06, 0x04, 0xFF]
- Reset:         [0x81, 0x01, 0x06, 0x05, 0xFF]

Speed Parameters:
- Pan speed: 0x01 (slow) to 0x18 (fast)
- Tilt speed: 0x01 (slow) to 0x14 (fast)
- Medium speed: 0x08 (commonly used)

Preset Commands:
- Save Preset 1:   [0x81, 0x01, 0x04, 0x3F, 0x01, 0x01, 0xFF]
- Recall Preset 1: [0x81, 0x01, 0x04, 0x3F, 0x02, 0x01, 0xFF]

Configuration:
- Change camera IP in the main() function
- Modify the 5-second interval in command_timer()
- Add error handling or logging as needed
"""
