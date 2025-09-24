"""Enhanced violation report generation with time-of-day formatting and detailed analysis"""

import os
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

from .time_utils import (
    parse_log_timestamp,
    datetime_to_time_of_day,
    calculate_duration_string,
    extract_bark_info_from_log,
    parse_audio_filename_timestamp,
    get_audio_file_bark_offset
)

# Import unified ViolationReport from legal models
from ..legal.models import ViolationReport as UnifiedViolationReport


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


class ReportViolation:
    """Lightweight wrapper for violation reporting that works with the unified models."""

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
    
    def get_audio_file_duration(self, audio_file_path: Path) -> Optional[float]:
        """Get actual duration of audio file in seconds"""
        if not SOUNDFILE_AVAILABLE:
            # Fallback to estimated duration if soundfile not available
            return 30 * 60  # 30 minutes default
        
        try:
            with sf.SoundFile(audio_file_path) as f:
                duration_seconds = len(f) / f.samplerate
                return duration_seconds
        except Exception as e:
            print(f"Warning: Could not read audio file {audio_file_path}: {e}")
            return 30 * 60  # Fallback to 30 minutes
    
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
        """Correlate bark events with their corresponding audio files using actual audio durations"""
        
        # Parse audio file timestamps and get actual durations
        audio_file_info = {}
        for audio_file in audio_files:
            timestamp = parse_audio_filename_timestamp(audio_file.name)
            if timestamp:
                duration_seconds = self.get_audio_file_duration(audio_file)
                if duration_seconds:
                    end_time = timestamp + timedelta(seconds=duration_seconds)
                    audio_file_info[timestamp] = {
                        'file': audio_file,
                        'end_time': end_time,
                        'duration_seconds': duration_seconds
                    }
        
        # Match bark events to audio files
        for bark_event in bark_events:
            # Find the audio file that contains this bark
            best_match = None
            best_offset = None
            closest_distance = None
            
            for audio_start_time, file_info in audio_file_info.items():
                audio_end_time = file_info['end_time']
                
                # Check if bark event falls within this audio file's timespan
                if audio_start_time <= bark_event.timestamp <= audio_end_time:
                    offset = get_audio_file_bark_offset(audio_start_time, bark_event.timestamp)
                    
                    # Validate that offset doesn't exceed actual file duration
                    offset_seconds = (bark_event.timestamp - audio_start_time).total_seconds()
                    if offset_seconds <= file_info['duration_seconds']:
                        # Use the audio file with the closest start time to bark event
                        distance = abs((bark_event.timestamp - audio_start_time).total_seconds())
                        if best_match is None or distance < closest_distance:
                            best_match = audio_start_time
                            best_offset = offset
                            closest_distance = distance
            
            if best_match and best_offset:
                bark_event.audio_file = audio_file_info[best_match]['file'].name
                bark_event.offset_in_file = best_offset
    
    def generate_violation_summary_report(self, target_date: date,
                                        violations: List[ReportViolation]) -> str:
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
                                         violation: ReportViolation,
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
    
    def create_violations_from_bark_events(self, bark_events: List[BarkEvent]) -> List[ReportViolation]:
        """Create violation reports from bark events using proper legal detection logic"""
        if not bark_events:
            return []
        
        # Import necessary models for session creation
        from ..core.models import BarkEvent as CoreBarkEvent, BarkingSession
        from ..legal.tracker import LegalViolationTracker
        
        # Convert report BarkEvent objects to core BarkEvent objects
        core_bark_events = []
        for event in bark_events:
            # Convert datetime timestamp to seconds since start of day for core models
            start_of_day = event.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            start_time_seconds = (event.timestamp - start_of_day).total_seconds()
            end_time_seconds = start_time_seconds + 1.0  # Assume 1 second duration for log events
            
            core_event = CoreBarkEvent(
                start_time=start_time_seconds,
                end_time=end_time_seconds,
                confidence=event.confidence,
                intensity=event.intensity
            )
            core_bark_events.append(core_event)
        
        if not core_bark_events:
            return []
        
        # Create sessions using 10-second gap threshold (standard for recording sessions)
        session_gap_threshold = 10.0
        sessions = self._events_to_sessions(core_bark_events, session_gap_threshold)
        
        # Use LegalViolationTracker for proper violation detection
        tracker = LegalViolationTracker(interactive=False)  # Non-interactive for report generation
        legal_violations = tracker.analyze_violations(sessions)
        
        # Convert legal violation reports to our report format
        report_violations = []
        start_of_day = bark_events[0].timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for legal_violation in legal_violations:
            # The legal violation has start_time/end_time as strings (HH:MM AM/PM format)
            # We need to parse them back to datetime objects
            try:
                # Parse the time strings - they can be in multiple formats
                violation_start_str = legal_violation.start_time
                violation_end_str = legal_violation.end_time
                violation_date_str = legal_violation.date
                
                # Try different timestamp formats
                timestamp_formats = [
                    "%Y-%m-%d %I:%M %p",      # "2025-08-15 6:25 AM"
                    "%Y-%m-%d %H:%M:%S",      # "2025-08-15 20:47:39" 
                    "%Y-%m-%d %H:%M",         # "2025-08-15 20:47"
                    "%I:%M %p",               # "6:25 AM" (time only)
                    "%H:%M:%S",               # "20:47:39" (time only)
                    "%H:%M"                   # "20:47" (time only)
                ]
                
                violation_start = None
                violation_end = None
                
                # Try parsing start time
                for fmt in timestamp_formats:
                    try:
                        if fmt.startswith("%Y"):
                            # Full datetime string - use violation_start_str directly if it contains date
                            if violation_start_str.count("-") >= 2:  # Contains date (YYYY-MM-DD)
                                violation_start = datetime.strptime(violation_start_str.strip(), fmt)
                            else:
                                # Combine with date
                                violation_start = datetime.strptime(f"{violation_date_str} {violation_start_str}".strip(), fmt)
                        else:
                            # Time only - combine with date
                            time_part = datetime.strptime(violation_start_str, fmt).time()
                            date_part = datetime.strptime(violation_date_str, "%Y-%m-%d").date()
                            violation_start = datetime.combine(date_part, time_part)
                        break
                    except ValueError:
                        continue
                
                # Try parsing end time
                for fmt in timestamp_formats:
                    try:
                        if fmt.startswith("%Y"):
                            # Full datetime string - use violation_end_str directly if it contains date
                            if violation_end_str.count("-") >= 2:  # Contains date (YYYY-MM-DD)
                                violation_end = datetime.strptime(violation_end_str.strip(), fmt)
                            else:
                                # Combine with date
                                violation_end = datetime.strptime(f"{violation_date_str} {violation_end_str}".strip(), fmt)
                        else:
                            # Time only - combine with date
                            time_part = datetime.strptime(violation_end_str, fmt).time()
                            date_part = datetime.strptime(violation_date_str, "%Y-%m-%d").date()
                            violation_end = datetime.combine(date_part, time_part)
                        break
                    except ValueError:
                        continue
                
                # Check if parsing succeeded
                if violation_start is None or violation_end is None:
                    raise ValueError(f"Could not parse timestamps: start='{violation_start_str}', end='{violation_end_str}'")
                
            except (ValueError, AttributeError) as e:
                # Fallback: if parsing fails, try to extract times from the violation data
                print(f"Warning: Could not parse violation times: {e}")
                # Skip this violation rather than crash
                continue
            
            # Create our report violation
            report_violation = ReportViolation(legal_violation.violation_type, violation_start, violation_end)
            
            # Add bark events that fall within this violation timespan
            for bark_event in bark_events:
                if violation_start <= bark_event.timestamp <= violation_end:
                    report_violation.add_bark_event(bark_event)
            
            report_violations.append(report_violation)
        
        return report_violations
    
    def _events_to_sessions(self, bark_events: List, gap_threshold: float) -> List:
        """Convert bark events to barking sessions using gap threshold (mirrored from LegalViolationTracker)"""
        from ..core.models import BarkingSession
        
        if not bark_events:
            return []
        
        sessions = []
        current_session_events = [bark_events[0]]
        
        for i in range(1, len(bark_events)):
            current_event = bark_events[i]
            last_event = current_session_events[-1]
            
            # Calculate gap between end of last event and start of current event
            gap = current_event.start_time - last_event.end_time
            
            if gap <= gap_threshold:
                # Within gap threshold - add to current session
                current_session_events.append(current_event)
            else:
                # Gap too large - finalize current session and start new one
                if current_session_events:
                    session = self._create_session_from_events(current_session_events)
                    sessions.append(session)
                
                current_session_events = [current_event]
        
        # Add final session
        if current_session_events:
            session = self._create_session_from_events(current_session_events)
            sessions.append(session)
        
        return sessions
    
    def _create_session_from_events(self, events: List) -> 'BarkingSession':
        """Create a BarkingSession from a list of BarkEvents (mirrored from LegalViolationTracker)"""
        from ..core.models import BarkingSession
        
        if not events:
            return None
        
        start_time = events[0].start_time
        end_time = events[-1].end_time
        total_duration = sum(event.end_time - event.start_time for event in events)
        total_barks = len(events)
        avg_confidence = sum(event.confidence for event in events) / len(events)
        peak_confidence = max(event.confidence for event in events)
        
        session_duration = end_time - start_time
        barks_per_second = total_barks / session_duration if session_duration > 0 else 0
        
        # Calculate average intensity
        avg_intensity = sum(getattr(event, 'intensity', 0.0) for event in events) / len(events)
        
        return BarkingSession(
            start_time=start_time,
            end_time=end_time,
            events=events,
            total_barks=total_barks,
            total_duration=total_duration,
            avg_confidence=avg_confidence,
            peak_confidence=peak_confidence,
            barks_per_second=barks_per_second,
            intensity=avg_intensity
        )