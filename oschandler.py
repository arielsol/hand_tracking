import global_vars
from pythonosc import udp_client

class OSCHandler:
    def __init__(self, input_handler):
        self.input_handler = input_handler
        self.was_streaming = False
        self.last_gestures = {}  # Format: { hand_idx: "gesture_name" }

        # ---------- OSC Send Setup ----------
        self.ip = global_vars.OSC_IP_ADDRESS
        self.port = global_vars.OSC_PORT
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)

    def process_hand_data(self, results):
        # --- Handle Stream End ---
        if not self.input_handler.should_stream and self.was_streaming:
            print("--- OSC Streaming Complete ---")
            self.input_handler.is_first_frame = False
            self.was_streaming = False
            self.last_gestures.clear()

        if not results.hand_landmarks:
            return

        active_hand_indices = set()

        # --- Process MediaPipe Results ---
        for hand_idx, landmarks in enumerate(results.hand_landmarks):
            active_hand_indices.add(hand_idx) # Mark hand index as active
            hand_label = results.handedness[hand_idx][0].category_name.lower()

            # Gesture recognition
            gesture_name = "None"
            gesture_confidence = 0.0
            
            if hasattr(results, 'gestures') and results.gestures and len(results.gestures) > hand_idx:
                hand_gestures = results.gestures[hand_idx]
                if hand_gestures:
                    gesture_name = hand_gestures[0].category_name
                    gesture_confidence = round(float(hand_gestures[0].score), 3)
            
            # Data formatting
            screen_coords = []
            world_coords = []

            for i, lm in enumerate(landmarks):
                screen_coords.extend([float(lm.x), float(lm.y), float(lm.z)])
                w_lm = results.hand_world_landmarks[hand_idx][i]
                world_coords.extend([float(w_lm.x), float(w_lm.y), float(w_lm.z)])

            # --- Handle Stream Start ---
            if self.input_handler.is_first_frame and self.input_handler.should_stream:
                formatted_screen_coords = [round(x, 3) for x in screen_coords]
                formatted_world_coords = [round(x, 3) for x in world_coords]

                print("\n--- OSC Streaming Started ---")
                print(f"IP address: {self.ip}\nPort: {self.port}")
                print("\nSample OSC Messages: ")
                print(f"/hand/{hand_idx}/{hand_label}/screen", formatted_screen_coords)
                print(f"/hand/{hand_idx}/{hand_label}/world", formatted_world_coords, "\n")
                self.input_handler.is_first_frame = False
                self.was_streaming = True

            # --- Stream OSC ---
            if self.input_handler.should_stream:
                self.client.send_message(f"/hand/{hand_idx}/{hand_label}/screen", screen_coords)
                self.client.send_message(f"/hand/{hand_idx}/{hand_label}/world", world_coords) 

                previous_gesture = self.last_gestures.get(hand_idx, "None")
                
                # Don't send "None" gesture messages
                if gesture_name != "None": 
                    if gesture_name != previous_gesture: 
                        self.client.send_message(
                            f"/hand/{hand_idx}/{hand_label}/gesture_change", 
                            [gesture_name, gesture_confidence]
                        )
                        print(f"{hand_label.capitalize()} hand gesture: {gesture_name} ({gesture_confidence})")
                    
                    self.last_gestures[hand_idx] = gesture_name

            # --- Print OSC Snapshot ---
            if self.input_handler.should_print:
                print("\n" + "="*50)
                print(f"SNAPSHOT: HAND {hand_idx} COORDINATES")
                print("="*50)
                for i in range(21):
                    start = i * 3
                    x, y, z = screen_coords[start : start+3]
                    print(f"Joint {i:02d} | X: {x:+.4f} | Y: {y:+.4f} | Z: {z:+.4f}")
                print("="*50)

        # Memory cleanup
        stale_indices = [idx for idx in self.last_gestures if idx not in active_hand_indices]
        for idx in stale_indices:
            del self.last_gestures[idx]

        # Reset print snapshot flags
        if self.input_handler.should_print:
            self.input_handler.should_print = False