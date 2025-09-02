# PTZOptics Camera Motion Detection

A Python example demonstrating real-time motion detection using PTZOptics cameras with OpenCV. This system detects both general motion and specifically identifies when faces are present in the camera's view.

## Features

- Real-time RTSP video streaming from PTZOptics cameras
- Motion detection using background subtraction
- Face detection using Haar cascade classifiers
- Live display with visual indicators and bounding boxes
- Configurable sensitivity and detection parameters
- Single window interface with red/green status indicator

## Requirements

- PTZOptics camera with RTSP streaming enabled
- Network connectivity to the camera
- Python 3.8+
- Required packages: opencv-python, numpy

## Installation

### Using uv (Recommended)

```bash
# Clone or download this project
cd motion-detection

# Install dependencies automatically
uv sync
```

### Using pip

```bash
# Install required packages
pip install opencv-python>=4.8.0 numpy>=1.24.0
```

## Usage

### Basic Commands

```bash
# Basic motion detection with display - using uv
uv run main.py <CAMERA_IP>
```

### Without uv

```bash
# Basic motion detection with display
python main.py <CAMERA_IP>
```

### Advanced Options

```bash
# Increase sensitivity for smaller movements (lower = more sensitive)
uv run main.py <CAMERA_IP> --sensitivity 10

# Detect smaller motion areas (lower = catches smaller movements)
uv run main.py <CAMERA_IP> --min-area 100

# Use stream1 for higher quality (stream2 is default for lower latency)
uv run main.py <CAMERA_IP> --stream 1

# Combine for maximum sensitivity
uv run main.py <CAMERA_IP> --sensitivity 10 --min-area 50
```

### Example

```bash
uv run main.py 192.168.1.100 --sensitivity 15 --min-area 200
```

## Configuration

Key settings can be modified at the top of `main.py`:

- **DEFAULT_SENSITIVITY** (25): Motion detection sensitivity
- **DEFAULT_MIN_AREA** (300): Minimum pixel area to trigger detection  
- **MOTION_HOLD_FRAMES** (10): Frames to hold motion state (reduces flickering)
- **DEFAULT_RTSP_STREAM** ("stream2"): Camera stream to use (stream2 = lower latency)

## Camera Setup

Ensure your PTZOptics camera has:
1. RTSP streaming enabled
2. Network connectivity
3. Proper IP address configuration
4. Stream2 available for lower latency detection

## Troubleshooting

**Motion not detected for small movements?**
- Lower sensitivity: `--sensitivity 10`
- Reduce minimum area: `--min-area 100`

**Connection issues?**
- Verify camera IP address
- Check network connectivity
- Ensure RTSP streaming is enabled on camera

**Performance issues?**
- Using stream2 (default) for lower latency
- Ensure stable network connection to camera

## Controls

- **q**: Quit the application (when display window is active)
- **Ctrl+C**: Force quit from terminal

## Output

- Live display shows:
  - Green boxes around motion areas
  - Red boxes around detected faces
  - Red/green status indicator in top-left
  - Status text ("NO MOTION", "MOTION DETECTED", "MOTION + FACE")