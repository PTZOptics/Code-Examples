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
import numpy as np
from pyzbar import pyzbar
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
        # Computer the Scharr gradient magnitude and representation of the images
        ddepth = cv2.CV_32F
        gradient_x = cv2.Sobel(gray, ddepth=ddepth, dx=1, dy=0, ksize=-1)
        gradient_y = cv2.Sobel(gray, ddepth=ddepth, dx=0, dy=1, ksize=-1)

        # Subtract the gradient_y from the gradient_x
        gradient = cv2.subtract(gradient_x, gradient_y)
        gradient = cv2.convertScaleAbs(gradient)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.blur(gradient, (9,9))
        #blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        (_, threshold) = cv2.threshold(blurred, 255, 255, cv2.THRESH_BINARY)

        # Construct a closing kernel and apply it to the thresholded image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        closed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)

        # Perform a series of erosions and dilations
        closed = cv2.erode(closed, kernel, iterations=4)
        closed = cv2.dilate(closed, kernel, iterations=4)

        # Find contours in the edge-detected image
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=lambda c: cv2.contourArea(np.array(c)), default=None)
            x, y, w, h = cv2.boundingRect(np.array(largest_contour))
            # Return the bounding box coordinates
            #return x, y, w, h
            #             # Crop the region of interest (ROI) for decoding
            roi = frame[y:y + h, x:x + w]

            # Attempt to decode the barcode using pyzbar
            decoded_objects = pyzbar.decode(roi)
            if decoded_objects:
                # Extract the first decoded barcode's data and type
                barcode_data = decoded_objects[0].data.decode("utf-8")
                barcode_type = decoded_objects[0].type

                # Draw the rectangle on the frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Return the bounding box and decoded information
                return {
                    "rect": (x, y, w, h),
                    "data": barcode_data,
                    "type": barcode_type
                }
        else:
            return None

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
        barcode_info = self.recognize_and_decode_barcodes(frame.copy())

        if barcode_info:
            x, y, w, h = barcode_info["rect"]
            barcode_data = barcode_info["data"]
            barcode_type = barcode_info["type"]

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
