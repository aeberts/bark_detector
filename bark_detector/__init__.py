"""Bark Detector - Advanced YAMNet ML-based bark detection system

A modular bark detection system for collecting evidence of dog barking incidents.
"""

__version__ = "3.0.0"
__author__ = "Bark Detector Project"

# Main components for easy importing
from .core.detector import AdvancedBarkDetector
from .core.models import BarkEvent, BarkingSession, CalibrationProfile
from .legal.tracker import LegalViolationTracker
from .recording.recorder import ManualRecorder
from .calibration.file_calibration import FileBasedCalibration

__all__ = [
    'AdvancedBarkDetector',
    'BarkEvent', 
    'BarkingSession',
    'CalibrationProfile',
    'LegalViolationTracker',
    'ManualRecorder',
    'FileBasedCalibration'
]