#!/usr/bin/env python3
"""
Debug script to investigate why 1490 bark events resulted in 0 violations
for 2025-09-17.
"""

import json
from pathlib import Path
from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.legal.database import ViolationDatabase

def analyze_event_gaps():
    """Analyze the gaps between bark events to understand violation detection failure."""

    # Load the events data
    events_file = Path("/Users/zand/dev/bark_detector/violations/2025-09-17/2025-09-17_events.json")
    with open(events_file) as f:
        data = json.load(f)

    events = data['events']
    print(f"Total events: {len(events)}")

    # Convert time strings to seconds since midnight for gap analysis
    def time_to_seconds(time_str):
        """Convert HH:MM:SS to seconds since midnight."""
        parts = time_str.split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    # Convert events to simplified format for gap analysis
    event_times = []
    for event in events:
        seconds = time_to_seconds(event['realworld_time'])
        event_times.append({
            'time': seconds,
            'confidence': event['confidence'],
            'original_time': event['realworld_time']
        })

    # Sort by time
    event_times.sort(key=lambda x: x['time'])

    print(f"\nFirst 10 events:")
    for i, event in enumerate(event_times[:10]):
        print(f"  {i+1}. {event['original_time']} (confidence: {event['confidence']:.3f})")

    # Analyze gaps between consecutive events
    gaps = []
    for i in range(1, len(event_times)):
        gap = event_times[i]['time'] - event_times[i-1]['time']
        gaps.append(gap)

    print(f"\nGap analysis:")
    print(f"  Mean gap: {sum(gaps)/len(gaps):.1f} seconds")
    print(f"  Max gap: {max(gaps)} seconds")
    print(f"  Min gap: {min(gaps)} seconds")

    # Count gaps by threshold
    gap_5min = sum(1 for g in gaps if g <= 300)  # 5 minutes
    gap_15min = sum(1 for g in gaps if g <= 900)  # 15 minutes

    print(f"  Gaps <= 5 minutes: {gap_5min}/{len(gaps)} ({gap_5min/len(gaps)*100:.1f}%)")
    print(f"  Gaps <= 15 minutes: {gap_15min}/{len(gaps)} ({gap_15min/len(gaps)*100:.1f}%)")

    # Look for continuous sequences
    print(f"\nLooking for potential violations...")

    # Group events by 5-minute gaps (sporadic violation threshold)
    groups = []
    current_group = [event_times[0]]

    for i in range(1, len(event_times)):
        gap = event_times[i]['time'] - event_times[i-1]['time']
        if gap <= 300:  # 5 minutes
            current_group.append(event_times[i])
        else:
            groups.append(current_group)
            current_group = [event_times[i]]

    if current_group:
        groups.append(current_group)

    print(f"Found {len(groups)} sporadic groups (5-min gap threshold)")

    # Check for potential violations
    for i, group in enumerate(groups):
        if len(group) < 2:
            continue

        duration = group[-1]['time'] - group[0]['time']
        print(f"  Group {i+1}: {len(group)} events, {duration/60:.1f} minutes")

        if duration >= 900:  # 15 minutes for sporadic violation
            print(f"    *** POTENTIAL SPORADIC VIOLATION: {duration/60:.1f} minutes ***")

        # Sample events in this group
        print(f"    First: {group[0]['original_time']}")
        print(f"    Last: {group[-1]['original_time']}")

def test_violation_logic():
    """Test the violation detection logic with mock events."""
    print("\n" + "="*60)
    print("TESTING VIOLATION DETECTION LOGIC")
    print("="*60)

    # Create mock events that should trigger violations
    class MockEvent:
        def __init__(self, start_time, end_time, confidence):
            self.start_time = start_time
            self.end_time = end_time
            self.confidence = confidence

    # Create a series of events spanning 20 minutes with 1-minute events
    # This should definitely trigger sporadic violation (15+ minutes)
    test_events = []
    for i in range(20):
        # Each event is 1 minute long, starting every 1.5 minutes
        start = i * 90  # 90 seconds apart
        end = start + 60  # 60 seconds duration
        test_events.append(MockEvent(start, end, 0.75))

    print(f"Created {len(test_events)} mock events over {test_events[-1].end_time/60:.1f} minutes")

    # Test with violation tracker
    tracker = LegalViolationTracker()

    # Test continuous violations
    continuous_violations = tracker._analyze_continuous_violations_from_events(test_events)
    print(f"Continuous violations detected: {len(continuous_violations)}")

    # Test sporadic violations
    sporadic_violations = tracker._analyze_sporadic_violations_from_events(test_events)
    print(f"Sporadic violations detected: {len(sporadic_violations)}")

    if continuous_violations:
        for v in continuous_violations:
            print(f"  Continuous: duration={v.total_bark_duration/60:.1f}min")

    if sporadic_violations:
        for v in sporadic_violations:
            print(f"  Sporadic: duration={v.total_bark_duration/60:.1f}min")

if __name__ == "__main__":
    print("VIOLATION DETECTION DEBUG ANALYSIS")
    print("="*50)

    analyze_event_gaps()
    test_violation_logic()