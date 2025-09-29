#!/usr/bin/env python3
"""
Test the intensity logic to understand the discrepancy.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bark_detector.utils.pdf_generator import PDFConfig
from bark_detector.legal.database import ViolationDatabase

def test_intensity_logic():
    """Test the intensity processing logic."""

    # Load the data
    violation_db = ViolationDatabase()
    violations = violation_db.load_violations_new("2025-09-23")
    bark_events = violation_db.load_events("2025-09-23")

    config = PDFConfig()
    target_id = "8fdaba48-428a-411e-b1ad-42084ad43c0e"

    # Find the target event
    target_event = None
    for event in bark_events:
        if event.bark_id == target_id:
            target_event = event
            break

    if not target_event:
        print("Target event not found!")
        return

    print(f"Target event intensity: {target_event.intensity}")
    print(f"Default intensity: {config.default_intensity}")

    # Test both code paths
    print(f"\n--- Timeline Graph Logic (_generate_activity_timeline) ---")
    timeline_intensity = getattr(target_event, 'intensity', config.default_intensity)
    if timeline_intensity == 0.0:
        timeline_intensity = config.default_intensity
    print(f"Timeline intensity: {timeline_intensity}")

    print(f"\n--- Violation Detail Graph Logic (_generate_bark_intensity_graph) ---")
    detail_intensity = target_event.intensity if target_event.intensity > 0 else config.default_intensity
    print(f"Detail graph intensity: {detail_intensity}")

    print(f"\n--- Testing the condition ---")
    print(f"target_event.intensity > 0: {target_event.intensity > 0}")
    print(f"target_event.intensity > 0.0: {target_event.intensity > 0.0}")
    print(f"target_event.intensity != 0.0: {target_event.intensity != 0.0}")

    # Check if this event is part of a violation
    associated_violation = None
    for violation in violations:
        if target_id in violation.barkEventIds:
            associated_violation = violation
            break

    if associated_violation:
        print(f"\n--- Associated Violation ---")
        print(f"Violation type: {associated_violation.type}")
        print(f"Start: {associated_violation.startTimestamp}")
        print(f"End: {associated_violation.endTimestamp}")

        # Get all events for this violation
        violation_events = [e for e in bark_events if e.bark_id in associated_violation.barkEventIds]
        print(f"Events in violation: {len(violation_events)}")

        # Test the intensity processing for the violation detail graph
        print(f"\n--- Violation Events Intensity Processing ---")
        for i, event in enumerate(violation_events[:5]):  # First 5 events
            processed_intensity = event.intensity if event.intensity > 0 else config.default_intensity
            print(f"  Event {i+1}: {event.realworld_time}, raw={event.intensity:.6f}, processed={processed_intensity:.6f}")

if __name__ == "__main__":
    test_intensity_logic()