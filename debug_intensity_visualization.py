#!/usr/bin/env python3
"""
Debug script to reproduce the intensity visualization issue.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path to import bark_detector modules
sys.path.insert(0, str(Path(__file__).parent))

from bark_detector.utils.pdf_generator import PDFGenerationService
from bark_detector.legal.database import ViolationDatabase

def debug_intensity_visualization():
    """Debug the intensity visualization for the specific event."""

    # Load the data for 2025-09-23
    violation_db = ViolationDatabase()
    violations = violation_db.load_violations_new("2025-09-23")
    bark_events = violation_db.load_events("2025-09-23")

    print(f"Loaded {len(violations)} violations and {len(bark_events)} events")

    # Find the specific event
    target_id = "8fdaba48-428a-411e-b1ad-42084ad43c0e"
    target_event = None

    for event in bark_events:
        if event.bark_id == target_id:
            target_event = event
            break

    if target_event:
        print(f"\nFound target event:")
        print(f"  ID: {target_event.bark_id}")
        print(f"  Time: {target_event.realworld_time}")
        print(f"  Intensity: {target_event.intensity}")
        print(f"  Confidence: {target_event.confidence}")

        # Check how this event is processed in the visualization
        event_dt = datetime.fromisoformat(f"{target_event.realworld_date}T{target_event.realworld_time}.000Z")
        event_hour = event_dt.hour + event_dt.minute / 60

        print(f"\nVisualization processing:")
        print(f"  Event hour: {event_hour}")
        print(f"  Is in 6am-8pm window? {6 <= event_hour <= 20}")

        # Check intensity processing logic from pdf_generator.py
        from bark_detector.utils.pdf_generator import PDFConfig
        config = PDFConfig()

        intensity = getattr(target_event, 'intensity', config.default_intensity)
        if intensity == 0.0:
            intensity = config.default_intensity

        print(f"  Processed intensity: {intensity}")
        print(f"  Default intensity: {config.default_intensity}")

        # Check if the event is associated with a violation
        associated_violations = []
        for violation in violations:
            if target_id in violation.barkEventIds:
                associated_violations.append(violation)

        print(f"\nAssociated violations: {len(associated_violations)}")
        for i, v in enumerate(associated_violations):
            print(f"  Violation {i+1}: {v.type} from {v.startTimestamp} to {v.endTimestamp}")

    else:
        print(f"Target event {target_id} not found!")

if __name__ == "__main__":
    debug_intensity_visualization()