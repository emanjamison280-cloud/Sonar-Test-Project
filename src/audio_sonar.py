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
            
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        # Linear frequency sweep
        chirp = np.sin(2 * np.pi * (start_freq * t + (end_freq - start_freq) * t**2 / (2 * duration)))
        # Apply envelope to avoid clicks
        envelope = np.hann(len(chirp))
        return (chirp * envelope * 0.3).astype(np.float32)  # Reduce volume for safety
    
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
            detections: List of (distance, angle, confidence) tuples
        """
        if self.stream_input is None:
            return []
        
        detections = []
        listen_samples = int(self.sample_rate * self.listen_duration)
        
        try:
            # Record audio during listen window
            frames = []
            for _ in range(listen_samples // self.chunk_size + 1):
                data = self.stream_input.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                frames.append(audio_data)
                self.audio_buffer.extend(audio_data)
            
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
            detections: List of (distance, angle, confidence) tuples
        """
        detections = []
        
        # Apply high-pass filter to focus on chirp frequency
        filtered = self._bandpass_filter(audio_data, 8000, 22000)
        
        # Compute spectrogram to find chirp returns
        # Look for energy spikes at chirp frequency
        fft = np.abs(np.fft.fft(filtered))
        freqs = np.fft.fftfreq(len(fft), 1/self.sample_rate)
        
        # Find peaks in the chirp frequency range
        chirp_range = np.where((freqs > 10000) & (freqs < 20000))[0]
        if len(chirp_range) > 0:
            peak_idx = chirp_range[np.argmax(fft[chirp_range])]
            peak_energy = fft[peak_idx]
            
            # Detect echo peaks using correlation
            echo_distances = self._detect_echo_delays(filtered)
            
            for delay in echo_distances:
                if delay > 0:  # Valid echo
                    # Convert time delay to distance
                    distance = (delay * SOLIC_SPEED) / 2  # Divide by 2 for round trip
                    distance = np.clip(distance, MIN_DISTANCE, MAX_DISTANCE)
                    
                    # Estimate confidence based on energy
                    confidence = min(1.0, peak_energy / np.max(fft) if np.max(fft) > 0 else 0)
                    
                    # Random angle for now (can be improved with multi-mic array)
                    angle = np.random.uniform(0, 360)
                    
                    detections.append({
                        'distance': distance,
                        'angle': angle,
                        'confidence': confidence
                    })
        
        return detections
    
    def _bandpass_filter(self, signal, low_freq, high_freq):
        """Apply bandpass filter to audio signal"""
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(fft), 1/self.sample_rate)
        
        # Create bandpass mask
        mask = (np.abs(freqs) > low_freq) & (np.abs(freqs) < high_freq)
        fft_filtered = fft.copy()
        fft_filtered[~mask] = 0
        
        return np.real(np.fft.ifft(fft_filtered))
    
    def _detect_echo_delays(self, signal):
        """
        Detect echo delays by finding peaks in correlation
        
        Returns:
            delays: List of time delays (in seconds) for detected echoes
        """
        delays = []
        
        # Cross-correlate signal with itself to find repeating patterns (echoes)
        reference = signal[:int(self.sample_rate * self.chirp_duration)]
        if len(reference) < 100:
            return delays
        
        correlation = np.correlate(signal, reference, mode='same')
        
        # Normalize
        correlation = correlation / np.max(np.abs(correlation)) if np.max(np.abs(correlation)) > 0 else correlation
        
        # Find peaks (echoes) with threshold
        threshold = 0.3
        peaks = np.where(correlation > threshold)[0]
        
        # Convert peak indices to time delays
        for peak in peaks:
            if abs(peak - len(signal)//2) > int(self.sample_rate * 0.01):  # Skip center (original signal)
                delay_samples = abs(peak - len(signal)//2)
                delay_time = delay_samples / self.sample_rate
                delays.append(delay_time)
        
        # Keep only unique delays (remove duplicates)
        return list(set([round(d, 4) for d in delays]))
    
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
                time.sleep(0.05)  # Small delay after chirp
                
                # Listen for echo
                detections = self.listen_for_echo()
                
                # Add valid detections
                for detection in detections:
                    self.add_detection(detection)
                
                # Wait before next chirp
                time.sleep(0.2)
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
        if self.stream_input:
            self.stream_input.stop_stream()
            self.stream_input.close()
        if self.stream_output:
            self.stream_output.stop_stream()
            self.stream_output.close()
        self.p.terminate()
        print("Audio sonar stopped")
