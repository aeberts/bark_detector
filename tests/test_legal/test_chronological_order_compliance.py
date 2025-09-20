"""
Regression test for FR1 compliance: chronological order of recording analysis.

This test ensures that recording files are analyzed in chronological order
based on their filename timestamps, as required by FR1 in the PRD.
"""

import pytest
import tempfile
import librosa
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.legal.database import ViolationDatabase
from bark_detector.core.models import BarkEvent


class TestChronologicalOrderCompliance:
    """Tests for FR1 compliance: chronological order of recording analysis."""

    def test_fr1_recordings_processed_in_chronological_order(self):
        """Test that recordings are processed in chronological order (FR1)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            recordings_dir = Path(temp_dir) / 'recordings'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Create test recordings directory
            date_dir = recordings_dir / '2025-08-18'
            date_dir.mkdir(parents=True)

            # Create mock audio files with timestamps in non-chronological filesystem order
            # But we want them processed in chronological order
            test_files = [
                "bark_recording_20250818_114413.wav",  # 11:44:13 AM (3rd chronologically)
                "bark_recording_20250818_073259.wav",  # 07:32:59 AM (1st chronologically)
                "bark_recording_20250818_081958.wav",  # 08:19:58 AM (2nd chronologically)
                "bark_recording_20250818_154500.wav",  # 15:45:00 PM (4th chronologically)
            ]

            # Create actual files to avoid file not found errors
            for filename in test_files:
                file_path = date_dir / filename
                file_path.touch()

            # Create a mock detector that tracks the order files are processed
            processed_files_order = []

            def mock_detect_barks(audio_data):
                # This gets called for each file, allowing us to track processing order
                return [BarkEvent(start_time=0.0, end_time=1.0, confidence=0.8, intensity=0.5)]

            mock_detector = Mock()
            mock_detector.sample_rate = 16000
            mock_detector.session_gap_threshold = 10.0
            mock_detector.analysis_sensitivity = 0.30
            mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=[BarkEvent(start_time=0.0, end_time=1.0, confidence=0.8, intensity=0.5)])

            # Mock librosa.load to track which files are being loaded in what order
            def mock_librosa_load(file_path, sr=None):
                filename = Path(file_path).name
                processed_files_order.append(filename)
                # Return dummy audio data
                return np.random.random(16000), sr  # 1 second of dummy audio

            with patch('librosa.load', side_effect=mock_librosa_load):
                # Mock the bark detection to avoid real ML processing
                with patch.object(mock_detector, '_detect_barks_in_buffer_with_sensitivity') as mock_detection:
                    mock_event = BarkEvent(start_time=0.0, end_time=1.0, confidence=0.8, intensity=0.5)
                    mock_event.triggering_classes = ["Bark"]
                    mock_detection.return_value = [mock_event]

                    # Run the analysis
                    tracker.analyze_recordings_for_date(recordings_dir, "2025-08-18", mock_detector)

            # Verify files were processed in chronological order (FR1 compliance)
            expected_chronological_order = [
                "bark_recording_20250818_073259.wav",  # 07:32:59 AM (earliest)
                "bark_recording_20250818_081958.wav",  # 08:19:58 AM
                "bark_recording_20250818_114413.wav",  # 11:44:13 AM
                "bark_recording_20250818_154500.wav",  # 15:45:00 PM (latest)
            ]

            assert processed_files_order == expected_chronological_order, \
                f"Files processed in wrong order. Expected: {expected_chronological_order}, Got: {processed_files_order}"

            print("✅ FR1 Compliance verified: Recordings processed in chronological order")

    def test_fr1_events_json_in_chronological_order(self):
        """Test that events in _events.json file are in chronological order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            recordings_dir = Path(temp_dir) / 'recordings'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Create test recordings directory
            date_dir = recordings_dir / '2025-08-18'
            date_dir.mkdir(parents=True)

            # Create files in filesystem order that's NOT chronological
            test_files_filesystem_order = [
                ("bark_recording_20250818_114413.wav", 0.0),   # 11:44:13 AM + 0 sec = 11:44:13
                ("bark_recording_20250818_073259.wav", 45.0),  # 07:32:59 AM + 45 sec = 07:33:44
                ("bark_recording_20250818_081958.wav", 120.0), # 08:19:58 AM + 120 sec = 08:21:58
            ]

            # Create actual files
            for filename, _ in test_files_filesystem_order:
                file_path = date_dir / filename
                file_path.touch()

            # Mock detector and librosa
            mock_detector = Mock()
            mock_detector.sample_rate = 16000

            def mock_librosa_load(file_path, sr=None):
                return np.random.random(16000), sr

            # Track which file is currently being processed
            current_file_offsets = {}

            def mock_librosa_load_with_tracking(file_path, sr=None):
                filename = Path(file_path).name
                # Store the offset for this file
                offset = next((offset for fname, offset in test_files_filesystem_order if fname == filename), 0.0)
                current_file_offsets[filename] = offset
                return np.random.random(16000), sr

            def mock_detect_barks_with_sensitivity(audio_data, sensitivity):
                # Use the most recently loaded file's offset
                if current_file_offsets:
                    filename = list(current_file_offsets.keys())[-1]  # Most recent file
                    offset = current_file_offsets[filename]
                else:
                    offset = 0.0

                event = BarkEvent(start_time=offset, end_time=offset+1.0, confidence=0.8, intensity=0.5)
                event.triggering_classes = ["Bark"]
                return [event]

            with patch('librosa.load', side_effect=mock_librosa_load_with_tracking):
                with patch.object(mock_detector, '_detect_barks_in_buffer_with_sensitivity', side_effect=mock_detect_barks_with_sensitivity):
                    # Run analysis
                    tracker.analyze_recordings_for_date(recordings_dir, "2025-08-18", mock_detector)

            # Check that events were saved in chronological order
            events_file = violations_dir / "2025-08-18" / "2025-08-18_events.json"
            assert events_file.exists(), "Events file should have been created"

            # Load and check the saved events
            saved_events = db.load_events("2025-08-18")

            # Extract realworld_time from saved events
            realworld_times = [event.realworld_time for event in saved_events]

            # Expected chronological order of realworld_time values
            expected_times = [
                "07:33:44",  # 07:32:59 + 45 sec
                "08:21:58",  # 08:19:58 + 120 sec
                "11:44:13",  # 11:44:13 + 0 sec
            ]

            assert realworld_times == expected_times, \
                f"Events not in chronological order. Expected: {expected_times}, Got: {realworld_times}"

            print("✅ FR1 Compliance verified: Events in JSON file are chronologically ordered")

    def test_unparseable_filenames_handled_gracefully(self):
        """Test that files with unparseable timestamps are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            recordings_dir = Path(temp_dir) / 'recordings'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Create test recordings directory
            date_dir = recordings_dir / '2025-08-18'
            date_dir.mkdir(parents=True)

            # Mix of parseable and unparseable filenames
            test_files = [
                "bark_recording_20250818_081958.wav",  # Parseable - should be first
                "invalid_filename_format.wav",         # Unparseable - should be last
                "bark_recording_20250818_073259.wav",  # Parseable - should be second
                "another_bad_name.wav",                # Unparseable - should be last
            ]

            # Create actual files
            for filename in test_files:
                file_path = date_dir / filename
                file_path.touch()

            processed_files_order = []

            def mock_librosa_load(file_path, sr=None):
                filename = Path(file_path).name
                processed_files_order.append(filename)
                return np.random.random(16000), sr

            mock_detector = Mock()
            mock_detector.sample_rate = 16000
            mock_detector._detect_barks_in_buffer.return_value = []  # No events to simplify test

            with patch('librosa.load', side_effect=mock_librosa_load):
                # Capture log messages to verify warnings
                with patch('bark_detector.legal.tracker.logger') as mock_logger:
                    tracker.analyze_recordings_for_date(recordings_dir, "2025-08-18", mock_detector)

                    # Verify warnings were logged for unparseable files
                    warning_calls = [call for call in mock_logger.warning.call_args_list]
                    assert len(warning_calls) >= 2, "Should have warned about unparseable filenames"

            # Verify chronological processing: parseable files first in time order, unparseable files last
            expected_order = [
                "bark_recording_20250818_073259.wav",  # 07:32:59 (earliest parseable)
                "bark_recording_20250818_081958.wav",  # 08:19:58 (latest parseable)
                # Unparseable files come last (order among them doesn't matter)
            ]

            # Check that parseable files came first in correct order
            assert processed_files_order[:2] == expected_order, \
                f"Parseable files not in correct chronological order. Expected start: {expected_order}, Got start: {processed_files_order[:2]}"

            # Check that unparseable files came last
            unparseable_files = {"invalid_filename_format.wav", "another_bad_name.wav"}
            files_processed_last = set(processed_files_order[2:])
            assert files_processed_last == unparseable_files, \
                f"Unparseable files should be processed last. Expected last: {unparseable_files}, Got last: {files_processed_last}"

            print("✅ Unparseable filenames handled gracefully and processed after chronological files")