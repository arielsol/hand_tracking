import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from pygrabber.dshow_graph import FilterGraph

from inputhandler import InputHandler
from oschandler import OSCHandler
from csvhandler import CSVHandler

import cv2
import threading
import time
import global_vars 

class CaptureThread(threading.Thread):
    cap = None
    ret = None
    frame = None
    isRunning = False
    counter = 0
    timer = 0.0
    printBuffer = 0.5

    def run(self):
        # Try to open with DirectShow (Best for USB Webcams)
        self.cap = cv2.VideoCapture(global_vars.WEBCAM_INDEX, cv2.CAP_DSHOW)

        # If that fails, try the default (MSMF)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(global_vars.WEBCAM_INDEX)

        # SAFETY CHECK: If it still won't open, don't just continue!
        if not self.cap.isOpened():
            print(f"FATAL: Could not open camera at index {global_vars.WEBCAM_INDEX}")
            self.cap = None # Ensure it is None so we can check it later
            return # Exit the thread early

        if global_vars.USE_CUSTOM_CAM_SETTINGS:
            self.cap.set(cv2.CAP_PROP_FPS, global_vars.FPS)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, global_vars.WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, global_vars.HEIGHT)

        time.sleep(1)
        # print("Opened Capture @ %s fps" % str(self.cap.get(cv2.CAP_PROP_FPS)))
        
        while not global_vars.KILL_THREADS:
            self.ret, self.frame = self.cap.read()
            self.isRunning = True
            if global_vars.DEBUG:
                self.counter += 1
                if time.time() - self.timer >= 3:
                    print("Capture FPS: ", self.counter / (time.time() - self.timer))
                    self.counter = 0
                    self.timer = time.time()

    def pick_camera():
        graph = FilterGraph()
        devices = graph.get_input_devices()
        
        if not devices:
            print("No cameras detected!")
            return None

        print("\n--- AVAILABLE CAMERAS ---")
        for i, name in enumerate(devices):
            print(f"[{i}] : {name}")
        
        try:
            selection = int(input("\nSelect Camera Index (default 0): ") or 0)
            if 0 <= selection < len(devices):
                print(f"Starting with: {devices[selection]}")
                return selection
            else:
                print("Invalid index. Defaulting to 0.")
                return 0
        except ValueError:
            return 0

class HandThread(threading.Thread): 
    def __init__(self):
        super().__init__()

        # ---------- Camera Setup ----------
        chosen_index = CaptureThread.pick_camera()
        if chosen_index is None:
            return
        global_vars.WEBCAM_INDEX = chosen_index

        # ---------- Debug Draw Setup ----------
        self.latest_landmarks = None
        self.timeSincePostStatistics = 0

    def run(self):
        # ---------- Input Setup ----------
        self.input_handler = InputHandler(print_interval=CaptureThread.printBuffer)
        print("\n--- Inputs Available ---")
        print("Note: Click the CAMERA WINDOW to enable input.")
        print("Press ENTER to stop the program.")
        print("Press SPACE to start/stop OSC streaming.")
        print("Press S to print a hand data snapshot.")

        # ---------- Logging Setup ----------
        self.osc_handler = OSCHandler(self.input_handler)
        self.csv_handler = CSVHandler(self.input_handler)

        # ---------- MediaPipe Hand Setup ----------
        base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")
        options = vision.HandLandmarkerOptions(
            base_options = base_options,
            running_mode = vision.RunningMode.LIVE_STREAM, 
            num_hands = global_vars.NUMBER_HANDS,
            min_hand_detection_confidence = 0.35,
            min_hand_presence_confidence = 0.25,
            result_callback = self.handle_live_stream_result
        )
        hand_tracker = vision.HandLandmarker.create_from_options(options)    

        # ---------- Handle Capture ----------
        capture = CaptureThread()
        capture.start()
        print("\n--- MediaPipe Started ---")
        print("Beginning Hand Tracking...")

        while not global_vars.KILL_THREADS and not capture.isRunning:
            time.sleep(0.1)

        while not global_vars.KILL_THREADS and capture.cap.isOpened():
            key = cv2.waitKey(1) & 0xFF
            self.input_handler.process_key(key)

            if global_vars.KILL_THREADS:
                break   
            
            image_raw = capture.frame
            if image_raw is None:
                continue
            
            # --- Raw Image for Processing ---
            image_rgb = cv2.cvtColor(image_raw, cv2.COLOR_BGR2RGB)
            image_contiguous = image_rgb.copy()
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_contiguous)
            
            timestamp_ms = int(time.time() * 1000)
            hand_tracker.detect_async(mp_image, timestamp_ms)

            # --- Mirror Image for Debug ---
            if global_vars.DEBUG:
                debug_image = cv2.flip(image_raw, 1) 

                if self.latest_landmarks is not None:
                    for landmarks in self.latest_landmarks:
                        for lm in landmarks:
                            mirrored_x = 1.0 - lm.x 
                            
                            cx = int(mirrored_x * debug_image.shape[1]) 
                            cy = int(lm.y * debug_image.shape[0])
                            cv2.circle(debug_image, (cx, cy), 4, (0, 255, 255), -1)

                cv2.imshow('Hand Tracking Debug', debug_image)

        capture.cap.release()
        cv2.destroyAllWindows()

    def handle_live_stream_result(self, results: vision.HandLandmarkerResults, output_image: mp.Image, timestamp_ms: int):
        if results.hand_landmarks:
            self.latest_landmarks = results.hand_landmarks
        else:
            self.latest_landmarks = None

        if hasattr(self, 'osc_handler'):
            self.osc_handler.process_hand_data(results)

        if hasattr(self, 'csv_handler'):
            self.csv_handler.process_hand_data(results)