#!/usr/bin/env python3
"""
Bark Detector - Advanced YAMNet ML-based bark detection system
Monitors audio input and records when barking is detected using machine learning
"""

# Suppress TensorFlow info/debug messages
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=no INFO, 2=no INFO/WARNING, 3=no INFO/WARNING/ERROR

import pyaudio
import numpy as np
import wave
import time
import os
import threading
import logging
import csv
import io
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
import tensorflow as tf
import tensorflow_hub as hub
import librosa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bark_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class BarkEvent:
    """Represents a detected barking event."""
    start_time: float
    end_time: float
    confidence: float
    intensity: float = 0.0


@dataclass
class BarkingSession:
    """Represents a continuous barking session."""
    start_time: float
    end_time: float
    events: List[BarkEvent]
    total_barks: int
    total_duration: float
    avg_confidence: float
    peak_confidence: float
    barks_per_second: float
    intensity: float = 0.0


class AdvancedBarkDetector:
    """Advanced bark detector using YAMNet with comprehensive analysis."""
    
    def __init__(self, 
                 sensitivity: float = 0.05,
                 sample_rate: int = 16000,
                 chunk_size: int = 1024,
                 channels: int = 1,
                 quiet_duration: float = 30.0,
                 session_gap_threshold: float = 10.0,
                 output_dir: str = "recordings"):
        """Initialize the advanced bark detector."""
        self.sensitivity = sensitivity
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.quiet_duration = quiet_duration
        self.session_gap_threshold = session_gap_threshold
        self.output_dir = output_dir
        
        # YAMNet model components
        self.yamnet_model = None
        self.class_names = None
        self.bark_class_indices = []
        
        # Session tracking
        self.session_start_time: Optional[datetime] = None
        self.session_bark_count = 0
        self.current_session_events = []
        self.current_session_barks = []
        
        # Audio processing
        self.is_recording = False
        self.is_running = False
        self.recording_data = []
        self.last_bark_time = 0.0
        self.audio = None
        self.stream = None
        self.audio_buffer = []
        
        # Analysis buffer for event detection
        self.analysis_buffer = []
        self.detection_buffer_duration = 1.0  # 1 second for analysis
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize YAMNet
        self._load_yamnet_model()
        
        logger.info(f"Advanced Bark Detector initialized:")
        logger.info(f"  Sensitivity: {sensitivity}")
        logger.info(f"  Sample Rate: {sample_rate} Hz")
        logger.info(f"  Session Gap Threshold: {session_gap_threshold}s")
        logger.info(f"  Quiet Duration: {quiet_duration}s")
        logger.info(f"  Output Directory: {output_dir}")
    
    def _show_download_progress(self, message: str, stop_event: threading.Event) -> None:
        """Show download progress indicator."""
        print(f"\r{message}", end="", flush=True)
        dot_count = 0
        while not stop_event.is_set():
            time.sleep(0.5)
            if not stop_event.is_set():
                print(".", end="", flush=True)
                dot_count += 1
                if dot_count >= 6:
                    print(f"\r{message}", end="", flush=True)
                    dot_count = 0
    
    def _load_yamnet_model(self) -> None:
        """Load YAMNet model with advanced class detection."""
        try:
            logger.info("Downloading YAMNet model (this may take a few minutes on first run)...")
            
            # Show progress indicator
            stop_event = threading.Event()
            progress_thread = threading.Thread(
                target=self._show_download_progress, 
                args=("Downloading YAMNet model", stop_event)
            )
            progress_thread.daemon = True
            progress_thread.start()
            
            # Load YAMNet model
            self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
            
            # Stop progress indicator
            stop_event.set()
            progress_thread.join(timeout=1.0)
            print("\r" + " " * 60 + "\r", end="", flush=True)
            
            logger.info("YAMNet model downloaded successfully!")
            logger.info("Loading class names...")
            
            # Load class names using model's built-in method
            class_map_path = self.yamnet_model.class_map_path().numpy()
            self.class_names = self._load_class_names(class_map_path)
            
            # Find bark-related classes
            self._find_bark_classes()
            
            logger.info(f"YAMNet model loaded successfully!")
            logger.info(f"Model supports {len(self.class_names)} audio classes")
            logger.info(f"Found {len(self.bark_class_indices)} bark-related classes")
            
        except Exception as e:
            logger.error(f"Error loading YAMNet model: {e}")
            raise
    
    def _load_class_names(self, class_map_path: bytes) -> List[str]:
        """Load class names from YAMNet's class map."""
        try:
            csv_file_path = class_map_path.decode('utf-8')
            logger.debug(f"Loading class names from: {csv_file_path}")
            
            with open(csv_file_path, 'r') as f:
                content = f.read()
            
            class_names = []
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            
            # Skip header row if present
            if rows and rows[0] and rows[0][0] == 'index':
                rows = rows[1:]
            
            for row in rows:
                if len(row) >= 3:
                    class_names.append(row[2])  # Display name
                else:
                    logger.warning(f"Unexpected row format: {row}")
            
            logger.debug(f"Loaded {len(class_names)} class names")
            return class_names
            
        except Exception as e:
            logger.error(f"Error loading class names: {e}")
            raise
    
    def _find_bark_classes(self):
        """Find class indices related to dog barking."""
        bark_keywords = [
            'dog', 'bark', 'barking', 'bow-wow', 'yip', 'yelp', 
            'whimper', 'howl', 'growl', 'animal'
        ]
        
        self.bark_class_indices = []
        logger.debug(f"Searching through {len(self.class_names)} classes for bark-related sounds")
        
        for i, class_name in enumerate(self.class_names):
            if any(keyword.lower() in class_name.lower() for keyword in bark_keywords):
                self.bark_class_indices.append(i)
                logger.debug(f"Found bark-related class: {i} - {class_name}")
        
        if len(self.bark_class_indices) == 0:
            logger.warning("No bark-related classes found in YAMNet model")
    
    def _detect_barks_in_buffer(self, audio_chunk: np.ndarray) -> List[BarkEvent]:
        """Detect barks in audio buffer using YAMNet."""
        try:
            # Normalize audio to [-1, 1] range
            waveform = audio_chunk.astype(np.float32)
            if np.max(np.abs(waveform)) > 0:
                waveform = waveform / np.max(np.abs(waveform))
            
            # Ensure minimum length for YAMNet
            min_samples = int(0.975 * self.sample_rate)
            if len(waveform) < min_samples:
                waveform = np.pad(waveform, (0, min_samples - len(waveform)))
            
            # Run YAMNet inference
            scores, embeddings, spectrogram = self.yamnet_model(waveform)
            
            # Get bark-related scores
            bark_scores = self._get_bark_scores(scores.numpy())
            
            # Convert scores to events
            bark_events = self._scores_to_events(bark_scores)
            
            return bark_events
            
        except Exception as e:
            logger.error(f"Error in bark detection: {e}")
            return []
    
    def _get_bark_scores(self, scores: np.ndarray) -> np.ndarray:
        """Extract bark-related confidence scores."""
        if len(self.bark_class_indices) == 0:
            return np.zeros(scores.shape[0])
        
        # Get scores for bark-related classes
        bark_class_scores = scores[:, self.bark_class_indices]
        
        # Take maximum score across all bark classes for each time frame
        bark_scores = np.max(bark_class_scores, axis=1)
        
        return bark_scores
    
    def _scores_to_events(self, bark_scores: np.ndarray) -> List[BarkEvent]:
        """Convert YAMNet scores to bark events."""
        # YAMNet produces one prediction every 0.48 seconds
        time_per_frame = 0.48
        
        # Find frames above threshold
        bark_frames = np.where(bark_scores > self.sensitivity)[0]
        
        if len(bark_frames) == 0:
            return []
        
        # Group consecutive frames into events
        events = []
        current_start = bark_frames[0]
        current_end = bark_frames[0]
        
        for i in range(1, len(bark_frames)):
            if bark_frames[i] == current_end + 1:
                current_end = bark_frames[i]
            else:
                # Create event from current group
                start_time = current_start * time_per_frame
                end_time = (current_end + 1) * time_per_frame
                confidence = np.mean(bark_scores[current_start:current_end + 1])
                
                events.append(BarkEvent(
                    start_time=start_time,
                    end_time=end_time,
                    confidence=confidence
                ))
                
                current_start = bark_frames[i]
                current_end = bark_frames[i]
        
        # Add final event
        start_time = current_start * time_per_frame
        end_time = (current_end + 1) * time_per_frame
        confidence = np.mean(bark_scores[current_start:current_end + 1])
        
        events.append(BarkEvent(
            start_time=start_time,
            end_time=end_time,
            confidence=confidence
        ))
        
        return events
    
    def _calculate_event_intensity(self, audio_data: np.ndarray, event: BarkEvent) -> float:
        """Calculate intensity for a bark event."""
        try:
            start_sample = int(event.start_time * self.sample_rate)
            end_sample = int(event.end_time * self.sample_rate)
            
            if start_sample >= len(audio_data) or end_sample > len(audio_data):
                return event.confidence * 0.5  # Fallback to confidence-based intensity
            
            event_audio = audio_data[start_sample:end_sample]
            
            if len(event_audio) == 0:
                return event.confidence * 0.5
            
            # Calculate RMS volume
            rms = np.sqrt(np.mean(event_audio ** 2))
            volume_intensity = min(1.0, rms * 10)  # Scale RMS to reasonable range
            
            # Combine volume and confidence
            intensity = 0.6 * volume_intensity + 0.4 * event.confidence
            return min(1.0, max(0.0, intensity))
            
        except Exception as e:
            logger.warning(f"Error calculating event intensity: {e}")
            return event.confidence * 0.5
    
    def _group_events_into_sessions(self, events: List[BarkEvent]) -> List[BarkingSession]:
        """Group bark events into sessions."""
        if not events:
            return []
        
        # Sort events by start time
        sorted_events = sorted(events, key=lambda x: x.start_time)
        
        sessions = []
        current_session_events = [sorted_events[0]]
        
        for i in range(1, len(sorted_events)):
            current_event = sorted_events[i]
            last_event = current_session_events[-1]
            
            # Check gap between events
            gap = current_event.start_time - last_event.end_time
            
            if gap <= self.session_gap_threshold:
                current_session_events.append(current_event)
            else:
                # Create session and start new one
                session = self._create_session(current_session_events)
                sessions.append(session)
                current_session_events = [current_event]
        
        # Add final session
        if current_session_events:
            session = self._create_session(current_session_events)
            sessions.append(session)
        
        return sessions
    
    def _create_session(self, events: List[BarkEvent]) -> BarkingSession:
        """Create a barking session from events."""
        start_time = min(event.start_time for event in events)
        end_time = max(event.end_time for event in events)
        total_duration = sum(event.end_time - event.start_time for event in events)
        session_duration = end_time - start_time
        
        confidences = [event.confidence for event in events]
        avg_confidence = np.mean(confidences)
        peak_confidence = np.max(confidences)
        
        barks_per_second = len(events) / session_duration if session_duration > 0 else 0
        
        # Calculate session intensity
        intensities = [event.intensity for event in events if event.intensity > 0]
        avg_intensity = np.mean(intensities) if intensities else avg_confidence
        
        return BarkingSession(
            start_time=start_time,
            end_time=end_time,
            events=events,
            total_barks=len(events),
            total_duration=total_duration,
            avg_confidence=avg_confidence,
            peak_confidence=peak_confidence,
            barks_per_second=barks_per_second,
            intensity=avg_intensity
        )
    
    def save_recording(self) -> str:
        """Save recording with comprehensive analysis."""
        if not self.recording_data:
            return ""
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bark_recording_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert recording data
        audio_data = np.concatenate(self.recording_data)
        
        # Save WAV file
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        # Analyze the complete recording
        self._analyze_complete_recording(audio_data, filepath)
        
        duration = len(audio_data) / self.sample_rate
        logger.info(f"Recording saved: {filepath} (Duration: {duration:.1f}s)")
        
        return filepath
    
    def _analyze_complete_recording(self, audio_data: np.ndarray, filepath: str):
        """Perform comprehensive analysis of the complete recording."""
        try:
            logger.info("Analyzing complete recording...")
            
            # Convert to float and normalize
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Detect all barks in the recording
            bark_events = self._detect_barks_in_buffer(audio_float)
            
            if not bark_events:
                logger.info("No barks detected in final analysis")
                return
            
            # Calculate intensities for events
            for event in bark_events:
                event.intensity = self._calculate_event_intensity(audio_float, event)
            
            # Group into sessions
            sessions = self._group_events_into_sessions(bark_events)
            
            # Log detailed analysis
            total_duration = len(audio_data) / self.sample_rate
            total_bark_duration = sum(event.end_time - event.start_time for event in bark_events)
            bark_percentage = (total_bark_duration / total_duration) * 100
            
            avg_confidence = np.mean([event.confidence for event in bark_events])
            avg_intensity = np.mean([event.intensity for event in bark_events])
            
            logger.info(f"Recording Analysis Complete:")
            logger.info(f"  Total Events: {len(bark_events)}")
            logger.info(f"  Sessions: {len(sessions)}")
            logger.info(f"  Total Bark Duration: {total_bark_duration:.1f}s ({bark_percentage:.1f}%)")
            logger.info(f"  Average Confidence: {avg_confidence:.3f}")
            logger.info(f"  Average Intensity: {avg_intensity:.3f}")
            
            # Log session details
            for i, session in enumerate(sessions, 1):
                logger.info(f"  Session {i}: {session.total_barks} barks, "
                           f"{session.barks_per_second:.1f} barks/sec, "
                           f"intensity: {session.intensity:.3f}")
            
        except Exception as e:
            logger.error(f"Error analyzing complete recording: {e}")
    
    def _log_session_summary(self) -> None:
        """Log comprehensive session summary."""
        if self.session_start_time and self.current_session_barks:
            session_end = datetime.now()
            session_duration = (session_end - self.session_start_time).total_seconds()
            
            # Calculate session statistics
            confidences = [bark['confidence'] for bark in self.current_session_barks]
            avg_confidence = np.mean(confidences) if confidences else 0
            peak_confidence = np.max(confidences) if confidences else 0
            
            summary = (f"Session Summary - "
                      f"Start: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                      f"End: {session_end.strftime('%Y-%m-%d %H:%M:%S')}, "
                      f"Duration: {session_duration:.1f}s, "
                      f"Barks: {len(self.current_session_barks)}, "
                      f"Avg Confidence: {avg_confidence:.3f}, "
                      f"Peak Confidence: {peak_confidence:.3f}")
            
            logger.info(summary)
            
            # Reset session tracking
            self.current_session_barks = []
            self.session_start_time = None
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """Process audio chunk with advanced bark detection."""
        current_time = time.time()
        
        # Add to analysis buffer
        self.analysis_buffer.extend(audio_data.astype(np.float32) / 32768.0)
        
        # Process when we have enough data for analysis
        buffer_samples = int(self.detection_buffer_duration * self.sample_rate)
        if len(self.analysis_buffer) >= buffer_samples:
            # Analyze the buffer
            analysis_chunk = np.array(self.analysis_buffer[-buffer_samples:])
            
            # Detect barks
            bark_events = self._detect_barks_in_buffer(analysis_chunk)
            
            # Process any detected barks
            for event in bark_events:
                # Adjust timing to current time
                event.start_time = current_time - self.detection_buffer_duration + event.start_time
                event.end_time = current_time - self.detection_buffer_duration + event.end_time
                
                # Calculate intensity
                event.intensity = self._calculate_event_intensity(analysis_chunk, 
                    BarkEvent(event.start_time - (current_time - self.detection_buffer_duration), 
                             event.end_time - (current_time - self.detection_buffer_duration), 
                             event.confidence))
                
                self.last_bark_time = current_time
                bark_time = datetime.now()
                
                # Log bark detection
                logger.info(f"🐕 BARK DETECTED! Confidence: {event.confidence:.3f}, "
                           f"Intensity: {event.intensity:.3f}, "
                           f"Duration: {event.end_time - event.start_time:.2f}s")
                
                if not self.is_recording:
                    logger.info("Starting recording session...")
                    self.is_recording = True
                    self.recording_data = []
                    self.session_start_time = bark_time
                    self.session_bark_count = 0
                
                # Track bark
                self.current_session_barks.append({
                    'time': bark_time,
                    'confidence': event.confidence,
                    'intensity': event.intensity,
                    'duration': event.end_time - event.start_time
                })
                self.session_bark_count += 1
            
            # Manage buffer size
            if len(self.analysis_buffer) > buffer_samples * 2:
                self.analysis_buffer = self.analysis_buffer[-buffer_samples:]
        
        # Handle recording state
        if self.is_recording:
            self.recording_data.append(audio_data)
            
            # Check for quiet period
            if current_time - self.last_bark_time > self.quiet_duration:
                logger.info("Quiet period detected. Stopping recording...")
                self.save_recording()
                self._log_session_summary()
                self.is_recording = False
                self.recording_data = []
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        self.process_audio_chunk(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def start(self) -> None:
        """Start the advanced bark detector."""
        if self.is_running:
            logger.warning("Bark detector is already running!")
            return
        
        logger.info("Starting Advanced YAMNet Bark Detector...")
        
        try:
            self.audio = pyaudio.PyAudio()
            
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
            
            logger.info("Advanced bark detector started successfully!")
            logger.info("Monitoring for barking sounds with comprehensive analysis...")
            logger.info("Press Ctrl+C to stop")
            
        except Exception as e:
            logger.error(f"Error starting bark detector: {e}")
            self.cleanup()
    
    def stop(self) -> None:
        """Stop the bark detector."""
        if not self.is_running:
            return
        
        logger.info("Stopping bark detector...")
        self.is_running = False
        
        if self.is_recording:
            logger.info("Saving final recording...")
            self.save_recording()
            self._log_session_summary()
            self.is_recording = False
        
        self.cleanup()
        logger.info("Bark detector stopped.")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
    
    def run(self) -> None:
        """Run the bark detector."""
        self.start()
        
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal...")
        finally:
            self.stop()


def main():
    """Main function."""
    config = {
        'sensitivity': 0.05,           # Lower threshold for better detection
        'sample_rate': 16000,          # YAMNet requirement
        'chunk_size': 1024,
        'channels': 1,
        'quiet_duration': 30.0,
        'session_gap_threshold': 10.0,  # Group barks within 10 seconds
        'output_dir': 'recordings'
    }
    
    logger.info("=" * 70)
    logger.info("Advanced YAMNet Bark Detector v3.0")
    logger.info("ML-based Detection with Comprehensive Analysis")
    logger.info("=" * 70)
    
    detector = AdvancedBarkDetector(**config)
    detector.run()


if __name__ == "__main__":
    main()