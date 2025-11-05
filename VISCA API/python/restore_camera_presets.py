"""
PTZOptics VISCA Preset Position Restore
Restores preset positions from preset_positions.json to the camera
"""

import socket
import time
import sys
import json
import os

TIME_BETWEEN_MOVES = 10  # Seconds to wait for camera to reach position
TIMEOUT = 10  # Seconds


class PTZOpticsVISCAController:
    def __init__(self, host, port=5678):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """Establish TCP connection to the PTZ camera"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.connect((self.host, self.port))

            # Clear any initial data in buffer
            self.socket.setblocking(False)
            try:
                while self.socket.recv(1024):
                    pass
            except:
                pass
            self.socket.setblocking(True)
            self.socket.settimeout(TIMEOUT)
            print(f"Connected to {self.host}:{self.port}\n")
            return True
        except socket.error as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Close the connection"""
        if self.socket:
            self.socket.close()
            self.socket = None

    def send_command(self, command):
        """Send a VISCA command and get response"""
        if not self.socket:
            return None

        try:
            command_bytes = bytes(command)
            self.socket.send(command_bytes)
            response = self.socket.recv(16)
            return response
        except socket.error as e:
            print(f"Send error: {e}")
            return None

    def clear_buffer(self):
        self.socket.setblocking(False)
        try:
            while self.socket.recv(1024):
                pass
        except:
            pass
        self.socket.setblocking(True)
        self.socket.settimeout(TIMEOUT)

    def set_zoom_position(self, zoom_hex):
        """Set zoom to specific position

        Args:
            zoom_hex: Hex string like "0000" or "4000"
        """
        zoom_value = int(zoom_hex, 16)
        p = (zoom_value >> 12) & 0x0F
        q = (zoom_value >> 8) & 0x0F
        r = (zoom_value >> 4) & 0x0F
        s = zoom_value & 0x0F

        command = [0x81, 0x01, 0x04, 0x47, p, q, r, s, 0xFF]
        print(f"Setting zoom to {zoom_hex}...")
        self.send_command(command)
        time.sleep(0.2)
        self.clear_buffer()

    def set_pan_tilt_position(self, pan_hex, tilt_hex, pan_speed=0x18, tilt_speed=0x18):
        """Set pan/tilt to specific position

        Args:
            pan_hex: Hex string like "0000" or "8A3C"
            tilt_hex: Hex string like "0000" or "05F4"
            pan_speed: Pan speed (0x01-0x18), default 0x18 (max)
            tilt_speed: Tilt speed (0x01-0x18), default 0x18 (max)
        """
        pan_value = int(pan_hex, 16)
        tilt_value = int(tilt_hex, 16)

        # Break down pan into 4 nibbles
        pan_y1 = (pan_value >> 12) & 0x0F
        pan_y2 = (pan_value >> 8) & 0x0F
        pan_y3 = (pan_value >> 4) & 0x0F
        pan_y4 = pan_value & 0x0F

        # Break down tilt into 4 nibbles
        tilt_z1 = (tilt_value >> 12) & 0x0F
        tilt_z2 = (tilt_value >> 8) & 0x0F
        tilt_z3 = (tilt_value >> 4) & 0x0F
        tilt_z4 = tilt_value & 0x0F

        command = [
            0x81, 0x01, 0x06, 0x02,
            pan_speed, tilt_speed,
            pan_y1, pan_y2, pan_y3, pan_y4,
            tilt_z1, tilt_z2, tilt_z3, tilt_z4,
            0xFF
        ]
        print(f"Setting pan/tilt to {pan_hex}/{tilt_hex} at speed {pan_speed:02X}/{tilt_speed:02X}...")
        self.send_command(command)
        time.sleep(0.2)
        self.clear_buffer()

    def set_preset(self, preset_number):
        """Save current position as a preset

        Args:
            preset_number: Preset number (0-254)
        """
        if not (0 <= preset_number <= 254):
            print(f"Invalid preset number: {preset_number}")
            return False

        command = [0x81, 0x01, 0x04, 0x3F, 0x01, preset_number, 0xFF]
        print(f"Saving preset {preset_number}...")
        response = self.send_command(command)
        time.sleep(0.2)
        self.clear_buffer()
        return True


def main():
    # Check if preset file exists
    if not os.path.exists("preset_positions.json"):
        print("Error: preset_positions.json not found!")
        print("Please run save_camera_presets.py first to create the preset file.")
        sys.exit(1)

    # Load preset data
    try:
        with open("preset_positions.json", "r") as f:
            preset_data = json.load(f)
        print(f"Loaded {len(preset_data)} presets from preset_positions.json\n")
    except json.JSONDecodeError as e:
        print(f"Error reading preset_positions.json: {e}")
        sys.exit(1)

    # Get camera connection info
    try:
        ip_address = input("Please enter an IP address: ")
        port_str = input("Please enter TCP Port # [default: 5678]: ").strip()
        port = int(port_str) if port_str else 5678
    except Exception as e:
        print("Please verify your IP address and enter a valid port number.")
        print(e)
        sys.exit(1)

    # Connect and restore presets
    controller = PTZOpticsVISCAController(host=ip_address, port=port)

    if not controller.connect():
        sys.exit(1)

    try:
        restored_count = 0
        skipped_count = 0

        for preset_key, position_data in preset_data.items():
            # Extract preset number from key like "preset_0", "preset_1", etc.
            preset_number = int(preset_key.split("_")[1])

            print(f"\n{'='*60}")
            print(f"Restoring {preset_key} (preset #{preset_number})")
            print(f"Position data: {position_data}")
            print(f"{'='*60}")

            # Check if we have required position data
            if "pan" not in position_data or "tilt" not in position_data or "zoom" not in position_data:
                print(f"Warning: Incomplete position data for {preset_key}. Skipping.")
                skipped_count += 1
                continue

            # Set zoom position
            controller.set_zoom_position(position_data["zoom"])

            # Set pan/tilt position
            controller.set_pan_tilt_position(
                position_data["pan"],
                position_data["tilt"]
            )

            # Wait for camera to reach position
            print(f"Waiting {TIME_BETWEEN_MOVES} seconds for camera to reach position...")
            time.sleep(TIME_BETWEEN_MOVES)
            controller.clear_buffer()

            # Save the preset
            if controller.set_preset(preset_number):
                print(f"✓ Successfully restored preset {preset_number}\n")
                restored_count += 1
            else:
                print(f"✗ Failed to save preset {preset_number}\n")
                skipped_count += 1

        print(f"\n{'='*60}")
        print(f"Restoration complete!")
        print(f"Restored: {restored_count} presets")
        if skipped_count > 0:
            print(f"Skipped: {skipped_count} presets")
        print(f"{'='*60}")

    finally:
        controller.disconnect()


if __name__ == "__main__":
    main()
