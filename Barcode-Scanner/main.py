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

import argparse
import cv2
#import numpy as np
from pyzbar import pyzbar
from curses.ascii import isalnum
#import matplotlib.pyplot as plt
import time


# =============================================================================

class BarcodeScanner:
    """
    PTZOptics Camera Barcode Scanner
    """

    def __init__(self, addr):
        """
        Initialize the barcode scanner
        """
        self.addr = addr
        self.rtsp_url = f"rtsp://{self.addr}/2"
        self.cap = None

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
        for _ in range(10):
            _, _ = self.cap.read()
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            print("Failed to read frame from RTSP stream, attempting reconnection...")
            # Try to reconnect
            self.cap.release()
            self.cap = None
            return None

    def cleanup(self):
        """
        Clean up camera resources.

        Releases the RTSP video capture object to free system resources.
        Should be called when detection is finished.
        """
        if self.cap is not None:
            self.cap.release()
    def recognize_and_decode_barcodes(self, frame):
        """
        Recognize and decode barcodes from a frame.

        This function preprocesses the frame to enhance barcode detection,
        such as by applying edge detection and contour finding.

        Args:
            frame (numpy.ndarray): The input frame.

        Returns:
            list: A list of detected barcodes with their data and types.
        """
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Use edge detection to find potential barcode regions
        edges = cv2.Canny(blurred, 50, 200)

        # Find contours in the edge-detected image
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_barcodes = []

        for contour in contours:
            # Approximate the contour to a polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Ignore small or non-rectangular contours
            if len(approx) < 4 or cv2.contourArea(contour) < 100:
                continue

            # Get the bounding box of the contour
            x, y, w, h = cv2.boundingRect(approx)

            # Extract the region of interest (ROI) for barcode decoding
            roi = gray[y:y + h, x:x + w]

            # Decode barcodes in the ROI
            barcodes = pyzbar.decode(roi)

            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type

                # Append the detected barcode information
                detected_barcodes.append({
                    "data": barcode_data,
                    "type": barcode_type,
                    "rect": (x, y, w, h)
                })

        return detected_barcodes

    def detect_barcode_from_frame(self, frame):
        """
        Detect and annotate barcodes in a frame.

        This method now uses the recognize_and_decode_barcodes function
        to preprocess and decode barcodes.

        Args:
            frame (numpy.ndarray): The input frame.

        Returns:
            numpy.ndarray: The annotated frame with barcode information, or None if no barcodes are detected.
        """
        detected_barcodes = self.recognize_and_decode_barcodes(frame.copy())

        if detected_barcodes:
            for barcode in detected_barcodes:
                x, y, w, h = barcode["rect"]
                barcode_data = barcode["data"]
                barcode_type = barcode["type"]

                # Draw a rectangle around the barcode
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Put barcode data and type on the image
                cv2.putText(frame, f"{barcode_data} ({barcode_type})",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            return frame
        else:
            return None

    def run_detection(self):
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
        print(f"Starting PTZOptics motion detection for camera at {self.addr}")
        print("Press 'q' to quit the display window")

        frame_count = 0

        while True:
            frame = self.get_camera_frame()
            if frame is None:
                print("Failed to get frame, retrying in 2 seconds...")
                time.sleep(2)
                continue

            frame_count += 1

            processed_frame = self.detect_barcode_from_frame(frame)
            if processed_frame is not None:
                frame = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB)
                cv2.imshow("PTZOptics Barcode Scanner", frame)
                input("Press enter to continue")
            else:
                cv2.imshow("PTZOptics Barcode Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Brief pause to prevent excessive CPU usage
            #time.sleep(0.01)

        self.cleanup()
        cv2.destroyAllWindows()

def main():
    """
    Main entry point for PTZOptics motion detection example.

    Parses command line arguments and starts the motion detection system.
    Run with --help for usage information.
    """
    parser = argparse.ArgumentParser(
        description='PTZOptics Barcode Scanner',
        epilog='Example: python main.py --addr 192.168.1.100'
    )
    parser.add_argument('-a', '--addr', type=str, help='IP address of PTZOptics camera')

    args = parser.parse_args()

    detector = BarcodeScanner(
        addr=args.addr,
    )

    try:
        detector.run_detection()
    except KeyboardInterrupt:
        print("\nPTZOptics motion detection stopped by user")

if __name__ == "__main__":
    main()
