"""Updated wave visualizer with audio sonar detection support"""

import cv2
import numpy as np
import math
from config.config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, RADAR_RADIUS, WAVE_COLOR,
    DETECTION_COLOR, BACKGROUND_COLOR, WAVE_SPEED, WAVE_THICKNESS, MAX_DISTANCE,
    AUDIO_DETECTION_COLOR
)


class WaveVisualizer:
    """Creates radar-style sonar wave visualization"""
    
    def __init__(self, width=CAMERA_WIDTH, height=CAMERA_HEIGHT):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.radar_radius = RADAR_RADIUS
        self.active_waves = []  # List of expanding waves
        self.frame_count = 0
        self.audio_detections = []  # Store audio sonar detections
        
    def add_wave(self, distance):
        """
        Add a new sonar wave at detected distance
        
        Args:
            distance: Distance in meters
        """
        # Convert distance to pixel radius
        pixel_distance = (distance / MAX_DISTANCE) * self.radar_radius
        
        wave = {
            'start_radius': 5,
            'current_radius': 5,
            'target_radius': pixel_distance,
            'age': 0,
            'max_age': 60
        }
        self.active_waves.append(wave)
    
    def add_audio_detection(self, distance, angle, confidence):
        """
        Add audio sonar detection
        
        Args:
            distance: Distance in meters
            angle: Angle in degrees (0-360)
            confidence: Confidence level (0-1)
        """
        # Convert distance to pixel radius
        pixel_distance = (distance / MAX_DISTANCE) * self.radar_radius
        
        # Convert angle to radians and calculate x, y
        angle_rad = math.radians(angle)
        x = self.center[0] + pixel_distance * math.cos(angle_rad)
        y = self.center[1] + pixel_distance * math.sin(angle_rad)
        
        detection = {
            'x': x,
            'y': y,
            'distance': distance,
            'angle': angle,
            'confidence': confidence,
            'age': 0,
            'max_age': 30  # Show for 30 frames
        }
        self.audio_detections.append(detection)
    
    def update_waves(self):
        """Update wave animations"""
        for wave in self.active_waves:
            wave['age'] += 1
            # Expand wave
            wave['current_radius'] += WAVE_SPEED
        
        # Remove old waves
        self.active_waves = [w for w in self.active_waves if w['age'] < w['max_age']]
        
        # Update audio detections
        for detection in self.audio_detections:
            detection['age'] += 1
        
        self.audio_detections = [d for d in self.audio_detections if d['age'] < d['max_age']]
    
    def draw_radar_background(self, frame):
        """
        Draw radar grid and circles
        
        Args:
            frame: Frame to draw on
        """
        # Draw concentric circles
        circle_spacing = self.radar_radius // 4
        for i in range(1, 5):
            radius = i * circle_spacing
            cv2.circle(frame, self.center, radius, (100, 100, 100), 1)
        
        # Draw crosshairs (N, S, E, W)
        cv2.line(frame, (self.center[0] - 20, self.center[1]), 
                 (self.center[0] + 20, self.center[1]), (100, 100, 100), 1)
        cv2.line(frame, (self.center[0], self.center[1] - 20), 
                 (self.center[0], self.center[1] + 20), (100, 100, 100), 1)
        
        # Draw outer circle
        cv2.circle(frame, self.center, self.radar_radius, (150, 150, 150), 2)
        
        # Add distance labels
        for i in range(1, 5):
            dist_label = f"{(i * MAX_DISTANCE / 4):.1f}m"
            y = self.center[1] - (i * circle_spacing)
            cv2.putText(frame, dist_label, (self.center[0] + 10, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        # Add direction labels
        cv2.putText(frame, "N", (self.center[0] - 5, self.center[1] - self.radar_radius - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        cv2.putText(frame, "S", (self.center[0] - 5, self.center[1] + self.radar_radius + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        cv2.putText(frame, "E", (self.center[0] + self.radar_radius + 5, self.center[1] + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        cv2.putText(frame, "W", (self.center[0] - self.radar_radius - 15, self.center[1] + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    def draw_waves(self, frame, detected_distances):
        """
        Draw sonar waves and detection points
        
        Args:
            frame: Frame to draw on
            detected_distances: List of recently detected distances
        """
        self.update_waves()
        
        # Draw expanding waves
        for wave in self.active_waves:
            if wave['current_radius'] <= self.radar_radius:
                cv2.circle(frame, self.center, int(wave['current_radius']),
                          WAVE_COLOR, WAVE_THICKNESS)
                
                # Fade effect
                fade_factor = 1.0 - (wave['age'] / wave['max_age'])
                color = tuple(int(c * fade_factor) for c in WAVE_COLOR)
        
        # Draw detection points
        for detection in detected_distances:
            distance = detection['distance']
            confidence = detection['confidence']
            
            # Convert distance to pixel radius
            pixel_distance = (distance / MAX_DISTANCE) * self.radar_radius
            
            # Vary angle based on time for scanning effect
            angle = (self.frame_count * 2) % 360
            angle_rad = math.radians(angle)
            
            x = self.center[0] + pixel_distance * math.cos(angle_rad)
            y = self.center[1] + pixel_distance * math.sin(angle_rad)
            
            # Draw detection point
            size = int(5 * confidence)
            cv2.circle(frame, (int(x), int(y)), size, DETECTION_COLOR, -1)
    
    def draw_audio_detections(self, frame):
        """
        Draw audio sonar detections on radar
        
        Args:
            frame: Frame to draw on
        """
        for detection in self.audio_detections:
            x = int(detection['x'])
            y = int(detection['y'])
            confidence = detection['confidence']
            distance = detection['distance']
            angle = detection['angle']
            
            # Size based on confidence
            size = int(8 * confidence)
            
            # Fade out as age increases
            fade_factor = 1.0 - (detection['age'] / detection['max_age'])
            color_faded = tuple(int(c * fade_factor) for c in AUDIO_DETECTION_COLOR)
            
            # Draw point
            cv2.circle(frame, (x, y), size, color_faded, -1)
            
            # Draw line from center to detection
            cv2.line(frame, self.center, (x, y), color_faded, 1)
            
            # Draw info label
            info = f"{distance:.2f}m"
            cv2.putText(frame, info, (x + 10, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, color_faded, 1)
    
    def draw_info(self, frame, fps=0, avg_distance=None, audio_detection_count=0):
        """
        Draw information overlay
        
        Args:
            frame: Frame to draw on
            fps: Frames per second
            avg_distance: Average detected distance
            audio_detection_count: Number of active audio detections
        """
        y_offset = 30
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        if avg_distance is not None:
            cv2.putText(frame, f"Distance: {avg_distance:.2f}m", (10, y_offset + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.putText(frame, f"Waves: {len(self.active_waves)}", (10, y_offset + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.putText(frame, f"Audio Detections: {audio_detection_count}", (10, y_offset + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, AUDIO_DETECTION_COLOR, 2)
    
    def create_display(self, camera_frame, detected_distances, fps=0, avg_distance=None):
        """
        Create complete visualization display
        
        Args:
            camera_frame: Original camera frame
            detected_distances: List of detected distances
            fps: Current FPS
            avg_distance: Averaged distance
            
        Returns:
            display_frame: Final visualization frame
        """
        display_frame = camera_frame.copy()
        
        # Draw radar background
        self.draw_radar_background(display_frame)
        
        # Draw waves and detections
        self.draw_waves(display_frame, detected_distances)
        
        # Draw audio sonar detections
        self.draw_audio_detections(display_frame)
        
        # Draw info
        self.draw_info(display_frame, fps, avg_distance, len(self.audio_detections))
        
        self.frame_count += 1
        
        return display_frame
