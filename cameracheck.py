import cv2

def scan_for_cam():
    # Check the standard ones first
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"✅ Success! Camera found at index {i}")
            cap.release()
        else:
            print(f"❌ Nothing at index {i}")

scan_for_cam()