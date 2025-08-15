"""Core data models for bark detection system"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union


def seconds_to_timestamp(seconds: float) -> str:
    """Convert decimal seconds to HH:MM:SS.mmm format.
    
    Args:
        seconds: Time in decimal seconds (e.g., 125.450)
        
    Returns:
        Formatted timestamp string (e.g., "00:02:05.450")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    # Split seconds into whole seconds and milliseconds
    whole_seconds = int(secs)
    # Truncate milliseconds to match test expectations, but handle precision
    milliseconds_precise = (secs - whole_seconds) * 1000
    milliseconds = int(milliseconds_precise)
    
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"


def timestamp_to_seconds(timestamp: str) -> float:
    """Convert HH:MM:SS.mmm format to decimal seconds.
    
    Supports flexible formats:
    - SS.mmm (e.g., "05.250" = 5.25 seconds)
    - MM:SS.mmm (e.g., "01:05.250" = 65.25 seconds)  
    - HH:MM:SS.mmm (e.g., "01:01:05.250" = 3665.25 seconds)
    
    Args:
        timestamp: Formatted timestamp string
        
    Returns:
        Time in decimal seconds
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    timestamp = timestamp.strip()
    
    # Check for different patterns with proper precedence
    # Pattern 1: HH:MM:SS.mmm (most specific - must match first)
    hms_pattern = r'^(\d{1,2}):(\d{2}):(\d{2})\.(\d{1,3})$'
    hms_match = re.match(hms_pattern, timestamp)
    
    if hms_match:
        hours_str, minutes_str, seconds_str, milliseconds_str = hms_match.groups()
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)
        
        # Validate ranges
        if hours > 23 or minutes > 59 or seconds > 59:
            raise ValueError(f"Invalid timestamp format: {timestamp}. Time values out of range")
            
        milliseconds = int(milliseconds_str.ljust(3, '0')[:3])  # Pad or truncate to 3 digits
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    
    # Pattern 2: MM:SS.mmm
    ms_pattern = r'^(\d{1,2}):(\d{2})\.(\d{1,3})$'
    ms_match = re.match(ms_pattern, timestamp)
    
    if ms_match:
        minutes_str, seconds_str, milliseconds_str = ms_match.groups()
        minutes = int(minutes_str)
        seconds = int(seconds_str)
        
        # Validate ranges
        if minutes > 59 or seconds > 59:
            raise ValueError(f"Invalid timestamp format: {timestamp}. Time values out of range")
            
        milliseconds = int(milliseconds_str.ljust(3, '0')[:3])  # Pad or truncate to 3 digits
        return minutes * 60 + seconds + milliseconds / 1000.0
    
    # Pattern 3: SS.mmm - only if milliseconds part has exactly 3 digits to avoid ambiguity
    s_pattern = r'^(\d{1,2})\.(\d{3})$'
    s_match = re.match(s_pattern, timestamp)
    
    if s_match:
        seconds_str, milliseconds_str = s_match.groups()
        seconds = int(seconds_str)
        
        # Validate ranges
        if seconds > 59:
            raise ValueError(f"Invalid timestamp format: {timestamp}. Seconds out of range")
            
        milliseconds = int(milliseconds_str)
        return seconds + milliseconds / 1000.0
    
    raise ValueError(f"Invalid timestamp format: {timestamp}. Expected HH:MM:SS.mmm, MM:SS.mmm, or SS.mmm")


def detect_timestamp_format(value: Union[str, float, int]) -> str:
    """Detect whether a timestamp is in seconds (float) or HH:MM:SS.mmm (string) format.
    
    Args:
        value: Timestamp value to check
        
    Returns:
        Format type: "seconds" or "timestamp"
    """
    if isinstance(value, (int, float)):
        return "seconds"
    elif isinstance(value, str):
        # Try to parse as timestamp format first
        try:
            timestamp_to_seconds(value)
            return "timestamp"
        except ValueError:
            # If timestamp parsing failed, check if it's a string representation of a number
            try:
                float(value)
                return "seconds"
            except ValueError:
                raise ValueError(f"Unrecognized timestamp format: {value}")
    else:
        raise ValueError(f"Unsupported timestamp type: {type(value)}")


@dataclass
class BarkEvent:
    """Represents a detected barking event."""
    start_time: float
    end_time: float
    confidence: float
    intensity: float = 0.0
    # Class analysis fields for debugging false positives
    triggering_classes: Optional[List[str]] = None  # Which YAMNet classes triggered this detection
    class_confidences: Optional[dict] = None  # Confidence scores by class name


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
    source_file: Optional[Path] = None
    file_start_timestamp: Optional[float] = None


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
    """Represents a ground truth bark event with timestamp.
    
    Supports both decimal seconds (legacy) and HH:MM:SS.mmm timestamp formats.
    Times are stored internally as float seconds for compatibility.
    """
    start_time: float
    end_time: float
    description: str = ""
    confidence_expected: float = 1.0
    
    def __post_init__(self):
        """Convert string timestamps to float seconds if needed."""
        # Handle both legacy float and new string timestamp formats
        if isinstance(self.start_time, str):
            self.start_time = timestamp_to_seconds(self.start_time)
        if isinstance(self.end_time, str):
            self.end_time = timestamp_to_seconds(self.end_time)
            
        # Validate that start_time < end_time
        if self.start_time >= self.end_time:
            raise ValueError(f"Invalid event: start_time ({self.start_time}s) must be < end_time ({self.end_time}s)")
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GroundTruthEvent':
        """Create GroundTruthEvent from dictionary with format auto-detection."""
        return cls(
            start_time=data['start_time'],  # __post_init__ will handle conversion
            end_time=data['end_time'],      # __post_init__ will handle conversion
            description=data.get('description', ''),
            confidence_expected=data.get('confidence_expected', 1.0)
        )
    
    def to_dict(self, use_timestamp_format: bool = True) -> dict:
        """Convert to dictionary with optional timestamp format.
        
        Args:
            use_timestamp_format: If True, use HH:MM:SS.mmm format. If False, use float seconds.
        """
        if use_timestamp_format:
            return {
                'start_time': seconds_to_timestamp(self.start_time),
                'end_time': seconds_to_timestamp(self.end_time),
                'description': self.description,
                'confidence_expected': self.confidence_expected
            }
        else:
            return {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'description': self.description,
                'confidence_expected': self.confidence_expected
            }
    
    @property
    def duration(self) -> float:
        """Duration of the event in seconds."""
        return self.end_time - self.start_time
    
    @property
    def start_timestamp(self) -> str:
        """Start time in HH:MM:SS.mmm format."""
        return seconds_to_timestamp(self.start_time)
    
    @property
    def end_timestamp(self) -> str:
        """End time in HH:MM:SS.mmm format."""
        return seconds_to_timestamp(self.end_time)