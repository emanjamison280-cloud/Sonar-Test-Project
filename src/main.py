"""Main application entry point for Sonar Test Project"""

import cv2
import time
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera_handler import CameraHandler
from sonar_detector import SonarDetector
from wave_visualizer import WaveVisualizer
from config.config import BACKGROUND_COLOR


def main():
    """Main application loop"""
    print("=" * 50)
    print("Sonar Test Project - Camera-Based Detection")
    print("=" * 50)
    print("Controls:")
    print("  q - Quit")
    print("  SPACE - Force wave trigger")
    print("=" * 50)
    
    # Initialize components
    try:
        camera = CameraHandler()
        sonar = SonarDetector()
        visualizer = WaveVisualizer()
    except Exception as e:
        print(f"Error initializing components: {e}")
        return
    
    # Timing variables
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    print("Starting camera stream... (Press 'q' to quit)\n")
    
    try:
        while True:
            # Capture frame
            frame, success = camera.get_frame()
            if not success:
                print("Error: Failed to capture frame")
                break
            
            # Preprocess frame
            processed_frame = camera.preprocess_frame(frame)
            
            # Detect sonar distance
            distance, confidence = sonar.estimate_distance(processed_frame)
            
            # Add detection to sonar history
            if distance is not None:
                sonar.add_detection(distance, confidence)
                visualizer.add_wave(distance)
                print(f"Detection - Distance: {distance:.2f}m, Confidence: {confidence:.2%}")
            
            # Get average distance
            avg_distance = sonar.get_average_distance(window_size=5)
            
            # Create visualization
            display_frame = visualizer.create_display(
                processed_frame,
                sonar.get_detected_distances(),
                fps,
                avg_distance
            )
            
            # Display
            cv2.imshow('Sonar Detection - Radar View', display_frame)
            cv2.imshow('Camera Input', processed_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord(' '):
                # Force wave trigger
                if avg_distance:
                    visualizer.add_wave(avg_distance)
                    print(f"Wave triggered at {avg_distance:.2f}m")
            
            # Calculate FPS
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        camera.release()
        cv2.destroyAllWindows()
        print("Application closed.")


if __name__ == "__main__":
    main()
