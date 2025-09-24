"""Legal evidence data models"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from ..core.models import BarkingSession


@dataclass
class AlgorithmInputEvent:
    """Algorithm input event for violation detection processing."""
    id: str  # Unique identifier (mapped from bark_id)
    startTimestamp: str  # ISO 8601 format timestamp

    @classmethod
    def from_persisted_bark_event(cls, event: 'PersistedBarkEvent') -> 'AlgorithmInputEvent':
        """Convert PersistedBarkEvent to AlgorithmInputEvent format."""
        # Combine realworld_date and realworld_time into ISO 8601 format
        datetime_str = f"{event.realworld_date}T{event.realworld_time}.000Z"
        return cls(
            id=event.bark_id,
            startTimestamp=datetime_str
        )


@dataclass
class LegalIntermittentSession:
    """Represents a legal intermittent session for bylaw violation detection."""
    start_time: float
    end_time: float
    barking_sessions: List[BarkingSession]
    total_bark_duration: float
    total_session_duration: float
    violation_type: Optional[str] = None  # "Constant" or "Intermittent"
    is_violation: bool = False


@dataclass
class PersistedBarkEvent:
    """Represents a raw, persistent log of every individual bark event detected during analysis."""
    realworld_date: str  # YYYY-MM-DD format
    realworld_time: str  # HH:MM:SS format when bark occurred in real world
    bark_id: str  # Unique identifier for this bark event
    bark_type: str  # Type of bark detection (e.g., "Bark", "Howl", "Yip")
    est_dog_size: Optional[str]  # Estimated dog size (nullable for future use)
    audio_file_name: str  # Name of the audio file containing this bark
    bark_audiofile_timestamp: str  # HH:MM:SS.mmm timestamp within the audio file
    confidence: float  # Detection confidence score (0.0 to 1.0)
    intensity: float  # Bark intensity/volume measurement
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersistedBarkEvent':
        """Create instance from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PersistedBarkEvent':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Violation:
    """Enhanced violation model with three-timestamp architecture for legal compliance."""
    type: str  # "Continuous" or "Intermittent"
    startTimestamp: str  # ISO 8601 - when barking incident began (legal compliance)
    violationTriggerTimestamp: str  # ISO 8601 - when violation was detected (system audit)
    endTimestamp: str  # ISO 8601 - when barking incident actually ended (legal compliance)
    durationMinutes: float  # Total incident duration for legal evidence (endTimestamp - startTimestamp)
    violationDurationMinutes: float  # Duration from trigger to end (endTimestamp - violationTriggerTimestamp)
    barkEventIds: List[str]  # Array of UUIDs of all bark events in the session
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Violation':
        """Create instance from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Violation':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ViolationReport:
    """Presentation-layer object for violation display and reporting. Generated on-demand from Violation data."""
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM AM/PM format
    end_time: str  # HH:MM AM/PM format
    violation_type: str  # "Constant" or "Intermittent"
    total_bark_duration: float  # Total barking time in seconds
    total_incident_duration: float  # Total incident time in seconds
    audio_files: List[str]  # List of associated recording files
    audio_file_start_times: List[str]  # Start times relative to each audio file (HH:MM:SS)
    audio_file_end_times: List[str]  # End times relative to each audio file (HH:MM:SS)
    confidence_scores: List[float]  # Confidence scores from detections
    peak_confidence: float
    avg_confidence: float
    created_timestamp: str  # ISO format timestamp when report was generated

    @classmethod
    def from_violation(cls, violation: 'Violation', bark_events: List['PersistedBarkEvent'] = None,
                      audio_files: List[str] = None) -> 'ViolationReport':
        """Create ViolationReport from Violation object and associated data.

        Args:
            violation: Source Violation object
            bark_events: Associated PersistedBarkEvent objects for this violation
            audio_files: List of audio file paths associated with this violation

        Returns:
            ViolationReport object for presentation/reporting
        """
        from datetime import datetime

        # Parse ISO timestamps for presentation formatting
        start_dt = datetime.fromisoformat(violation.startTimestamp.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(violation.endTimestamp.replace('Z', '+00:00'))

        # Format times for presentation
        start_time_str = start_dt.strftime("%I:%M %p").lstrip('0')
        end_time_str = end_dt.strftime("%I:%M %p").lstrip('0')
        date_str = start_dt.strftime("%Y-%m-%d")

        # Calculate confidence metrics from bark events
        confidence_scores = []
        peak_confidence = 0.0
        avg_confidence = 0.0

        if bark_events and hasattr(bark_events, '__iter__') and not isinstance(bark_events, str):
            try:
                confidence_scores = [event.confidence for event in bark_events
                                   if hasattr(event, 'bark_id') and event.bark_id in violation.barkEventIds]
                if confidence_scores:
                    peak_confidence = max(confidence_scores)
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
            except (AttributeError, TypeError):
                # Handle mocked or invalid bark_events gracefully
                pass

        # Map violation type
        violation_type = "Constant" if violation.type == "Continuous" else "Intermittent"

        # Set default audio files if not provided
        if audio_files is None:
            audio_files = []

        return cls(
            date=date_str,
            start_time=start_time_str,
            end_time=end_time_str,
            violation_type=violation_type,
            total_bark_duration=violation.durationMinutes * 60,  # Convert to seconds (total incident duration for barking)
            total_incident_duration=violation.durationMinutes * 60,  # Convert to seconds (total incident duration)
            audio_files=audio_files,
            audio_file_start_times=[start_time_str],
            audio_file_end_times=[end_time_str],
            confidence_scores=confidence_scores,
            peak_confidence=peak_confidence,
            avg_confidence=avg_confidence,
            created_timestamp=datetime.now().isoformat()
        )