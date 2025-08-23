"""Time conversion utilities for log parsing and report generation"""

import re
from datetime import datetime, time
from typing import Optional, Tuple


def parse_log_timestamp(log_line: str) -> Optional[datetime]:
    """
    Extract timestamp from a log line.
    
    Args:
        log_line: Log line in format '2025-08-18 07:51:08,946 - INFO - message'
        
    Returns:
        datetime object or None if parsing fails
    """
    # Match timestamp format: YYYY-MM-DD HH:MM:SS,mmm
    timestamp_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})'
    match = re.match(timestamp_pattern, log_line)
    
    if match:
        try:
            # Parse main timestamp
            main_timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
            # Add milliseconds (convert to microseconds)
            microseconds = int(match.group(2)) * 1000  # Convert milliseconds to microseconds
            return main_timestamp.replace(microsecond=microseconds)
        except ValueError:
            return None
    
    return None


def datetime_to_time_of_day(dt: datetime) -> str:
    """
    Convert datetime to time-of-day string (HH:MM:SS format).
    
    Args:
        dt: datetime object
        
    Returns:
        Time string in HH:MM:SS format
    """
    return dt.strftime('%H:%M:%S')


def calculate_duration_string(start_time: datetime, end_time: datetime) -> str:
    """
    Calculate duration between two datetimes and format as human-readable string.
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        
    Returns:
        Duration string like "22 mins 10 seconds"
    """
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    if not parts:
        return "0 seconds"
    
    return " ".join(parts)


def extract_bark_info_from_log(log_line: str) -> Optional[Tuple[datetime, float, float, str]]:
    """
    Extract bark detection information from a log line.
    
    Args:
        log_line: Log line containing bark detection info
        
    Returns:
        Tuple of (timestamp, confidence, intensity, audio_filename) or None
    """
    # Parse timestamp first
    timestamp = parse_log_timestamp(log_line)
    if not timestamp:
        return None
    
    # Extract bark detection details
    # Example: "🐕 BARK DETECTED! Confidence: 0.824, Intensity: 0.375, Duration: 0.96s"
    bark_pattern = r'🐕 BARK DETECTED! Confidence: ([\d.]+), Intensity: ([\d.]+)'
    match = re.search(bark_pattern, log_line)
    
    if match:
        confidence = float(match.group(1))
        intensity = float(match.group(2))
        
        # For now, we'll need to correlate with audio files separately
        # This returns the detection info that can be matched to audio files
        return timestamp, confidence, intensity, ""
    
    return None


def parse_audio_filename_timestamp(filename: str) -> Optional[datetime]:
    """
    Extract recording start timestamp from audio filename.
    
    Args:
        filename: Audio filename like 'bark_recording_20250815_062511.wav'
                 The timestamp represents when recording STARTED, not when it ended.
        
    Returns:
        datetime object representing recording start time, or None if parsing fails
    """
    # Pattern: bark_recording_YYYYMMDD_HHMMSS.wav
    pattern = r'bark_recording_(\d{8})_(\d{6})\.wav'
    match = re.search(pattern, filename)
    
    if match:
        try:
            date_str = match.group(1)  # YYYYMMDD
            time_str = match.group(2)  # HHMMSS
            
            # Parse date
            date_part = datetime.strptime(date_str, '%Y%m%d').date()
            
            # Parse time
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            time_part = time(hour, minute, second)
            
            return datetime.combine(date_part, time_part)
        except ValueError:
            return None
    
    return None


def get_audio_file_bark_offset(audio_start_time: datetime, bark_time: datetime) -> str:
    """
    Calculate offset of bark within audio file.
    
    Args:
        audio_start_time: When audio recording started
        bark_time: When bark was detected
        
    Returns:
        Offset string like "00:02:34.123"
    """
    if bark_time < audio_start_time:
        return "00:00:00.000"  # Bark before recording started
    
    offset = bark_time - audio_start_time
    total_seconds = offset.total_seconds()
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"