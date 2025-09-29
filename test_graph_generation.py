#!/usr/bin/env python3
"""
Test script to generate the actual graph and inspect intensity values.
"""

import sys
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt

# Add current directory to path to import bark_detector modules
sys.path.insert(0, str(Path(__file__).parent))

from bark_detector.utils.pdf_generator import PDFGenerationService, PDFConfig
from bark_detector.legal.database import ViolationDatabase

def test_activity_timeline_generation():
    """Test the activity timeline generation and print intensity values."""

    # Load the data for 2025-09-23
    violation_db = ViolationDatabase()
    violations = violation_db.load_violations_new("2025-09-23")
    bark_events = violation_db.load_events("2025-09-23")

    print(f"Loaded {len(violations)} violations and {len(bark_events)} events")

    # Create PDF service and config
    config = PDFConfig()

    # Create mapping of bark events to violation types for color coding (copied from pdf_generator.py)
    bark_event_colors = {}
    for violation in violations:
        color = '#DC2626' if violation.type == "Continuous" else '#F59E0B'  # Red for continuous, orange for intermittent
        for bark_id in violation.barkEventIds:
            bark_event_colors[bark_id] = color

    # Track our target event
    target_id = "8fdaba48-428a-411e-b1ad-42084ad43c0e"
    target_event_processed = False

    print(f"\nProcessing events for visualization:")
    event_count = 0

    # Process events (copied logic from _generate_activity_timeline)
    for event in bark_events:
        # Parse event timestamp
        event_dt = datetime.fromisoformat(f"{event.realworld_date}T{event.realworld_time}.000Z")
        event_hour = event_dt.hour + event_dt.minute / 60

        # Only process events within 6am-8pm window
        if 6 <= event_hour <= 20:
            event_count += 1

            # Determine color based on violation association
            color = bark_event_colors.get(event.bark_id, '#9CA3AF')  # Gray for non-violation events

            # Process intensity (exact logic from pdf_generator.py)
            intensity = getattr(event, 'intensity', config.default_intensity)
            # Use default intensity if intensity is 0.0 (missing/invalid data)
            if intensity == 0.0:
                intensity = config.default_intensity

            # Check if this is our target event
            if event.bark_id == target_id:
                target_event_processed = True
                print(f"\n*** TARGET EVENT PROCESSED ***")
                print(f"  ID: {event.bark_id}")
                print(f"  Time: {event.realworld_time}")
                print(f"  Hour: {event_hour}")
                print(f"  Raw intensity: {event.intensity}")
                print(f"  Processed intensity: {intensity}")
                print(f"  Color: {color}")
                print(f"  In violation? {event.bark_id in bark_event_colors}")

            # Print first few events for debugging
            if event_count <= 5:
                print(f"  Event {event_count}: {event.realworld_time}, intensity: {event.intensity} -> {intensity}")

    print(f"\nTotal events in 6am-8pm window: {event_count}")
    print(f"Target event processed: {target_event_processed}")

    # Also check the y-axis configuration
    print(f"\nY-axis configuration:")
    print(f"  Y-axis range: 0 to 1")
    print(f"  Y-axis ticks: [0, 0.2, 0.4, 0.6, 0.8, 1.0]")
    print(f"  Y-axis labels: ['0.0', '0.2', '0.4', '0.6', '0.8', '1.0']")

if __name__ == "__main__":
    test_activity_timeline_generation()