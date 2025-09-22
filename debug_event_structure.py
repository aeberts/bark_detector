#!/usr/bin/env python3
"""
Debug script to check the actual structure of events returned by the detector
"""

import librosa
import numpy as np
from pathlib import Path
from bark_detector.core.detector import AdvancedBarkDetector

def test_detector_events():
    """Test what the detector actually returns for a sample audio file."""

    # Initialize detector
    detector = AdvancedBarkDetector(
        sensitivity=0.68,
        analysis_sensitivity=0.30,
        output_dir="recordings"
    )

    # Find a sample audio file from 2025-09-17
    audio_file = Path("/Users/zand/dev/bark_detector/recordings/2025-09-17/bark_recording_20250917_062651.wav")

    if not audio_file.exists():
        print(f"Audio file not found: {audio_file}")
        return

    print(f"Analyzing: {audio_file.name}")

    # Load audio
    audio_data, sr = librosa.load(str(audio_file), sr=detector.sample_rate)
    print(f"Audio duration: {len(audio_data) / sr:.2f} seconds")

    # Analyze with analysis sensitivity
    bark_events = detector._detect_barks_in_buffer_with_sensitivity(audio_data, detector.analysis_sensitivity)

    print(f"Detected {len(bark_events)} bark events:")

    for i, event in enumerate(bark_events):
        print(f"  Event {i+1}:")
        print(f"    start_time: {event.start_time:.3f}s")
        print(f"    end_time: {event.end_time:.3f}s")
        print(f"    duration: {event.end_time - event.start_time:.3f}s")
        print(f"    confidence: {event.confidence:.3f}")
        print(f"    triggering_classes: {event.triggering_classes}")
        print()

    # Test the violation analysis with these actual events
    print("="*50)
    print("TESTING VIOLATION DETECTION WITH ACTUAL EVENTS")
    print("="*50)

    from bark_detector.legal.tracker import LegalViolationTracker
    tracker = LegalViolationTracker()

    # Create absolute timestamp events (simulating the real process)
    absolute_events = []
    for event in bark_events:
        absolute_event = type('BarkEvent', (), {
            'start_time': event.start_time,  # Using relative time for test
            'end_time': event.end_time,
            'confidence': event.confidence
        })()
        absolute_events.append(absolute_event)

    continuous_violations = tracker._analyze_continuous_violations_from_events(absolute_events)
    sporadic_violations = tracker._analyze_sporadic_violations_from_events(absolute_events)

    print(f"Continuous violations: {len(continuous_violations)}")
    print(f"Sporadic violations: {len(sporadic_violations)}")

    # Calculate total bark duration
    total_duration = sum(event.end_time - event.start_time for event in absolute_events)
    print(f"Total bark duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")

if __name__ == "__main__":
    test_detector_events()