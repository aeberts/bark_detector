#!/usr/bin/env python3
"""
Debug script to investigate violation boundary markers.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bark_detector.legal.database import ViolationDatabase

def investigate_violation_boundaries():
    """Investigate violation boundary events and their processing."""

    # Load the data for 2025-09-23
    violation_db = ViolationDatabase()
    violations = violation_db.load_violations_new("2025-09-23")
    bark_events = violation_db.load_events("2025-09-23")

    target_id = "8fdaba48-428a-411e-b1ad-42084ad43c0e"

    print(f"Loaded {len(violations)} violations and {len(bark_events)} events")
    print(f"Target event ID: {target_id}")

    # Find the violation containing our target event
    target_violation = None
    for violation in violations:
        if target_id in violation.barkEventIds:
            target_violation = violation
            break

    if not target_violation:
        print("Target event not found in any violation!")
        return

    print(f"\n--- Target Violation Details ---")
    print(f"Type: {target_violation.type}")
    print(f"Start: {target_violation.startTimestamp}")
    print(f"End: {target_violation.endTimestamp}")
    print(f"Event IDs in violation: {len(target_violation.barkEventIds)}")

    # Get all events for this violation, sorted by time
    violation_events = []
    for event in bark_events:
        if event.bark_id in target_violation.barkEventIds:
            violation_events.append(event)

    # Sort events by time
    violation_events.sort(key=lambda e: f"{e.realworld_date}T{e.realworld_time}")

    print(f"\n--- Violation Events (first 5 and last 5) ---")
    print(f"Total events in violation: {len(violation_events)}")

    # Show first 5 events
    print(f"\nFirst 5 events:")
    for i, event in enumerate(violation_events[:5]):
        is_target = "*** TARGET ***" if event.bark_id == target_id else ""
        print(f"  {i+1}. {event.realworld_time} - ID: {event.bark_id[:8]}... - Intensity: {event.intensity:.6f} {is_target}")

    # Show last 5 events
    print(f"\nLast 5 events:")
    for i, event in enumerate(violation_events[-5:]):
        idx = len(violation_events) - 5 + i + 1
        is_target = "*** TARGET ***" if event.bark_id == target_id else ""
        print(f"  {idx}. {event.realworld_time} - ID: {event.bark_id[:8]}... - Intensity: {event.intensity:.6f} {is_target}")

    # Parse violation timestamps to get exact times
    start_dt = datetime.fromisoformat(target_violation.startTimestamp.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(target_violation.endTimestamp.replace('Z', '+00:00'))

    start_hour = start_dt.hour + start_dt.minute / 60
    end_hour = end_dt.hour + end_dt.minute / 60

    print(f"\n--- Violation Boundary Analysis ---")
    print(f"Violation start time: {start_dt.strftime('%H:%M:%S')} (hour: {start_hour:.3f})")
    print(f"Violation end time: {end_dt.strftime('%H:%M:%S')} (hour: {end_hour:.3f})")

    # Check if target event time matches violation start time
    target_event = next(e for e in violation_events if e.bark_id == target_id)
    target_time = f"{target_event.realworld_date}T{target_event.realworld_time}.000Z"
    target_dt = datetime.fromisoformat(target_time)

    print(f"\nTarget event time: {target_dt.strftime('%H:%M:%S')}")
    print(f"Is target event at violation start? {target_dt == start_dt}")
    print(f"Is target event the first event? {violation_events[0].bark_id == target_id}")

    # Show the axvline boundary markers that will be plotted
    print(f"\n--- Boundary Markers (axvline commands) ---")
    print(f"These are FULL HEIGHT lines from y=0 to y=1.0:")

    # Simulate the boundary marker logic from pdf_generator.py
    if 6 <= start_hour <= 20:  # Within 6am-8pm window
        plot_start = max(6, start_hour)
        color = '#DC2626' if target_violation.type == "Continuous" else '#F59E0B'
        print(f"  Start marker: ax.axvline(x={plot_start:.3f}, color='{color}', alpha=0.6, linewidth=2.5)")

    if 6 <= end_hour <= 20:  # Within 6am-8pm window
        plot_end = min(20, end_hour)
        if plot_end != plot_start:
            print(f"  End marker: ax.axvline(x={plot_end:.3f}, color='{color}', alpha=0.6, linewidth=2.5)")

    print(f"\n--- CONCLUSION ---")
    print(f"The 1.0 intensity you see is NOT the event intensity!")
    print(f"It's a violation boundary marker (axvline) that goes from 0 to 1.0 to mark the start/end of violations.")
    print(f"Your target event has actual intensity: {target_event.intensity:.6f}")

if __name__ == "__main__":
    investigate_violation_boundaries()