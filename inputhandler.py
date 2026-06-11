import time
import global_vars

class InputHandler:
    def __init__(self, print_interval=0.5):
        self.last_print_time = 0
        self.print_interval = print_interval
        self.should_print = False # gate allows OSC to print to terminal
        self.should_stream = False # gate allows OSC to stream
        self.is_first_frame = False

    def process_key(self, key_code):

        # ENTER (Shutdown)
        if key_code == 13 or key_code == 10:
            print("\nShutting down...")
            global_vars.KILL_THREADS = True
        
        # SPACE (Begin Streaming)
        # Eventually should separate OSC and CSV commands
        elif key_code == 32:
            self.should_stream = not self.should_stream
            self.is_first_frame = self.should_stream

        # s (Print Snapshot)
        elif key_code == 115:
            current_time = time.time()
            if current_time - self.last_print_time >= self.print_interval:
                self.last_print_time = current_time
                self.should_print = True 