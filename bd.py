#!/usr/bin/env python3
"""
Bark Detector - A simple decibel threshold-based bark detection system
Monitors audio input and records when sound exceeds configured threshold
"""

import pyaudio
import numpy as np
import wave
import time
import os
import threading
from datetime import datetime
from typing import Optional


class BarkDetector:
    """
    A bark detector that uses decibel threshold to detect barking sounds
    and records audio when barking is detected.
    """
    
    def __init__(self, 
                 threshold_db: float = -30.0,
                 sample_rate: int = 44100,
                 chunk_size: int = 1024,
                 channels: int = 1,
                 quiet_duration: float = 30.0,
                 output_dir: str = "recordings"):
        """
        Initialize the bark detector
        
        Args:
            threshold_db: Decibel threshold for bark detection (default: -30.0)
            sample_rate: Audio sample rate in Hz (default: 44100)
            chunk_size: Audio chunk size for processing (default: 1024)
            channels: Number of audio channels (default: 1 - mono)
            quiet_duration: Duration of quiet time before stopping recording (default: 30.0 seconds)
            output_dir: Directory to save recordings (default: "recordings")
        """
        self.threshold_db = threshold_db
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.quiet_duration = quiet_duration
        self.output_dir = output_dir
        
        # Internal state
        self.is_recording = False
        self.is_running = False
        self.recording_data = []
        self.last_bark_time = 0.0
        self.audio = None
        self.stream = None
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"Bark Detector initialized:")
        print(f"  Threshold: {threshold_db} dB")
        print(f"  Sample Rate: {sample_rate} Hz")
        print(f"  Quiet Duration: {quiet_duration}s")
        print(f"  Output Directory: {output_dir}")
    
    def calculate_decibel_level(self, audio_data: np.ndarray) -> float:
        """
        Calculate the decibel level of audio data
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Decibel level as float
        """
        # Convert to float and normalize
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(audio_float ** 2))
        
        # Avoid log(0) by setting minimum RMS
        rms = max(rms, 1e-10)
        
        # Convert to decibels
        db_level = 20 * np.log10(rms)
        return db_level
    
    def save_recording(self) -> str:
        """
        Save the current recording to a WAV file
        
        Returns:
            Path to the saved file
        """
        if not self.recording_data:
            return ""
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bark_recording_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert recording data to numpy array
        audio_data = np.concatenate(self.recording_data)
        
        # Save as WAV file
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        duration = len(audio_data) / self.sample_rate
        print(f"Recording saved: {filepath} (Duration: {duration:.1f}s)")
        return filepath
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """
        Process a chunk of audio data for bark detection
        
        Args:
            audio_data: Audio data chunk as numpy array
        """
        current_time = time.time()
        db_level = self.calculate_decibel_level(audio_data)
        
        # Check if sound exceeds threshold
        if db_level > self.threshold_db:
            self.last_bark_time = current_time
            
            if not self.is_recording:
                print(f"Bark detected! Starting recording... (Level: {db_level:.1f} dB)")
                self.is_recording = True
                self.recording_data = []
            
            # Add chunk to recording
            self.recording_data.append(audio_data)
            
        elif self.is_recording:
            # Still recording, add chunk even if below threshold
            self.recording_data.append(audio_data)
            
            # Check if quiet period has elapsed
            if current_time - self.last_bark_time > self.quiet_duration:
                print(f"Quiet period detected. Stopping recording...")
                self.save_recording()
                self.is_recording = False
                self.recording_data = []
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for audio stream processing
        """
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert audio data to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Process the audio chunk
        self.process_audio_chunk(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def start(self) -> None:
        """
        Start the bark detector
        """
        if self.is_running:
            print("Bark detector is already running!")
            return
        
        print("Starting bark detector...")
        
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self.audio_callback
            )
            
            self.is_running = True
            self.stream.start_stream()
            
            print("Bark detector started successfully!")
            print("Monitoring for barking sounds...")
            print(f"Press Ctrl+C to stop")
            
        except Exception as e:
            print(f"Error starting bark detector: {e}")
            self.cleanup()
    
    def stop(self) -> None:
        """
        Stop the bark detector
        """
        if not self.is_running:
            return
        
        print("Stopping bark detector...")
        self.is_running = False
        
        # Save any ongoing recording
        if self.is_recording:
            print("Saving final recording...")
            self.save_recording()
            self.is_recording = False
        
        self.cleanup()
        print("Bark detector stopped.")
    
    def cleanup(self) -> None:
        """
        Clean up audio resources
        """
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
    
    def run(self) -> None:
        """
        Run the bark detector (blocking call)
        """
        self.start()
        
        try:
            # Keep the main thread alive
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            self.stop()


def main():
    """
    Main function to run the bark detector
    """
    # Configuration - adjust these values as needed
    config = {
        'threshold_db': -25.0,      # Adjust based on your environment
        'sample_rate': 44100,       # CD quality
        'chunk_size': 1024,         # Good balance of responsiveness and efficiency
        'channels': 1,              # Mono recording
        'quiet_duration': 30.0,     # 30 seconds of quiet before stopping
        'output_dir': 'recordings'  # Directory for saved recordings
    }
    
    print("=" * 50)
    print("Bark Detector v1.0")
    print("=" * 50)
    
    # Create and run bark detector
    detector = BarkDetector(**config)
    detector.run()


if __name__ == "__main__":
    main()