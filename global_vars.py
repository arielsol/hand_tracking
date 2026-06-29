# Internally used, don't mind this.
KILL_THREADS = False

# Toggle this in order to view how your WebCam is being interpreted (reduces performance).
DEBUG = False

# To switch cameras. Sometimes takes a while.
WEBCAM_INDEX = 0

# Settings do not universally apply, not all WebCams support all frame rates and resolutions
USE_CUSTOM_CAM_SETTINGS = False
FPS = 60
WIDTH = 1920
HEIGHT = 1080

# [0, 2] Higher numbers are more precise, but also cost more performance. Good environment conditions = 1, otherwise 2.
MODEL_COMPLEXITY = 2

# [1, 4] recommended for CPU
NUMBER_HANDS = 2

# To recognize gestures upside down. For use with certain camera angles
INVERT_GESTURES = True

# OSC Settings
OSC_IP_ADDRESS = "127.0.0.1"
OSC_PORT = 3131

# Limits how many samples per second can be written to CSV
SAMPLES_PER_SECOND = 10