import cv2
from main import BarcodeScanner

def test_barcode_scanner_with_image():
    # Path to the sample image file
    sample_image_path = "wikipedia.png"

    # Load the sample image
    frame = cv2.imread(sample_image_path)

    if frame is None:
        print("Failed to load the sample image. Please check the file path.")
        return

    # Create an instance of BarcodeScanner with a dummy address
    scanner = BarcodeScanner(addr="dummy_address")

    # Test the detect_barcode_from_frame method
    result_frame = scanner.detect_barcode_from_frame(frame)

    if result_frame is not None:
        print("Barcode detected successfully!")
    else:
        print("No barcode detected in the sample image.")

# Run the test
if __name__ == "__main__":
    test_barcode_scanner_with_image()
