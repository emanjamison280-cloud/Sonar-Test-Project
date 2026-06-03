"""Audio-based sonar detection using ultrasonic chirps and microphone"""

import numpy as np
import pyaudio
import threading
from collections import deque
from config.config import MAX_DISTANCE, MIN_DISTANCE, SOLIC_SPEED
import time


class AudioSonarDetector:
    """Detects objects using ultrasonic chirps and microphone echo detection"""
    
    def __init__(self, sample_rate=44100, chunk_size=2048):
        """
        Initialize audio sonar detector
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Size of audio chunks to process
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.chirp_frequency = 15000  # 15 kHz ultrasonic chirp
        self.chirp_duration = 0.1  # 100ms chirp
        self.listen_duration = 0.5  # Listen for 500ms for echo
        
        self.detections = deque(maxlen=30)
        self.audio_buffer = deque(maxlen=int(sample_rate * self.listen_duration))
        
        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.stream_input = None
        self.stream_output = None
        self.is_listening = False
        self.detection_lock = threading.Lock()
        
        self._initialize_streams()
        
    def _initialize_streams(self):
        """Initialize input and output audio streams"""
        try:
            # Output stream for emitting chirps
            self.stream_output = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Input stream for listening to echoes
            self.stream_input = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print("Audio streams initialized successfully")
        except Exception as e:
            print(f"Error initializing audio streams: {e}")
    
    def generate_chirp(self, start_freq=10000, end_freq=20000, duration=None):
        """
        Generate a chirp (frequency sweep) signal
        
        Args:
            start_freq: Starting frequency (Hz)
            end_freq: Ending frequency (Hz)
            duration: Duration in seconds
            
        Returns:
            chirp_signal: Numpy array of audio samples
        """
        if duration is None:
            duration = self.chirp_duration
            
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        
        # Linear frequency sweep
        chirp = np.sin(2 * np.pi * (start_freq * t + (end_freq - start_freq) * t**2 / (2 * duration)))
        
        # Apply simple envelope (fade in/out)
        envelope = np.ones(len(chirp))
        fade_samples = int(num_samples * 0.1)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        return (chirp * envelope * 0.3).astype(np.float32)
    
    def emit_chirp(self):
        """Emit a chirp signal"""
        if self.stream_output is None:
            return
            
        chirp = self.generate_chirp()
        try:
            self.stream_output.write(chirp.tobytes())
        except Exception as e:
            print(f"Error emitting chirp: {e}")
    
    def listen_for_echo(self):
        """
        Listen for echoes and detect distances
        
        Returns:
            detections: List of detection dicts
        """
        if self.stream_input is None:
            return []
        
        detections = []
        listen_samples = int(self.sample_rate * self.listen_duration)
        
        try:
            # Record audio during listen window
            frames = []
            for _ in range(listen_samples // self.chunk_size + 1):
                try:
                    data = self.stream_input.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    frames.append(audio_data)
                except:
                    continue
            
            if frames:
                recorded = np.concatenate(frames)
                detections = self._analyze_echo(recorded)
        except Exception as e:
            print(f"Error listening for echo: {e}")
        
        return detections
    
    def _analyze_echo(self, audio_data):
        """
        Analyze recorded audio for echoes
        
        Args:
            audio_data: Recorded audio samples
            
        Returns:
            detections: List of detection dicts
        """
        detections = []
        
        try:
            # Simple energy detection
            energy = np.sum(np.abs(audio_data))
            
            if energy < 0.01:  # No significant audio
                return detections
            
            # Detect peaks in the signal
            rms = np.sqrt(np.mean(audio_data**2))
            
            if rms > 0.05:  # Detect significant signal
                # Calculate a rough distance estimate based on signal strength
                # Stronger signal = closer object
                distance = MAX_DISTANCE * (1.0 - min(1.0, rms / 0.3))
                distance = max(MIN_DISTANCE, distance)
                
                confidence = min(1.0, rms / 0.3)
                
                # Random angle (can be improved with multiple mics)
                angle = np.random.uniform(0, 360)
                
                detections.append({
                    'distance': distance,
                    'angle': angle,
                    'confidence': confidence
                })
        
        except Exception as e:
            print(f"Error analyzing echo: {e}")
        
        return detections
    
    def get_detections(self):
        """Get current detections"""
        with self.detection_lock:
            return list(self.detections)
    
    def add_detection(self, detection):
        """Add a new detection"""
        with self.detection_lock:
            self.detections.append(detection)
    
    def run_detection_loop(self):
        """Run continuous detection in background thread"""
        self.is_listening = True
        while self.is_listening:
            try:
                # Emit chirp
                self.emit_chirp()
                time.sleep(0.05)
                
                # Listen for echo
                detections = self.listen_for_echo()
                
                # Add valid detections
                for detection in detections:
                    self.add_detection(detection)
                
                # Wait before next chirp
                time.sleep(0.3)
            except Exception as e:
                print(f"Error in detection loop: {e}")
    
    def start(self):
        """Start background detection thread"""
        self.thread = threading.Thread(target=self.run_detection_loop, daemon=True)
        self.thread.start()
        print("Audio sonar started")
    
    def stop(self):
        """Stop detection and cleanup"""
        self.is_listening = False
        try:
            if self.stream_input:
                self.stream_input.stop_stream()
                self.stream_input.close()
            if self.stream_output:
                self.stream_output.stop_stream()
                self.stream_output.close()
            self.p.terminate()
        except:
            pass
        print("Audio sonar stopped")
