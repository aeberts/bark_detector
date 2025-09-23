"""Tests for bark_detector.legal.tracker"""

import pytest
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.legal.models import ViolationReport, PersistedBarkEvent, Violation, AlgorithmInputEvent
from bark_detector.legal.database import ViolationDatabase
from bark_detector.core.models import BarkEvent, BarkingSession


def create_continuous_bark_events(total_minutes: float = 6.0, gap_seconds: float = 8.0, confidence: float = 0.8):
    """Generate BarkEvent sequences that satisfy continuous violation criteria."""
    events = []
    total_seconds = total_minutes * 60.0
    start = 0.0
    while start <= total_seconds:
        event = BarkEvent(start_time=start, end_time=start + 2.0, confidence=confidence, intensity=0.5)
        event.triggering_classes = ["Bark"]
        events.append(event)
        start += gap_seconds
    return events


def build_tracker_with_temp_db(temp_dir: Path, interactive: bool = False) -> LegalViolationTracker:
    """Create a tracker whose violation database writes to a temporary directory."""
    violations_dir = Path(temp_dir) / 'violations'
    db = ViolationDatabase(violations_dir=violations_dir)
    return LegalViolationTracker(violation_db=db, interactive=interactive)


class TestLegalViolationTracker:
    """Test LegalViolationTracker class"""
    
    def test_initialization(self):
        """Test basic tracker initialization"""
        tracker = LegalViolationTracker(interactive=False)
        
        assert tracker.violations == []
        assert tracker.sessions == []
    
    def test_analyze_violations_continuous(self):
        """Test analysis of continuous violations (5+ minutes)"""
        tracker = LegalViolationTracker(interactive=False)
        
        # Create a long continuous barking session (6 minutes)
        long_session = BarkingSession(
            start_time=0.0,
            end_time=360.0,  # 6 minutes
            events=[],
            total_barks=100,
            total_duration=360.0,  # 6 minutes of actual barking
            avg_confidence=0.8,
            peak_confidence=0.9,
            barks_per_second=0.28,
            source_file=Path("test.wav")
        )
        
        # Short session (under 5 minutes)
        short_session = BarkingSession(
            start_time=400.0,
            end_time=520.0,  # 2 minutes
            events=[],
            total_barks=20,
            total_duration=120.0,
            avg_confidence=0.75,
            peak_confidence=0.85,
            barks_per_second=0.17,
            source_file=Path("test2.wav")
        )
        
        with patch.object(tracker, '_create_violation_report') as mock_create:
            mock_create.return_value = Mock(spec=ViolationReport)
            
            violations = tracker.analyze_violations([long_session, short_session])
            
            # Should only create violation for long session
            assert len(violations) == 1
            mock_create.assert_called_once_with(long_session, "Constant")
    
    @patch('bark_detector.legal.tracker.librosa.load')
    def test_analyze_recordings_for_date(self, mock_librosa_load, temp_dir):
        """Test analyzing recordings for a specific date"""
        tracker = build_tracker_with_temp_db(temp_dir)
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        mock_detector.analysis_sensitivity = 0.30

        # Mock the _detect_barks_in_buffer_with_sensitivity method to return bark events for continuous violation
        mock_bark_events = create_continuous_bark_events(total_minutes=6.0, gap_seconds=8.0)
        mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=mock_bark_events)

        # Create test recording files
        date_folder = temp_dir / "2025-08-14"
        date_folder.mkdir()
        test_file = date_folder / "bark_recording_20250814_120000.wav"
        test_file.touch()

        # Mock audio loading - simulate 6 minute file (continuous violation)
        mock_librosa_load.return_value = (np.random.rand(5760000), 16000)  # 6 minutes at 16kHz

        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)

        print(f"DEBUG: librosa.load called {mock_librosa_load.call_count} times")
        print(f"DEBUG: detector method called {mock_detector._detect_barks_in_buffer_with_sensitivity.call_count} times")
        print(f"DEBUG: violations returned: {len(violations)}")

        assert len(violations) == 1
        violation = violations[0]
        assert violation.date == "2025-08-14"
        assert violation.violation_type == "Constant"
        assert violation.total_bark_duration >= 300.0  # 5+ minutes
        assert str(test_file) in violation.audio_files
    
    @patch('librosa.load')
    def test_analyze_recordings_no_violations(self, mock_librosa_load, temp_dir):
        """Test analyzing recordings with no violations"""
        tracker = build_tracker_with_temp_db(temp_dir)
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        mock_detector.analysis_sensitivity = 0.30

        # Mock the _detect_barks_in_buffer_with_sensitivity method to return short bark events (no violations)
        mock_bark_events = [
            BarkEvent(start_time=10.0, end_time=50.0, confidence=0.7)  # Short bark event (40 seconds)
        ]
        mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=mock_bark_events)
        
        # Create test recording files
        date_folder = temp_dir / "2025-08-14"
        date_folder.mkdir()
        test_file = date_folder / "bark_recording_20250814_120000.wav"
        test_file.touch()
        
        # Mock audio loading - simulate short 2 minute file (no violation)
        mock_librosa_load.return_value = (np.random.rand(1920000), 16000)  # 2 minutes at 16kHz
        
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)
        
        assert len(violations) == 0
    
    def test_analyze_recordings_no_files(self, temp_dir):
        """Test analyzing recordings when no files exist"""
        tracker = build_tracker_with_temp_db(temp_dir)
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)
        
        assert len(violations) == 0
    
    @patch('librosa.load')
    def test_analyze_recordings_flat_structure(self, mock_librosa_load, temp_dir):
        """Test analyzing recordings in flat directory structure"""
        tracker = build_tracker_with_temp_db(temp_dir)
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        mock_detector.analysis_sensitivity = 0.30

        # Mock the _detect_barks_in_buffer_with_sensitivity method to return bark events for continuous violation
        mock_bark_events = create_continuous_bark_events(total_minutes=6.0, gap_seconds=8.0)
        mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=mock_bark_events)

        # Create test recording file in flat structure
        test_file = temp_dir / "bark_recording_20250814_120000.wav"
        test_file.touch()

        # Mock audio loading - simulate 6 minute file
        mock_librosa_load.return_value = (np.random.rand(5760000), 16000)

        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)
        
        assert len(violations) == 1
        violation = violations[0]
        assert violation.violation_type == "Constant"
        assert str(test_file) in violation.audio_files
    
    @patch('librosa.load')
    def test_analyze_recordings_audio_error(self, mock_librosa_load, temp_dir):
        """Test handling audio loading errors"""
        tracker = build_tracker_with_temp_db(temp_dir)
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        # Create test recording file
        date_folder = temp_dir / "2025-08-14"
        date_folder.mkdir()
        test_file = date_folder / "corrupted.wav"
        test_file.touch()
        
        # Mock audio loading error
        mock_librosa_load.side_effect = Exception("Corrupted audio file")
        
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)
        
        # Should handle error gracefully and return no violations
        assert len(violations) == 0
    
    def test_create_violation_report_integration(self):
        """Test that _create_violation_report would work with real session data"""
        tracker = LegalViolationTracker(interactive=False)
        
        session = BarkingSession(
            start_time=0.0,
            end_time=360.0,
            events=[BarkEvent(10.0, 11.0, 0.8), BarkEvent(20.0, 21.5, 0.75)],
            total_barks=50,
            total_duration=300.0,
            avg_confidence=0.77,
            peak_confidence=0.85,
            barks_per_second=0.14,
            source_file=Path("test_recording.wav")
        )
        
        # Test that analyze_violations can process this session
        # We can't test _create_violation_report directly since it's private,
        # but we can test that analyze_violations handles it
        violations = tracker.analyze_violations([session])
        
        # Should create one violation for this long session
        assert len(violations) == 1

    # ===============================================
    # Story 1.2 Refactoring Tests
    # ===============================================

    def test_convert_to_persisted_events(self):
        """Test conversion of bark events to PersistedBarkEvent objects"""
        tracker = LegalViolationTracker(interactive=False)

        # Create mock bark events
        bark_events = [
            BarkEvent(start_time=10.5, end_time=11.2, confidence=0.85, intensity=0.6),
            BarkEvent(start_time=15.8, end_time=16.4, confidence=0.72, intensity=0.4)
        ]

        # Add triggering_classes attribute to test bark type extraction
        bark_events[0].triggering_classes = ["Bark", "Dog"]
        bark_events[1].triggering_classes = ["Yip"]

        result = tracker._convert_to_persisted_events(bark_events, "test_audio.wav", "2025-09-15")

        assert len(result) == 2
        assert all(isinstance(event, PersistedBarkEvent) for event in result)

        # Check first event
        event1 = result[0]
        assert event1.realworld_date == "2025-09-15"
        assert event1.bark_type == "Bark"  # First from triggering_classes
        assert event1.audio_file_name == "test_audio.wav"
        assert event1.confidence == 0.85
        assert event1.intensity == 0.6
        assert event1.bark_audiofile_timestamp == "00:00:10.500"

        # Check second event
        event2 = result[1]
        assert event2.bark_type == "Yip"
        assert event2.bark_audiofile_timestamp == "00:00:15.800"

    def test_convert_to_violation_objects(self):
        """Test conversion of ViolationReport objects to Violation objects"""
        tracker = LegalViolationTracker(interactive=False)

        # Create mock ViolationReport
        violation_reports = [
            ViolationReport(
                date="2025-09-15",
                start_time="06:30 AM",
                end_time="06:38 AM",
                violation_type="Constant",
                total_bark_duration=480.0,
                total_incident_duration=480.0,
                audio_files=["test1.wav"],
                audio_file_start_times=["00:00:00"],
                audio_file_end_times=["00:08:00"],
                confidence_scores=[0.8],
                peak_confidence=0.9,
                avg_confidence=0.8,
                created_timestamp="2025-09-15T06:30:00"
            )
        ]

        # Create mock bark events
        bark_events = [
            PersistedBarkEvent(
                realworld_date="2025-09-15",
                realworld_time="06:31:00",
                bark_id="event-123",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="test1.wav",
                bark_audiofile_timestamp="00:01:00.000",
                confidence=0.8,
                intensity=0.5
            )
        ]

        result = tracker._convert_to_violation_objects(violation_reports, bark_events, "2025-09-15")

        assert len(result) == 1
        violation = result[0]
        assert isinstance(violation, Violation)
        assert violation.type == "Continuous"
        assert violation.startTimestamp == "2025-09-15T06:30:00.000Z"
        assert violation.endTimestamp == "2025-09-15T06:38:00.000Z"
        assert pytest.approx(violation.durationMinutes, rel=1e-3) == 8.0
        assert pytest.approx(violation.violationDurationMinutes, rel=1e-3) == 8.0
        assert "event-123" in violation.barkEventIds

    def test_format_timestamp_with_milliseconds(self):
        """Test timestamp formatting with millisecond precision"""
        tracker = LegalViolationTracker(interactive=False)

        # Test various timestamp values
        assert tracker._format_timestamp_with_milliseconds(10.5) == "00:00:10.500"
        assert tracker._format_timestamp_with_milliseconds(65.123) == "00:01:05.123"
        assert tracker._format_timestamp_with_milliseconds(3661.789) == "01:01:01.789"
        assert tracker._format_timestamp_with_milliseconds(0.001) == "00:00:00.001"

    def test_parse_time_to_seconds(self):
        """Test time string parsing to seconds"""
        tracker = LegalViolationTracker(interactive=False)

        # Test HH:MM:SS format
        assert tracker._parse_time_to_seconds("01:30:45") == 5445.0
        assert tracker._parse_time_to_seconds("00:05:30.500") == 330.5

        # Test AM/PM format
        assert tracker._parse_time_to_seconds("6:30 AM") == 23400.0  # 6.5 * 3600
        assert tracker._parse_time_to_seconds("6:30 PM") == 66600.0  # 18.5 * 3600
        assert tracker._parse_time_to_seconds("12:30 AM") == 1800.0  # 0.5 * 3600
        assert tracker._parse_time_to_seconds("12:30 PM") == 45000.0  # 12.5 * 3600

    def test_find_events_for_violation(self):
        """Test finding bark events that correlate with violations"""
        tracker = LegalViolationTracker(interactive=False)

        # Create violation report
        violation_report = ViolationReport(
            date="2025-09-15",
            start_time="06:30:00",
            end_time="06:32:00",
            violation_type="Constant",
            total_bark_duration=120.0,
            total_incident_duration=120.0,
            audio_files=["test.wav"],
            audio_file_start_times=["00:00:00"],
            audio_file_end_times=["00:02:00"],
            confidence_scores=[0.8],
            peak_confidence=0.9,
            avg_confidence=0.8,
            created_timestamp="2025-09-15T06:30:00"
        )

        # Create bark events - some inside, some outside the violation time range
        bark_events = [
            PersistedBarkEvent(
                realworld_date="2025-09-15",
                realworld_time="06:29:30",  # Before violation
                bark_id="event-1",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="test.wav",
                bark_audiofile_timestamp="00:00:30.000",
                confidence=0.8,
                intensity=0.5
            ),
            PersistedBarkEvent(
                realworld_date="2025-09-15",
                realworld_time="06:31:00",  # During violation
                bark_id="event-2",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="test.wav",
                bark_audiofile_timestamp="00:01:00.000",
                confidence=0.8,
                intensity=0.5
            ),
            PersistedBarkEvent(
                realworld_date="2025-09-15",
                realworld_time="06:33:00",  # After violation
                bark_id="event-3",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="test.wav",
                bark_audiofile_timestamp="00:03:00.000",
                confidence=0.8,
                intensity=0.5
            )
        ]

        result = tracker._find_events_for_violation(violation_report, bark_events)

        # Only event-2 should be included (within time range)
        assert len(result) == 1
        assert "event-2" in result
        assert "event-1" not in result
        assert "event-3" not in result

    @patch('bark_detector.legal.tracker.librosa')
    def test_analyze_recordings_for_date_with_new_persistence(self, mock_librosa):
        """Test analyze_recordings_for_date with new PersistedBarkEvent and Violation persistence"""
        # Setup mock ViolationDatabase
        mock_db = Mock(spec=ViolationDatabase)
        mock_db.use_date_structure = True
        tracker = LegalViolationTracker(violation_db=mock_db, interactive=False)

        # Mock detector
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        mock_detector.analysis_sensitivity = 0.30

        # Mock audio data and bark events
        mock_librosa.load.return_value = (np.array([0.1, 0.2, 0.3] * 1000), 16000)

        bark_events = create_continuous_bark_events(total_minutes=6.0, gap_seconds=8.0)
        # Adjust bark types for coverage
        if bark_events:
            bark_events[0].triggering_classes = ["Bark"]
        if len(bark_events) > 1:
            bark_events[1].triggering_classes = ["Yip"]

        mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=bark_events)

        # Create test directory structure
        recordings_dir = Path("/fake/recordings")

        # Mock file discovery
        with patch('pathlib.Path.glob') as mock_glob, \
             patch('pathlib.Path.exists') as mock_exists:

            mock_exists.return_value = True
            mock_glob.return_value = [Path("/fake/recordings/2025-09-15/test.wav")]

            # Mock session creation
            with patch.object(tracker, '_events_to_sessions') as mock_sessions:
                mock_session = BarkingSession(
                    start_time=1.0,
                    end_time=6.0,
                    events=bark_events,
                    total_barks=2,
                    total_duration=360.0,  # 6 minutes - should trigger violation
                    avg_confidence=0.75,
                    peak_confidence=0.8,
                    barks_per_second=0.33,
                    source_file=Path("test.wav")
                )
                mock_sessions.return_value = [mock_session]

                result = tracker.analyze_recordings_for_date(recordings_dir, "2025-09-15", mock_detector)

                # Verify save_events was called
                mock_db.save_events.assert_called_once()
                saved_events = mock_db.save_events.call_args[0][0]
                # The number of events depends on how many files are processed
                # Each file produces 2 events, so verify events were created and are correct type
                assert len(saved_events) >= 2
                assert all(isinstance(event, PersistedBarkEvent) for event in saved_events)

                # Verify the events have the expected properties
                assert saved_events[0].bark_type == "Bark"
                assert saved_events[1].bark_type == "Yip"

                # Verify save_violations_new was called if violations were detected
                if mock_db.save_violations_new.called:
                    saved_violations = mock_db.save_violations_new.call_args[0][0]
                    assert len(saved_violations) >= 1
                    assert isinstance(saved_violations[0], Violation)

                # Verify return value (backward compatibility)
                assert len(result) >= 1
                assert all(isinstance(r, ViolationReport) for r in result)

    def test_realworld_timestamp_calculation_fix(self):
        """Test that realworld_time is calculated correctly from filename + offset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Create test bark events with known start times
            bark_events = [
                BarkEvent(start_time=0.0, end_time=1.0, confidence=0.8, intensity=0.5),    # Right at start
                BarkEvent(start_time=15.5, end_time=16.5, confidence=0.9, intensity=0.6),  # 15.5 seconds in
                BarkEvent(start_time=125.0, end_time=126.0, confidence=0.7, intensity=0.4)  # 2 min 5 sec in
            ]

            # Add required attributes
            for event in bark_events:
                event.triggering_classes = ["Bark"]

            # Test with specific filename: bark_recording_20250818_081958.wav
            # This means recording started at 08:19:58
            audio_file_name = "bark_recording_20250818_081958.wav"
            target_date = "2025-08-18"

            # Convert to PersistedBarkEvent objects
            persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

            # Verify correct timestamp calculations
            assert len(persisted_events) == 3

            # Event 1: 08:19:58 + 0 seconds = 08:19:58
            assert persisted_events[0].realworld_time == "08:19:58"
            assert persisted_events[0].bark_audiofile_timestamp == "00:00:00.000"

            # Event 2: 08:19:58 + 15.5 seconds = 08:20:13 (rounded to seconds)
            assert persisted_events[1].realworld_time == "08:20:13"
            assert persisted_events[1].bark_audiofile_timestamp == "00:00:15.500"

            # Event 3: 08:19:58 + 125 seconds = 08:22:03
            assert persisted_events[2].realworld_time == "08:22:03"
            assert persisted_events[2].bark_audiofile_timestamp == "00:02:05.000"

            # Verify all events have correct date and audio file reference
            for event in persisted_events:
                assert event.realworld_date == target_date
                assert event.audio_file_name == audio_file_name

    def test_realworld_timestamp_fallback_for_invalid_filename(self):
        """Test fallback behavior when filename cannot be parsed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Create test bark event
            bark_events = [
                BarkEvent(start_time=65.0, end_time=66.0, confidence=0.8, intensity=0.5)
            ]
            bark_events[0].triggering_classes = ["Bark"]

            # Use invalid filename format
            audio_file_name = "invalid_filename_format.wav"
            target_date = "2025-08-18"

            # Convert to PersistedBarkEvent objects
            with patch('bark_detector.legal.tracker.logger') as mock_logger:
                persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

                # Should log warning and use fallback
                mock_logger.warning.assert_called_once()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "Could not parse timestamp from filename" in warning_call
                assert audio_file_name in warning_call

                # Should use fallback: convert 65 seconds to HH:MM:SS format
                assert len(persisted_events) == 1
                assert persisted_events[0].realworld_time == "00:01:05"  # 65 seconds = 1 min 5 sec

    def test_realworld_timestamp_edge_cases(self):
        """Test edge cases for timestamp calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Test with midnight recording
            bark_events = [
                BarkEvent(start_time=30.0, end_time=31.0, confidence=0.8, intensity=0.5)
            ]
            bark_events[0].triggering_classes = ["Bark"]

            # Recording at midnight: 00:00:00
            audio_file_name = "bark_recording_20250818_000000.wav"
            target_date = "2025-08-18"

            persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

            # 00:00:00 + 30 seconds = 00:00:30
            assert persisted_events[0].realworld_time == "00:00:30"

            # Test with late evening recording
            bark_events = [
                BarkEvent(start_time=3600.0, end_time=3601.0, confidence=0.8, intensity=0.5)  # 1 hour offset
            ]
            bark_events[0].triggering_classes = ["Bark"]

            # Recording at 23:00:00
            audio_file_name = "bark_recording_20250818_230000.wav"

            persisted_events = tracker._convert_to_persisted_events(bark_events, audio_file_name, target_date)

            # 23:00:00 + 3600 seconds (1 hour) = 24:00:00 = 00:00:00 next day
            # But we only display time, so it shows as 00:00:00
            assert persisted_events[0].realworld_time == "00:00:00"

    @patch('librosa.load')
    def test_analyze_recordings_uses_analysis_sensitivity(self, mock_librosa_load, temp_dir):
        """Test that analyze_recordings_for_date uses analysis_sensitivity instead of real-time sensitivity."""
        tracker = build_tracker_with_temp_db(temp_dir)

        # Create mock detector with different sensitivities
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        mock_detector.sensitivity = 0.68  # Real-time sensitivity
        mock_detector.analysis_sensitivity = 0.30  # Analysis sensitivity

        # Mock analysis method specifically
        mock_detector._detect_barks_in_buffer_with_sensitivity = Mock()
        mock_detector._detect_barks_in_buffer_with_sensitivity.return_value = create_continuous_bark_events(total_minutes=6.5, gap_seconds=8.0)

        # Create test recording files
        date_folder = temp_dir / "2025-08-14"
        date_folder.mkdir()
        test_file = date_folder / "bark_recording_20250814_120000.wav"
        test_file.touch()

        # Mock audio loading
        mock_librosa_load.return_value = (np.random.rand(5760000), 16000)  # 6 minutes at 16kHz

        # Run analysis
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)

        # Verify analysis_sensitivity was used (not real-time sensitivity)
        mock_detector._detect_barks_in_buffer_with_sensitivity.assert_called()
        call_args = mock_detector._detect_barks_in_buffer_with_sensitivity.call_args

        # Second argument should be analysis_sensitivity (0.30), not real-time sensitivity (0.68)
        assert call_args[0][1] == 0.30, f"Expected analysis_sensitivity 0.30, got {call_args[0][1]}"

        # Verify we got violations
        assert len(violations) == 1

    @patch('librosa.load')
    def test_dual_sensitivity_advantage_more_detections(self, mock_librosa_load, temp_dir):
        """Test that analysis_sensitivity detects more bark events than real-time sensitivity would."""
        tracker = build_tracker_with_temp_db(temp_dir)

        # Create mock detector
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        mock_detector.sensitivity = 0.68
        mock_detector.analysis_sensitivity = 0.30

        # Simulate different detection results based on sensitivity
        def mock_detect_with_sensitivity(audio_data, sensitivity):
            if sensitivity == 0.68:
                # Real-time sensitivity detects fewer events that do not reach violation threshold
                events = create_continuous_bark_events(total_minutes=2.0, gap_seconds=8.0, confidence=0.75)
                return events
            elif sensitivity == 0.30:
                # Analysis sensitivity detects enough events to form a violation
                return create_continuous_bark_events(total_minutes=6.0, gap_seconds=8.0, confidence=0.55)

        mock_detector._detect_barks_in_buffer_with_sensitivity.side_effect = mock_detect_with_sensitivity

        # Create test recording
        date_folder = temp_dir / "2025-08-14"
        date_folder.mkdir()
        test_file = date_folder / "bark_recording_20250814_120000.wav"
        test_file.touch()

        mock_librosa_load.return_value = (np.random.rand(5760000), 16000)

        # Run analysis
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)

        # Verify analysis_sensitivity was used and detected more events (leading to violations)
        mock_detector._detect_barks_in_buffer_with_sensitivity.assert_called_with(mock_librosa_load.return_value[0], 0.30)

        # Should detect violation from longer analysis
        assert len(violations) == 1
        assert violations[0].violation_type == "Constant"

    # New Tests for Direct Event Analysis (Story 1.8)

    def test_group_events_by_gaps(self):
        """Test the _group_events_by_gaps utility method."""
        tracker = LegalViolationTracker(interactive=False)

        # Create test events with different gaps
        events = [
            type('BarkEvent', (), {'start_time': 0.0, 'end_time': 1.0})(),    # Group 1
            type('BarkEvent', (), {'start_time': 2.0, 'end_time': 3.0})(),    # Group 1 (2s gap)
            type('BarkEvent', (), {'start_time': 65.0, 'end_time': 66.0})(),  # Group 2 (62s gap)
            type('BarkEvent', (), {'start_time': 67.0, 'end_time': 68.0})(),  # Group 2 (1s gap)
        ]

        # Test with 60s gap threshold
        groups = tracker._group_events_by_gaps(events, 60.0)

        assert len(groups) == 2
        assert len(groups[0]) == 2  # First two events
        assert len(groups[1]) == 2  # Last two events

        # Test with larger gap threshold
        groups = tracker._group_events_by_gaps(events, 70.0)
        assert len(groups) == 1  # All events in one group

        # Test with small gap threshold
        groups = tracker._group_events_by_gaps(events, 1.0)
        assert len(groups) == 2  # Events 1,2 in group 1, events 3,4 in group 2

    def test_analyze_continuous_violations_from_events(self):
        """Test direct continuous violation analysis from AlgorithmInputEvent objects."""
        tracker = LegalViolationTracker(interactive=False)

        # Create AlgorithmInputEvent objects for a 6-minute continuous violation (gaps ≤10s)
        # Based on algorithm spec: 10-second max gap, 5-minute minimum session
        events = []
        base_datetime = datetime(2025, 9, 21, 10, 0, 0)

        # Create events with 5-second gaps (within 10-second threshold)
        for i in range(61):  # 61 events over 300 seconds = 5+ minutes
            event_time = base_datetime + timedelta(seconds=i * 5)
            events.append(AlgorithmInputEvent(
                id=f"bark-{i:03d}",
                startTimestamp=event_time.isoformat() + ".000Z"
            ))

        violations = tracker._analyze_constant_violations_from_events(events)

        assert len(violations) == 1
        assert violations[0].type == "Continuous"
        assert violations[0].durationMinutes >= 5.0  # ≥5 minutes

        # Test with short duration (should not trigger violation)
        short_events = []
        for i in range(30):  # 30 events over 145 seconds = <5 minutes
            event_time = base_datetime + timedelta(seconds=i * 5)
            short_events.append(AlgorithmInputEvent(
                id=f"short-{i:03d}",
                startTimestamp=event_time.isoformat() + ".000Z"
            ))

        violations = tracker._analyze_constant_violations_from_events(short_events)
        assert len(violations) == 0

        # Test with gaps too large (should not trigger violation)
        gap_events = []
        for i in range(61):  # Events with 15-second gaps (>10 second threshold)
            event_time = base_datetime + timedelta(seconds=i * 15)
            gap_events.append(AlgorithmInputEvent(
                id=f"gap-{i:03d}",
                startTimestamp=event_time.isoformat() + ".000Z"
            ))

        violations = tracker._analyze_constant_violations_from_events(gap_events)
        assert len(violations) == 0

    def test_analyze_intermittent_violations_from_events(self):
        """Test direct intermittent violation analysis from AlgorithmInputEvent objects."""
        tracker = LegalViolationTracker(interactive=False)

        # Create AlgorithmInputEvent objects for 16-minute intermittent violation (gaps ≤5min)
        # Based on algorithm spec: 5-minute max gap, 15-minute minimum session
        events = []
        base_datetime = datetime(2025, 9, 21, 10, 0, 0)

        # Create events with 4-minute gaps (within 5-minute threshold)
        for i in range(5):  # 5 events over 16 minutes = 15+ minutes duration
            event_time = base_datetime + timedelta(minutes=i * 4)
            events.append(AlgorithmInputEvent(
                id=f"intermittent-{i:03d}",
                startTimestamp=event_time.isoformat() + ".000Z"
            ))

        violations = tracker._analyze_intermittent_violations_from_events(events)

        assert len(violations) == 1
        assert violations[0].type == "Intermittent"
        assert violations[0].durationMinutes >= 15.0  # ≥15 minutes

        # Test with short duration (should not trigger violation)
        short_events = []
        for i in range(3):  # 3 events over 8 minutes = <15 minutes
            event_time = base_datetime + timedelta(minutes=i * 4)
            short_events.append(AlgorithmInputEvent(
                id=f"short-intermittent-{i:03d}",
                startTimestamp=event_time.isoformat() + ".000Z"
            ))

        violations = tracker._analyze_intermittent_violations_from_events(short_events)
        assert len(violations) == 0

        # Test with gaps too large (should not trigger violation)
        gap_events = []
        for i in range(5):  # Events with 6-minute gaps (>5 minute threshold)
            event_time = base_datetime + timedelta(minutes=i * 6)
            gap_events.append(AlgorithmInputEvent(
                id=f"gap-intermittent-{i:03d}",
                startTimestamp=event_time.isoformat() + ".000Z"
            ))

        violations = tracker._analyze_intermittent_violations_from_events(gap_events)
        assert len(violations) == 0

    def test_convert_to_algorithm_input_events(self):
        """Test conversion of PersistedBarkEvent to AlgorithmInputEvent objects."""
        tracker = LegalViolationTracker(interactive=False)

        # Create test PersistedBarkEvent objects
        persisted_events = [
            PersistedBarkEvent(
                realworld_date="2025-09-21",
                realworld_time="10:00:00",
                bark_id="test-001",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250921_100000.wav",
                bark_audiofile_timestamp="00:00:05.000",
                confidence=0.8,
                intensity=0.5
            ),
            PersistedBarkEvent(
                realworld_date="2025-09-21",
                realworld_time="10:00:15",
                bark_id="test-002",
                bark_type="Howl",
                est_dog_size=None,
                audio_file_name="bark_recording_20250921_100000.wav",
                bark_audiofile_timestamp="00:00:20.000",
                confidence=0.9,
                intensity=0.7
            )
        ]

        # Convert to algorithm input events
        algorithm_events = tracker._convert_to_algorithm_input_events(persisted_events)

        assert len(algorithm_events) == 2

        # Verify first event
        assert algorithm_events[0].id == "test-001"
        assert algorithm_events[0].startTimestamp == "2025-09-21T10:00:00.000Z"

        # Verify second event
        assert algorithm_events[1].id == "test-002"
        assert algorithm_events[1].startTimestamp == "2025-09-21T10:00:15.000Z"

        # Verify sorted by timestamp
        assert algorithm_events[0].startTimestamp <= algorithm_events[1].startTimestamp

        # Test with invalid timestamp (should skip)
        invalid_event = PersistedBarkEvent(
            realworld_date="invalid-date",
            realworld_time="invalid-time",
            bark_id="test-invalid",
            bark_type="Bark",
            est_dog_size=None,
            audio_file_name="test.wav",
            bark_audiofile_timestamp="00:00:05.000",
            confidence=0.8,
            intensity=0.5
        )

        algorithm_events = tracker._convert_to_algorithm_input_events([invalid_event])
        assert len(algorithm_events) == 0  # Should skip invalid event

    def test_convert_to_absolute_timestamps(self):
        """Test conversion of PersistedBarkEvent to absolute timestamps."""
        tracker = LegalViolationTracker(interactive=False)

        # Create test PersistedBarkEvent objects
        persisted_events = [
            PersistedBarkEvent(
                realworld_date="2025-08-18",
                realworld_time="08:19:58",
                bark_id="test-1",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250818_081958.wav",
                bark_audiofile_timestamp="00:00:15.500",  # 15.5 seconds into file
                confidence=0.8,
                intensity=0.5
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-18",
                realworld_time="08:22:03",
                bark_id="test-2",
                bark_type="Yip",
                est_dog_size=None,
                audio_file_name="bark_recording_20250818_081958.wav",
                bark_audiofile_timestamp="00:02:05.000",  # 125 seconds into file
                confidence=0.9,
                intensity=0.6
            )
        ]

        absolute_events = tracker._convert_to_absolute_timestamps(persisted_events)

        assert len(absolute_events) == 2

        # Events should have absolute timestamps (seconds since epoch)
        for event in absolute_events:
            assert hasattr(event, 'start_time')
            assert hasattr(event, 'end_time')
            assert hasattr(event, 'confidence')
            assert event.start_time > 1693000000  # Reasonable timestamp (after 2023)
            assert event.end_time > event.start_time

        # Events should be ordered by absolute time
        assert absolute_events[0].start_time < absolute_events[1].start_time

    def test_hybrid_architecture_analysis(self):
        """Test that the hybrid approach (sessions + direct events) works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            tracker = LegalViolationTracker(violation_db=db)

            # Mock detector with dual sensitivity
            mock_detector = Mock()
            mock_detector.sample_rate = 16000
            mock_detector.session_gap_threshold = 10.0
            mock_detector.analysis_sensitivity = 0.3

            # Mock bark events for violation analysis
            mock_bark_events = create_continuous_bark_events(total_minutes=6.0, gap_seconds=8.0)

            # Mock the detector's detection method
            mock_detector._detect_barks_in_buffer_with_sensitivity.return_value = mock_bark_events

            # Create test audio file
            date_folder = Path(temp_dir) / "2025-08-18"
            date_folder.mkdir()
            test_file = date_folder / "bark_recording_20250818_081958.wav"
            test_file.touch()

            # Mock librosa.load
            with patch('librosa.load') as mock_librosa_load:
                mock_librosa_load.return_value = (np.random.rand(5760000), 16000)

                # Run hybrid analysis
                violations = tracker.analyze_recordings_for_date(Path(temp_dir), "2025-08-18", mock_detector)

                # Should detect violations using direct event analysis
                assert len(violations) >= 1

                # Verify violations have proper structure
                for violation in violations:
                    assert hasattr(violation, 'violation_type')
                    assert hasattr(violation, 'total_bark_duration')
                    assert violation.violation_type in ["Constant", "Intermittent"]
                    assert violation.date == "2025-08-18"
