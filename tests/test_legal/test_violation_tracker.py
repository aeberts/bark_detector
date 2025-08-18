"""Tests for bark_detector.legal.tracker"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.legal.models import ViolationReport
from bark_detector.core.models import BarkEvent, BarkingSession


class TestLegalViolationTracker:
    """Test LegalViolationTracker class"""
    
    def test_initialization(self):
        """Test basic tracker initialization"""
        tracker = LegalViolationTracker()
        
        assert tracker.violations == []
        assert tracker.sessions == []
    
    def test_analyze_violations_continuous(self):
        """Test analysis of continuous violations (5+ minutes)"""
        tracker = LegalViolationTracker()
        
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
    
    @patch('librosa.load')
    def test_analyze_recordings_for_date(self, mock_librosa_load, temp_dir):
        """Test analyzing recordings for a specific date"""
        tracker = LegalViolationTracker()
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        # Mock the _detect_barks_in_buffer method to return bark events for a 6-minute file
        mock_bark_events = [
            BarkEvent(start_time=10.0, end_time=370.0, confidence=0.8)  # 6+ minute bark event
        ]
        mock_detector._detect_barks_in_buffer.return_value = mock_bark_events
        
        # Create test recording files
        date_folder = temp_dir / "2025-08-14"
        date_folder.mkdir()
        test_file = date_folder / "bark_recording_20250814_120000.wav"
        test_file.touch()
        
        # Mock audio loading - simulate 6 minute file (continuous violation)
        mock_librosa_load.return_value = (np.random.rand(5760000), 16000)  # 6 minutes at 16kHz
        
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)
        
        assert len(violations) == 1
        violation = violations[0]
        assert violation.date == "2025-08-14"
        assert violation.violation_type == "Constant"
        assert violation.total_bark_duration >= 300.0  # 5+ minutes
        assert str(test_file) in violation.audio_files
    
    @patch('librosa.load')
    def test_analyze_recordings_no_violations(self, mock_librosa_load, temp_dir):
        """Test analyzing recordings with no violations"""
        tracker = LegalViolationTracker()
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        # Mock the _detect_barks_in_buffer method to return short bark events (no violations)
        mock_bark_events = [
            BarkEvent(start_time=10.0, end_time=50.0, confidence=0.7)  # Short bark event (40 seconds)
        ]
        mock_detector._detect_barks_in_buffer.return_value = mock_bark_events
        
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
        tracker = LegalViolationTracker()
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        violations = tracker.analyze_recordings_for_date(temp_dir, "2025-08-14", mock_detector)
        
        assert len(violations) == 0
    
    @patch('librosa.load')
    def test_analyze_recordings_flat_structure(self, mock_librosa_load, temp_dir):
        """Test analyzing recordings in flat directory structure"""
        tracker = LegalViolationTracker()
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        # Mock the _detect_barks_in_buffer method to return bark events for a 6-minute file
        mock_bark_events = [
            BarkEvent(start_time=10.0, end_time=370.0, confidence=0.8)  # 6+ minute bark event
        ]
        mock_detector._detect_barks_in_buffer.return_value = mock_bark_events
        
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
        tracker = LegalViolationTracker()
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
        tracker = LegalViolationTracker()
        
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