"""Core data models for bark detection system"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


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
    """Represents a ground truth bark event with timestamp."""
    start_time: float
    end_time: float
    description: str = ""
    confidence_expected: float = 1.0