"""Enhanced violation report generation with time-of-day formatting and detailed analysis"""

import os
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

from .time_utils import (
    parse_log_timestamp, 
    datetime_to_time_of_day, 
    calculate_duration_string,
    extract_bark_info_from_log,
    parse_audio_filename_timestamp,
    get_audio_file_bark_offset
)


class BarkEvent:
    """Represents a single bark detection event"""
    
    def __init__(self, timestamp: datetime, confidence: float, intensity: float, 
                 audio_file: str = "", offset_in_file: str = ""):
        self.timestamp = timestamp
        self.confidence = confidence
        self.intensity = intensity
        self.audio_file = audio_file
        self.offset_in_file = offset_in_file
    
    def time_of_day(self) -> str:
        """Get time of day as HH:MM:SS"""
        return datetime_to_time_of_day(self.timestamp)


class ViolationReport:
    """Represents a violation with detailed bark events"""
    
    def __init__(self, violation_type: str, start_time: datetime, end_time: datetime):
        self.violation_type = violation_type
        self.start_time = start_time
        self.end_time = end_time
        self.bark_events: List[BarkEvent] = []
        self.audio_files: List[str] = []
    
    def add_bark_event(self, bark_event: BarkEvent):
        """Add a bark event to this violation"""
        self.bark_events.append(bark_event)
        if bark_event.audio_file and bark_event.audio_file not in self.audio_files:
            self.audio_files.append(bark_event.audio_file)
    
    def start_time_of_day(self) -> str:
        """Get start time as HH:MM:SS"""
        return datetime_to_time_of_day(self.start_time)
    
    def end_time_of_day(self) -> str:
        """Get end time as HH:MM:SS"""
        return datetime_to_time_of_day(self.end_time)
    
    def duration_string(self) -> str:
        """Get duration as human-readable string"""
        return calculate_duration_string(self.start_time, self.end_time)
    
    def total_barks(self) -> int:
        """Get total number of bark events"""
        return len(self.bark_events)


class LogBasedReportGenerator:
    """Generates enhanced violation reports by parsing log files"""
    
    def __init__(self, logs_directory: str = "logs", recordings_directory: str = "recordings"):
        self.logs_directory = Path(logs_directory)
        self.recordings_directory = Path(recordings_directory)
    
    def find_log_file_for_date(self, target_date: date) -> Optional[Path]:
        """Find log file for a specific date"""
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Check date-based folder structure first
        date_folder = self.logs_directory / date_str
        if date_folder.exists():
            log_files = list(date_folder.glob(f"bark_detector-{date_str}.log"))
            if log_files:
                return log_files[0]
        
        # Fallback to legacy single log file
        legacy_log = Path("bark_detector.log")
        if legacy_log.exists():
            return legacy_log
        
        return None
    
    def parse_log_for_barks(self, log_file: Path, target_date: date) -> List[BarkEvent]:
        """Parse log file and extract bark events for a specific date"""
        bark_events = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Extract bark detection info
                    bark_info = extract_bark_info_from_log(line)
                    if bark_info:
                        timestamp, confidence, intensity, _ = bark_info
                        
                        # Filter by target date
                        if timestamp.date() == target_date:
                            bark_event = BarkEvent(timestamp, confidence, intensity)
                            bark_events.append(bark_event)
        
        except Exception as e:
            print(f"Error parsing log file {log_file}: {e}")
        
        return bark_events
    
    def find_audio_files_for_date(self, target_date: date) -> List[Path]:
        """Find audio files for a specific date"""
        audio_files = []
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Check date-based recordings folder first
        date_folder = self.recordings_directory / date_str
        if date_folder.exists():
            audio_files.extend(date_folder.glob("*.wav"))
        
        # Also check flat structure for legacy recordings
        for audio_file in self.recordings_directory.glob("*.wav"):
            file_timestamp = parse_audio_filename_timestamp(audio_file.name)
            if file_timestamp and file_timestamp.date() == target_date:
                audio_files.append(audio_file)
        
        return sorted(audio_files)
    
    def correlate_barks_with_audio_files(self, bark_events: List[BarkEvent], 
                                       audio_files: List[Path]) -> None:
        """Correlate bark events with their corresponding audio files"""
        
        # Parse audio file timestamps
        audio_timestamps = {}
        for audio_file in audio_files:
            timestamp = parse_audio_filename_timestamp(audio_file.name)
            if timestamp:
                audio_timestamps[timestamp] = audio_file
        
        # Match bark events to audio files
        for bark_event in bark_events:
            # Find the audio file that contains this bark
            best_match = None
            best_offset = None
            
            for audio_start_time, audio_file in audio_timestamps.items():
                # Assume recordings are up to 30 minutes long (configurable)
                # This could be improved by reading actual audio file duration
                estimated_end_time = audio_start_time + timedelta(minutes=30)
                
                if audio_start_time <= bark_event.timestamp <= estimated_end_time:
                    offset = get_audio_file_bark_offset(audio_start_time, bark_event.timestamp)
                    if best_match is None or bark_event.timestamp > best_match:
                        best_match = audio_start_time
                        best_offset = offset
            
            if best_match and best_offset:
                bark_event.audio_file = audio_timestamps[best_match].name
                bark_event.offset_in_file = best_offset
    
    def generate_violation_summary_report(self, target_date: date, 
                                        violations: List[ViolationReport]) -> str:
        """Generate the violation summary report as specified in improvements.md"""
        
        report_lines = []
        report_lines.append("Barking Violation Report Summary")
        report_lines.append(f"Date: {target_date.strftime('%Y-%m-%d')}")
        report_lines.append("")
        
        # Summary section
        report_lines.append("SUMMARY:")
        report_lines.append(f"Total Violations: {len(violations)}")
        
        constant_count = sum(1 for v in violations if v.violation_type == "Constant")
        intermittent_count = sum(1 for v in violations if v.violation_type == "Intermittent")
        
        report_lines.append(f"Constant Violations: {constant_count}")
        report_lines.append(f"Intermittent Violations: {intermittent_count}")
        report_lines.append("")
        
        # Individual violations
        for i, violation in enumerate(violations, 1):
            report_lines.append(f"Violation {i} ({violation.violation_type}):")
            report_lines.append(f"Start time: {violation.start_time_of_day()}  End Time {violation.end_time_of_day()}")
            report_lines.append(f"Duration: {violation.duration_string()}")
            report_lines.append(f"Total Barks: {violation.total_barks()}")
            
            if violation.audio_files:
                report_lines.append("Supporting audio files:")
                for audio_file in violation.audio_files:
                    report_lines.append(f"- {audio_file}")
            
            report_lines.append("")
        
        # Generated timestamp
        generated_time = datetime.now().strftime('%Y-%m-%d at %H:%M:%S')
        report_lines.append(f"Generated: {generated_time}")
        
        return "\n".join(report_lines)
    
    def generate_detailed_violation_report(self, target_date: date, 
                                         violation: ViolationReport, 
                                         violation_number: int) -> str:
        """Generate detailed violation report for a specific violation"""
        
        report_lines = []
        report_lines.append(f"Barking Detail Report for {target_date.strftime('%Y-%m-%d')}, Violation {violation_number}")
        report_lines.append("")
        
        report_lines.append(f"Violation Type: {violation.violation_type}")
        report_lines.append(f"Start time: {violation.start_time_of_day()} End Time {violation.end_time_of_day()}")
        report_lines.append(f"Duration: {violation.duration_string()}")
        report_lines.append(f"Total Barks: {violation.total_barks()}")
        report_lines.append("")
        
        # Visual graph placeholder
        report_lines.append("<Visual Graph of Barking Session>")
        report_lines.append(f"<X-axis is time with X=0 being the start time of the violation (in this case {violation.start_time_of_day()})>")
        report_lines.append(f"<The x-axis should stretch slightly past the end time of the violation (in this case {violation.end_time_of_day()})>")
        report_lines.append("<The x-axis should be scaled to fit the width of a letter sized pdf.>")
        report_lines.append("")
        
        # Group bark events by audio file
        barks_by_file = defaultdict(list)
        for bark_event in violation.bark_events:
            if bark_event.audio_file:
                barks_by_file[bark_event.audio_file].append(bark_event)
        
        if barks_by_file:
            report_lines.append("Supporting Audio Files:")
            report_lines.append("")
            
            for audio_file, bark_events in barks_by_file.items():
                report_lines.append(f"# {audio_file}")
                for bark_event in bark_events:
                    time_str = bark_event.time_of_day()
                    offset_str = bark_event.offset_in_file
                    report_lines.append(f"- {target_date.strftime('%Y-%m-%d')} {time_str} BARK ({offset_str})")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_reports_for_date(self, target_date: date) -> Dict[str, str]:
        """Generate all reports for a specific date by analyzing logs"""
        
        # Find and parse log file
        log_file = self.find_log_file_for_date(target_date)
        if not log_file:
            return {"error": f"No log file found for date {target_date}"}
        
        # Extract bark events from logs
        bark_events = self.parse_log_for_barks(log_file, target_date)
        if not bark_events:
            return {"error": f"No bark events found in logs for date {target_date}"}
        
        # Find audio files for correlation
        audio_files = self.find_audio_files_for_date(target_date)
        
        # Correlate bark events with audio files
        self.correlate_barks_with_audio_files(bark_events, audio_files)
        
        # Create violations based on bark events
        # This is a simplified version - in practice, you'd use the same logic
        # as the existing violation detection system
        violations = self.create_violations_from_bark_events(bark_events)
        
        # Generate reports
        reports = {}
        
        if violations:
            # Summary report
            reports["summary"] = self.generate_violation_summary_report(target_date, violations)
            
            # Detailed reports for each violation
            for i, violation in enumerate(violations, 1):
                reports[f"violation_{i}_detail"] = self.generate_detailed_violation_report(
                    target_date, violation, i
                )
        else:
            reports["summary"] = f"No violations detected for {target_date.strftime('%Y-%m-%d')}"
        
        return reports
    
    def create_violations_from_bark_events(self, bark_events: List[BarkEvent]) -> List[ViolationReport]:
        """Create violation reports from bark events (simplified version)"""
        # This is a placeholder implementation
        # In practice, you'd implement the full violation detection logic here
        # For now, just create a simple violation if there are enough bark events
        
        if len(bark_events) < 5:  # Need at least 5 barks for a violation
            return []
        
        # Create a simple intermittent violation spanning all bark events
        start_time = min(event.timestamp for event in bark_events)
        end_time = max(event.timestamp for event in bark_events)
        
        # Determine violation type based on duration and bark density
        duration_minutes = (end_time - start_time).total_seconds() / 60
        
        if duration_minutes >= 15:
            violation_type = "Intermittent"
        elif duration_minutes >= 5:
            violation_type = "Constant"
        else:
            return []  # Not enough duration for a violation
        
        violation = ViolationReport(violation_type, start_time, end_time)
        for bark_event in bark_events:
            violation.add_bark_event(bark_event)
        
        return [violation]