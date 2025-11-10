"""
PTZOptics VISCA Preset Position Query
"""

import json
import socket
import sys
import time

TIMEOUT = 10  # Seconds


# PTZOptics Blue: #93cce8 -> RGB(147, 206, 232)
class Colors:
    PTZOPTICS_BLUE = "\033[38;2;147;206;232m"
    BRIGHT_BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def print_banner():
    """Display PTZOptics ASCII art banner"""
    banner = f"""{Colors.PTZOPTICS_BLUE}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗ ████████╗███████╗ ██████╗ ██████╗ ████████╗██╗ ██████╗███████╗  ║
║   ██╔══██╗╚══██╔══╝╚══███╔╝██╔═══██╗██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝  ║
║   ██████╔╝   ██║     ███╔╝ ██║   ██║██████╔╝   ██║   ██║██║     ███████╗  ║
║   ██╔═══╝    ██║    ███╔╝  ██║   ██║██╔═══╝    ██║   ██║██║     ╚════██║  ║
║   ██║        ██║   ███████╗╚██████╔╝██║        ██║   ██║╚██████╗███████║  ║
║   ╚═╝        ╚═╝   ╚══════╝ ╚═════╝ ╚═╝        ╚═╝   ╚═╝ ╚═════╝╚══════╝  ║
║                                                                           ║
║                   {Colors.RESET}{Colors.PTZOPTICS_BLUE}VISCA Preset Position Saver{Colors.BOLD}                             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)


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

    def go_home(self):
        """Move camera to HOME position"""
        command = [0x81, 0x01, 0x06, 0x04, 0xFF]
        print("Moving to HOME position...")
        self.send_command(command)
        time.sleep(0.5)
        self.clear_buffer()

    def set_max_preset_speed(self):
        """Set preset speed to maximum (0x18)"""
        command = [0x81, 0x01, 0x06, 0x01, 0x18, 0xFF]
        print("Setting preset speed to maximum...")
        response = self.send_command(command)
        time.sleep(0.2)
        self.clear_buffer()
        return response

    def recall_preset(self, preset):
        """Recall a preset position"""
        command = [0x81, 0x01, 0x04, 0x3F, 0x02, preset, 0xFF]
        print(f"Recalling preset {preset}...")
        self.send_command(command)
        time.sleep(0.5)  # Brief wait for preset to execute
        self.clear_buffer()  # Clear ACK and completion responses

    def get_position(self, capture_focus=True):
        """Query and return current pan, tilt, zoom, and optionally focus positions

        Args:
            capture_focus: If True, capture focus position. If False, skip focus (useful for auto-focus cameras)
        """
        position = {}

        # Pan/Tilt Inquiry with retry
        for attempt in range(3):
            response = self.send_command([0x81, 0x09, 0x06, 0x12, 0xFF])
            if response and len(response) >= 11 and response[1] == 0x50:
                pan = (
                    (response[2] << 12)
                    | (response[3] << 8)
                    | (response[4] << 4)
                    | response[5]
                )
                tilt = (
                    (response[6] << 12)
                    | (response[7] << 8)
                    | (response[8] << 4)
                    | response[9]
                )
                position["pan"] = f"{pan:04X}"
                position["tilt"] = f"{tilt:04X}"
                break
            else:
                print(f"Pan/Tilt inquiry attempt {attempt + 1} failed, retrying...")
                time.sleep(0.2)

        # Zoom Inquiry
        response = self.send_command([0x81, 0x09, 0x04, 0x47, 0xFF])
        if response and len(response) >= 7 and response[1] == 0x50:
            zoom = (
                (response[2] << 12)
                | (response[3] << 8)
                | (response[4] << 4)
                | response[5]
            )
            position["zoom"] = f"{zoom:04X}"

        # Focus Inquiry (optional)
        if capture_focus:
            response = self.send_command([0x81, 0x09, 0x04, 0x48, 0xFF])
            if response and len(response) >= 7 and response[1] == 0x50:
                focus = (
                    (response[2] << 12)
                    | (response[3] << 8)
                    | (response[4] << 4)
                    | response[5]
                )
                position["focus"] = f"{focus:04X}"

        return position


def main():
    print_banner()

    try:
        ip_address = input("Please enter an IP address: ")
        port_str = input("Please enter TCP Port # [default: 5678]: ").strip()
        port = int(port_str) if port_str else 5678

        print("\n" + "=" * 65)
        print("Preset Ranges:")
        print("    1-89    → Assignable")
        print("      90    → Calls Home Position")
        print("   91-94    → Reserved")
        print("      95    → Toggles OSD")
        print("   96-99    → Reserved")
        print("     150    → Enable Tracking")
        print("     151    → Disable Tracking")
        print("=" * 65 + "\n")

        start_preset_str = input(
            "Please enter starting preset (1-89, 100-149, 152-254): "
        )
        end_preset_str = input("Please enter ending preset (1-89, 100-149, 152-254): ")

        print("\n" + "=" * 65)
        print("Timing Configuration")
        print("=" * 65)
        print("⚠️  WARNING: Using less than 10 seconds may cause incomplete movements")
        print("    Recommended: 10+ seconds for reliable preset capture\n")

        time_between_str = input(
            "Seconds to wait for camera movement [default: 10]: "
        ).strip()
        time_between_preset = int(time_between_str) if time_between_str else 10

        initial_check_str = input(
            "Seconds for initial preset check [default: 1]: "
        ).strip()
        initial_check_delay = int(initial_check_str) if initial_check_str else 1

        print("=" * 65 + "\n")

        capture_focus_str = (
            input("Capture focus position? (y/n) [default: n]: ").strip().lower()
        )
        capture_focus = (
            capture_focus_str == "y"
        )  # Default to False unless 'y' is entered
    except Exception as e:
        print(
            "Please verify your IP address and enter a number for port, start/end preset numbers."
        )
        print(e)
        sys.exit(1)

    try:
        start_preset = int(start_preset_str)
        end_preset = int(end_preset_str)
        if not (
            1 <= start_preset <= 89
            or 100 <= start_preset <= 149
            or 152 <= start_preset <= 254
        ) or not (
            1 <= end_preset <= 89
            or 100 <= end_preset <= 149
            or 152 <= end_preset <= 254
        ):
            print(
                "Presets must be between 1 and 89, or between 100 and 149, or between 152 and 254"
            )
            sys.exit(1)
        if start_preset > end_preset:
            print("Starting preset must be less than or equal to ending preset")
            sys.exit(1)
    except ValueError:
        print("Invalid preset number")
        sys.exit(1)

    # Connect and query
    controller = PTZOpticsVISCAController(host=ip_address, port=port)

    if not controller.connect():
        sys.exit(1)

    try:
        # Initialize camera to HOME position with max speed
        controller.set_max_preset_speed()
        controller.go_home()
        print(
            f"Waiting {time_between_preset} seconds for HOME movement to complete..."
        )
        time.sleep(time_between_preset)
        controller.clear_buffer()

        home_position = controller.get_position(capture_focus=capture_focus)
        print(f"HOME position captured: {home_position}")
        if capture_focus:
            print("(Capturing focus positions)\n")
        else:
            print("(Skipping focus - only capturing Pan/Tilt/Zoom)\n")

        all_positions = {}
        skipped_presets = []

        for preset in range(start_preset, end_preset + 1):
            if 90 <= preset <= 99:
                continue
            controller.recall_preset(preset)

            # Brief delay to allow movement to start
            print(
                f"Waiting {initial_check_delay} second(s) to check if preset exists..."
            )
            time.sleep(initial_check_delay)
            controller.clear_buffer()

            # Check if position changed from HOME
            current_position = controller.get_position(capture_focus=capture_focus)

            if current_position == home_position:
                print(
                    f"Preset {preset} appears to not exist (still at HOME). Skipping.\n"
                )
                skipped_presets.append(preset)
                continue

            # Position changed, wait for full movement to complete
            print(
                f"Preset {preset} exists. Waiting {time_between_preset} seconds for movement to complete..."
            )
            time.sleep(time_between_preset)
            controller.clear_buffer()

            # Get final position
            position = controller.get_position(capture_focus=capture_focus)

            # Store result
            all_positions[f"preset_{preset}"] = position
            print(f"Captured: {position}\n")

            # Return to HOME for next preset
            controller.go_home()
            time.sleep(time_between_preset)
            controller.clear_buffer()

        with open("preset_positions.json", "w") as f:
            json.dump(all_positions, f, indent=2)

        print(f"\nSaved {len(all_positions)} preset positions to preset_positions.json")
        if skipped_presets:
            print(
                f"Skipped {len(skipped_presets)} non-existent presets: {skipped_presets}"
            )

    finally:
        controller.disconnect()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user. Exiting gracefully...{Colors.RESET}")
        sys.exit(0)
