"""Tests for bark_detector.core.models"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from bark_detector.core.models import (
    BarkEvent, BarkingSession, CalibrationProfile, GroundTruthEvent
)


class TestBarkEvent:
    """Test BarkEvent data model"""
    
    def test_creation(self):
        """Test basic BarkEvent creation"""
        event = BarkEvent(
            start_time=1.0,
            end_time=1.5,
            confidence=0.75
        )
        
        assert event.start_time == 1.0
        assert event.end_time == 1.5
        assert event.confidence == 0.75
        assert event.intensity == 0.0  # Default value
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        event = BarkEvent(0.5, 2.0, 0.8)
        duration = event.end_time - event.start_time
        assert duration == 1.5
    
    def test_with_intensity(self):
        """Test BarkEvent with intensity"""
        event = BarkEvent(1.0, 1.5, 0.75, 0.9)
        assert event.intensity == 0.9


class TestBarkingSession:
    """Test BarkingSession data model"""
    
    def test_creation(self, sample_barking_session):
        """Test basic BarkingSession creation"""
        session = sample_barking_session
        
        assert session.start_time == 1.0
        assert session.end_time == 4.0
        assert len(session.events) == 3
        assert session.total_barks == 3
        assert session.total_duration == 1.8
        assert session.avg_confidence == 0.75
        assert session.peak_confidence == 0.82
        assert session.barks_per_second == 1.0
    
    def test_session_duration_calculation(self, sample_barking_session):
        """Test session duration calculation"""
        session = sample_barking_session
        session_duration = session.end_time - session.start_time
        assert session_duration == 3.0  # 4.0 - 1.0
    
    def test_bark_count(self, sample_barking_session):
        """Test bark count"""
        session = sample_barking_session
        assert session.total_barks == 3
        assert len(session.events) == 3


class TestCalibrationProfile:
    """Test CalibrationProfile data model"""
    
    def test_creation(self, sample_calibration_profile):
        """Test basic CalibrationProfile creation"""
        profile = sample_calibration_profile
        
        assert profile.name == "test_profile"
        assert profile.sensitivity == 0.68
        assert profile.min_bark_duration == 0.5
        assert profile.session_gap_threshold == 10.0
        assert profile.background_noise_level == 0.01
        assert profile.location == "Test Environment"
        assert profile.notes == "Test profile for unit tests"
    
    def test_save_and_load(self, sample_calibration_profile, temp_dir):
        """Test saving and loading profiles"""
        profile = sample_calibration_profile
        profile_path = temp_dir / "test_profile.json"
        
        # Save profile
        profile.save(profile_path)
        assert profile_path.exists()
        
        # Load profile
        loaded_profile = CalibrationProfile.load(profile_path)
        
        # Verify all fields match
        assert loaded_profile.name == profile.name
        assert loaded_profile.sensitivity == profile.sensitivity
        assert loaded_profile.min_bark_duration == profile.min_bark_duration
        assert loaded_profile.session_gap_threshold == profile.session_gap_threshold
        assert loaded_profile.background_noise_level == profile.background_noise_level
        assert loaded_profile.location == profile.location
        assert loaded_profile.notes == profile.notes
        assert loaded_profile.created_date == profile.created_date
    
    def test_load_nonexistent_file(self, temp_dir):
        """Test loading non-existent profile file"""
        nonexistent_path = temp_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            CalibrationProfile.load(nonexistent_path)
    
    def test_load_invalid_json(self, temp_dir):
        """Test loading invalid JSON file"""
        invalid_path = temp_dir / "invalid.json"
        
        # Create invalid JSON file
        with open(invalid_path, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            CalibrationProfile.load(invalid_path)


class TestGroundTruthEvent:
    """Test GroundTruthEvent data model"""
    
    def test_creation(self):
        """Test basic GroundTruthEvent creation"""
        event = GroundTruthEvent(
            start_time=2.0,
            end_time=3.5,
            description="Loud bark",
            confidence_expected=0.9
        )
        
        assert event.start_time == 2.0
        assert event.end_time == 3.5
        assert event.description == "Loud bark"
        assert event.confidence_expected == 0.9
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        event = GroundTruthEvent(1.0, 2.5, "Test bark")
        duration = event.end_time - event.start_time
        assert duration == 1.5
    
    def test_default_values(self):
        """Test default values"""
        event = GroundTruthEvent(1.0, 2.0)
        assert event.description == ""
        assert event.confidence_expected == 1.0