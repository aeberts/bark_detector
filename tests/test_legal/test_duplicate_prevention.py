"""Tests for B8 duplicate violation prevention fix"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from bark_detector.legal.database import ViolationDatabase
from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.legal.models import ViolationReport
from bark_detector.core.models import BarkEvent


class TestDuplicateViolationPrevention:
    """Test duplicate violation prevention functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            db_path = Path(tmp.name)
        
        yield db_path
        
        # Cleanup
        if db_path.exists():
            os.unlink(db_path)
    
    def test_has_violations_for_date(self, temp_db):
        """Test checking if violations exist for a date"""
        db = ViolationDatabase(temp_db)
        
        # Initially no violations
        assert not db.has_violations_for_date("2025-08-15")
        
        # Add violation
        violation = ViolationReport(
            date="2025-08-15",
            start_time="09:00:00",
            end_time="09:15:00",
            violation_type="Intermittent",
            total_bark_duration=900.0,
            total_incident_duration=1067.0,
            audio_files=["test1.wav"],
            audio_file_start_times=["09:00:00"],
            audio_file_end_times=["09:15:00"],
            confidence_scores=[0.8],
            peak_confidence=0.9,
            avg_confidence=0.8,
            created_timestamp="2025-08-18T10:00:00"
        )
        
        db.add_violation(violation)
        
        # Now should have violations
        assert db.has_violations_for_date("2025-08-15")
        assert not db.has_violations_for_date("2025-08-16")
    
    def test_remove_violations_for_date(self, temp_db):
        """Test removing violations for a specific date"""
        db = ViolationDatabase(temp_db)
        
        # Add violations for different dates
        violation1 = ViolationReport(
            date="2025-08-15", start_time="09:00:00", end_time="09:15:00",
            violation_type="Intermittent", total_bark_duration=900.0,
            total_incident_duration=1067.0, audio_files=["test1.wav"],
            audio_file_start_times=["09:00:00"], audio_file_end_times=["09:15:00"],
            confidence_scores=[0.8], peak_confidence=0.9, avg_confidence=0.8,
            created_timestamp="2025-08-18T10:00:00"
        )
        
        violation2 = ViolationReport(
            date="2025-08-16", start_time="10:00:00", end_time="10:15:00",
            violation_type="Constant", total_bark_duration=600.0,
            total_incident_duration=600.0, audio_files=["test2.wav"],
            audio_file_start_times=["10:00:00"], audio_file_end_times=["10:15:00"],
            confidence_scores=[0.75], peak_confidence=0.8, avg_confidence=0.75,
            created_timestamp="2025-08-18T11:00:00"
        )
        
        db.add_violation(violation1)
        db.add_violation(violation2)
        
        assert len(db.get_violations_by_date("2025-08-15")) == 1
        assert len(db.get_violations_by_date("2025-08-16")) == 1
        
        # Remove violations for one date
        removed_count = db.remove_violations_for_date("2025-08-15")
        
        assert removed_count == 1
        assert len(db.get_violations_by_date("2025-08-15")) == 0
        assert len(db.get_violations_by_date("2025-08-16")) == 1
    
    def test_add_violations_for_date_overwrite(self, temp_db):
        """Test adding violations with overwrite functionality"""
        db = ViolationDatabase(temp_db)
        
        # Add initial violation
        violation1 = ViolationReport(
            date="2025-08-15", start_time="09:00:00", end_time="09:15:00",
            violation_type="Intermittent", total_bark_duration=900.0,
            total_incident_duration=1067.0, audio_files=["test1.wav"],
            audio_file_start_times=["09:00:00"], audio_file_end_times=["09:15:00"],
            confidence_scores=[0.8], peak_confidence=0.9, avg_confidence=0.8,
            created_timestamp="2025-08-18T10:00:00"
        )
        
        db.add_violations_for_date([violation1], "2025-08-15")
        assert len(db.get_violations_by_date("2025-08-15")) == 1
        
        # Add new violation with overwrite
        violation2 = ViolationReport(
            date="2025-08-15", start_time="10:00:00", end_time="10:05:00",
            violation_type="Constant", total_bark_duration=300.0,
            total_incident_duration=300.0, audio_files=["test2.wav"],
            audio_file_start_times=["10:00:00"], audio_file_end_times=["10:05:00"],
            confidence_scores=[0.75], peak_confidence=0.8, avg_confidence=0.75,
            created_timestamp="2025-08-18T11:00:00"
        )
        
        db.add_violations_for_date([violation2], "2025-08-15", overwrite=True)
        
        violations = db.get_violations_by_date("2025-08-15")
        assert len(violations) == 1
        assert violations[0].violation_type == "Constant"
    
    def test_add_violations_for_date_no_overwrite(self, temp_db):
        """Test adding violations without overwrite"""
        db = ViolationDatabase(temp_db)
        
        # Add initial violation
        violation1 = ViolationReport(
            date="2025-08-15", start_time="09:00:00", end_time="09:15:00",
            violation_type="Intermittent", total_bark_duration=900.0,
            total_incident_duration=1067.0, audio_files=["test1.wav"],
            audio_file_start_times=["09:00:00"], audio_file_end_times=["09:15:00"],
            confidence_scores=[0.8], peak_confidence=0.9, avg_confidence=0.8,
            created_timestamp="2025-08-18T10:00:00"
        )
        
        db.add_violations_for_date([violation1], "2025-08-15")
        
        # Add new violation without overwrite
        violation2 = ViolationReport(
            date="2025-08-15", start_time="10:00:00", end_time="10:05:00",
            violation_type="Constant", total_bark_duration=300.0,
            total_incident_duration=300.0, audio_files=["test2.wav"],
            audio_file_start_times=["10:00:00"], audio_file_end_times=["10:05:00"],
            confidence_scores=[0.75], peak_confidence=0.8, avg_confidence=0.75,
            created_timestamp="2025-08-18T11:00:00"
        )
        
        db.add_violations_for_date([violation2], "2025-08-15", overwrite=False)
        
        violations = db.get_violations_by_date("2025-08-15")
        assert len(violations) == 2
        assert violations[0].violation_type == "Intermittent"
        assert violations[1].violation_type == "Constant"
    
    @patch('bark_detector.legal.tracker.librosa.load')
    def test_tracker_non_interactive_mode(self, mock_librosa_load, tmp_path):
        """Test that tracker in non-interactive mode overwrites existing violations"""
        # Use date-based violations directory
        violations_dir = tmp_path / "violations"
        db = ViolationDatabase(violations_dir=violations_dir)
        tracker = LegalViolationTracker(violation_db=db, interactive=False)
        
        # Create mock detector
        mock_detector = Mock()
        mock_detector.sample_rate = 16000
        mock_detector.session_gap_threshold = 10.0
        
        # Mock bark events for 6-minute violation
        mock_bark_events = [
            BarkEvent(start_time=10.0, end_time=370.0, confidence=0.8)
        ]
        mock_detector._detect_barks_in_buffer.return_value = mock_bark_events
        
        # Create test recording file
        test_file = tmp_path / "bark_recording_20250815_120000.wav"
        test_file.touch()
        
        # Mock audio loading - simulate 6 minute file
        mock_librosa_load.return_value = (np.random.rand(5760000), 16000)
        
        # First analysis
        violations1 = tracker.analyze_recordings_for_date(tmp_path, "2025-08-15", mock_detector)
        assert len(violations1) == 1
        assert len(db.get_violations_by_date("2025-08-15")) == 1
        
        # Second analysis (should overwrite in non-interactive mode)
        violations2 = tracker.analyze_recordings_for_date(tmp_path, "2025-08-15", mock_detector)
        assert len(violations2) == 1
        assert len(db.get_violations_by_date("2025-08-15")) == 1  # Still only 1, not 2