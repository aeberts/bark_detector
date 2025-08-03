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
import argparse
import sys
import select
import termios
import tty
import json
from pathlib import Path

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


def convert_numpy_types(obj):
    """
    Recursively convert NumPy data types to native Python types for JSON serialization.
    
    Args:
        obj: Object that may contain NumPy types
        
    Returns:
        Object with NumPy types converted to native Python types
    """
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        # Handle NaN and infinity
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(item) for item in obj.tolist()]
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj


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


@dataclass
class CalibrationProfile:
    """Stores calibration settings for a specific environment."""
    name: str
    sensitivity: float
    min_bark_duration: float
    session_gap_threshold: float
    background_noise_level: float
    created_date: str
    location: str = ""
    notes: str = ""

    def save(self, filepath: Path):
        """Save profile to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path):
        """Load profile from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


@dataclass
class GroundTruthEvent:
    """Represents a ground truth bark event with timestamp."""
    start_time: float
    end_time: float
    description: str = ""
    confidence_expected: float = 1.0


@dataclass
class LegalSporadicSession:
    """Represents a legal sporadic session for bylaw violation detection."""
    start_time: float
    end_time: float
    barking_sessions: List['BarkingSession']
    total_bark_duration: float
    total_session_duration: float
    violation_type: Optional[str] = None  # "Constant" or "Intermittent"
    is_violation: bool = False


@dataclass
class ViolationReport:
    """Represents a detected bylaw violation with RDCO-compliant information."""
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM AM/PM format
    end_time: str  # HH:MM AM/PM format
    violation_type: str  # "Constant" or "Intermittent"
    total_bark_duration: float  # Total barking time in seconds
    total_incident_duration: float  # Total incident time in seconds
    audio_files: List[str]  # List of associated recording files
    confidence_scores: List[float]  # Confidence scores from detections
    peak_confidence: float
    avg_confidence: float
    created_timestamp: str  # ISO format timestamp when report was generated


class ViolationDatabase:
    """Manages collection and persistence of violation reports."""
    
    def __init__(self, db_path: Path = None):
        """Initialize violation database."""
        if db_path is None:
            db_path = Path.home() / '.bark_detector' / 'violations.json'
        
        self.db_path = db_path
        self.violations: List[ViolationReport] = []
        self._load_violations()
    
    def _load_violations(self):
        """Load existing violations from database file."""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.violations = [
                        ViolationReport(**violation_data) 
                        for violation_data in data.get('violations', [])
                    ]
        except Exception as e:
            logger.warning(f"Could not load violation database: {e}")
            self.violations = []
    
    def save_violations(self):
        """Save violations to database file."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'violations': [
                    {
                        'date': v.date,
                        'start_time': v.start_time,
                        'end_time': v.end_time,
                        'violation_type': v.violation_type,
                        'total_bark_duration': convert_numpy_types(v.total_bark_duration),
                        'total_incident_duration': convert_numpy_types(v.total_incident_duration),
                        'audio_files': v.audio_files,
                        'confidence_scores': convert_numpy_types(v.confidence_scores),
                        'peak_confidence': convert_numpy_types(v.peak_confidence),
                        'avg_confidence': convert_numpy_types(v.avg_confidence),
                        'created_timestamp': v.created_timestamp
                    }
                    for v in self.violations
                ]
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save violation database: {e}")
    
    def add_violation(self, violation: ViolationReport):
        """Add a violation report to the database."""
        self.violations.append(violation)
        self.save_violations()
    
    def get_violations_by_date_range(self, start_date: str, end_date: str) -> List[ViolationReport]:
        """Get violations within date range (YYYY-MM-DD format)."""
        return [
            v for v in self.violations 
            if start_date <= v.date <= end_date
        ]
    
    def get_violations_by_date(self, date: str) -> List[ViolationReport]:
        """Get violations for specific date (YYYY-MM-DD format)."""
        return [v for v in self.violations if v.date == date]
    
    def export_to_csv(self, output_path: Path) -> None:
        """Export violations to CSV format for RDCO submission."""
        import csv
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'Date', 'Start Time', 'End Time', 'Violation Type',
                'Total Bark Duration (min)', 'Total Incident Duration (min)',
                'Audio Files', 'Peak Confidence', 'Avg Confidence'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for v in self.violations:
                writer.writerow({
                    'Date': v.date,
                    'Start Time': v.start_time,
                    'End Time': v.end_time,
                    'Violation Type': v.violation_type,
                    'Total Bark Duration (min)': f"{v.total_bark_duration / 60:.1f}",
                    'Total Incident Duration (min)': f"{v.total_incident_duration / 60:.1f}",
                    'Audio Files': '; '.join(v.audio_files),
                    'Peak Confidence': f"{v.peak_confidence:.3f}",
                    'Avg Confidence': f"{v.avg_confidence:.3f}"
                })


class LegalViolationTracker:
    """Enhanced legal violation tracker for City of Kelowna bylaw violations."""
    
    def __init__(self, violation_db: ViolationDatabase = None):
        """Initialize legal violation tracker."""
        self.violation_db = violation_db or ViolationDatabase()
        
        # Legal session tracking
        self.current_legal_sporadic_session: Optional[LegalSporadicSession] = None
        self.legal_gap_threshold = 300.0  # 5 minutes for legal sporadic sessions
        self.continuous_violation_threshold = 300.0  # 5 minutes for continuous violations
        self.sporadic_violation_threshold = 900.0  # 15 minutes for sporadic violations
        self.sequence_gap_threshold = 30.0  # 30 seconds for continuous sequence detection
        
        # Tracking state
        self.last_session_end_time = 0.0
        self.processed_sessions: List[BarkingSession] = []
    
    def process_barking_sessions(self, sessions: List[BarkingSession], recording_date: str = None) -> List[ViolationReport]:
        """
        Process a list of barking sessions and detect violations.
        
        Args:
            sessions: List of BarkingSession objects to analyze
            recording_date: Date string (YYYY-MM-DD) for the recordings
            
        Returns:
            List of ViolationReport objects for detected violations
        """
        if not sessions:
            return []
        
        # Sort sessions by start time
        sorted_sessions = sorted(sessions, key=lambda x: x.start_time)
        
        # Group sessions into legal sporadic sessions
        legal_sessions = self._group_sessions_into_legal_sessions(sorted_sessions)
        
        # Detect violations in each legal session
        violations = []
        for legal_session in legal_sessions:
            # Check for continuous violations within this legal session
            continuous_violations = self._detect_continuous_violations(legal_session, recording_date)
            violations.extend(continuous_violations)
            
            # Check for sporadic violations across the entire legal session
            sporadic_violation = self._detect_sporadic_violation(legal_session, recording_date)
            if sporadic_violation:
                violations.append(sporadic_violation)
        
        # Add violations to database
        for violation in violations:
            self.violation_db.add_violation(violation)
        
        return violations
    
    def _group_sessions_into_legal_sessions(self, sessions: List[BarkingSession]) -> List[LegalSporadicSession]:
        """Group barking sessions into legal sporadic sessions using 5-minute gap threshold."""
        if not sessions:
            return []
        
        legal_sessions = []
        current_session_groups = [sessions[0]]
        
        for i in range(1, len(sessions)):
            current_session = sessions[i]
            last_session = current_session_groups[-1]
            
            # Check gap between sessions
            gap = current_session.start_time - last_session.end_time
            
            if gap <= self.legal_gap_threshold:
                # Continue current legal sporadic session
                current_session_groups.append(current_session)
            else:
                # Create legal sporadic session and start new one
                legal_session = self._create_legal_sporadic_session(current_session_groups)
                legal_sessions.append(legal_session)
                current_session_groups = [current_session]
        
        # Add final legal session
        if current_session_groups:
            legal_session = self._create_legal_sporadic_session(current_session_groups)
            legal_sessions.append(legal_session)
        
        return legal_sessions
    
    def _create_legal_sporadic_session(self, sessions: List[BarkingSession]) -> LegalSporadicSession:
        """Create a LegalSporadicSession from a group of BarkingSessions."""
        start_time = min(session.start_time for session in sessions)
        end_time = max(session.end_time for session in sessions)
        total_bark_duration = sum(session.total_duration for session in sessions)
        total_session_duration = end_time - start_time
        
        return LegalSporadicSession(
            start_time=start_time,
            end_time=end_time,
            barking_sessions=sessions,
            total_bark_duration=total_bark_duration,
            total_session_duration=total_session_duration
        )
    
    def _detect_continuous_violations(self, legal_session: LegalSporadicSession, recording_date: str) -> List[ViolationReport]:
        """Detect continuous violations within a legal sporadic session."""
        violations = []
        
        # Method 1: Check individual sessions ≥ 5 minutes
        for session in legal_session.barking_sessions:
            if session.total_duration >= self.continuous_violation_threshold:
                violation = self._create_violation_report(
                    sessions=[session],
                    violation_type="Constant",
                    recording_date=recording_date,
                    start_time=session.start_time,
                    end_time=session.end_time
                )
                violations.append(violation)
        
        # Method 2: Check sequences of sessions with gaps ≤ 30 seconds that total ≥ 5 minutes
        sequence_violations = self._detect_continuous_sequences(legal_session.barking_sessions, recording_date)
        violations.extend(sequence_violations)
        
        return violations
    
    def _detect_continuous_sequences(self, sessions: List[BarkingSession], recording_date: str) -> List[ViolationReport]:
        """Detect continuous violation sequences (sessions with gaps ≤30s totaling ≥5min)."""
        violations = []
        
        if len(sessions) < 2:
            return violations
        
        i = 0
        while i < len(sessions):
            # Start a potential sequence
            sequence_sessions = [sessions[i]]
            sequence_bark_duration = sessions[i].total_duration
            j = i + 1
            
            # Extend sequence while gaps are ≤ 30 seconds
            while j < len(sessions):
                gap = sessions[j].start_time - sequence_sessions[-1].end_time
                if gap <= self.sequence_gap_threshold:
                    sequence_sessions.append(sessions[j])
                    sequence_bark_duration += sessions[j].total_duration
                    j += 1
                else:
                    break
            
            # Check if sequence qualifies as continuous violation
            if len(sequence_sessions) > 1 and sequence_bark_duration >= self.continuous_violation_threshold:
                # Make sure we haven't already detected this as a single session violation
                if not any(session.total_duration >= self.continuous_violation_threshold for session in sequence_sessions):
                    violation = self._create_violation_report(
                        sessions=sequence_sessions,
                        violation_type="Constant",
                        recording_date=recording_date,
                        start_time=sequence_sessions[0].start_time,
                        end_time=sequence_sessions[-1].end_time
                    )
                    violations.append(violation)
            
            # Move to next potential sequence start
            i = max(i + 1, j)
        
        return violations
    
    def _detect_sporadic_violation(self, legal_session: LegalSporadicSession, recording_date: str) -> Optional[ViolationReport]:
        """Detect sporadic violations (≥15 minutes total barking in legal session)."""
        if legal_session.total_bark_duration >= self.sporadic_violation_threshold:
            return self._create_violation_report(
                sessions=legal_session.barking_sessions,
                violation_type="Intermittent",
                recording_date=recording_date,
                start_time=legal_session.start_time,
                end_time=legal_session.end_time
            )
        return None
    
    def _create_violation_report(self, sessions: List[BarkingSession], violation_type: str, 
                               recording_date: str, start_time: float, end_time: float) -> ViolationReport:
        """Create a ViolationReport from detected violation."""
        from datetime import datetime
        
        # Calculate violation metrics
        total_bark_duration = sum(session.total_duration for session in sessions)
        total_incident_duration = end_time - start_time
        
        # Extract confidence data
        all_confidences = []
        for session in sessions:
            all_confidences.extend([event.confidence for event in session.events])
        
        peak_confidence = max(all_confidences) if all_confidences else 0.0
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # Convert timestamps to readable format
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        
        # Use provided date or extract from timestamp
        if recording_date:
            report_date = recording_date
        else:
            report_date = start_dt.strftime("%Y-%m-%d")
        
        start_time_str = start_dt.strftime("%I:%M %p").lstrip('0')
        end_time_str = end_dt.strftime("%I:%M %p").lstrip('0')
        
        # Generate audio file references (placeholder - would need actual file mapping)
        audio_files = [f"bark_recording_{start_dt.strftime('%Y%m%d_%H%M%S')}.wav"]
        
        return ViolationReport(
            date=report_date,
            start_time=start_time_str,
            end_time=end_time_str,
            violation_type=violation_type,
            total_bark_duration=convert_numpy_types(total_bark_duration),
            total_incident_duration=convert_numpy_types(total_incident_duration),
            audio_files=audio_files,
            confidence_scores=convert_numpy_types(all_confidences),
            peak_confidence=convert_numpy_types(peak_confidence),
            avg_confidence=convert_numpy_types(avg_confidence),
            created_timestamp=datetime.now().isoformat()
        )
    
    def analyze_recordings_for_date(self, recordings_dir: Path, target_date: str, detector: 'AdvancedBarkDetector' = None) -> List[ViolationReport]:
        """
        Analyze all recordings for a specific date and detect violations.
        
        Args:
            recordings_dir: Path to recordings directory
            target_date: Date string in YYYY-MM-DD format
            detector: AdvancedBarkDetector instance for analysis
            
        Returns:
            List of detected violations for that date
        """
        if not detector:
            logger.error("Detector instance required for recording analysis")
            return []
        
        # Create recording file parser
        parser = RecordingFileParser(detector)
        
        # Get all barking sessions for the date
        sessions = parser.analyze_recordings_for_date(recordings_dir, target_date)
        
        if not sessions:
            logger.info(f"No barking sessions found for {target_date}")
            return []
        
        # Process sessions and detect violations
        violations = self.process_barking_sessions(sessions, target_date)
        
        if violations:
            logger.info(f"Detected {len(violations)} violations for {target_date}")
            for violation in violations:
                logger.info(f"  {violation.violation_type} violation: {violation.start_time} - {violation.end_time} "
                           f"({violation.total_bark_duration/60:.1f}min barking)")
        else:
            logger.info(f"No violations detected for {target_date}")
        
        return violations


class RecordingFileParser:
    """Parser for analyzing existing recording files and reconstructing sessions."""
    
    def __init__(self, detector: 'AdvancedBarkDetector'):
        """Initialize recording file parser."""
        self.detector = detector
        
    def get_recordings_for_date(self, recordings_dir: Path, target_date: str) -> List[Path]:
        """
        Get all recording files for a specific date.
        
        Args:
            recordings_dir: Path to recordings directory
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            List of recording file paths for that date
        """
        date_parts = target_date.split('-')
        if len(date_parts) != 3:
            raise ValueError(f"Invalid date format: {target_date}. Use YYYY-MM-DD")
        
        year, month, day = date_parts
        date_pattern = f"{year}{month}{day}"
        
        recording_files = []
        pattern = f"bark_recording_{date_pattern}_*.wav"
        
        for file_path in recordings_dir.glob(pattern):
            recording_files.append(file_path)
        
        # Sort by timestamp in filename
        recording_files.sort(key=lambda x: self._extract_timestamp_from_filename(x.name))
        
        return recording_files
    
    def _extract_timestamp_from_filename(self, filename: str) -> float:
        """
        Extract timestamp from recording filename.
        Expected format: bark_recording_YYYYMMDD_HHMMSS.wav
        """
        try:
            # Remove extension and split
            name_parts = filename.replace('.wav', '').split('_')
            if len(name_parts) >= 4 and name_parts[0] == 'bark' and name_parts[1] == 'recording':
                date_str = name_parts[2]  # YYYYMMDD
                time_str = name_parts[3]  # HHMMSS
                
                # Parse date and time
                from datetime import datetime
                dt_str = f"{date_str}_{time_str}"
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                return dt.timestamp()
        except Exception as e:
            logger.warning(f"Could not parse timestamp from filename {filename}: {e}")
        
        return 0.0
    
    def analyze_recording_file(self, recording_path: Path) -> List[BarkingSession]:
        """
        Analyze a single recording file and extract barking sessions.
        
        Args:
            recording_path: Path to the recording file
            
        Returns:
            List of BarkingSession objects detected in the file
        """
        try:
            import librosa
            
            logger.info(f"Analyzing recording: {recording_path.name}")
            
            # Load audio file
            audio_data, sample_rate = librosa.load(str(recording_path), sr=16000, mono=True)
            
            if len(audio_data) == 0:
                logger.warning(f"Empty audio file: {recording_path}")
                return []
            
            # Get file timestamp from filename
            file_timestamp = self._extract_timestamp_from_filename(recording_path.name)
            
            # Detect bark events in the recording
            bark_events = self.detector._detect_barks_in_buffer(audio_data)
            
            if not bark_events:
                logger.info(f"No barks detected in {recording_path.name}")
                return []
            
            # Adjust event timestamps to real time based on file timestamp
            duration = len(audio_data) / sample_rate
            for event in bark_events:
                event.start_time = file_timestamp + event.start_time
                event.end_time = file_timestamp + event.end_time
                # Calculate intensity
                event.intensity = self.detector._calculate_event_intensity(audio_data, 
                    BarkEvent(event.start_time - file_timestamp, 
                             event.end_time - file_timestamp, 
                             event.confidence))
            
            # Group events into barking sessions
            sessions = self.detector._group_events_into_sessions(bark_events)
            
            logger.info(f"Found {len(bark_events)} bark events in {len(sessions)} sessions from {recording_path.name}")
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error analyzing recording {recording_path}: {e}")
            return []
    
    def analyze_recordings_for_date(self, recordings_dir: Path, target_date: str) -> List[BarkingSession]:
        """
        Analyze all recordings for a specific date and return all barking sessions.
        
        Args:
            recordings_dir: Path to recordings directory
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            List of all BarkingSession objects for that date
        """
        recording_files = self.get_recordings_for_date(recordings_dir, target_date)
        
        if not recording_files:
            logger.info(f"No recordings found for date: {target_date}")
            return []
        
        logger.info(f"Found {len(recording_files)} recording files for {target_date}")
        
        all_sessions = []
        for recording_file in recording_files:
            sessions = self.analyze_recording_file(recording_file)
            all_sessions.extend(sessions)
        
        # Sort sessions by start time
        all_sessions.sort(key=lambda x: x.start_time)
        
        logger.info(f"Total sessions for {target_date}: {len(all_sessions)}")
        
        return all_sessions


class FileBasedCalibration:
    """File-based calibration using ground truth timestamps."""
    
    def __init__(self, detector):
        self.detector = detector
        self.test_files = []
        self.results = []
        
    def add_test_file(self, audio_path: Path, ground_truth_path: Path = None, 
                     ground_truth_events: List[GroundTruthEvent] = None):
        """Add a test file with ground truth data."""
        # Validate and potentially convert audio file
        converted_path = self._ensure_compatible_audio(audio_path)
        
        if ground_truth_path and ground_truth_path.exists():
            # Load ground truth from JSON file
            with open(ground_truth_path, 'r') as f:
                gt_data = json.load(f)
            
            events = []
            for event_data in gt_data.get('events', []):
                events.append(GroundTruthEvent(
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    description=event_data.get('description', ''),
                    confidence_expected=event_data.get('confidence_expected', 1.0)
                ))
            
        elif ground_truth_events:
            events = ground_truth_events
        else:
            # No ground truth - assume this is a negative file (no barks)
            events = []
            
        self.test_files.append({
            'audio_path': converted_path,
            'original_path': audio_path,
            'ground_truth': events,
            'is_negative': len(events) == 0
        })
        
        logger.info(f"📁 Added test file: {audio_path.name} ({len(events)} ground truth events)")
    
    def _ensure_compatible_audio(self, audio_path: Path) -> Path:
        """Ensure audio file is in compatible format (WAV, 16kHz)."""
        supported_extensions = ['.wav', '.m4a', '.mp3', '.aac', '.flac']
        
        if audio_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported audio format: {audio_path.suffix}")
        
        # If already WAV, check if it needs resampling
        if audio_path.suffix.lower() == '.wav':
            try:
                import soundfile as sf
                info = sf.info(str(audio_path))
                if info.samplerate == 16000 and info.channels == 1:
                    return audio_path  # Already in correct format
            except Exception:
                pass  # Fall through to conversion
        
        # Convert to WAV 16kHz mono
        converted_path = self._convert_audio_file(audio_path)
        return converted_path
    
    def _convert_audio_file(self, audio_path: Path) -> Path:
        """Convert audio file to WAV 16kHz mono format."""
        import librosa
        import soundfile as sf
        
        # Create converted file path
        converted_dir = audio_path.parent / 'converted'
        converted_dir.mkdir(exist_ok=True)
        converted_path = converted_dir / f"{audio_path.stem}_16khz.wav"
        
        # Skip if already converted
        if converted_path.exists():
            logger.info(f"🔄 Using existing converted file: {converted_path.name}")
            return converted_path
        
        try:
            logger.info(f"🔄 Converting {audio_path.name} to WAV 16kHz...")
            
            # Load and convert
            audio_data, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
            
            # Save as WAV
            sf.write(str(converted_path), audio_data, 16000, subtype='PCM_16')
            
            duration = len(audio_data) / 16000
            logger.info(f"✅ Converted: {converted_path.name} ({duration:.1f}s)")
            
            return converted_path
            
        except Exception as e:
            logger.error(f"❌ Failed to convert {audio_path}: {e}")
            raise
    
    def _extract_from_voice_memos(self, voice_memo_path: Path) -> Path:
        """Extract audio from Mac Voice Memos format."""
        # Voice Memos creates:
        # - file.m4a (the actual audio)
        # - file.composition (metadata)
        # - file.composition/ (folder with segments)
        
        base_path = voice_memo_path.parent / voice_memo_path.stem
        m4a_file = base_path.with_suffix('.m4a')
        
        if m4a_file.exists():
            logger.info(f"📱 Found Voice Memo M4A: {m4a_file.name}")
            return self._convert_audio_file(m4a_file)
        else:
            raise FileNotFoundError(f"No M4A file found for Voice Memo: {voice_memo_path}")
    
    def list_convertible_files(self, directory: Path) -> List[Dict]:
        """List audio files that can be converted for calibration."""
        supported_patterns = ['*.wav', '*.m4a', '*.mp3', '*.aac', '*.flac']
        found_files = []
        
        for pattern in supported_patterns:
            for file_path in directory.glob(pattern):
                try:
                    # Get basic info
                    if file_path.suffix.lower() == '.m4a':
                        # Could be Voice Memo
                        composition_file = file_path.with_suffix('.composition')
                        is_voice_memo = composition_file.exists()
                    else:
                        is_voice_memo = False
                    
                    # Get duration if possible
                    try:
                        import soundfile as sf
                        info = sf.info(str(file_path))
                        duration = info.duration
                        sample_rate = info.samplerate
                    except:
                        duration = 0
                        sample_rate = 0
                    
                    found_files.append({
                        'path': file_path,
                        'type': 'Voice Memo' if is_voice_memo else file_path.suffix.upper()[1:],
                        'duration': duration,
                        'sample_rate': sample_rate,
                        'size_mb': file_path.stat().st_size / (1024 * 1024)
                    })
                    
                except Exception as e:
                    logger.debug(f"Could not analyze {file_path}: {e}")
        
        return sorted(found_files, key=lambda x: x['path'].name)
    
    def create_ground_truth_template(self, audio_path: Path, output_path: Path = None):
        """Create a template ground truth file for manual annotation."""
        if output_path is None:
            output_path = audio_path.parent / f"{audio_path.stem}_ground_truth.json"
        
        # Get audio duration
        import soundfile as sf
        try:
            info = sf.info(str(audio_path))
            duration = info.duration
        except Exception:
            duration = 60.0  # Default if can't read
        
        template = {
            "audio_file": str(audio_path),
            "duration": duration,
            "instructions": "Add bark events with start_time and end_time in seconds",
            "events": [
                {
                    "start_time": 5.0,
                    "end_time": 7.5,
                    "description": "Example: Dog barking - replace with actual timestamps",
                    "confidence_expected": 1.0
                }
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"📝 Ground truth template created: {output_path}")
        logger.info("Edit this file to add actual bark timestamps, then run calibration")
        return output_path
    
    def run_sensitivity_sweep(self, sensitivity_range: Tuple[float, float] = (0.01, 0.5), 
                            steps: int = 20) -> Dict:
        """Run calibration across a range of sensitivity values."""
        logger.info(f"🔍 Running sensitivity sweep: {sensitivity_range[0]:.3f} to {sensitivity_range[1]:.3f}")
        logger.info(f"📊 Testing {len(self.test_files)} files with {steps} sensitivity levels")
        
        if not self.test_files:
            raise ValueError("No test files added. Use add_test_file() first.")
        
        # Generate sensitivity values to test
        sensitivity_values = np.linspace(sensitivity_range[0], sensitivity_range[1], steps)
        
        sweep_results = []
        
        for i, sensitivity in enumerate(sensitivity_values):
            logger.info(f"🎛️  Testing sensitivity {sensitivity:.3f} ({i+1}/{steps})")
            
            # Set detector sensitivity
            self.detector.sensitivity = sensitivity
            
            # Test all files at this sensitivity
            file_results = []
            total_matches = 0
            total_false_positives = 0
            total_missed = 0
            total_ground_truth = 0
            
            for test_file in self.test_files:
                result = self._test_single_file(test_file, sensitivity)
                file_results.append(result)
                
                total_matches += result['matches']
                total_false_positives += result['false_positives']
                total_missed += result['missed']
                total_ground_truth += len(test_file['ground_truth'])
            
            # Calculate overall metrics
            precision = total_matches / max(total_matches + total_false_positives, 1)
            recall = total_matches / max(total_ground_truth, 1)
            f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
            
            sweep_result = {
                'sensitivity': sensitivity,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'total_matches': total_matches,
                'total_false_positives': total_false_positives,
                'total_missed': total_missed,
                'total_ground_truth': total_ground_truth,
                'file_results': file_results
            }
            
            sweep_results.append(sweep_result)
            
            logger.info(f"   Precision: {precision:.1%}, Recall: {recall:.1%}, F1: {f1_score:.3f}")
        
        # Find optimal sensitivity
        best_result = max(sweep_results, key=lambda x: x['f1_score'])
        
        logger.info("🎯 Calibration Results:")
        logger.info(f"  Optimal Sensitivity: {best_result['sensitivity']:.3f}")
        logger.info(f"  Best F1 Score: {best_result['f1_score']:.3f}")
        logger.info(f"  Precision: {best_result['precision']:.1%}")
        logger.info(f"  Recall: {best_result['recall']:.1%}")
        logger.info(f"  Total Ground Truth Events: {best_result['total_ground_truth']}")
        logger.info(f"  Matches: {best_result['total_matches']}")
        logger.info(f"  False Positives: {best_result['total_false_positives']}")
        logger.info(f"  Missed: {best_result['total_missed']}")
        
        return {
            'optimal_sensitivity': best_result['sensitivity'],
            'best_result': best_result,
            'all_results': sweep_results
        }
    
    def _test_single_file(self, test_file: Dict, sensitivity: float) -> Dict:
        """Test detection on a single file."""
        audio_path = test_file['audio_path']
        ground_truth = test_file['ground_truth']
        
        try:
            # Load audio file
            import librosa
            audio_data, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
            
            # Run detection
            detected_events = self.detector._detect_barks_in_buffer(audio_data)
            
            # Calculate matches
            matches, false_positives, missed = self._calculate_matches(
                detected_events, ground_truth, tolerance=2.0
            )
            
            return {
                'file': audio_path.name,
                'sensitivity': sensitivity,
                'ground_truth_count': len(ground_truth),
                'detected_count': len(detected_events),
                'matches': matches,
                'false_positives': false_positives,
                'missed': missed,
                'precision': matches / max(len(detected_events), 1),
                'recall': matches / max(len(ground_truth), 1)
            }
            
        except Exception as e:
            logger.error(f"Error testing file {audio_path}: {e}")
            return {
                'file': audio_path.name,
                'error': str(e),
                'matches': 0,
                'false_positives': 0,
                'missed': len(ground_truth)
            }
    
    def _calculate_matches(self, detected_events: List[BarkEvent], 
                          ground_truth: List[GroundTruthEvent], 
                          tolerance: float = 2.0) -> Tuple[int, int, int]:
        """Calculate matches between detected and ground truth events."""
        matches = 0
        matched_detections = set()
        matched_ground_truth = set()
        
        # Find matches (detected event overlaps with ground truth within tolerance)
        for i, detected in enumerate(detected_events):
            if i in matched_detections:
                continue
                
            for j, gt_event in enumerate(ground_truth):
                if j in matched_ground_truth:
                    continue
                
                # Check for overlap or proximity
                detected_center = (detected.start_time + detected.end_time) / 2
                gt_center = (gt_event.start_time + gt_event.end_time) / 2
                
                if abs(detected_center - gt_center) <= tolerance:
                    matches += 1
                    matched_detections.add(i)
                    matched_ground_truth.add(j)
                    break
        
        false_positives = len(detected_events) - len(matched_detections)
        missed = len(ground_truth) - len(matched_ground_truth)
        
        return matches, false_positives, missed
    
    def generate_calibration_profile(self, calibration_results: Dict, 
                                   profile_name: str) -> CalibrationProfile:
        """Generate a calibration profile from results."""
        best_result = calibration_results['best_result']
        
        # Calculate background noise level from negative files
        background_noise = 0.0
        negative_files = [f for f in self.test_files if f['is_negative']]
        if negative_files:
            # TODO: Calculate actual background noise level
            background_noise = -45.0  # Placeholder
        
        profile = CalibrationProfile(
            name=profile_name,
            sensitivity=calibration_results['optimal_sensitivity'],
            min_bark_duration=0.3,
            session_gap_threshold=10.0,
            background_noise_level=background_noise,
            created_date=datetime.now().isoformat(),
            location="Kelowna",
            notes=f"File-based calibration: F1={best_result['f1_score']:.3f}, "
                  f"P={best_result['precision']:.1%}, R={best_result['recall']:.1%}, "
                  f"Files={len(self.test_files)}"
        )
        
        return profile


class ManualRecorder:
    """Manual recording mode for capturing calibration samples."""
    
    def __init__(self, detector, output_path: Path):
        self.detector = detector
        self.output_path = Path(output_path)
        self.sample_rate = 16000
        self.channels = 1
        self.format = pyaudio.paInt16
        self.chunk_size = 1024
        
        # Audio recording
        self.audio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        
        # Terminal settings for non-blocking input
        self.original_settings = None
        
    def start_recording(self):
        """Start manual recording session."""
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎙️  Manual Recording Mode")
        logger.info(f"Output: {self.output_path}")
        logger.info(f"Format: WAV 16kHz Mono (YAMNet compatible)")
        logger.info("")
        logger.info("Controls:")
        logger.info("  [SPACE] - Start/Stop recording")
        logger.info("  [ESC] or [Q] - Finish and save")
        logger.info("  [Ctrl+C] - Cancel without saving")
        logger.info("")
        logger.info("Press SPACE to start recording...")
        
        # Setup audio
        self._setup_audio()
        
        # Setup keyboard
        self._setup_keyboard()
        
        try:
            self._recording_loop()
        except KeyboardInterrupt:
            logger.info("\n❌ Recording cancelled by user")
        finally:
            self._cleanup()
            
    def _setup_audio(self):
        """Initialize PyAudio."""
        self.audio = pyaudio.PyAudio()
        
    def _setup_keyboard(self):
        """Setup non-blocking keyboard input."""
        if sys.platform != 'win32':
            self.original_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
    
    def _restore_keyboard(self):
        """Restore original keyboard settings."""
        if sys.platform != 'win32' and self.original_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
    
    def _get_key(self):
        """Get keyboard input without blocking."""
        if sys.platform == 'win32':
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                return key.decode('utf-8') if isinstance(key, bytes) else key
        else:
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                return key
        return None
    
    def _recording_loop(self):
        """Main recording loop."""
        running = True
        
        while running:
            key = self._get_key()
            
            if key:
                if key == ' ':  # Space - toggle recording
                    if self.is_recording:
                        self._stop_recording()
                    else:
                        self._start_recording()
                        
                elif key in ['\x1b', 'q', 'Q']:  # ESC or Q - finish
                    if self.is_recording:
                        self._stop_recording()
                    self._save_recording()
                    running = False
                    
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
    
    def _start_recording(self):
        """Start audio recording."""
        if self.is_recording:
            return
            
        logger.info("🔴 Recording started... Press SPACE to stop")
        
        self.frames = []
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        self.is_recording = True
    
    def _stop_recording(self):
        """Stop audio recording."""
        if not self.is_recording:
            return
            
        logger.info("⏹️  Recording stopped. Press SPACE to record more, or ESC/Q to finish")
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for recording."""
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _save_recording(self):
        """Save recorded audio to file."""
        if not self.frames:
            logger.info("❌ No audio recorded")
            return
            
        try:
            # Combine all frames
            audio_data = b''.join(self.frames)
            
            # Save as WAV file
            with wave.open(str(self.output_path), 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            # Calculate duration
            duration = len(audio_data) / (self.sample_rate * self.channels * 2)  # 2 bytes per sample
            
            logger.info(f"✅ Recording saved: {self.output_path}")
            logger.info(f"   Duration: {duration:.1f} seconds")
            logger.info(f"   Format: WAV 16kHz Mono")
            logger.info("")
            logger.info("💡 To use this file for calibration:")
            logger.info(f"   1. Create ground truth: uv run bd.py --create-template {self.output_path}")
            logger.info(f"   2. Edit the ground truth JSON file with bark timestamps")
            logger.info(f"   3. Run calibration: uv run bd.py --calibrate-files --audio-files {self.output_path} --ground-truth-files {self.output_path.with_suffix('.json')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save recording: {e}")
    
    def _cleanup(self):
        """Clean up resources."""
        if self.is_recording:
            self._stop_recording()
            
        if self.audio:
            self.audio.terminate()
            
        self._restore_keyboard()


class CalibrationMode:
    """Real-time calibration with human feedback."""
    
    def __init__(self, detector, duration_minutes: int = 10):
        self.detector = detector
        self.duration_seconds = duration_minutes * 60
        self.start_time = time.time()
        
        # Feedback tracking
        self.human_marks = []
        self.system_detections = []
        self.sensitivity_history = []
        
        # Terminal settings for non-blocking input
        self.original_settings = None
        self.is_calibrating = False
        
    def start_calibration(self):
        """Start real-time calibration mode."""
        logger.info("🎯 Starting Real-Time Calibration Mode")
        logger.info(f"Duration: {self.duration_seconds/60:.1f} minutes")
        logger.info("Instructions:")
        logger.info("  [SPACE] - Mark when you hear a bark")
        logger.info("  [ESC] - Finish calibration early")
        logger.info("  [Q] - Quit without saving")
        logger.info("")
        
        # Setup non-blocking keyboard input
        self._setup_keyboard()
        self.is_calibrating = True
        
        # Start calibration loop
        try:
            self._calibration_loop()
        finally:
            self._cleanup_keyboard()
            
    def _setup_keyboard(self):
        """Setup non-blocking keyboard input."""
        try:
            self.original_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        except Exception as e:
            logger.warning(f"Could not setup keyboard input: {e}")
            self.original_settings = None
    
    def _cleanup_keyboard(self):
        """Restore original keyboard settings."""
        if self.original_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
            except Exception as e:
                logger.warning(f"Could not restore keyboard settings: {e}")
    
    def _check_keyboard_input(self):
        """Check for keyboard input without blocking."""
        if self.original_settings is None:
            return None
            
        try:
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                return key
        except Exception:
            pass
        return None
    
    def _calibration_loop(self):
        """Main calibration loop."""
        last_status_update = time.time()
        last_optimization = time.time()
        
        while self.is_calibrating:
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Check if calibration time is up
            if elapsed >= self.duration_seconds:
                logger.info("⏰ Calibration time completed")
                break
            
            # Check for keyboard input
            key = self._check_keyboard_input()
            if key:
                if key == ' ':  # Spacebar
                    self._mark_human_bark(current_time)
                elif key == '\x1b':  # ESC
                    logger.info("🛑 Calibration ended by user")
                    break
                elif key.lower() == 'q':
                    logger.info("❌ Calibration cancelled")
                    return None
            
            # Update status every 5 seconds
            if current_time - last_status_update >= 5.0:
                self._show_status(elapsed)
                last_status_update = current_time
            
            # Auto-optimize sensitivity every 30 seconds
            if current_time - last_optimization >= 30.0:
                self._auto_optimize_sensitivity()
                last_optimization = current_time
            
            time.sleep(0.1)
        
        # Generate calibration results
        return self._generate_calibration_results()
    
    def _mark_human_bark(self, timestamp: float):
        """Record human bark marking."""
        self.human_marks.append(timestamp)
        logger.info(f"👤 Human marked bark at {timestamp:.1f}s")
    
    def record_system_detection(self, bark_event: BarkEvent):
        """Record system detection (called by detector)."""
        detection_time = time.time() - self.start_time
        self.system_detections.append({
            'time': detection_time,
            'confidence': bark_event.confidence,
            'intensity': bark_event.intensity,
            'duration': bark_event.end_time - bark_event.start_time
        })
    
    def _show_status(self, elapsed: float):
        """Show calibration status."""
        remaining = (self.duration_seconds - elapsed) / 60
        human_count = len(self.human_marks)
        system_count = len(self.system_detections)
        
        # Calculate match rate
        matches, false_pos, missed = self._calculate_matches()
        match_rate = matches / max(human_count, 1) * 100
        
        # Clear screen and show status
        print(f"\r\033[K🎯 Calibration: {elapsed/60:.1f}m / {self.duration_seconds/60:.1f}m remaining", end="")
        print(f"\r\033[K📊 Human: {human_count} | System: {system_count} | Match: {match_rate:.0f}% | Sensitivity: {self.detector.sensitivity:.3f}")
        print(f"\r\033[K✅ Matches: {matches} | ❌ False+: {false_pos} | ❓ Missed: {missed}")
        
    def _calculate_matches(self, tolerance: float = 3.0):
        """Calculate matches between human marks and system detections."""
        matches = 0
        false_positives = 0
        
        # Find matches (system detection within tolerance of human mark)
        matched_detections = set()
        
        for human_time in self.human_marks:
            for i, detection in enumerate(self.system_detections):
                if i in matched_detections:
                    continue
                if abs(detection['time'] - human_time) <= tolerance:
                    matches += 1
                    matched_detections.add(i)
                    break
        
        # Count false positives (unmatched detections)
        false_positives = len(self.system_detections) - len(matched_detections)
        
        # Count missed (unmatched human marks)
        missed = len(self.human_marks) - matches
        
        return matches, false_positives, missed
    
    def _auto_optimize_sensitivity(self):
        """Automatically adjust sensitivity based on feedback."""
        if len(self.human_marks) < 2 or len(self.system_detections) < 2:
            return
        
        matches, false_pos, missed = self._calculate_matches()
        
        # Calculate current performance
        precision = matches / max(len(self.system_detections), 1)
        recall = matches / max(len(self.human_marks), 1)
        
        # Adjust sensitivity
        current_sensitivity = self.detector.sensitivity
        new_sensitivity = current_sensitivity
        
        if false_pos > missed:
            # Too many false positives - decrease sensitivity
            new_sensitivity = current_sensitivity * 0.9
        elif missed > false_pos:
            # Missing too many - increase sensitivity  
            new_sensitivity = current_sensitivity * 1.1
        
        # Clamp to reasonable range
        new_sensitivity = max(0.01, min(0.5, new_sensitivity))
        
        if abs(new_sensitivity - current_sensitivity) > 0.005:
            self.detector.sensitivity = new_sensitivity
            self.sensitivity_history.append({
                'time': time.time() - self.start_time,
                'sensitivity': new_sensitivity,
                'precision': precision,
                'recall': recall
            })
            logger.info(f"🎛️ Auto-adjusted sensitivity: {current_sensitivity:.3f} → {new_sensitivity:.3f}")
    
    def _generate_calibration_results(self):
        """Generate final calibration results."""
        matches, false_pos, missed = self._calculate_matches()
        
        precision = matches / max(len(self.system_detections), 1)
        recall = matches / max(len(self.human_marks), 1)
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        
        results = {
            'optimal_sensitivity': self.detector.sensitivity,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'human_marks': len(self.human_marks),
            'system_detections': len(self.system_detections),
            'matches': matches,
            'false_positives': false_pos,
            'missed': missed,
            'calibration_duration': time.time() - self.start_time
        }
        
        logger.info("🎯 Calibration Results:")
        logger.info(f"  Optimal Sensitivity: {results['optimal_sensitivity']:.3f}")
        logger.info(f"  Precision: {precision:.1%} (accuracy of detections)")
        logger.info(f"  Recall: {recall:.1%} (% of barks caught)")
        logger.info(f"  F1 Score: {f1_score:.3f} (overall performance)")
        
        return results


class AdvancedBarkDetector:
    """Advanced bark detector using YAMNet with comprehensive analysis."""
    
    def __init__(self, 
                 sensitivity: float = 0.05,
                 sample_rate: int = 16000,
                 chunk_size: int = 1024,
                 channels: int = 1,
                 quiet_duration: float = 30.0,
                 session_gap_threshold: float = 10.0,
                 output_dir: str = "recordings",
                 profile_name: str = None):
        """Initialize the advanced bark detector."""
        self.sensitivity = sensitivity
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
        
        # Violation detection system
        self.violation_tracker = LegalViolationTracker()
        self.enable_real_time_violations = False  # Can be enabled for real-time violation detection
        
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
    
    def _should_report_detection(self, current_time: float, event: BarkEvent) -> bool:
        """
        Determine if a bark detection should be reported to console.
        Implements deduplication logic to prevent console spam from the same real-world bark.
        
        Args:
            current_time: Current timestamp
            event: The detected bark event
            
        Returns:
            True if this detection should be reported, False if it's likely a duplicate
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
        
        # This is a new bark - should be reported
        self.recent_detections.append(current_time)
        self.last_reported_bark_time = current_time
        
        # Trim list size
        if len(self.recent_detections) > self.max_recent_detections:
            self.recent_detections = self.recent_detections[-self.max_recent_detections:]
        
        return True
    
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
    
    def start_calibration(self, duration_minutes: int = 10) -> CalibrationProfile:
        """Start real-time calibration mode."""
        self.calibration_mode = CalibrationMode(self, duration_minutes)
        self.is_calibrating = True
        
        # Start detector in background
        self.start()
        
        try:
            # Run calibration
            results = self.calibration_mode.start_calibration()
            
            if results:
                # Create calibration profile
                profile = CalibrationProfile(
                    name=self.profile_name or f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    sensitivity=results['optimal_sensitivity'],
                    min_bark_duration=0.3,  # Default for now
                    session_gap_threshold=self.session_gap_threshold,
                    background_noise_level=0.0,  # TODO: calculate from calibration
                    created_date=datetime.now().isoformat(),
                    location="Kelowna",
                    notes=f"F1: {results['f1_score']:.3f}, Precision: {results['precision']:.1%}, Recall: {results['recall']:.1%}"
                )
                
                return profile
            else:
                logger.info("Calibration cancelled")
                return None
                
        finally:
            self.is_calibrating = False
            self.calibration_mode = None
            self.stop()
    
    def save_profile(self, profile: CalibrationProfile):
        """Save calibration profile to file."""
        profiles_dir = Path.home() / '.bark_detector' / 'profiles'
        profiles_dir.mkdir(parents=True, exist_ok=True)
        
        profile_path = profiles_dir / f"{profile.name}.json"
        profile.save(profile_path)
        
        logger.info(f"💾 Profile saved: {profile_path}")
        return profile_path
    
    def load_profile(self, profile_name: str) -> CalibrationProfile:
        """Load calibration profile from file."""
        profiles_dir = Path.home() / '.bark_detector' / 'profiles'
        profile_path = profiles_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")
        
        profile = CalibrationProfile.load(profile_path)
        
        # Apply profile settings
        self.sensitivity = profile.sensitivity
        self.session_gap_threshold = profile.session_gap_threshold
        
        logger.info(f"📂 Profile loaded: {profile.name}")
        logger.info(f"  Sensitivity: {profile.sensitivity}")
        logger.info(f"  Notes: {profile.notes}")
        
        return profile
    
    def list_profiles(self) -> List[str]:
        """List available calibration profiles."""
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
    
    def analyze_violations_for_date(self, target_date: str) -> List[ViolationReport]:
        """
        Analyze recordings for a specific date and detect bylaw violations.
        
        Args:
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            List of detected violations for that date
        """
        recordings_dir = Path(self.output_dir)
        return self.violation_tracker.analyze_recordings_for_date(recordings_dir, target_date, self)
    
    def generate_violation_report(self, start_date: str, end_date: str) -> List[ViolationReport]:
        """
        Generate violation report for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of violations in the date range
        """
        return self.violation_tracker.violation_db.get_violations_by_date_range(start_date, end_date)
    
    def export_violations_csv(self, output_path: Path, start_date: str = None, end_date: str = None):
        """
        Export violations to CSV format for RDCO submission.
        
        Args:
            output_path: Path for output CSV file
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
        """
        if start_date and end_date:
            # Filter violations by date range
            violations = self.violation_tracker.violation_db.get_violations_by_date_range(start_date, end_date)
            
            # Create temporary database with filtered violations
            temp_db = ViolationDatabase()
            temp_db.violations = violations
            temp_db.export_to_csv(output_path)
        else:
            # Export all violations
            self.violation_tracker.violation_db.export_to_csv(output_path)
        
        logger.info(f"Violations exported to: {output_path}")
    
    def list_violations(self) -> List[ViolationReport]:
        """List all detected violations."""
        return self.violation_tracker.violation_db.violations
    
    def enable_real_time_violation_detection(self, enable: bool = True):
        """Enable or disable real-time violation detection during monitoring."""
        self.enable_real_time_violations = enable
        if enable:
            logger.info("Real-time violation detection enabled")
        else:
            logger.info("Real-time violation detection disabled")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced YAMNet Bark Detector v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal detection mode
  uv run bd.py                                    # Use default settings
  uv run bd.py --profile kelowna_dogs            # Use saved profile
  
  # Real-time calibration (spacebar feedback)  
  uv run bd.py --calibrate --duration 10 --save-profile kelowna_dogs
  
  # File-based calibration (more accurate)
  uv run bd.py --create-template bark_sample.wav # Create ground truth template
  uv run bd.py --calibrate-files --audio-files bark1.wav bark2.wav \\
               --ground-truth-files bark1_gt.json bark2_gt.json \\
               --save-profile kelowna_optimized
  
  # Mixed calibration (positive + negative files)
  uv run bd.py --calibrate-files \\
               --audio-files bark1.wav bark2.wav background.wav traffic.wav \\
               --ground-truth-files bark1_gt.json bark2_gt.json \\
               --save-profile mixed_calibration
  
  # Profile management
  uv run bd.py --list-profiles                   # Show available profiles
  uv run bd.py --list-convertible ~/Downloads    # Find Voice Memo files
  uv run bd.py --record bark_sample.wav          # Record calibration sample
  
  # Violation analysis
  uv run bd.py --analyze-violations 2025-08-03   # Analyze recordings for specific date
  uv run bd.py --violation-report 2025-08-01 2025-08-05  # Generate report for date range
  uv run bd.py --list-violations                 # List all detected violations
  uv run bd.py --export-violations violations.csv  # Export violations to CSV
        """
    )
    
    # Main modes
    parser.add_argument(
        '--calibrate', 
        action='store_true',
        help='Start real-time calibration mode'
    )
    
    parser.add_argument(
        '--calibrate-files', 
        action='store_true',
        help='Start file-based calibration mode'
    )
    
    parser.add_argument(
        '--duration', 
        type=int, 
        default=10,
        help='Calibration duration in minutes (default: 10)'
    )
    
    # Profile management
    parser.add_argument(
        '--profile', 
        type=str,
        help='Load calibration profile by name'
    )
    
    parser.add_argument(
        '--save-profile', 
        type=str,
        help='Save calibration as profile with given name'
    )
    
    parser.add_argument(
        '--list-profiles', 
        action='store_true',
        help='List available calibration profiles'
    )
    
    parser.add_argument(
        '--list-convertible', 
        type=str,
        help='List convertible audio files in specified directory'
    )
    
    parser.add_argument(
        '--record', 
        type=str,
        help='Record calibration sample to specified file (WAV format)'
    )
    
    # Violation analysis commands
    parser.add_argument(
        '--analyze-violations',
        type=str,
        help='Analyze recordings for violations on specific date (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--violation-report',
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        help='Generate violation report for date range (YYYY-MM-DD YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--list-violations',
        action='store_true',
        help='List all detected violations'
    )
    
    parser.add_argument(
        '--export-violations',
        type=str,
        help='Export violations to CSV file'
    )
    
    # File-based calibration
    parser.add_argument(
        '--audio-files', 
        nargs='+',
        help='Audio files for file-based calibration (WAV format)'
    )
    
    parser.add_argument(
        '--ground-truth-files', 
        nargs='+',
        help='Ground truth JSON files (optional, can be fewer than audio files for background/negative samples)'
    )
    
    parser.add_argument(
        '--create-template', 
        type=str,
        help='Create ground truth template for specified audio file'
    )
    
    parser.add_argument(
        '--sensitivity-range', 
        nargs=2, 
        type=float, 
        default=[0.01, 0.5],
        help='Sensitivity range for sweep (default: 0.01 0.5)'
    )
    
    parser.add_argument(
        '--steps', 
        type=int, 
        default=20,
        help='Number of steps in sensitivity sweep (default: 20)'
    )
    
    # Detection parameters
    parser.add_argument(
        '--sensitivity', 
        type=float, 
        default=0.05,
        help='Detection sensitivity (0.01-0.5, default: 0.05)'
    )
    
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='recordings',
        help='Output directory for recordings (default: recordings)'
    )
    
    return parser.parse_args()


def main():
    """Main function with command line support."""
    args = parse_arguments()
    
    logger.info("=" * 70)
    logger.info("Advanced YAMNet Bark Detector v3.0")
    logger.info("ML-based Detection with Legal Evidence Collection")
    logger.info("=" * 70)
    
    # Initialize detector
    config = {
        'sensitivity': args.sensitivity,
        'sample_rate': 16000,          # YAMNet requirement
        'chunk_size': 1024,
        'channels': 1,
        'quiet_duration': 30.0,
        'session_gap_threshold': 10.0,  # Recording sessions
        'output_dir': args.output_dir,
        'profile_name': args.save_profile
    }
    
    detector = AdvancedBarkDetector(**config)
    
    # Handle different modes
    if args.list_profiles:
        profiles = detector.list_profiles()
        if profiles:
            logger.info("📂 Available Calibration Profiles:")
            for profile in profiles:
                logger.info(f"  {profile['name']} - Sensitivity: {profile['sensitivity']:.3f}")
                logger.info(f"    Created: {profile['created'][:10]} - {profile['notes']}")
        else:
            logger.info("No calibration profiles found")
        return
    
    if args.list_convertible:
        calibrator = FileBasedCalibration(detector)
        directory = Path(args.list_convertible).expanduser()
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return
        
        logger.info(f"🔍 Scanning {directory} for convertible audio files...")
        found_files = calibrator.list_convertible_files(directory)
        
        if found_files:
            logger.info(f"📁 Found {len(found_files)} convertible audio files:")
            total_duration = 0
            
            for file_info in found_files:
                path = file_info['path']
                file_type = file_info['type']
                duration = file_info['duration']
                sample_rate = file_info['sample_rate']
                size_mb = file_info['size_mb']
                
                duration_str = f"{duration:.1f}s" if duration > 0 else "Unknown"
                sr_str = f"{sample_rate}Hz" if sample_rate > 0 else "Unknown"
                
                logger.info(f"  📄 {path.name}")
                logger.info(f"     Type: {file_type}, Duration: {duration_str}, Sample Rate: {sr_str}, Size: {size_mb:.1f}MB")
                
                if duration > 0:
                    total_duration += duration
            
            if total_duration > 0:
                total_min = total_duration / 60
                logger.info(f"\n📊 Total duration: {total_min:.1f} minutes")
                
            logger.info(f"\n💡 To use these files for calibration:")
            logger.info(f"  uv run bd.py --calibrate-files --audio-files {' '.join(str(f['path']) for f in found_files[:3])}")
        else:
            logger.info("No convertible audio files found")
            logger.info("Supported formats: WAV, M4A, MP3, AAC, FLAC (including Voice Memos)")
        return
    
    # Manual recording mode
    if args.record:
        output_path = Path(args.record)
        
        # Ensure the file has .wav extension
        if output_path.suffix.lower() != '.wav':
            output_path = output_path.with_suffix('.wav')
        
        logger.info("🎙️  Starting manual recording mode for calibration...")
        recorder = ManualRecorder(detector, output_path)
        recorder.start_recording()
        return
    
    # Violation analysis commands
    if args.analyze_violations:
        target_date = args.analyze_violations
        logger.info(f"🔍 Analyzing recordings for violations on {target_date}")
        try:
            violations = detector.analyze_violations_for_date(target_date)
            if violations:
                logger.info(f"✅ Found {len(violations)} violations:")
                for violation in violations:
                    logger.info(f"  📅 {violation.date} {violation.start_time} - {violation.end_time}")
                    logger.info(f"     Type: {violation.violation_type}, Duration: {violation.total_bark_duration/60:.1f}min")
            else:
                logger.info("✅ No violations detected for this date")
        except Exception as e:
            logger.error(f"❌ Error analyzing violations: {e}")
        return
    
    if args.violation_report:
        start_date, end_date = args.violation_report
        logger.info(f"📊 Generating violation report for {start_date} to {end_date}")
        try:
            violations = detector.generate_violation_report(start_date, end_date)
            if violations:
                logger.info(f"📋 Violation Report ({len(violations)} violations):")
                for violation in violations:
                    logger.info(f"  📅 {violation.date} {violation.start_time} - {violation.end_time}")
                    logger.info(f"     Type: {violation.violation_type}")
                    logger.info(f"     Bark Duration: {violation.total_bark_duration/60:.1f}min")
                    logger.info(f"     Incident Duration: {violation.total_incident_duration/60:.1f}min")
                    logger.info(f"     Audio Files: {', '.join(violation.audio_files)}")
            else:
                logger.info("📋 No violations found in date range")
        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
        return
    
    if args.list_violations:
        logger.info("📋 Listing all detected violations:")
        try:
            violations = detector.list_violations()
            if violations:
                logger.info(f"Found {len(violations)} total violations:")
                for violation in violations:
                    logger.info(f"  📅 {violation.date} {violation.start_time} - {violation.end_time}")
                    logger.info(f"     Type: {violation.violation_type}, Duration: {violation.total_bark_duration/60:.1f}min")
            else:
                logger.info("No violations detected yet")
        except Exception as e:
            logger.error(f"❌ Error listing violations: {e}")
        return
    
    if args.export_violations:
        output_path = Path(args.export_violations)
        logger.info(f"📄 Exporting violations to {output_path}")
        try:
            detector.export_violations_csv(output_path)
            logger.info(f"✅ Violations exported successfully")
        except Exception as e:
            logger.error(f"❌ Error exporting violations: {e}")
        return
    
    # Create ground truth template
    if args.create_template:
        audio_path = Path(args.create_template)
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return
        
        calibrator = FileBasedCalibration(detector)
        template_path = calibrator.create_ground_truth_template(audio_path)
        logger.info(f"✅ Template created: {template_path}")
        logger.info("Edit the template file to add bark timestamps, then run:")
        logger.info(f"  uv run bd.py --calibrate-files --audio-files {audio_path} --ground-truth-files {template_path}")
        return
    
    # Load profile if specified
    if args.profile:
        try:
            detector.load_profile(args.profile)
        except FileNotFoundError:
            logger.error(f"Profile '{args.profile}' not found")
            profiles = detector.list_profiles()
            if profiles:
                logger.info("Available profiles:")
                for profile in profiles:
                    logger.info(f"  {profile['name']}")
            return
    
    # Run calibration mode
    if args.calibrate:
        logger.info(f"🎯 Starting {args.duration}-minute calibration session")
        logger.info("Make sure dogs are likely to bark during this time!")
        
        profile = detector.start_calibration(args.duration)
        
        if profile:
            # Save profile if name provided
            if args.save_profile:
                detector.save_profile(profile)
                logger.info(f"✅ Calibration complete! Profile '{args.save_profile}' saved.")
                logger.info(f"   To use: uv run bd.py --profile {args.save_profile}")
            else:
                logger.info("✅ Calibration complete! Use --save-profile to save settings.")
        
        return
    
    # File-based calibration mode
    if args.calibrate_files:
        if not args.audio_files:
            logger.error("--audio-files required for file-based calibration")
            logger.info("Example: uv run bd.py --calibrate-files --audio-files bark1.wav bark2.wav")
            return
        
        logger.info("📁 Starting file-based calibration...")
        
        calibrator = FileBasedCalibration(detector)
        
        # Add test files
        audio_paths = [Path(f) for f in args.audio_files]
        ground_truth_paths = []
        
        if args.ground_truth_files:
            if len(args.ground_truth_files) > len(args.audio_files):
                logger.error("Cannot have more ground truth files than audio files")
                return
            ground_truth_paths = [Path(f) for f in args.ground_truth_files]
        
        # Validate files exist
        for audio_path in audio_paths:
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return
        
        for gt_path in ground_truth_paths:
            if not gt_path.exists():
                logger.error(f"Ground truth file not found: {gt_path}")
                return
        
        # Add files to calibrator
        for i, audio_path in enumerate(audio_paths):
            gt_path = ground_truth_paths[i] if i < len(ground_truth_paths) else None
            calibrator.add_test_file(audio_path, gt_path)
        
        # Run calibration
        try:
            results = calibrator.run_sensitivity_sweep(
                sensitivity_range=tuple(args.sensitivity_range),
                steps=args.steps
            )
            
            # Create and save profile if requested
            if args.save_profile:
                profile = calibrator.generate_calibration_profile(results, args.save_profile)
                detector.save_profile(profile)
                logger.info(f"✅ File-based calibration complete! Profile '{args.save_profile}' saved.")
                logger.info(f"   To use: uv run bd.py --profile {args.save_profile}")
            else:
                logger.info("✅ File-based calibration complete! Use --save-profile to save settings.")
                
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
        
        return
    
    # Normal detection mode
    logger.info("🐕 Starting bark detection...")
    if args.profile:
        logger.info(f"📂 Using profile: {args.profile}")
    logger.info(f"🎛️ Sensitivity: {detector.sensitivity:.3f}")
    logger.info("Press Ctrl+C to stop")
    
    detector.run()


if __name__ == "__main__":
    main()