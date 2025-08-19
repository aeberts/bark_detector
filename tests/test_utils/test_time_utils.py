"""Tests for time utility functions"""

import pytest
from datetime import datetime, time
from bark_detector.utils.time_utils import (
    parse_log_timestamp,
    datetime_to_time_of_day,
    calculate_duration_string,
    extract_bark_info_from_log,
    parse_audio_filename_timestamp,
    get_audio_file_bark_offset
)


class TestParseLogTimestamp:
    """Test log timestamp parsing"""
    
    def test_parse_valid_timestamp(self):
        """Test parsing valid log timestamp"""
        log_line = "2025-08-15 06:25:13,456 - INFO - Some message"
        result = parse_log_timestamp(log_line)
        
        expected = datetime(2025, 8, 15, 6, 25, 13, 456000)
        assert result == expected
    
    def test_parse_timestamp_different_format(self):
        """Test parsing timestamp with different milliseconds"""
        log_line = "2025-12-31 23:59:59,999 - ERROR - Error message"
        result = parse_log_timestamp(log_line)
        
        expected = datetime(2025, 12, 31, 23, 59, 59, 999000)
        assert result == expected
    
    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamp"""
        log_line = "Invalid timestamp format"
        result = parse_log_timestamp(log_line)
        
        assert result is None
    
    def test_parse_malformed_timestamp(self):
        """Test parsing malformed timestamp"""
        log_line = "2025-13-45 25:70:80,999 - INFO - Message"
        result = parse_log_timestamp(log_line)
        
        assert result is None
    
    def test_parse_empty_line(self):
        """Test parsing empty line"""
        log_line = ""
        result = parse_log_timestamp(log_line)
        
        assert result is None


class TestDatetimeToTimeOfDay:
    """Test datetime to time-of-day conversion"""
    
    def test_morning_time(self):
        """Test morning time conversion"""
        dt = datetime(2025, 8, 15, 6, 25, 13)
        result = datetime_to_time_of_day(dt)
        
        assert result == "06:25:13"
    
    def test_evening_time(self):
        """Test evening time conversion"""
        dt = datetime(2025, 8, 15, 18, 47, 23)
        result = datetime_to_time_of_day(dt)
        
        assert result == "18:47:23"
    
    def test_midnight(self):
        """Test midnight conversion"""
        dt = datetime(2025, 8, 15, 0, 0, 0)
        result = datetime_to_time_of_day(dt)
        
        assert result == "00:00:00"
    
    def test_with_microseconds(self):
        """Test conversion ignores microseconds"""
        dt = datetime(2025, 8, 15, 12, 30, 45, 123456)
        result = datetime_to_time_of_day(dt)
        
        assert result == "12:30:45"


class TestCalculateDurationString:
    """Test duration string calculation"""
    
    def test_minutes_and_seconds(self):
        """Test duration with minutes and seconds"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 47, 23)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "22 mins 10 seconds"
    
    def test_hours_minutes_seconds(self):
        """Test duration with hours, minutes, and seconds"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 8, 30, 45)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "2 hours 5 mins 32 seconds"
    
    def test_only_seconds(self):
        """Test duration with only seconds"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 25, 30)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "17 seconds"
    
    def test_only_minutes(self):
        """Test duration with only minutes"""
        start_time = datetime(2025, 8, 15, 6, 25, 0)
        end_time = datetime(2025, 8, 15, 6, 30, 0)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "5 mins"
    
    def test_only_hours(self):
        """Test duration with only hours"""
        start_time = datetime(2025, 8, 15, 6, 0, 0)
        end_time = datetime(2025, 8, 15, 9, 0, 0)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "3 hours"
    
    def test_zero_duration(self):
        """Test zero duration"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 6, 25, 13)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "0 seconds"
    
    def test_singular_units(self):
        """Test singular units (1 hour, 1 min, 1 second)"""
        start_time = datetime(2025, 8, 15, 6, 25, 13)
        end_time = datetime(2025, 8, 15, 7, 26, 14)
        result = calculate_duration_string(start_time, end_time)
        
        assert result == "1 hour 1 min 1 second"


class TestExtractBarkInfoFromLog:
    """Test bark information extraction from log lines"""
    
    def test_extract_valid_bark_detection(self):
        """Test extracting bark detection info"""
        log_line = "2025-08-15 06:25:00,456 - INFO - 🐕 BARK DETECTED! Confidence: 0.824, Intensity: 0.375, Duration: 0.96s"
        result = extract_bark_info_from_log(log_line)
        
        assert result is not None
        timestamp, confidence, intensity, audio_filename = result
        
        assert timestamp == datetime(2025, 8, 15, 6, 25, 0, 456000)
        assert confidence == 0.824
        assert intensity == 0.375
        assert audio_filename == ""  # Not extracted from this log format
    
    def test_extract_different_values(self):
        """Test extracting with different confidence/intensity values"""
        log_line = "2025-08-15 12:30:45,123 - INFO - 🐕 BARK DETECTED! Confidence: 0.756, Intensity: 0.421, Duration: 1.44s"
        result = extract_bark_info_from_log(log_line)
        
        assert result is not None
        timestamp, confidence, intensity, audio_filename = result
        
        assert timestamp == datetime(2025, 8, 15, 12, 30, 45, 123000)
        assert confidence == 0.756
        assert intensity == 0.421
        assert audio_filename == ""
    
    def test_extract_no_bark_detection(self):
        """Test line without bark detection"""
        log_line = "2025-08-15 06:25:00,456 - INFO - YAMNet model loaded successfully"
        result = extract_bark_info_from_log(log_line)
        
        assert result is None
    
    def test_extract_invalid_timestamp(self):
        """Test bark detection with invalid timestamp"""
        log_line = "Invalid timestamp - 🐕 BARK DETECTED! Confidence: 0.824, Intensity: 0.375, Duration: 0.96s"
        result = extract_bark_info_from_log(log_line)
        
        assert result is None
    
    def test_extract_malformed_bark_line(self):
        """Test malformed bark detection line"""
        log_line = "2025-08-15 06:25:00,456 - INFO - 🐕 BARK DETECTED! Confidence: invalid, Intensity: 0.375"
        result = extract_bark_info_from_log(log_line)
        
        assert result is None


class TestParseAudioFilenameTimestamp:
    """Test audio filename timestamp parsing"""
    
    def test_parse_valid_filename(self):
        """Test parsing valid audio filename"""
        filename = "bark_recording_20250815_062511.wav"
        result = parse_audio_filename_timestamp(filename)
        
        expected = datetime(2025, 8, 15, 6, 25, 11)
        assert result == expected
    
    def test_parse_different_datetime(self):
        """Test parsing different date and time"""
        filename = "bark_recording_20251231_235959.wav"
        result = parse_audio_filename_timestamp(filename)
        
        expected = datetime(2025, 12, 31, 23, 59, 59)
        assert result == expected
    
    def test_parse_morning_time(self):
        """Test parsing morning time"""
        filename = "bark_recording_20250815_064746.wav"
        result = parse_audio_filename_timestamp(filename)
        
        expected = datetime(2025, 8, 15, 6, 47, 46)
        assert result == expected
    
    def test_parse_invalid_filename_format(self):
        """Test parsing invalid filename format"""
        filename = "invalid_filename.wav"
        result = parse_audio_filename_timestamp(filename)
        
        assert result is None
    
    def test_parse_invalid_date(self):
        """Test parsing invalid date"""
        filename = "bark_recording_20251301_062511.wav"  # Month 13
        result = parse_audio_filename_timestamp(filename)
        
        assert result is None
    
    def test_parse_invalid_time(self):
        """Test parsing invalid time"""
        filename = "bark_recording_20250815_256070.wav"  # Hour 25, minute 60
        result = parse_audio_filename_timestamp(filename)
        
        assert result is None
    
    def test_parse_no_extension(self):
        """Test parsing filename without .wav extension"""
        filename = "bark_recording_20250815_062511"
        result = parse_audio_filename_timestamp(filename)
        
        assert result is None
    
    def test_parse_different_extension(self):
        """Test parsing filename with different extension"""
        filename = "bark_recording_20250815_062511.mp3"
        result = parse_audio_filename_timestamp(filename)
        
        assert result is None


class TestGetAudioFileBarkOffset:
    """Test audio file bark offset calculation"""
    
    def test_calculate_offset_basic(self):
        """Test basic offset calculation"""
        audio_start_time = datetime(2025, 8, 15, 6, 25, 0)
        bark_time = datetime(2025, 8, 15, 6, 25, 15)
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "00:00:15.000"
    
    def test_calculate_offset_with_minutes(self):
        """Test offset calculation with minutes"""
        audio_start_time = datetime(2025, 8, 15, 6, 25, 0)
        bark_time = datetime(2025, 8, 15, 6, 27, 34)
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "00:02:34.000"
    
    def test_calculate_offset_with_microseconds(self):
        """Test offset calculation with microseconds"""
        audio_start_time = datetime(2025, 8, 15, 6, 25, 0, 0)
        bark_time = datetime(2025, 8, 15, 6, 25, 15, 267000)
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "00:00:15.267"
    
    def test_calculate_offset_hours(self):
        """Test offset calculation with hours"""
        audio_start_time = datetime(2025, 8, 15, 6, 0, 0)
        bark_time = datetime(2025, 8, 15, 7, 30, 45)
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "01:30:45.000"
    
    def test_calculate_offset_bark_before_audio(self):
        """Test offset when bark is before audio start"""
        audio_start_time = datetime(2025, 8, 15, 6, 25, 0)
        bark_time = datetime(2025, 8, 15, 6, 24, 30)  # 30 seconds before
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "00:00:00.000"
    
    def test_calculate_offset_same_time(self):
        """Test offset when bark and audio start at same time"""
        audio_start_time = datetime(2025, 8, 15, 6, 25, 0)
        bark_time = datetime(2025, 8, 15, 6, 25, 0)
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "00:00:00.000"
    
    def test_calculate_offset_precision(self):
        """Test offset calculation precision"""
        audio_start_time = datetime(2025, 8, 15, 6, 25, 0, 0)
        bark_time = datetime(2025, 8, 15, 6, 25, 5, 123456)  # 5.123456 seconds
        result = get_audio_file_bark_offset(audio_start_time, bark_time)
        
        assert result == "00:00:05.123"