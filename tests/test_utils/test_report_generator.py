"""Comprehensive tests for LogBasedReportGenerator"""

import pytest
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from bark_detector.utils.report_generator import (
    LogBasedReportGenerator, 
    BarkEvent, 
    ViolationReport
)
from bark_detector.utils.time_utils import extract_bark_info_from_log


class TestBarkEvent:
    """Test BarkEvent data model"""
    
    def test_bark_event_creation(self):
        """Test BarkEvent creation and basic properties"""
        timestamp = datetime(2025, 8, 15, 6, 25, 13)
        event = BarkEvent(timestamp, 0.824, 0.375, "bark_file.wav", "00:00:15.267")
        
        assert event.timestamp == timestamp
        assert event.confidence == 0.824
        assert event.intensity == 0.375
        assert event.audio_file == "bark_file.wav"
        assert event.offset_in_file == "00:00:15.267"
    
    def test_time_of_day(self):
        """Test time_of_day formatting"""
        timestamp = datetime(2025, 8, 15, 6, 25, 13)
        event = BarkEvent(timestamp, 0.824, 0.375)
        
        assert event.time_of_day() == "06:25:13"


class TestViolationReport:
    """Test ViolationReport data model"""
    
    def test_violation_report_creation(self):
        """Test ViolationReport creation and basic properties"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 47, 23)
        violation = ViolationReport("Intermittent", start_time, end_time)
        
        assert violation.violation_type == "Intermittent"
        assert violation.start_time == start_time
        assert violation.end_time == end_time
        assert len(violation.bark_events) == 0
        assert len(violation.audio_files) == 0
    
    def test_add_bark_event(self):
        """Test adding bark events to violation"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 47, 23)
        violation = ViolationReport("Intermittent", start_time, end_time)
        
        event1 = BarkEvent(datetime(2025, 8, 15, 6, 25, 15), 0.8, 0.4, "file1.wav")
        event2 = BarkEvent(datetime(2025, 8, 15, 6, 25, 20), 0.7, 0.3, "file2.wav")
        event3 = BarkEvent(datetime(2025, 8, 15, 6, 25, 25), 0.9, 0.5, "file1.wav")  # Same file
        
        violation.add_bark_event(event1)
        violation.add_bark_event(event2)
        violation.add_bark_event(event3)
        
        assert len(violation.bark_events) == 3
        assert len(violation.audio_files) == 2  # Only unique files
        assert "file1.wav" in violation.audio_files
        assert "file2.wav" in violation.audio_files
    
    def test_time_formatting(self):
        """Test time formatting methods"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 47, 23)
        violation = ViolationReport("Intermittent", start_time, end_time)
        
        assert violation.start_time_of_day() == "06:25:13"
        assert violation.end_time_of_day() == "06:47:23"
        assert violation.duration_string() == "22 mins 10 seconds"
    
    def test_total_barks(self):
        """Test total bark count"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 47, 23)
        violation = ViolationReport("Intermittent", start_time, end_time)
        
        # Add some events
        for i in range(5):
            event = BarkEvent(start_time + timedelta(seconds=i*60), 0.8, 0.4)
            violation.add_bark_event(event)
        
        assert violation.total_barks() == 5


class TestLogBasedReportGenerator:
    """Test LogBasedReportGenerator functionality"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            logs_dir = temp_path / "logs"
            recordings_dir = temp_path / "recordings"
            logs_dir.mkdir()
            recordings_dir.mkdir()
            
            yield {
                'base': temp_path,
                'logs': logs_dir,
                'recordings': recordings_dir
            }
    
    @pytest.fixture
    def sample_log_content(self):
        """Sample log content with bark detections"""
        return """2025-08-15 06:24:56,123 - INFO - YAMNet model loaded successfully!
2025-08-15 06:25:00,456 - INFO - 🐕 BARK DETECTED! Confidence: 0.824, Intensity: 0.375, Duration: 0.96s
2025-08-15 06:25:15,789 - INFO - 🐕 BARK DETECTED! Confidence: 0.756, Intensity: 0.421, Duration: 0.48s
2025-08-15 06:25:30,012 - INFO - 🐕 BARK DETECTED! Confidence: 0.892, Intensity: 0.512, Duration: 1.44s
2025-08-15 06:26:45,345 - INFO - Some other log message
2025-08-15 06:27:00,678 - INFO - 🐕 BARK DETECTED! Confidence: 0.731, Intensity: 0.398, Duration: 0.72s"""
    
    def test_find_log_file_for_date_date_folder(self, temp_dirs):
        """Test finding log file in date-based folder structure"""
        generator = LogBasedReportGenerator(
            logs_directory=str(temp_dirs['logs']),
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        # Create date-based log file
        date_folder = temp_dirs['logs'] / "2025-08-15"
        date_folder.mkdir()
        log_file = date_folder / "bark_detector-2025-08-15.log"
        log_file.write_text("test log content")
        
        target_date = date(2025, 8, 15)
        found_file = generator.find_log_file_for_date(target_date)
        
        assert found_file == log_file
    
    def test_find_log_file_for_date_legacy(self, temp_dirs):
        """Test finding legacy log file"""
        generator = LogBasedReportGenerator(
            logs_directory=str(temp_dirs['logs']),
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        # Create legacy log file in current directory and patch Path for legacy file check
        legacy_log = temp_dirs['base'] / "bark_detector.log"
        legacy_log.write_text("legacy log content")
        
        # Mock the Path constructor to return our temp legacy log file
        with patch('bark_detector.utils.report_generator.Path') as mock_path:
            mock_path.return_value = legacy_log
            
            target_date = date(2025, 8, 15)
            found_file = generator.find_log_file_for_date(target_date)
            
            assert found_file == legacy_log
    
    def test_find_log_file_for_date_not_found(self, temp_dirs):
        """Test when no log file is found"""
        generator = LogBasedReportGenerator(
            logs_directory=str(temp_dirs['logs']),
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        target_date = date(2025, 8, 15)
        found_file = generator.find_log_file_for_date(target_date)
        
        assert found_file is None
    
    def test_parse_log_for_barks(self, temp_dirs, sample_log_content):
        """Test parsing bark events from log file"""
        generator = LogBasedReportGenerator(
            logs_directory=str(temp_dirs['logs']),
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        # Create log file
        log_file = temp_dirs['logs'] / "test.log"
        log_file.write_text(sample_log_content)
        
        target_date = date(2025, 8, 15)
        bark_events = generator.parse_log_for_barks(log_file, target_date)
        
        assert len(bark_events) == 4
        
        # Check first event
        assert bark_events[0].timestamp == datetime(2025, 8, 15, 6, 25, 0, 456000)
        assert bark_events[0].confidence == 0.824
        assert bark_events[0].intensity == 0.375
        
        # Check last event
        assert bark_events[-1].timestamp == datetime(2025, 8, 15, 6, 27, 0, 678000)
        assert bark_events[-1].confidence == 0.731
        assert bark_events[-1].intensity == 0.398
    
    def test_find_audio_files_for_date_date_folder(self, temp_dirs):
        """Test finding audio files in date-based folder"""
        generator = LogBasedReportGenerator(
            logs_directory=str(temp_dirs['logs']),
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        # Create date-based audio files
        date_folder = temp_dirs['recordings'] / "2025-08-15"
        date_folder.mkdir()
        
        files = [
            "bark_recording_20250815_062511.wav",
            "bark_recording_20250815_064746.wav",
            "bark_recording_20250815_070123.wav"
        ]
        
        for filename in files:
            (date_folder / filename).write_text("audio data")
        
        target_date = date(2025, 8, 15)
        found_files = generator.find_audio_files_for_date(target_date)
        
        assert len(found_files) == 3
        assert all(f.name in files for f in found_files)
    
    def test_find_audio_files_for_date_flat_structure(self, temp_dirs):
        """Test finding audio files in flat structure"""
        generator = LogBasedReportGenerator(
            logs_directory=str(temp_dirs['logs']),
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        # Create flat structure audio files
        files = [
            "bark_recording_20250815_062511.wav",
            "bark_recording_20250815_064746.wav",
            "bark_recording_20250814_123456.wav"  # Different date
        ]
        
        for filename in files:
            (temp_dirs['recordings'] / filename).write_text("audio data")
        
        target_date = date(2025, 8, 15)
        found_files = generator.find_audio_files_for_date(target_date)
        
        assert len(found_files) == 2  # Only 2025-08-15 files
        expected_files = files[:2]
        assert all(f.name in expected_files for f in found_files)
    
    @patch('bark_detector.utils.report_generator.SOUNDFILE_AVAILABLE', True)
    @patch('bark_detector.utils.report_generator.sf')
    def test_get_audio_file_duration_success(self, mock_sf, temp_dirs):
        """Test getting actual audio file duration"""
        generator = LogBasedReportGenerator()
        
        # Mock soundfile
        mock_soundfile = Mock()
        mock_soundfile.__len__ = Mock(return_value=48000)  # 48000 samples
        mock_soundfile.samplerate = 16000  # 16kHz
        mock_sf.SoundFile.return_value.__enter__ = Mock(return_value=mock_soundfile)
        mock_sf.SoundFile.return_value.__exit__ = Mock(return_value=None)
        
        audio_file = temp_dirs['recordings'] / "test.wav"
        duration = generator.get_audio_file_duration(audio_file)
        
        assert duration == 3.0  # 48000 / 16000 = 3 seconds
    
    @patch('bark_detector.utils.report_generator.SOUNDFILE_AVAILABLE', False)
    def test_get_audio_file_duration_fallback(self, temp_dirs):
        """Test fallback when soundfile not available"""
        generator = LogBasedReportGenerator()
        
        audio_file = temp_dirs['recordings'] / "test.wav"
        duration = generator.get_audio_file_duration(audio_file)
        
        assert duration == 1800  # 30 minutes fallback
    
    @patch('bark_detector.utils.report_generator.SOUNDFILE_AVAILABLE', True)
    @patch('bark_detector.utils.report_generator.sf')
    def test_correlate_barks_with_audio_files(self, mock_sf, temp_dirs):
        """Test correlating bark events with audio files"""
        generator = LogBasedReportGenerator(
            recordings_directory=str(temp_dirs['recordings'])
        )
        
        # Mock soundfile for 30-second files
        mock_soundfile = Mock()
        mock_soundfile.__len__ = Mock(return_value=480000)  # 30 seconds at 16kHz
        mock_soundfile.samplerate = 16000
        mock_sf.SoundFile.return_value.__enter__ = Mock(return_value=mock_soundfile)
        mock_sf.SoundFile.return_value.__exit__ = Mock(return_value=None)
        
        # Create audio files
        audio_files = [
            temp_dirs['recordings'] / "bark_recording_20250815_062500.wav",  # 06:25:00
            temp_dirs['recordings'] / "bark_recording_20250815_062600.wav",  # 06:26:00
        ]
        for f in audio_files:
            f.write_text("audio")
        
        # Create bark events
        bark_events = [
            BarkEvent(datetime(2025, 8, 15, 6, 25, 10), 0.8, 0.4),  # Should match first file
            BarkEvent(datetime(2025, 8, 15, 6, 26, 15), 0.7, 0.3),  # Should match second file
            BarkEvent(datetime(2025, 8, 15, 6, 30, 0), 0.9, 0.5),   # Should not match any
        ]
        
        generator.correlate_barks_with_audio_files(bark_events, audio_files)
        
        # Check correlations
        assert bark_events[0].audio_file == "bark_recording_20250815_062500.wav"
        assert bark_events[0].offset_in_file == "00:00:10.000"
        
        assert bark_events[1].audio_file == "bark_recording_20250815_062600.wav"
        assert bark_events[1].offset_in_file == "00:00:15.000"
        
        # Third event should not be correlated (outside any file's duration)
        assert bark_events[2].audio_file == ""
        assert bark_events[2].offset_in_file == ""
    
    def test_generate_violation_summary_report(self):
        """Test generating violation summary report"""
        generator = LogBasedReportGenerator()
        
        # Create test violations
        start_time1 = datetime(2025, 8, 15, 6, 25, 13)
        end_time1 = datetime(2025, 8, 15, 6, 47, 23)
        violation1 = ViolationReport("Intermittent", start_time1, end_time1)
        violation1.audio_files = ["file1.wav", "file2.wav"]
        
        # Add some bark events
        for i in range(10):
            event = BarkEvent(start_time1 + timedelta(seconds=i*60), 0.8, 0.4)
            violation1.add_bark_event(event)
        
        start_time2 = datetime(2025, 8, 15, 8, 10, 0)
        end_time2 = datetime(2025, 8, 15, 8, 15, 30)
        violation2 = ViolationReport("Constant", start_time2, end_time2)
        violation2.audio_files = ["file3.wav"]
        
        violations = [violation1, violation2]
        target_date = date(2025, 8, 15)
        
        report = generator.generate_violation_summary_report(target_date, violations)
        
        # Check report content
        lines = report.split('\n')
        assert "Barking Violation Report Summary" in lines[0]
        assert "Date: 2025-08-15" in lines[1]
        assert "Total Violations: 2" in report
        assert "Constant Violations: 1" in report
        assert "Intermittent Violations: 1" in report
        assert "Violation 1 (Intermittent):" in report
        assert "Start time: 06:25:13  End Time 06:47:23" in report
        assert "Duration: 22 mins 10 seconds" in report
        assert "Total Barks: 10" in report
        assert "- file1.wav" in report
        assert "- file2.wav" in report
    
    def test_generate_detailed_violation_report(self):
        """Test generating detailed violation report"""
        generator = LogBasedReportGenerator()
        
        # Create test violation with bark events
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 47, 23)
        violation = ViolationReport("Intermittent", start_time, end_time)
        
        # Add bark events with different audio files
        events = [
            BarkEvent(datetime(2025, 8, 15, 6, 25, 15), 0.8, 0.4, "file1.wav", "00:00:02.01"),
            BarkEvent(datetime(2025, 8, 15, 6, 25, 20), 0.7, 0.3, "file1.wav", "00:00:07.01"),
            BarkEvent(datetime(2025, 8, 15, 6, 26, 0), 0.9, 0.5, "file2.wav", "00:00:15.34"),
        ]
        
        for event in events:
            violation.add_bark_event(event)
        
        target_date = date(2025, 8, 15)
        report = generator.generate_detailed_violation_report(target_date, violation, 1)
        
        # Check report content
        assert "Barking Detail Report for 2025-08-15, Violation 1" in report
        assert "Violation Type: Intermittent" in report
        assert "Start time: 06:25:13 End Time 06:47:23" in report
        assert "Duration: 22 mins 10 seconds" in report
        assert "Total Barks: 3" in report
        assert "# file1.wav" in report
        assert "# file2.wav" in report
        assert "- 2025-08-15 06:25:15 BARK (00:00:02.01)" in report
        assert "- 2025-08-15 06:25:20 BARK (00:00:07.01)" in report
        assert "- 2025-08-15 06:26:00 BARK (00:00:15.34)" in report
    
    @patch.object(LogBasedReportGenerator, 'find_log_file_for_date')
    @patch.object(LogBasedReportGenerator, 'parse_log_for_barks')
    @patch.object(LogBasedReportGenerator, 'find_audio_files_for_date')
    @patch.object(LogBasedReportGenerator, 'correlate_barks_with_audio_files')
    @patch.object(LogBasedReportGenerator, 'create_violations_from_bark_events')
    def test_generate_reports_for_date_success(self, mock_create_violations, mock_correlate, 
                                              mock_find_audio, mock_parse_log, mock_find_log):
        """Test successful report generation for a date"""
        generator = LogBasedReportGenerator()
        
        # Mock the various components
        log_file = Path("test.log")
        mock_find_log.return_value = log_file
        
        bark_events = [
            BarkEvent(datetime(2025, 8, 15, 6, 25, 0), 0.8, 0.4),
            BarkEvent(datetime(2025, 8, 15, 6, 25, 30), 0.7, 0.3),
        ]
        mock_parse_log.return_value = bark_events
        
        audio_files = [Path("file1.wav"), Path("file2.wav")]
        mock_find_audio.return_value = audio_files
        
        violation = ViolationReport("Intermittent", 
                                  datetime(2025, 8, 15, 6, 25, 0),
                                  datetime(2025, 8, 15, 6, 26, 0))
        mock_create_violations.return_value = [violation]
        
        target_date = date(2025, 8, 15)
        reports = generator.generate_reports_for_date(target_date)
        
        # Verify method calls
        mock_find_log.assert_called_once_with(target_date)
        mock_parse_log.assert_called_once_with(log_file, target_date)
        mock_find_audio.assert_called_once_with(target_date)
        mock_correlate.assert_called_once_with(bark_events, audio_files)
        mock_create_violations.assert_called_once_with(bark_events)
        
        # Check reports generated
        assert "summary" in reports
        assert "violation_1_detail" in reports
        assert "Barking Violation Report Summary" in reports["summary"]
    
    def test_generate_reports_for_date_no_log(self):
        """Test report generation when no log file found"""
        generator = LogBasedReportGenerator()
        
        target_date = date(2025, 8, 15)
        reports = generator.generate_reports_for_date(target_date)
        
        assert "error" in reports
        assert "No log file found for date 2025-08-15" in reports["error"]
    
    @patch.object(LogBasedReportGenerator, 'find_log_file_for_date')
    @patch.object(LogBasedReportGenerator, 'parse_log_for_barks')
    def test_generate_reports_for_date_no_barks(self, mock_parse_log, mock_find_log):
        """Test report generation when no bark events found"""
        generator = LogBasedReportGenerator()
        
        log_file = Path("test.log")
        mock_find_log.return_value = log_file
        mock_parse_log.return_value = []  # No bark events
        
        target_date = date(2025, 8, 15)
        reports = generator.generate_reports_for_date(target_date)
        
        assert "error" in reports
        assert "No bark events found in logs for date 2025-08-15" in reports["error"]


class TestViolationDetectionIntegration:
    """Test integration with real violation detection logic"""
    
    @patch('bark_detector.legal.tracker.LegalViolationTracker')
    def test_create_violations_from_bark_events(self, mock_tracker_class):
        """Test creating violations using real legal detection logic"""
        generator = LogBasedReportGenerator()
        
        # Mock the tracker
        mock_tracker = Mock()
        mock_tracker.analyze_violations.return_value = []
        mock_tracker_class.return_value = mock_tracker
        
        # Create bark events
        bark_events = [
            BarkEvent(datetime(2025, 8, 15, 6, 25, 0), 0.8, 0.4),
            BarkEvent(datetime(2025, 8, 15, 6, 25, 30), 0.7, 0.3),
            BarkEvent(datetime(2025, 8, 15, 6, 26, 0), 0.9, 0.5),
        ]
        
        violations = generator.create_violations_from_bark_events(bark_events)
        
        # Verify tracker was called correctly
        mock_tracker_class.assert_called_once_with(interactive=False)
        mock_tracker.analyze_violations.assert_called_once()
        
        # Verify sessions were created and passed to tracker
        call_args = mock_tracker.analyze_violations.call_args[0][0]  # First argument (sessions)
        assert len(call_args) > 0  # Sessions were created
        
    def test_events_to_sessions(self):
        """Test converting bark events to sessions"""
        generator = LogBasedReportGenerator()
        
        # Create bark events with different gaps
        from bark_detector.core.models import BarkEvent as CoreBarkEvent
        
        events = [
            CoreBarkEvent(start_time=0, end_time=1, confidence=0.8, intensity=0.4),
            CoreBarkEvent(start_time=5, end_time=6, confidence=0.7, intensity=0.3),     # 4s gap - same session
            CoreBarkEvent(start_time=20, end_time=21, confidence=0.9, intensity=0.5),   # 14s gap - new session
        ]
        
        sessions = generator._events_to_sessions(events, gap_threshold=10.0)
        
        assert len(sessions) == 2  # Two sessions due to large gap
        assert len(sessions[0].events) == 2  # First session has 2 events
        assert len(sessions[1].events) == 1  # Second session has 1 event
        
    def test_create_session_from_events(self):
        """Test creating session from events"""
        generator = LogBasedReportGenerator()
        
        from bark_detector.core.models import BarkEvent as CoreBarkEvent
        
        events = [
            CoreBarkEvent(start_time=0, end_time=1, confidence=0.8, intensity=0.4),
            CoreBarkEvent(start_time=2, end_time=3, confidence=0.7, intensity=0.3),
            CoreBarkEvent(start_time=4, end_time=5, confidence=0.9, intensity=0.5),
        ]
        
        session = generator._create_session_from_events(events)
        
        assert session.start_time == 0
        assert session.end_time == 5
        assert session.total_barks == 3
        assert session.total_duration == 3.0  # Sum of individual event durations
        assert abs(session.avg_confidence - 0.8) < 0.01  # (0.8 + 0.7 + 0.9) / 3 with floating point tolerance
        assert session.peak_confidence == 0.9
        assert abs(session.intensity - 0.4) < 0.01  # (0.4 + 0.3 + 0.5) / 3 with floating point tolerance