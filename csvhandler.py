import csv
import os
import time
import global_vars 
from datetime import datetime
from collections import deque, Counter

class CSVHandler:
    def __init__(self, input_handler):
        self.input_handler = input_handler
        self.handedness_history = {i: deque(maxlen=3) for i in range(4)}
        self.target_sample_interval = 1.0 / global_vars.SAMPLES_PER_SECOND
        self.last_sample_time = 0.0

        self.csv_file = None
        self.writer = None
        self.was_streaming = False
        self.current_filepath = None

        # ---------- Handle File Path ----------
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.export_dir = os.path.join(script_dir, "CSV_Exports")  # Saved as self.export_dir
        os.makedirs(self.export_dir, exist_ok=True)

    def _initialize_file(self):
        # ---------- Handle File Name ----------
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") 
        filename = f"{timestamp_str}_hand_tracking.csv"
        self.current_filepath = os.path.join(self.export_dir, filename) # Updates instance state smoothly
        
        # ---------- Write Header Row ----------
        self.csv_file = open(self.current_filepath, mode='a', newline='', encoding='utf-8')
        self.writer = csv.writer(self.csv_file)

        headers = ["Timestamp_MS", "Hand_Index", "Hand_Label", "Gesture_Name", "Gesture_Confidence", "Coordinate_Type"]
        for i in range(21):
            headers.append(f"Joint_{i:02d}")
        
        self.writer.writerow(headers)
        self.csv_file.flush()

        for k in self.handedness_history:
            self.handedness_history[k].clear()

        self.last_sample_time = 0.0

    def process_hand_data(self, results):
        current_stream_state = self.input_handler.should_stream

        # --- On Activated ---
        if current_stream_state and not self.was_streaming:
            self._initialize_file()
            print("--- CSV Logging Started ---")
            print(f"Writing data to {self.current_filepath}\n")
            self.was_streaming = True

        # --- On Deactivated ---
        elif not current_stream_state and self.was_streaming:
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
                self.writer = None
            print("--- CSV Logging Complete ---")
            print("File Saved.")
            self.was_streaming = False

        if not current_stream_state or not results.hand_landmarks:
            return
        
        current_time = time.time()
        if current_time - self.last_sample_time < self.target_sample_interval:
            return  # Skip this iteration and try again on the next loop tick

        self.last_sample_time = current_time
        timestamp_ms = int(time.time() * 1000)

        for hand_idx, landmarks in enumerate(results.hand_landmarks):

            # --- Smooth Handedness ---
            raw_label = results.handedness[hand_idx][0].category_name.lower()

            if hand_idx in self.handedness_history:
                self.handedness_history[hand_idx].append(raw_label)
                hand_label = Counter(self.handedness_history[hand_idx]).most_common(1)[0][0]
            else:
                hand_label = raw_label

            gesture_name = "unknown"
            gesture_confidence = 0.0

            if hasattr(results, 'gestures') and results.gestures and len(results.gestures) > hand_idx:
                hand_gestures = results.gestures[hand_idx]
                if hand_gestures:
                    gesture_name = hand_gestures[0].category_name
                    gesture_confidence = float(hand_gestures[0].score)

            # hand_label = results.handedness[hand_idx][0].category_name.lower()
            
            # --- Write Coordinates to CSV ---
            screen_coords = []
            # world_coords = []

            for i, lm in enumerate(landmarks):
                screen_coords.append([float(lm.x), float(lm.y), float(lm.z)])
                # w_lm = results.hand_world_landmarks[hand_idx][i]
                # world_coords.append([float(w_lm.x), float(w_lm.y), float(w_lm.z)])

            screen_row = [f'="{timestamp_ms}"', hand_idx, hand_label, gesture_name, f"{gesture_confidence:.3f}", "screen"] + screen_coords
            self.writer.writerow(screen_row)

            # world_row = [f'="{timestamp_ms}"', hand_idx, hand_label, gesture_name, f"{gesture_confidence:.3f}", "world"] + world_coords
            # self.writer.writerow(world_row)

        if self.csv_file:
            self.csv_file.flush()