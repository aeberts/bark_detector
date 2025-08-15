"""Legal evidence data models"""

from dataclasses import dataclass
from typing import List, Optional
from ..core.models import BarkingSession


@dataclass
class LegalSporadicSession:
    """Represents a legal sporadic session for bylaw violation detection."""
    start_time: float
    end_time: float
    barking_sessions: List[BarkingSession]
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
    audio_file_start_times: List[str]  # Start times relative to each audio file (HH:MM:SS)
    audio_file_end_times: List[str]  # End times relative to each audio file (HH:MM:SS)
    confidence_scores: List[float]  # Confidence scores from detections
    peak_confidence: float
    avg_confidence: float
    created_timestamp: str  # ISO format timestamp when report was generated