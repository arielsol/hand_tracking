import time
import global_vars
from body import HandThread
import sys

def main():
    body_pose_thread = HandThread()
    body_pose_thread.start()

    try:
        while not global_vars.KILL_THREADS:
            time.sleep(0.1)
    except KeyboardInterrupt:
        global_vars.KILL_THREADS = True

    time.sleep(0.5) # make sure threads finish closing
    
    print("\nExiting.\n")
    sys.exit()

if __name__ == "__main__":
    main()