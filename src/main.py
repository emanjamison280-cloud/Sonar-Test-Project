"""Updated main application with audio sonar integration"""

import cv2
import time
import sys
import os
import numpy as np

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera_handler import CameraHandler
from sonar_detector import SonarDetector
from wave_visualizer import WaveVisualizer
from audio_sonar import AudioSonarDetector
from config.config import BACKGROUND_COLOR, USE_AUDIO_SONAR, USE_CAMERA_SONAR


def main():
    """Main application loop"""
    print("=" * 60)
    print("Sonar Test Project - Audio & Camera Detection System")
    print("=" * 60)
    print("Controls:")
    print("  q - Quit")
    print("  SPACE - Force wave trigger")
    print("  a - Toggle audio sonar")
    print("  c - Toggle camera sonar")
    print("=" * 60)
    
    # Initialize components
    try:
        if USE_CAMERA_SONAR:
            camera = CameraHandler()
            sonar = SonarDetector()
        else:
            camera = None
            sonar = None
        
        visualizer = WaveVisualizer()
        
        if USE_AUDIO_SONAR:
            try:
                audio_sonar = AudioSonarDetector()
                audio_sonar.start()
                print("Audio sonar initialized and started")
            except Exception as e:
                print(f"Warning: Could not initialize audio sonar: {e}")
                print("Continuing with camera sonar only...")
                audio_sonar = None
        else:
            audio_sonar = None
            
    except Exception as e:
        print(f"Error initializing components: {e}")
        return
    
    # Timing variables
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    print("Starting sonar system... (Press 'q' to quit)\n")
    
    audio_sonar_enabled = USE_AUDIO_SONAR and audio_sonar is not None
    camera_sonar_enabled = USE_CAMERA_SONAR and camera is not None
    
    try:
        while True:
            # Create black canvas if no camera
            if camera_sonar_enabled:
                frame, success = camera.get_frame()
                if not success:
                    print("Error: Failed to capture frame")
                    break
                processed_frame = camera.preprocess_frame(frame)
            else:
                processed_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Camera-based sonar detection
            if camera_sonar_enabled and sonar:
                distance, confidence = sonar.estimate_distance(processed_frame)
                
                if distance is not None:
                    sonar.add_detection(distance, confidence)
                    visualizer.add_wave(distance)
                    print(f"[CAMERA] Detection - Distance: {distance:.2f}m, Confidence: {confidence:.2%}")
            
            # Audio-based sonar detection
            if audio_sonar_enabled:
                try:
                    audio_detections = audio_sonar.get_detections()
                    for detection in audio_detections:
                        visualizer.add_audio_detection(
                            detection['distance'],
                            detection['angle'],
                            detection['confidence']
                        )
                        print(f"[AUDIO] Detection - Distance: {detection['distance']:.2f}m, "
                              f"Angle: {detection['angle']:.1f}°, Confidence: {detection['confidence']:.2%}")
                except Exception as e:
                    print(f"Error reading audio detections: {e}")
            
            # Get average distance
            if camera_sonar_enabled and sonar:
                avg_distance = sonar.get_average_distance(window_size=5)
                detected_distances = sonar.get_detected_distances()
            else:
                avg_distance = None
                detected_distances = []
            
            # Create visualization
            display_frame = visualizer.create_display(
                processed_frame,
                detected_distances,
                fps,
                avg_distance
            )
            
            # Display
            cv2.imshow('Sonar Detection - Radar View', display_frame)
            if camera_sonar_enabled:
                cv2.imshow('Camera Input', processed_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord(' '):
                # Force wave trigger
                if camera_sonar_enabled and avg_distance:
                    visualizer.add_wave(avg_distance)
                    print(f"Wave triggered at {avg_distance:.2f}m")
            elif key == ord('a'):
                # Toggle audio sonar
                if audio_sonar:
                    audio_sonar_enabled = not audio_sonar_enabled
                    status = "enabled" if audio_sonar_enabled else "disabled"
                    print(f"Audio sonar {status}")
            elif key == ord('c'):
                # Toggle camera sonar
                camera_sonar_enabled = not camera_sonar_enabled
                status = "enabled" if camera_sonar_enabled else "disabled"
                print(f"Camera sonar {status}")
            
            # Calculate FPS
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        if camera_sonar_enabled and camera:
            camera.release()
        if audio_sonar_enabled and audio_sonar:
            audio_sonar.stop()
        cv2.destroyAllWindows()
        print("Application closed.")


if __name__ == "__main__":
    main()
