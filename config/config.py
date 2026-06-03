"""Configuration settings for Sonar Test Project"""

# Camera settings
CAMERA_INDEX = 0  # Default webcam
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Audio settings
AUDIO_SAMPLE_RATE = 44100  # Hz
AUDIO_CHUNK_SIZE = 2048
CHIRP_FREQUENCY = 15000  # Hz (ultrasonic)
CHIRP_DURATION = 0.1  # seconds

# Sonar settings
MAX_DISTANCE = 6.0  # 6 meters
SOLIC_SPEED = 343.0  # Speed of sound in m/s at 20°C
MIN_DISTANCE = 0.1  # Minimum detectable distance in meters

# Visualization settings
RADAR_RADIUS = 300  # Pixels
WAVE_COLOR = (0, 255, 0)  # BGR format (Green)
DETECTION_COLOR = (0, 0, 255)  # BGR format (Red)
BACKGROUND_COLOR = (0, 0, 0)  # BGR format (Black)
AUDIO_DETECTION_COLOR = (255, 255, 0)  # BGR format (Cyan - for audio detections)

# Wave settings
WAVE_SPEED = 2  # Pixels per frame
WAVE_THICKNESS = 2
WAVE_MAX_AGE = 100  # Frames before wave disappears

# Distance estimation
DISTANCE_THRESHOLD = 0.5  # Meters
CONFIDENCE_THRESHOLD = 0.6

# Detection mode
USE_AUDIO_SONAR = True  # Enable audio-based sonar
USE_CAMERA_SONAR = True  # Enable camera-based sonar
