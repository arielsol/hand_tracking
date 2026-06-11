from pythonosc import udp_client

class OSCHandler:
    def __init__(self, input_handler):
        self.input_handler = input_handler
        self.was_streaming = False

        # ---------- OSC Send Setup ----------
        self.ip = "127.0.0.1"
        self.port = 3131
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)

    def process_hand_data(self, results):
        if not results.hand_landmarks:
            return

        for hand_idx, landmarks in enumerate(results.hand_landmarks):
            hand_label = results.handedness[hand_idx][0].category_name.lower()
            
            screen_coords = []
            world_coords = []

            # Flatten out the coordinate matrices
            for i, lm in enumerate(landmarks):
                screen_coords.extend([float(lm.x), float(lm.y), float(lm.z)])
                
                w_lm = results.hand_world_landmarks[hand_idx][i]
                world_coords.extend([float(w_lm.x), float(w_lm.y), float(w_lm.z)])

            # --- Stream OSC ---
            if self.input_handler.should_stream:
                self.client.send_message(f"/hand/{hand_idx}/{hand_label}/screen", screen_coords)
                self.client.send_message(f"/hand/{hand_idx}/{hand_label}/world", world_coords) 
            elif self.was_streaming:
                print("--- OSC Streaming Complete ---")
                self.input_handler.is_first_frame = False
                self.was_streaming = False

            # Print first frame sample
            if self.input_handler.is_first_frame:
                formatted_screen_coords = [round(x, 3) for x in screen_coords]
                formatted_world_coords = [round(x, 3) for x in world_coords]

                print("\n--- OSC Streaming Started ---")
                print(f"IP address: {self.ip}\nPort: {self.port}")
                print("\nSample OSC Messages: ")
                print(f"/hand/{hand_idx}/{hand_label}/screen", formatted_screen_coords)
                print(f"/hand/{hand_idx}/{hand_label}/world", formatted_world_coords, "\n")
                self.input_handler.is_first_frame = False
                self.was_streaming = True
            
            # --- Print OSC Snapshot ---
            if self.input_handler.should_print:
                print("\n" + "="*50)
                print(f"SNAPSHOT: HAND {hand_idx} COORDINATES")
                print("="*50)
                
                # Print in a readable grid (Joint Index: X, Y, Z)
                for i in range(21):
                    start = i * 3
                    x, y, z = screen_coords[start : start+3]
                    print(f"Joint {i:02d} | X: {x:+.4f} | Y: {y:+.4f} | Z: {z:+.4f}")
                
                print("="*50)

        # Reset the print snapshot flag ONLY AFTER processing all tracked hands
        if self.input_handler.should_print:
            self.input_handler.should_print = False