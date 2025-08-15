"""Tests for bark_detector.core.models"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from bark_detector.core.models import (
    BarkEvent, BarkingSession, CalibrationProfile, GroundTruthEvent,
    seconds_to_timestamp, timestamp_to_seconds, detect_timestamp_format
)


class TestTimestampUtilities:
    """Test timestamp conversion utility functions"""
    
    def test_seconds_to_timestamp_basic(self):
        """Test basic seconds to timestamp conversion"""
        assert seconds_to_timestamp(0.0) == "00:00:00.000"
        assert seconds_to_timestamp(1.5) == "00:00:01.500"
        assert seconds_to_timestamp(65.250) == "00:01:05.250"
        assert seconds_to_timestamp(3661.123) == "01:01:01.123"
        
    def test_seconds_to_timestamp_precision(self):
        """Test timestamp precision handling"""
        assert seconds_to_timestamp(1.1234) == "00:00:01.123"  # Truncated to milliseconds
        assert seconds_to_timestamp(1.9999) == "00:00:01.999"
        
    def test_timestamp_to_seconds_basic(self):
        """Test basic timestamp to seconds conversion"""
        assert timestamp_to_seconds("00:00:00.000") == 0.0
        assert timestamp_to_seconds("00:00:01.500") == 1.5
        assert timestamp_to_seconds("00:01:05.250") == 65.25
        assert timestamp_to_seconds("01:01:01.123") == 3661.123
        
    def test_timestamp_to_seconds_flexible_format(self):
        """Test flexible timestamp format parsing"""
        assert timestamp_to_seconds("05.250") == 5.25  # SS.mmm
        assert timestamp_to_seconds("01:05.250") == 65.25  # MM:SS.mmm
        assert timestamp_to_seconds("01:01:05.250") == 3665.25  # HH:MM:SS.mmm
        
    def test_timestamp_to_seconds_invalid_format(self):
        """Test invalid timestamp format handling"""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            timestamp_to_seconds("invalid")
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            timestamp_to_seconds("25:00:00.000")  # No validation for now, but format is wrong
            
    def test_detect_timestamp_format(self):
        """Test timestamp format detection"""
        assert detect_timestamp_format(1.5) == "seconds"
        assert detect_timestamp_format(0) == "seconds"
        assert detect_timestamp_format("00:00:01.500") == "timestamp"
        assert detect_timestamp_format("01:05.250") == "timestamp"
        assert detect_timestamp_format("5.250") == "timestamp"
        
    def test_detect_timestamp_format_string_numbers(self):
        """Test format detection with string representations of numbers"""
        assert detect_timestamp_format("1.5") == "seconds"
        assert detect_timestamp_format("0") == "seconds"
        
    def test_roundtrip_conversion(self):
        """Test that conversion is reversible"""
        test_values = [0.0, 1.5, 65.25, 3661.123, 7200.999]
        
        for seconds in test_values:
            timestamp = seconds_to_timestamp(seconds)
            converted_back = timestamp_to_seconds(timestamp)
            assert abs(converted_back - seconds) < 0.0011  # Within 1ms precision (accounting for floating point errors)


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
        
    def test_timestamp_format_creation(self):
        """Test creating GroundTruthEvent with HH:MM:SS.mmm format"""
        event = GroundTruthEvent(
            start_time="00:00:02.000",
            end_time="00:00:03.500",
            description="Timestamp format bark"
        )
        
        assert event.start_time == 2.0
        assert event.end_time == 3.5
        assert event.duration == 1.5
        assert event.start_timestamp == "00:00:02.000"
        assert event.end_timestamp == "00:00:03.500"
        
    def test_mixed_format_creation(self):
        """Test creating GroundTruthEvent with mixed float/string formats"""
        event = GroundTruthEvent(
            start_time=2.5,  # float
            end_time="00:00:04.250",  # string
            description="Mixed format bark"
        )
        
        assert event.start_time == 2.5
        assert event.end_time == 4.25
        assert event.duration == 1.75
        
    def test_from_dict_legacy_format(self):
        """Test from_dict with legacy decimal seconds format"""
        data = {
            'start_time': 1.5,
            'end_time': 2.8,
            'description': 'Legacy format',
            'confidence_expected': 0.85
        }
        
        event = GroundTruthEvent.from_dict(data)
        assert event.start_time == 1.5
        assert event.end_time == 2.8
        assert event.description == 'Legacy format'
        assert event.confidence_expected == 0.85
        
    def test_from_dict_timestamp_format(self):
        """Test from_dict with HH:MM:SS.mmm format"""
        data = {
            'start_time': '00:00:01.500',
            'end_time': '00:00:02.800',
            'description': 'Timestamp format',
            'confidence_expected': 0.85
        }
        
        event = GroundTruthEvent.from_dict(data)
        assert event.start_time == 1.5
        assert event.end_time == 2.8
        assert event.description == 'Timestamp format'
        assert event.confidence_expected == 0.85
        
    def test_to_dict_timestamp_format(self):
        """Test to_dict with timestamp format output"""
        event = GroundTruthEvent(1.5, 2.75, "Test event")  # Use 2.75 which is exactly representable
        
        data = event.to_dict(use_timestamp_format=True)
        assert data['start_time'] == '00:00:01.500'
        assert data['end_time'] == '00:00:02.750'
        assert data['description'] == 'Test event'
        assert data['confidence_expected'] == 1.0
        
    def test_to_dict_seconds_format(self):
        """Test to_dict with decimal seconds format output"""
        event = GroundTruthEvent("00:00:01.500", "00:00:02.750", "Test event")
        
        data = event.to_dict(use_timestamp_format=False)
        assert data['start_time'] == 1.5
        assert data['end_time'] == 2.75
        assert data['description'] == 'Test event'
        assert data['confidence_expected'] == 1.0
        
    def test_invalid_timestamp_validation(self):
        """Test validation catches invalid timestamps"""
        with pytest.raises(ValueError, match="Invalid event.*start_time.*must be.*end_time"):
            GroundTruthEvent(5.0, 2.0)  # start > end
            
        with pytest.raises(ValueError, match="Invalid event.*start_time.*must be.*end_time"):
            GroundTruthEvent(2.0, 2.0)  # start == end