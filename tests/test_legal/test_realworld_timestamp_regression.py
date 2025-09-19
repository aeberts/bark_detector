"""
Regression test for realworld timestamp calculation bug.

This test ensures that the bug where realworld_time was incorrectly
calculated as audio file offset instead of actual wall-clock time
does not reoccur.

Bug Details:
- Issue: realworld_time was showing "00:00:00" instead of actual time
- Example: bark_recording_20250818_081958.wav with bark at start
  should show realworld_time="08:19:58" not "00:00:00"
- Root cause: Used event.start_time directly instead of
  recording_start_time + event.start_time
"""

import pytest
import tempfile
from pathlib import Path

from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.legal.database import ViolationDatabase
from bark_detector.core.models import BarkEvent


class TestRealworldTimestampRegression:
    """Regression tests for realworld timestamp calculation bug."""

    def test_bug_reproduction_scenario(self):
        """Test the exact scenario reported in the bug report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Reproduce the exact scenario from the bug report
            bark_events = [
                BarkEvent(start_time=0.0, end_time=1.0, confidence=0.809010922908783, intensity=0.0)
            ]

            # Set the bark type as reported in the bug
            bark_events[0].triggering_classes = ["Domestic animals, pets"]

            # Use the exact filename from the bug report
            audio_file_name = "bark_recording_20250818_081958.wav"
            target_date = "2025-08-18"

            # Convert to PersistedBarkEvent objects
            persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

            # Verify the bug is fixed
            assert len(persisted_events) == 1
            event = persisted_events[0]

            # These are the CORRECT values (bug fixed)
            assert event.realworld_date == "2025-08-18"
            assert event.realworld_time == "08:19:58"  # NOT "00:00:00"
            assert event.bark_id is not None
            assert event.bark_type == "Domestic animals, pets"
            assert event.est_dog_size is None
            assert event.audio_file_name == "bark_recording_20250818_081958.wav"
            assert event.bark_audiofile_timestamp == "00:00:00.000"
            assert event.confidence == 0.809010922908783
            assert event.intensity == 0.0

            # The bug was that realworld_time was "00:00:00" instead of "08:19:58"
            # This test ensures it's fixed and doesn't regress
            assert event.realworld_time != "00:00:00", "Bug regression: realworld_time shows offset instead of actual time"

    def test_multiple_barks_in_same_file_timestamps(self):
        """Test that multiple barks in the same file have correctly calculated realworld times."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Multiple barks at different offsets in the same recording
            bark_events = [
                BarkEvent(start_time=0.0, end_time=1.0, confidence=0.8, intensity=0.0),      # At start
                BarkEvent(start_time=17.759, end_time=18.759, confidence=0.8, intensity=0.0), # 17.759 sec in
                BarkEvent(start_time=22.559, end_time=23.559, confidence=0.8, intensity=0.0), # 22.559 sec in
                BarkEvent(start_time=24.480, end_time=25.480, confidence=0.7, intensity=0.0)  # 24.480 sec in
            ]

            for event in bark_events:
                event.triggering_classes = ["Domestic animals, pets"]

            # Based on second event from bug report: bark_recording_20250818_094038.wav
            audio_file_name = "bark_recording_20250818_094038.wav"  # Started at 09:40:38
            target_date = "2025-08-18"

            persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

            # Verify each bark has correct realworld_time
            assert len(persisted_events) == 4

            # Event 1: 09:40:38 + 0 seconds = 09:40:38
            assert persisted_events[0].realworld_time == "09:40:38"
            assert persisted_events[0].bark_audiofile_timestamp == "00:00:00.000"

            # Event 2: 09:40:38 + 17.759 seconds = 09:40:55 (rounded to seconds)
            assert persisted_events[1].realworld_time == "09:40:55"
            assert persisted_events[1].bark_audiofile_timestamp == "00:00:17.759"

            # Event 3: 09:40:38 + 22.559 seconds = 09:41:00 (rounded to seconds)
            assert persisted_events[2].realworld_time == "09:41:00"
            assert persisted_events[2].bark_audiofile_timestamp == "00:00:22.559"

            # Event 4: 09:40:38 + 24.480 seconds = 09:41:02 (rounded to seconds)
            assert persisted_events[3].realworld_time == "09:41:02"
            assert persisted_events[3].bark_audiofile_timestamp == "00:00:24.480"

            # Ensure NONE of them have the buggy "00:00:XX" pattern for realworld_time
            for event in persisted_events:
                assert not event.realworld_time.startswith("00:00:"), \
                    f"Bug regression detected: {event.realworld_time} should not start with 00:00:"

    def test_cross_midnight_boundary_timestamps(self):
        """Test timestamp calculation when bark crosses midnight boundary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Recording started just before midnight
            bark_events = [
                BarkEvent(start_time=180.0, end_time=181.0, confidence=0.8, intensity=0.0)  # 3 minutes in
            ]
            bark_events[0].triggering_classes = ["Bark"]

            # Recording started at 23:58:00
            audio_file_name = "bark_recording_20250818_235800.wav"
            target_date = "2025-08-18"

            persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

            # 23:58:00 + 180 seconds = 23:58:00 + 3:00 = 00:01:00 (next day)
            # But we only track time, not date rollover
            assert persisted_events[0].realworld_time == "00:01:00"

            # The key test: it should NOT be "00:03:00" (which would be the offset time)
            assert persisted_events[0].realworld_time != "00:03:00", \
                "Bug regression: showing offset time instead of actual time"

    def test_regression_prevention_with_various_filenames(self):
        """Test various filename formats to ensure timestamp extraction works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            test_cases = [
                # (filename, expected_start_time, bark_offset, expected_realworld_time)
                ("bark_recording_20250818_081958.wav", "08:19:58", 0.0, "08:19:58"),
                ("bark_recording_20250818_000000.wav", "00:00:00", 30.0, "00:00:30"),
                ("bark_recording_20250818_235959.wav", "23:59:59", 2.0, "00:00:01"),  # Cross midnight
                ("bark_recording_20250818_120000.wav", "12:00:00", 3665.0, "13:01:05"),  # 1hr 1min 5sec offset
            ]

            for filename, start_time, offset, expected_realworld_time in test_cases:
                bark_events = [
                    BarkEvent(start_time=offset, end_time=offset+1.0, confidence=0.8, intensity=0.0)
                ]
                bark_events[0].triggering_classes = ["Bark"]

                persisted_events = tracker._convert_to_persisted_events(bark_events, filename, "2025-08-18")

                assert len(persisted_events) == 1
                actual_time = persisted_events[0].realworld_time

                assert actual_time == expected_realworld_time, \
                    f"Failed for {filename}: expected {expected_realworld_time}, got {actual_time}"

                # Ensure it's not just using the offset time
                offset_time_hhmmss = f"{int(offset//3600):02d}:{int((offset%3600)//60):02d}:{int(offset%60):02d}"
                if expected_realworld_time != offset_time_hhmmss:  # Only check if they should be different
                    assert actual_time != offset_time_hhmmss, \
                        f"Bug regression for {filename}: showing offset time {offset_time_hhmmss} instead of actual time"