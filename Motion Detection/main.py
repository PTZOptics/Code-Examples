"""
PTZOptics Camera Motion Detection Example

This example demonstrates how to connect to a PTZOptics camera and perform
real-time motion detection using OpenCV. The system can detect both general
motion and specifically identify when people are moving in the camera's view.

Requirements:
- PTZOptics camera with RTSP streaming enabled
- Network connectivity to the camera
- OpenCV Python package
"""

import cv2
import numpy as np
import time
from datetime import datetime
import argparse

# =============================================================================
# CONFIGURATION VARIABLES - Modify these for your specific setup
# =============================================================================

# Camera connection settings
DEFAULT_RTSP_STREAM = "stream2"  # Use stream2 for lower latency, stream1 for higher quality

# Motion detection parameters
DEFAULT_SENSITIVITY = 25         # Motion sensitivity (lower = more sensitive)
DEFAULT_MIN_AREA = 300           # Minimum motion area in pixels to trigger detection
MOTION_HOLD_FRAMES = 10          # Frames to hold motion state (reduces flickering)

# Face detection parameters
FACE_DETECTION_INTERVAL = 5      # Run face detection every N frames (for performance)
FACE_HOLD_FRAMES = 15            # Frames to hold face detection state

# Background subtractor settings
BACKGROUND_DETECT_SHADOWS = True # Enable shadow detection in background subtraction
MORPH_KERNEL_SIZE = (3, 3)       # Kernel size for morphological operations

# Person detection settings
PERSON_SCALE_FACTOR = 1.1        # Scale factor for person detection
PERSON_MIN_NEIGHBORS = 3         # Minimum neighbors for person detection
PERSON_MIN_SIZE = (30, 30)       # Minimum size for person detection

# Display settings
MOTION_COLOR = (0, 255, 0)       # Green color for motion bounding boxes (BGR)
PERSON_COLOR = (0, 0, 255)       # Red color for person bounding boxes (BGR)
STATUS_COLOR = (0, 255, 255)     # Yellow color for status text (BGR)

# Status indicator settings
STATUS_INDICATOR_SIZE = 50       # Size of the status indicator circle
STATUS_INDICATOR_POSITION = (30, 40)  # Position (x, y) from top-left corner
GREEN_LIGHT = (0, 255, 0)        # Green for active motion/person detection
RED_LIGHT = (0, 0, 255)          # Red for no motion detected


# =============================================================================

class PTZMotionDetector:
    """
    PTZOptics Camera Motion Detection System
    
    This class provides real-time motion detection capabilities for PTZOptics cameras
    using RTSP streaming. It combines background subtraction for motion detection 
    with Haar cascade classifiers for face detection.
    """
    
    def __init__(self, camera_ip, sensitivity=DEFAULT_SENSITIVITY, min_area=DEFAULT_MIN_AREA, stream="stream2"):
        """
        Initialize the motion detector for a PTZOptics camera.
        
        Args:
            camera_ip (str): IP address of the PTZOptics camera
            sensitivity (int): Motion sensitivity threshold (lower = more sensitive)
            min_area (int): Minimum area in pixels to consider as motion
            stream (str): RTSP stream to use (stream1 for higher quality, stream2 for lower latency)
        """
        self.camera_ip = camera_ip
        self.rtsp_url = f"rtsp://{camera_ip}/{stream}"
        self.cap = None
        
        self.sensitivity = sensitivity
        self.min_area = min_area
        
        # Initialize background subtractor for motion detection
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=BACKGROUND_DETECT_SHADOWS
        )
        
        # Load Haar cascade classifier for face detection
        self.person_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Motion smoothing to reduce flickering between motion/no-motion states
        self.motion_frames_count = 0
        self.motion_hold_frames = MOTION_HOLD_FRAMES
        
        # Face detection frame skipping and persistence
        self.face_detection_counter = 0
        self.face_frames_count = 0
        self.face_hold_frames = FACE_HOLD_FRAMES
        self.last_face_result = (False, [])
        
    def get_camera_frame(self):
        """
        Retrieve a single frame from the PTZOptics camera via RTSP.
        
        Establishes RTSP connection on first call and maintains the stream
        for subsequent frame captures.
        
        Returns:
            numpy.ndarray: Camera frame as BGR image, or None if retrieval failed
        """
        if self.cap is None:
            print(f"Connecting to RTSP stream: {self.rtsp_url}")
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if not self.cap.isOpened():
                print("Failed to open RTSP stream")
                return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            print("Failed to read frame from RTSP stream, attempting reconnection...")
            # Try to reconnect
            self.cap.release()
            self.cap = None
            return None
    
    def detect_motion(self, frame):
        """
        Detect motion in the current frame using background subtraction.
        
        This method uses MOG2 background subtractor to identify moving objects
        by comparing the current frame against a learned background model.
        
        Args:
            frame (numpy.ndarray): Input frame from camera
            
        Returns:
            tuple: (motion_detected, motion_areas, foreground_mask)
                - motion_detected (bool): True if motion above threshold detected
                - motion_areas (list): List of (x,y,w,h) bounding rectangles
                - foreground_mask (numpy.ndarray): Binary mask of detected motion
        """
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
        
        # Remove noise with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, MORPH_KERNEL_SIZE)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_areas = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                motion_areas.append((x, y, w, h))
        
        return motion_detected, motion_areas, fg_mask
    
    def smooth_motion_detection(self, raw_motion_detected):
        """Apply smoothing to motion detection to reduce flickering"""
        if raw_motion_detected:
            self.motion_frames_count = self.motion_hold_frames
            return True
        else:
            if self.motion_frames_count > 0:
                self.motion_frames_count -= 1
                return True
            else:
                return False
    
    def detect_person(self, frame):
        """
        Detect faces in the frame using Haar cascade classifier.
        
        Uses OpenCV's pre-trained face detector to identify human faces.
        More reliable than full-body detection for people at desks or partially visible.
        
        Args:
            frame (numpy.ndarray): Input frame from camera
            
        Returns:
            tuple: (person_detected, people_rectangles)
                - person_detected (bool): True if one or more faces detected
                - people_rectangles (list): List of (x,y,w,h) detection rectangles
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using Haar cascade classifier
        people = self.person_cascade.detectMultiScale(
            gray, 
            scaleFactor=PERSON_SCALE_FACTOR, 
            minNeighbors=PERSON_MIN_NEIGHBORS,
            minSize=PERSON_MIN_SIZE
        )
        
        return len(people) > 0, people
    
    def detect_person_with_persistence(self, frame):
        """
        Detect faces with frame skipping and result persistence for performance.
        
        Runs face detection every N frames and persists the result for smooth display.
        This reduces CPU usage while maintaining responsive face detection.
        
        Args:
            frame (numpy.ndarray): Input frame from camera
            
        Returns:
            tuple: (person_detected, people_rectangles)
                - person_detected (bool): True if faces detected (with persistence)
                - people_rectangles (list): List of (x,y,w,h) detection rectangles
        """
        self.face_detection_counter += 1
        
        # Run actual face detection every N frames
        if self.face_detection_counter >= FACE_DETECTION_INTERVAL:
            self.face_detection_counter = 0
            face_detected, faces = self.detect_person(frame)
            
            if face_detected:
                # Face found - reset persistence counter and store result
                self.face_frames_count = self.face_hold_frames
                self.last_face_result = (True, faces)
                return True, faces
            else:
                # No face found - but don't immediately clear if we were persisting
                if self.face_frames_count <= 0:
                    self.last_face_result = (False, [])
        
        # Check if we should persist previous face detection
        if self.face_frames_count > 0:
            self.face_frames_count -= 1
            # Return the persisted result with the original face rectangles
            return self.last_face_result
        else:
            return False, []
    
    def cleanup(self):
        """
        Clean up camera resources.
        
        Releases the RTSP video capture object to free system resources.
        Should be called when detection is finished.
        """
        if self.cap is not None:
            self.cap.release()
    
    def run_detection(self, display=False, save_detections=False):
        """
        Run the main motion detection loop.
        
        Continuously captures frames from the camera and processes them for motion
        and person detection. Optionally displays results and saves detection images.
        
        Args:
            display (bool): Show live video feed with detection overlays
            save_detections (bool): Save images when person motion is detected
            
        Note:
            Press 'q' to quit when display is enabled, or use Ctrl+C to interrupt.
        """
        print(f"Starting PTZOptics motion detection for camera at {self.camera_ip}")
        print("Press 'q' to quit the display window")
        
        frame_count = 0
        
        while True:
            frame = self.get_camera_frame()
            if frame is None:
                print("Failed to get frame, retrying in 2 seconds...")
                time.sleep(2)
                continue
            
            frame_count += 1
            
            # Detect motion
            raw_motion_detected, motion_areas, fg_mask = self.detect_motion(frame)
            
            # Apply smoothing to motion detection
            motion_detected = self.smooth_motion_detection(raw_motion_detected)
            
            # Check for faces with frame skipping and persistence (runs independently of motion)
            person_detected, people = self.detect_person_with_persistence(frame)
            
            
            # Display if requested
            if display:
                display_frame = frame.copy()
                
                # Draw motion detection areas in green
                for (x, y, w, h) in motion_areas:
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), MOTION_COLOR, 2)
                
                # Draw face detections in red
                for (x, y, w, h) in people:
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), PERSON_COLOR, 2)
                    cv2.putText(display_frame, "Face", (x, y - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, PERSON_COLOR, 2)
                
                # Draw status indicator circle (red/green light)
                indicator_color = GREEN_LIGHT if motion_detected else RED_LIGHT
                cv2.circle(display_frame, STATUS_INDICATOR_POSITION, 
                          STATUS_INDICATOR_SIZE//2, indicator_color, -1)
                
                # Add a white border around the status indicator
                cv2.circle(display_frame, STATUS_INDICATOR_POSITION, 
                          STATUS_INDICATOR_SIZE//2, (255, 255, 255), 2)
                
                # Display detection status text
                status = "MOTION + FACE" if (motion_detected and person_detected) else \
                        "MOTION DETECTED" if motion_detected else "NO MOTION"
                cv2.putText(display_frame, status, (STATUS_INDICATOR_POSITION[0] + 40, STATUS_INDICATOR_POSITION[1] + 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, STATUS_COLOR, 2)
                
                # Add quit instruction at bottom of frame
                frame_height = display_frame.shape[0]
                cv2.putText(display_frame, "Press 'q' to quit", (10, frame_height - 15), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                cv2.imshow("PTZOptics Motion Detection", display_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Brief pause to prevent excessive CPU usage
            time.sleep(0.01)
        
        self.cleanup()
        if display:
            cv2.destroyAllWindows()

def main():
    """
    Main entry point for PTZOptics motion detection example.
    
    Parses command line arguments and starts the motion detection system.
    Run with --help for usage information.
    """
    parser = argparse.ArgumentParser(
        description='PTZOptics Camera Motion Detection Example',
        epilog='Example: python main.py 192.168.1.100'
    )
    parser.add_argument('camera_ip', help='IP address of PTZOptics camera')
    parser.add_argument('--sensitivity', type=int, default=DEFAULT_SENSITIVITY, 
                       help=f'Motion sensitivity (lower = more sensitive, default: {DEFAULT_SENSITIVITY})')
    parser.add_argument('--min-area', type=int, default=DEFAULT_MIN_AREA, 
                       help=f'Minimum motion area in pixels (default: {DEFAULT_MIN_AREA})')
    parser.add_argument('--stream', type=int, default=2, choices=[1, 2],
                       help='Camera stream to use: 1 for higher quality, 2 for lower latency (default: 2)')
    
    args = parser.parse_args()
    
    detector = PTZMotionDetector(
        camera_ip=args.camera_ip,
        sensitivity=args.sensitivity,
        min_area=args.min_area,
        stream=f"stream{args.stream}"
    )
    
    try:
        detector.run_detection(display=True, save_detections=False)
    except KeyboardInterrupt:
        print("\nPTZOptics motion detection stopped by user")

if __name__ == "__main__":
    main()
