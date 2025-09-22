#!/usr/bin/env python3
"""Debug script to test violation detection algorithm"""

import sys
sys.path.insert(0, '/Users/zand/dev/bark_detector')

from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.core.models import BarkEvent
from unittest.mock import Mock
import tempfile
from pathlib import Path
import numpy as np
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Disable numba to see pure Python execution
import os
os.environ['NUMBA_DISABLE_JIT'] = '1'

# Create test setup
tracker = LegalViolationTracker(interactive=False)
mock_detector = Mock()
mock_detector.sample_rate = 16000
mock_detector.session_gap_threshold = 10.0
mock_detector.analysis_sensitivity = 0.30

# Create mock bark events for continuous violation (≤10s gaps, ≥5min session)
mock_bark_events = [
    BarkEvent(start_time=10.0, end_time=20.0, confidence=0.8, triggering_classes=["Bark"]),   # Event 1
    BarkEvent(start_time=25.0, end_time=35.0, confidence=0.8, triggering_classes=["Bark"]),   # Event 2 (5s gap)
    BarkEvent(start_time=40.0, end_time=50.0, confidence=0.8, triggering_classes=["Bark"]),   # Event 3 (5s gap)
    BarkEvent(start_time=55.0, end_time=65.0, confidence=0.8, triggering_classes=["Bark"]),   # Event 4 (5s gap)
    BarkEvent(start_time=70.0, end_time=80.0, confidence=0.8, triggering_classes=["Bark"]),   # Event 5 (5s gap)
    BarkEvent(start_time=85.0, end_time=95.0, confidence=0.8, triggering_classes=["Bark"]),   # Event 6 (5s gap)
    BarkEvent(start_time=100.0, end_time=110.0, confidence=0.8, triggering_classes=["Bark"]), # Event 7 (5s gap)
    BarkEvent(start_time=120.0, end_time=130.0, confidence=0.8, triggering_classes=["Bark"]), # Event 8 (10s gap - max allowed)
    BarkEvent(start_time=140.0, end_time=150.0, confidence=0.8, triggering_classes=["Bark"]), # Event 9 (10s gap)
    BarkEvent(start_time=160.0, end_time=170.0, confidence=0.8, triggering_classes=["Bark"]), # Event 10 (10s gap)
    BarkEvent(start_time=180.0, end_time=190.0, confidence=0.8, triggering_classes=["Bark"]), # Event 11 (10s gap)
    BarkEvent(start_time=200.0, end_time=210.0, confidence=0.8, triggering_classes=["Bark"]), # Event 12 (10s gap)
    BarkEvent(start_time=220.0, end_time=230.0, confidence=0.8, triggering_classes=["Bark"]), # Event 13 (10s gap)
    BarkEvent(start_time=240.0, end_time=250.0, confidence=0.8, triggering_classes=["Bark"]), # Event 14 (10s gap)
    BarkEvent(start_time=260.0, end_time=270.0, confidence=0.8, triggering_classes=["Bark"]), # Event 15 (10s gap)
    BarkEvent(start_time=280.0, end_time=290.0, confidence=0.8, triggering_classes=["Bark"]), # Event 16 (10s gap)
    BarkEvent(start_time=300.0, end_time=310.0, confidence=0.8, triggering_classes=["Bark"]), # Event 17 (10s gap)
    BarkEvent(start_time=320.0, end_time=330.0, confidence=0.8, triggering_classes=["Bark"]), # Event 18 (10s gap) - Session duration: 320-10 = 310s = 5.17min > 5min threshold
]

def debug_mock_method(audio_data, sensitivity):
    print(f"DEBUG: Mock method called with audio_data shape: {audio_data.shape if hasattr(audio_data, 'shape') else 'no shape'}, sensitivity: {sensitivity}")
    return mock_bark_events

mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(side_effect=debug_mock_method)

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)

    # Create test recording file
    date_folder = temp_path / "2025-08-14"
    date_folder.mkdir()
    test_file = date_folder / "bark_recording_20250814_120000.wav"
    test_file.touch()

    print(f"Testing with {len(mock_bark_events)} bark events")
    print(f"Session duration: {mock_bark_events[-1].start_time - mock_bark_events[0].start_time} seconds")

    violations = tracker.analyze_recordings_for_date(temp_path, "2025-08-14", mock_detector)

    print(f"Found {len(violations)} violations")
    for i, v in enumerate(violations):
        print(f"  {i+1}. {v.violation_type} - {v.start_time} to {v.end_time}")

    print(f"Mock detector called {mock_detector._detect_barks_in_buffer_with_sensitivity.call_count} times")