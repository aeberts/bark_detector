"""Advanced bark detection using YAMNet ML model"""

import os
import time
import threading
import logging
import csv
import io
import wave
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# Apply comprehensive TensorFlow logging suppression (critical for Intel Macs)
from ..utils.tensorflow_suppression import suppress_tensorflow_logging, configure_tensorflow_after_import
suppress_tensorflow_logging()

import numpy as np
import pyaudio
import tensorflow as tf
import tensorflow_hub as hub

# Configure TensorFlow after import
configure_tensorflow_after_import()

from .models import BarkEvent, BarkingSession
from ..utils.helpers import convert_numpy_types, get_detection_logger
from ..legal.tracker import LegalViolationTracker
from ..utils.config import BarkDetectorConfig

logger = get_detection_logger()


class AdvancedBarkDetector:
    """Advanced bark detector using YAMNet with comprehensive analysis."""
    
    def __init__(self,
                 sensitivity: float = 0.68,
                 analysis_sensitivity: float = 0.30,
                 sample_rate: int = 16000,
                 chunk_size: int = 1024,
                 channels: int = 1,
                 quiet_duration: float = 30.0,
                 session_gap_threshold: float = 10.0,
                 output_dir: str = "recordings",
                 profile_name: str = None,
                 config: Optional[BarkDetectorConfig] = None):
        """Initialize the advanced bark detector."""
        self.sensitivity = sensitivity
        self.analysis_sensitivity = analysis_sensitivity
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.quiet_duration = quiet_duration
        self.session_gap_threshold = session_gap_threshold
        self.output_dir = output_dir
        self.profile_name = profile_name
        
        # Calibration mode
        self.calibration_mode = None
        self.is_calibrating = False
        
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
        self.recording_start_time: Optional[datetime] = None  # Timestamp when recording starts (for filename)
        self.last_bark_time = 0.0
        self.audio = None
        self.stream = None
        self.audio_buffer = []
        
        # Analysis buffer for event detection
        self.analysis_buffer = []
        self.detection_buffer_duration = 1.0  # 1 second for analysis
        
        # Detection deduplication system
        self.recent_detections = []  # List of recent detection timestamps
        self.last_reported_bark_time = 0.0  # Last time we reported a bark to console
        self.detection_cooldown_duration = 2.5  # Seconds to wait before reporting another bark
        self.max_recent_detections = 10  # Maximum number of recent detections to track
        
        # Violation detection system (use project-local violations/ directory)
        violations_dir = Path('violations')
        self.violation_tracker = LegalViolationTracker(violations_dir=violations_dir, interactive=True, config=config)  # Interactive by default for CLI usage
        self.enable_real_time_violations = False  # Can be enabled for real-time violation detection
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize YAMNet
        self._load_yamnet_model()
        
        logger.info(f"Advanced Bark Detector initialized:")
        logger.info(f"  Sensitivity: {sensitivity}")
        logger.info(f"  Analysis Sensitivity: {analysis_sensitivity}")
        logger.info(f"  Sample Rate: {sample_rate} Hz")
        logger.info(f"  Session Gap Threshold: {session_gap_threshold}s")
        logger.info(f"  Quiet Duration: {quiet_duration}s")
        logger.info(f"  Output Directory: {output_dir}")
    
    def _load_yamnet_model(self) -> None:
        """Load YAMNet model with advanced class detection."""
        try:
            logger.info("Downloading YAMNet model (this may take a few minutes on first run)...")
            
            # Load YAMNet model
            self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
            
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
        
        # Classes to exclude (too broad, cause false positives)
        excluded_classes = [
            'Animal',  # Too broad - catches birds, insects, etc.
            'Wild animals',  # Too broad - environmental sounds
            # 'Livestock, farm animals, working animals'  # May also be problematic
        ]
        
        self.bark_class_indices = []
        excluded_count = 0
        logger.debug(f"Searching through {len(self.class_names)} classes for bark-related sounds")
        
        for i, class_name in enumerate(self.class_names):
            if any(keyword.lower() in class_name.lower() for keyword in bark_keywords):
                # Check if this class should be excluded
                if class_name in excluded_classes:
                    logger.info(f"🚫 Excluding problematic class: [{i:3d}] {class_name}")
                    excluded_count += 1
                else:
                    self.bark_class_indices.append(i)
                    logger.debug(f"Found bark-related class: {i} - {class_name}")
        
        if excluded_count > 0:
            logger.info(f"📊 Excluded {excluded_count} problematic classes to reduce false positives")
        
        if len(self.bark_class_indices) == 0:
            logger.warning("No bark-related classes found in YAMNet model")
        else:
            # Log detailed information about bark classes for analysis
            logger.info("📋 Detected bark-related classes:")
            for i, class_idx in enumerate(self.bark_class_indices):
                class_name = self.class_names[class_idx]
                logger.info(f"   {i+1:2d}. [{class_idx:3d}] {class_name}")
    
    def get_bark_class_names(self) -> List[str]:
        """Get list of bark-related class names for analysis."""
        return [self.class_names[idx] for idx in self.bark_class_indices]
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        self.process_audio_chunk(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
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
                
                # Check if this detection should be reported (deduplication)
                should_report = self._should_report_detection(current_time, event)
                
                # Log bark detection only if not a duplicate
                if should_report:
                    logger.info(f"🐕 BARK DETECTED! Confidence: {event.confidence:.3f}, "
                               f"Intensity: {event.intensity:.3f}, "
                               f"Duration: {event.end_time - event.start_time:.2f}s")
                
                # Always record detection in calibration mode (regardless of deduplication)
                if self.is_calibrating and self.calibration_mode:
                    self.calibration_mode.record_system_detection(event)
                
                if not self.is_recording:
                    # Only log "Starting recording session" if we're reporting this detection
                    if should_report:
                        logger.info("Starting recording session...")
                    self.is_recording = True
                    self.recording_data = []
                    self.recording_start_time = datetime.now()  # Capture start time for filename
                    self.session_start_time = bark_time
                    
                # Store the bark event for session tracking
                self.current_session_events.append(event)
                
                # Track for violation detection if enabled
                if self.enable_real_time_violations:
                    self.violation_tracker.track_event(event)
        
        # Add to recording buffer if we're recording
        if self.is_recording:
            self.recording_data.append(audio_data)
            
            # Check if we should stop recording (no barks for quiet_duration)
            if current_time - self.last_bark_time > self.quiet_duration:
                logger.info("Saving recording...")
                self.save_recording()
                self._log_session_summary()
                self.is_recording = False
        
        # Trim analysis buffer to prevent memory growth
        max_buffer_samples = buffer_samples * 2
        if len(self.analysis_buffer) > max_buffer_samples:
            self.analysis_buffer = self.analysis_buffer[-buffer_samples:]
    
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
    
    def start_monitoring(self):
        """Start monitoring for bark detection."""
        self.start()
        
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal...")
        finally:
            self.stop()
        
    def stop_monitoring(self):
        """Stop monitoring for bark detection."""
        self.stop()
    
    def _detect_barks_in_buffer(self, audio_chunk: np.ndarray) -> List[BarkEvent]:
        """Detect barks in audio buffer using YAMNet with real-time sensitivity."""
        return self._detect_barks_in_buffer_with_sensitivity(audio_chunk, self.sensitivity)

    def _detect_barks_in_buffer_with_sensitivity(self, audio_chunk: np.ndarray, sensitivity: float) -> List[BarkEvent]:
        """Detect barks in audio buffer using YAMNet with custom sensitivity.

        Args:
            audio_chunk: Audio data to analyze
            sensitivity: Custom sensitivity threshold for detection

        Returns:
            List of detected bark events
        """
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

            # Get bark-related scores with detailed class information
            bark_scores, class_details = self._get_bark_scores(scores.numpy())

            # Convert scores to events with class analysis using custom sensitivity
            bark_events = self._scores_to_events_with_sensitivity(bark_scores, class_details, sensitivity)

            # Log which mode was used for analysis
            mode = "real-time" if sensitivity == self.sensitivity else "analysis"
            logger.debug(f"Detection mode: {mode} (sensitivity: {sensitivity:.3f})")

            return bark_events

        except Exception as e:
            logger.error(f"Error in bark detection: {e}")
            return []
    
    def _get_bark_scores(self, scores: np.ndarray) -> tuple:
        """Extract bark-related confidence scores with detailed class information.
        
        Returns:
            tuple: (bark_scores, class_details) where class_details contains 
                   per-frame information about which classes triggered detection
        """
        if len(self.bark_class_indices) == 0:
            return np.zeros(scores.shape[0]), []
        
        # Get scores for bark-related classes
        bark_class_scores = scores[:, self.bark_class_indices]
        
        # Take maximum score across all bark classes for each time frame
        bark_scores = np.max(bark_class_scores, axis=1)
        
        # Capture detailed class information for analysis
        class_details = []
        for frame_idx in range(scores.shape[0]):
            frame_details = {
                'frame': frame_idx,
                'max_score': bark_scores[frame_idx],
                'class_scores': {}
            }
            
            # Record scores for each bark-related class
            for i, class_idx in enumerate(self.bark_class_indices):
                class_name = self.class_names[class_idx]
                class_score = bark_class_scores[frame_idx, i]
                frame_details['class_scores'][class_name] = float(class_score)
            
            # Identify which class(es) achieved the maximum score
            max_score_indices = np.where(bark_class_scores[frame_idx] == bark_scores[frame_idx])[0]
            frame_details['triggering_classes'] = [
                self.class_names[self.bark_class_indices[idx]] for idx in max_score_indices
            ]
            
            class_details.append(frame_details)
        
        return bark_scores, class_details
    
    def _scores_to_events(self, bark_scores: np.ndarray, class_details: List[dict]) -> List[BarkEvent]:
        """Convert YAMNet scores to bark events with class analysis using real-time sensitivity."""
        return self._scores_to_events_with_sensitivity(bark_scores, class_details, self.sensitivity)

    def _scores_to_events_with_sensitivity(self, bark_scores: np.ndarray, class_details: List[dict], sensitivity: float) -> List[BarkEvent]:
        """Convert YAMNet scores to bark events with class analysis using custom sensitivity.

        Args:
            bark_scores: Array of bark confidence scores
            class_details: Detailed class information per frame
            sensitivity: Custom sensitivity threshold for detection

        Returns:
            List of detected bark events
        """
        # YAMNet produces one prediction every 0.48 seconds
        time_per_frame = 0.48

        # Find frames above threshold using custom sensitivity
        bark_frames = np.where(bark_scores > sensitivity)[0]
        
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
                # Create event from current group with class analysis
                event = self._create_event_with_class_info(
                    current_start, current_end, time_per_frame, bark_scores, class_details
                )
                events.append(event)
                
                current_start = bark_frames[i]
                current_end = bark_frames[i]
        
        # Don't forget the last group
        event = self._create_event_with_class_info(
            current_start, current_end, time_per_frame, bark_scores, class_details
        )
        events.append(event)
        
        return events
    
    def _create_event_with_class_info(self, start_frame: int, end_frame: int, 
                                     time_per_frame: float, bark_scores: np.ndarray, 
                                     class_details: List[dict]) -> BarkEvent:
        """Create a BarkEvent with detailed class analysis information."""
        start_time = start_frame * time_per_frame
        end_time = (end_frame + 1) * time_per_frame
        confidence = float(np.mean(bark_scores[start_frame:end_frame+1]))
        
        # Analyze class information for this event
        event_frames = range(start_frame, end_frame + 1)
        all_triggering_classes = set()
        class_confidence_sums = {}
        frame_count = 0
        
        for frame_idx in event_frames:
            if frame_idx < len(class_details):
                frame_info = class_details[frame_idx]
                
                # Collect triggering classes
                all_triggering_classes.update(frame_info.get('triggering_classes', []))
                
                # Sum confidence scores for averaging
                for class_name, score in frame_info.get('class_scores', {}).items():
                    if class_name not in class_confidence_sums:
                        class_confidence_sums[class_name] = 0.0
                    class_confidence_sums[class_name] += score
                
                frame_count += 1
        
        # Calculate average confidence scores per class
        class_confidences = {}
        if frame_count > 0:
            for class_name, total_score in class_confidence_sums.items():
                class_confidences[class_name] = total_score / frame_count
        
        # Log detailed detection information for analysis
        logger.debug(f"Detection at {start_time:.2f}-{end_time:.2f}s: "
                    f"confidence={confidence:.3f}, "
                    f"triggering_classes={list(all_triggering_classes)}")
        
        return BarkEvent(
            start_time=start_time,
            end_time=end_time,
            confidence=confidence,
            triggering_classes=list(all_triggering_classes),
            class_confidences=class_confidences
        )
    
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
            logger.debug(f"Error calculating intensity: {e}")
            return event.confidence * 0.5
    
    def _should_report_detection(self, current_time: float, event: BarkEvent) -> bool:
        """
        Determine if a bark detection should be reported to console.
        Implements deduplication logic to prevent console spam from the same real-world bark.
        """
        # Clean up old detections from tracking list
        cutoff_time = current_time - self.detection_cooldown_duration * 2
        self.recent_detections = [t for t in self.recent_detections if t > cutoff_time]
        
        # Check if we're still in cooldown period from last reported bark
        if current_time - self.last_reported_bark_time < self.detection_cooldown_duration:
            # Add to recent detections but don't report
            self.recent_detections.append(current_time)
            # Trim list size
            if len(self.recent_detections) > self.max_recent_detections:
                self.recent_detections = self.recent_detections[-self.max_recent_detections:]
            return False
        
        # This is a new bark detection to report
        self.last_reported_bark_time = current_time
        self.recent_detections.append(current_time)
        
        # Trim list size
        if len(self.recent_detections) > self.max_recent_detections:
            self.recent_detections = self.recent_detections[-self.max_recent_detections:]
        
        return True
    
    def save_recording(self) -> str:
        """Save recording with comprehensive analysis.
        
        Note: Filename timestamp represents when recording STARTED, not when it ended.
        This ensures accurate bark-to-audio-file correlation in analysis tools.
        """
        if not self.recording_data:
            return ""
        
        # Use recording start time for filename timestamp (not end time)
        if self.recording_start_time:
            timestamp = self.recording_start_time.strftime("%Y%m%d_%H%M%S")
            date_str = self.recording_start_time.strftime("%Y-%m-%d")
        else:
            # Fallback to current time if start time not captured (shouldn't happen)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_str = datetime.now().strftime("%Y-%m-%d")
            logger.warning("Recording start time not captured, using current time as fallback")
        
        # Create date-based subdirectory
        date_dir = os.path.join(self.output_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        # Generate filename and full path
        filename = f"bark_recording_{timestamp}.wav"
        filepath = os.path.join(date_dir, filename)
        
        # Convert recording data with safety checks
        try:
            if len(self.recording_data) == 0:
                logger.warning("No recording data to save")
                return ""
            elif len(self.recording_data) == 1:
                # Single audio chunk - no concatenation needed
                audio_data = self.recording_data[0]
            else:
                # Multiple chunks - concatenate them
                audio_data = np.concatenate(self.recording_data)
                
            # Ensure we have actual audio data
            if len(audio_data) == 0:
                logger.warning("Empty audio data - cannot save recording")
                return ""
                
        except ValueError as e:
            logger.error(f"Error concatenating recording data: {e}")
            logger.error(f"Recording data structure: {len(self.recording_data)} chunks, "
                        f"shapes: {[chunk.shape for chunk in self.recording_data if hasattr(chunk, 'shape')]}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error processing recording data: {e}")
            return ""
        
        # Save WAV file
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        duration = len(audio_data) / self.sample_rate
        logger.info(f"Recording saved: {filepath} (Duration: {duration:.1f}s)")
        
        return filepath
    
    def _log_session_summary(self):
        """Log summary of the completed recording session."""
        if self.session_start_time and self.current_session_events:
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            bark_count = len(self.current_session_events)
            
            if bark_count > 0:
                avg_confidence = sum(e.confidence for e in self.current_session_events) / bark_count
                peak_confidence = max(e.confidence for e in self.current_session_events)
                
                logger.info(f"Session Summary - Start: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                           f"End: {datetime.now().strftime('%H:%M:%S')}, "
                           f"Duration: {session_duration:.1f}s, "
                           f"Barks: {bark_count}, "
                           f"Avg Confidence: {avg_confidence:.3f}, "
                           f"Peak Confidence: {peak_confidence:.3f}")
        
        # Reset for next session
        self.current_session_events = []
        self.session_start_time = None
    
    def list_profiles(self) -> List[dict]:
        """List available calibration profiles."""
        from ..core.models import CalibrationProfile
        
        profiles_dir = Path.home() / '.bark_detector' / 'profiles'
        
        if not profiles_dir.exists():
            return []
        
        profiles = []
        for profile_file in profiles_dir.glob("*.json"):
            try:
                profile = CalibrationProfile.load(profile_file)
                profiles.append({
                    'name': profile.name,
                    'created': profile.created_date,
                    'sensitivity': profile.sensitivity,
                    'notes': profile.notes
                })
            except Exception as e:
                logger.warning(f"Could not load profile {profile_file}: {e}")
        
        return profiles
    
    def analyze_violations_for_date(self, target_date: str) -> List:
        """
        Analyze recordings for a specific date and detect bylaw violations using analysis sensitivity.

        Args:
            target_date: Date string in YYYY-MM-DD format

        Returns:
            List of detected violations for that date
        """
        recordings_dir = Path(self.output_dir)

        # Log which sensitivity mode is being used for analysis
        logger.info(f"Using analysis sensitivity {self.analysis_sensitivity:.3f} for comprehensive violation detection")

        return self.violation_tracker.analyze_recordings_for_date(recordings_dir, target_date, self)
    
    def generate_violation_report(self, start_date: str, end_date: str) -> List:
        """
        Generate violation report for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of violations in the date range
        """
        # For now, return empty list - implementation will come with ViolationDatabase
        return []
    
    def export_violations_csv(self, output_path: Path, start_date: str = None, end_date: str = None):
        """
        Export violations to CSV format for RDCO submission.
        """
        # For now, just log - implementation will come with ViolationDatabase
        logger.info(f"Would export violations to {output_path} for {start_date} to {end_date}")
        logger.info("Export violations functionality requires ViolationDatabase implementation")