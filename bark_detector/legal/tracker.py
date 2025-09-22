"""Legal violation tracker for bylaw compliance"""

import logging
import uuid
import librosa
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from .models import ViolationReport, LegalSporadicSession, PersistedBarkEvent, Violation
from .database import ViolationDatabase
from ..core.models import BarkingSession
from ..utils.time_utils import parse_audio_filename_timestamp

logger = logging.getLogger(__name__)


class LegalViolationTracker:
    """Track and analyze bark events for legal violation detection."""
    
    def __init__(self, violation_db: Optional[ViolationDatabase] = None, violations_dir: Path = None, interactive: bool = True):
        """Initialize the legal violation tracker.
        
        Args:
            violation_db: ViolationDatabase instance for persistence (overrides violations_dir)
            violations_dir: Directory for date-organized violations (defaults to 'violations/')
            interactive: Whether to prompt user for duplicate handling (False for testing)
        """
        self.violations = []
        self.sessions = []
        
        if violation_db is not None:
            self.violation_db = violation_db
        else:
            # Create new ViolationDatabase with project-local violations directory
            self.violation_db = ViolationDatabase(violations_dir=violations_dir)
        
        self.interactive = interactive
    
    def analyze_violations(self, sessions: List[BarkingSession]) -> List[ViolationReport]:
        """Analyze barking sessions for legal violations."""
        violations = []
        
        # Check for continuous violations (5+ minutes per session)
        for session in sessions:
            if session.total_duration >= 300:  # 5 minutes
                violations.append(self._create_violation_report(session, "Constant"))
        
        # Check for sporadic violations (15+ minutes across multiple sessions within 5-minute gaps)
        sporadic_violations = self._detect_sporadic_violations(sessions)
        violations.extend(sporadic_violations)
        
        return violations

    def _group_events_by_gaps(self, events: List, gap_threshold: float) -> List[List]:
        """Group bark events by gap threshold for violation analysis.

        Args:
            events: List of bark events with start_time and end_time attributes
            gap_threshold: Maximum gap in seconds between events in same group

        Returns:
            List of event groups (each group is a list of events)
        """
        if not events:
            return []

        # Sort events by start time to ensure proper grouping
        sorted_events = sorted(events, key=lambda e: e.start_time)

        groups = []
        current_group = [sorted_events[0]]

        for i in range(1, len(sorted_events)):
            current_event = sorted_events[i]
            last_event = current_group[-1]

            # Check gap between events
            gap = current_event.start_time - last_event.end_time

            if gap <= gap_threshold:
                # Continue current group
                current_group.append(current_event)
            else:
                # End current group and start new one
                groups.append(current_group)
                current_group = [current_event]

        # Add final group
        if current_group:
            groups.append(current_group)

        return groups

    def _analyze_continuous_violations_from_events(self, events: List, gap_threshold: float = 60.0) -> List[ViolationReport]:
        """Analyze bark events directly for continuous (constant) violations.

        Args:
            events: List of bark events with start_time, end_time, confidence attributes
            gap_threshold: Maximum gap in seconds to consider events as continuous (default: 60s)

        Returns:
            List of ViolationReport objects for detected continuous violations
        """
        violations = []

        # Group events by gap threshold
        event_groups = self._group_events_by_gaps(events, gap_threshold)

        for group in event_groups:
            if not group:
                continue

            # Calculate total bark duration within this group
            total_bark_duration = sum(event.end_time - event.start_time for event in group)

            # Check if this group meets continuous violation criteria (5+ minutes)
            if total_bark_duration >= 300:  # 5 minutes in seconds
                # Create violation report for this continuous violation
                start_time = group[0].start_time
                end_time = group[-1].end_time

                # Calculate statistics
                confidences = [event.confidence for event in group]
                avg_confidence = sum(confidences) / len(confidences)
                peak_confidence = max(confidences)

                # Convert absolute timestamps back to relative for display
                # For now, use simplified relative timestamps for display
                # TODO: Improve to show actual time of day
                duration = end_time - start_time
                start_time_str = "00:00:00"  # Simplified for now
                end_time_str = str(timedelta(seconds=int(duration)))

                violation = ViolationReport(
                    date=datetime.now().strftime('%Y-%m-%d'),  # Will be updated by caller
                    start_time=start_time_str,
                    end_time=end_time_str,
                    violation_type="Constant",
                    total_bark_duration=total_bark_duration,
                    total_incident_duration=end_time - start_time,
                    audio_files=[],  # Will be populated by caller
                    audio_file_start_times=[start_time_str],
                    audio_file_end_times=[end_time_str],
                    confidence_scores=confidences,
                    peak_confidence=peak_confidence,
                    avg_confidence=avg_confidence,
                    created_timestamp=datetime.now().isoformat()
                )
                violations.append(violation)

        return violations

    def _analyze_sporadic_violations_from_events(self, events: List, sporadic_gap_threshold: float = 300.0) -> List[ViolationReport]:
        """Analyze bark events directly for sporadic (intermittent) violations.

        Args:
            events: List of bark events with start_time, end_time, confidence attributes
            sporadic_gap_threshold: Maximum gap in seconds for sporadic grouping (default: 5 minutes)

        Returns:
            List of ViolationReport objects for detected sporadic violations
        """
        violations = []

        # Group events by sporadic gap threshold (5 minutes)
        sporadic_groups = self._group_events_by_gaps(events, sporadic_gap_threshold)

        for group in sporadic_groups:
            if not group:
                continue

            # Calculate total bark duration within this sporadic group
            total_bark_duration = sum(event.end_time - event.start_time for event in group)

            # Check if this group meets sporadic violation criteria (15+ minutes total)
            if total_bark_duration >= 900:  # 15 minutes in seconds
                # Create violation report for this sporadic violation
                start_time = group[0].start_time
                end_time = group[-1].end_time

                # Calculate statistics
                confidences = [event.confidence for event in group]
                avg_confidence = sum(confidences) / len(confidences)
                peak_confidence = max(confidences)

                # Convert absolute timestamps back to relative for display
                # For now, use simplified relative timestamps for display
                # TODO: Improve to show actual time of day
                duration = end_time - start_time
                start_time_str = "00:00:00"  # Simplified for now
                end_time_str = str(timedelta(seconds=int(duration)))

                violation = ViolationReport(
                    date=datetime.now().strftime('%Y-%m-%d'),  # Will be updated by caller
                    start_time=start_time_str,
                    end_time=end_time_str,
                    violation_type="Intermittent",
                    total_bark_duration=total_bark_duration,
                    total_incident_duration=end_time - start_time,
                    audio_files=[],  # Will be populated by caller
                    audio_file_start_times=[start_time_str],
                    audio_file_end_times=[end_time_str],
                    confidence_scores=confidences,
                    peak_confidence=peak_confidence,
                    avg_confidence=avg_confidence,
                    created_timestamp=datetime.now().isoformat()
                )
                violations.append(violation)

        return violations

    def _convert_to_absolute_timestamps(self, persisted_events: List[PersistedBarkEvent]) -> List:
        """Convert PersistedBarkEvent objects to simple events with absolute timestamps.

        Args:
            persisted_events: List of PersistedBarkEvent objects with relative timestamps

        Returns:
            List of simple event objects with absolute timestamps for violation analysis
        """
        absolute_events = []

        for event in persisted_events:
            try:
                # Parse recording start time from audio filename
                recording_start = parse_audio_filename_timestamp(event.audio_file_name)
                if not recording_start:
                    logger.warning(f"Could not parse recording start time from {event.audio_file_name}")
                    continue

                # Convert recording start to seconds since epoch
                recording_start_seconds = recording_start.timestamp()

                # Parse the audiofile timestamp (HH:MM:SS.mmm) to seconds
                audiofile_timestamp_parts = event.bark_audiofile_timestamp.split(':')
                if len(audiofile_timestamp_parts) >= 3:
                    hours = int(audiofile_timestamp_parts[0])
                    minutes = int(audiofile_timestamp_parts[1])
                    seconds_and_ms = audiofile_timestamp_parts[2].split('.')
                    seconds = int(seconds_and_ms[0])
                    milliseconds = int(seconds_and_ms[1]) if len(seconds_and_ms) > 1 else 0

                    # Convert to total seconds offset within the audio file
                    audiofile_offset = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

                    # Calculate absolute timestamp
                    absolute_start = recording_start_seconds + audiofile_offset
                    absolute_end = absolute_start + 0.5  # Assume 0.5 second bark duration (simple estimation)

                    # Create simple event object for analysis
                    simple_event = type('BarkEvent', (), {
                        'start_time': absolute_start,
                        'end_time': absolute_end,
                        'confidence': event.confidence
                    })()

                    absolute_events.append(simple_event)

                else:
                    logger.warning(f"Invalid audiofile timestamp format: {event.bark_audiofile_timestamp}")

            except Exception as e:
                logger.warning(f"Error converting event to absolute timestamp: {e}")

        return absolute_events

    def analyze_recordings_for_date(self, recordings_dir: Path, target_date: str, detector) -> List[ViolationReport]:
        """
        Analyze recordings for a specific date and detect bylaw violations using advanced bark detection.
        
        Args:
            recordings_dir: Path to recordings directory
            target_date: Date string in YYYY-MM-DD format
            detector: AdvancedBarkDetector instance to use for ML analysis
            
        Returns:
            List of detected violations for that date
        """
        logger.info(f"🔍 Analyzing recordings for violations on {target_date}")
        
        # Look for recordings in both flat structure and date folders
        date_recordings = []
        
        # Check date-based folder first
        date_folder = recordings_dir / target_date
        if date_folder.exists():
            date_recordings.extend(list(date_folder.glob("*.wav")))
        
        # Check flat structure for files with date in name
        date_pattern = target_date.replace('-', '')  # YYYYMMDD format
        flat_recordings = list(recordings_dir.glob(f"*{date_pattern}*.wav"))
        date_recordings.extend(flat_recordings)
        
        if not date_recordings:
            logger.info(f"No recordings found for {target_date}")
            return []
        
        logger.info(f"Found {len(date_recordings)} recording files for {target_date}")

        # Sort recordings chronologically by filename timestamp (FR1 compliance)
        def get_recording_timestamp(recording_path):
            """Extract timestamp from recording filename for sorting."""
            timestamp = parse_audio_filename_timestamp(recording_path.name)
            if timestamp:
                return timestamp
            else:
                # For files with unparseable timestamps, put them at the end
                # This ensures they don't interfere with chronological ordering
                logger.warning(f"Could not parse timestamp from {recording_path.name}, will process last")
                return datetime.max  # Far future date to sort them last

        # Sort recordings in chronological order to ensure events are in order (FR1)
        date_recordings.sort(key=get_recording_timestamp)
        logger.info(f"Processing recordings in chronological order to comply with FR1")

        # Analyze each recording using advanced bark detection
        all_sessions = []
        all_bark_events = []  # Collect all PersistedBarkEvent objects
        all_original_events = []  # Keep original events with absolute timestamps
        total_analyzed_duration = 0
        
        for recording_file in date_recordings:
            logger.info(f"Analyzing recording: {recording_file.name}")
            try:
                # Parse recording start time from filename for absolute timestamps
                recording_start = parse_audio_filename_timestamp(recording_file.name)
                if not recording_start:
                    logger.warning(f"Could not parse recording start time from {recording_file.name}")
                    # Use current time as fallback for test compatibility
                    recording_start = datetime.now()

                recording_start_seconds = recording_start.timestamp()

                # Load and analyze audio with YAMNet
                audio_data, sr = librosa.load(str(recording_file), sr=detector.sample_rate)

                if len(audio_data) == 0:
                    logger.warning(f"Empty audio file: {recording_file}")
                    continue

                total_analyzed_duration += len(audio_data) / sr

                # Use detector's analysis sensitivity for comprehensive violation detection
                bark_events = detector._detect_barks_in_buffer_with_sensitivity(audio_data, detector.analysis_sensitivity)

                if not bark_events:
                    logger.debug(f"No bark events detected in {recording_file.name}")
                    continue

                # Convert bark events to PersistedBarkEvent objects
                file_persisted_events = self._convert_to_persisted_events(
                    bark_events, recording_file.name, target_date
                )
                all_bark_events.extend(file_persisted_events)

                # Create events with absolute timestamps for direct violation analysis
                for event in bark_events:
                    absolute_event = type('BarkEvent', (), {
                        'start_time': recording_start_seconds + event.start_time,
                        'end_time': recording_start_seconds + event.end_time,
                        'confidence': event.confidence
                    })()
                    all_original_events.append(absolute_event)

                # Convert events to sessions using gap threshold (preserve for recording management)
                sessions = self._events_to_sessions(bark_events, detector.session_gap_threshold)

                # Add metadata to sessions
                for session in sessions:
                    session.source_file = recording_file
                    session.date = target_date

                all_sessions.extend(sessions)
                logger.info(f"Found {len(bark_events)} bark events in {len(sessions)} sessions from {recording_file.name}")

            except Exception as e:
                logger.warning(f"Could not analyze {recording_file}: {e}")

        logger.info(f"Total sessions for {target_date}: {len(all_sessions)}")

        if not all_bark_events:
            logger.info(f"No bark events detected in recordings for {target_date}")
            return []

        # Save all detected bark events to database
        if all_bark_events:
            logger.info(f"💾 Saving {len(all_bark_events)} bark events to database")
            self.violation_db.save_events(all_bark_events, target_date)

        # Detect violations using DIRECT EVENT ANALYSIS (hybrid approach)
        # Use original events with absolute timestamps instead of converting from PersistedBarkEvent
        continuous_violations = self._analyze_continuous_violations_from_events(all_original_events)
        sporadic_violations = self._analyze_sporadic_violations_from_events(all_original_events)

        # Combine all violations
        violation_reports = continuous_violations + sporadic_violations

        # Add date context and audio file references to violation reports
        for violation in violation_reports:
            violation.date = target_date
            # Populate audio files list with all processed files
            violation.audio_files = [str(f) for f in date_recordings]

        # Convert ViolationReport objects to Violation objects for new persistence
        violations = self._convert_to_violation_objects(violation_reports, all_bark_events, target_date)
        
        logger.info(f"Detected {len(violation_reports)} violations for {target_date}")
        for i, violation in enumerate(violation_reports, 1):
            logger.info(f"  {violation.violation_type} violation: {violation.start_time} - {violation.end_time} ({violation.total_bark_duration/60:.1f}min barking)")
        
        # Save violations to database using new persistence layer
        if violations:
            logger.info(f"💾 Saving {len(violations)} violations to database")
            self.violation_db.save_violations_new(violations, target_date)

        return violation_reports
        
    def _events_to_sessions(self, bark_events: List, gap_threshold: float) -> List[BarkingSession]:
        """Convert bark events to barking sessions using gap threshold."""
        if not bark_events:
            return []
        
        sessions = []
        current_session_events = [bark_events[0]]
        
        for i in range(1, len(bark_events)):
            current_event = bark_events[i]
            last_event = current_session_events[-1]
            
            # Check gap between events
            gap = current_event.start_time - last_event.end_time
            
            if gap <= gap_threshold:
                # Continue current session
                current_session_events.append(current_event)
            else:
                # End current session and start new one
                if current_session_events:
                    session = self._create_session_from_events(current_session_events)
                    sessions.append(session)
                
                current_session_events = [current_event]
        
        # Add final session
        if current_session_events:
            session = self._create_session_from_events(current_session_events)
            sessions.append(session)
        
        return sessions
    
    def _create_session_from_events(self, events: List) -> BarkingSession:
        """Create a BarkingSession from a list of BarkEvents."""
        if not events:
            return None
        
        start_time = events[0].start_time
        end_time = events[-1].end_time
        total_barks = len(events)
        session_duration = end_time - start_time
        
        # Calculate total bark duration (sum of individual event durations)
        total_bark_duration = sum(event.end_time - event.start_time for event in events)
        
        # Calculate average confidence
        avg_confidence = sum(event.confidence for event in events) / len(events)
        
        # Calculate barks per second
        barks_per_second = total_barks / session_duration if session_duration > 0 else 0
        
        # Calculate intensity (average of event intensities if available, otherwise use confidence)
        if hasattr(events[0], 'intensity') and events[0].intensity is not None:
            intensity = sum(getattr(event, 'intensity', 0) for event in events) / len(events)
        else:
            intensity = avg_confidence  # Use confidence as proxy for intensity
        
        return BarkingSession(
            start_time=start_time,
            end_time=end_time,
            events=events,
            total_barks=total_barks,
            total_duration=total_bark_duration,
            avg_confidence=avg_confidence,
            peak_confidence=max(event.confidence for event in events),
            barks_per_second=barks_per_second,
            intensity=intensity
        )
    
    def _create_violation_report(self, session: BarkingSession, violation_type: str) -> ViolationReport:
        """Create a violation report from a barking session with accurate timing data."""
        from datetime import datetime, timedelta
        
        # Convert session times to readable format
        start_time = str(timedelta(seconds=int(session.start_time)))
        end_time = str(timedelta(seconds=int(session.end_time)))
        
        # Use session date if available, otherwise current date
        report_date = getattr(session, 'date', datetime.now().strftime('%Y-%m-%d'))
        
        # Calculate session duration (end - start, not just bark duration)
        session_duration = session.end_time - session.start_time
        
        # Get confidence scores from individual events
        confidence_scores = [event.confidence for event in session.events] if session.events else [session.avg_confidence]
        
        return ViolationReport(
            date=report_date,
            start_time=start_time,
            end_time=end_time,
            violation_type=violation_type,
            total_bark_duration=session.total_duration,  # Actual bark time
            total_incident_duration=session_duration,    # Total session time
            audio_files=[str(session.source_file)] if getattr(session, 'source_file', None) else [],
            audio_file_start_times=[start_time],
            audio_file_end_times=[end_time],
            confidence_scores=confidence_scores,
            peak_confidence=session.peak_confidence,
            avg_confidence=session.avg_confidence,
            created_timestamp=datetime.now().isoformat()
        )
    
    def _detect_sporadic_violations(self, sessions: List[BarkingSession]) -> List[ViolationReport]:
        """Detect sporadic violations (15+ minutes total barking across sessions with ≤5 minute gaps)."""
        if not sessions:
            return []
        
        # Sort sessions by start time
        sorted_sessions = sorted(sessions, key=lambda s: s.start_time)
        
        # Group sessions into Legal Sporadic Sessions using 5-minute gap threshold
        sporadic_sessions = self._group_sessions_for_sporadic_analysis(sorted_sessions)
        
        violations = []
        for sporadic_group in sporadic_sessions:
            # Calculate total bark duration across all sessions in group
            total_bark_duration = sum(session.total_duration for session in sporadic_group)
            
            # Check if meets 15-minute threshold
            if total_bark_duration >= 900:  # 15 minutes
                # Create combined violation report
                violation = self._create_sporadic_violation_report(sporadic_group)
                violations.append(violation)
        
        return violations
    
    def _group_sessions_for_sporadic_analysis(self, sorted_sessions: List[BarkingSession]) -> List[List[BarkingSession]]:
        """Group sessions for sporadic violation analysis using 5-minute gap threshold."""
        if not sorted_sessions:
            return []
        
        groups = []
        current_group = [sorted_sessions[0]]
        
        for i in range(1, len(sorted_sessions)):
            current_session = sorted_sessions[i]
            last_session = current_group[-1]
            
            # Calculate gap between end of last session and start of current session
            gap = current_session.start_time - last_session.end_time
            
            if gap <= 300:  # 5 minutes or less - continue current sporadic group
                current_group.append(current_session)
            else:
                # Gap is too large - end current group and start new one
                if len(current_group) > 0:
                    groups.append(current_group)
                current_group = [current_session]
        
        # Add final group
        if len(current_group) > 0:
            groups.append(current_group)
        
        return groups
    
    def _create_sporadic_violation_report(self, sessions: List[BarkingSession]) -> ViolationReport:
        """Create a violation report for sporadic violations (multiple sessions)."""
        from datetime import datetime, timedelta
        
        if not sessions:
            return None
        
        # Calculate overall time span
        start_time = min(session.start_time for session in sessions)
        end_time = max(session.end_time for session in sessions)
        
        # Calculate total bark duration across all sessions
        total_bark_duration = sum(session.total_duration for session in sessions)
        
        # Calculate average confidence across all events
        all_confidences = []
        peak_confidence = 0.0
        total_audio_files = []
        
        for session in sessions:
            all_confidences.append(session.avg_confidence)
            peak_confidence = max(peak_confidence, session.peak_confidence)
            
            # Collect audio files if available
            if hasattr(session, 'source_file') and session.source_file:
                total_audio_files.append(str(session.source_file))
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # Convert times to readable format
        start_time_str = str(timedelta(seconds=int(start_time)))
        end_time_str = str(timedelta(seconds=int(end_time)))
        
        # Get date from first session if available
        report_date = getattr(sessions[0], 'date', datetime.now().strftime('%Y-%m-%d'))
        
        return ViolationReport(
            date=report_date,
            start_time=start_time_str,
            end_time=end_time_str,
            violation_type="Intermittent",
            total_bark_duration=total_bark_duration,
            total_incident_duration=end_time - start_time,
            audio_files=total_audio_files,
            audio_file_start_times=[start_time_str],
            audio_file_end_times=[end_time_str],
            confidence_scores=all_confidences,
            peak_confidence=peak_confidence,
            avg_confidence=avg_confidence,
            created_timestamp=datetime.now().isoformat()
        )
    
    def track_session(self, session: BarkingSession):
        """Track a barking session for violation analysis."""
        self.sessions.append(session)
        logger.debug(f"Tracked session: {len(session.events)} bark events")

    def _convert_to_persisted_events(self, bark_events: List, audio_file_name: str, target_date: str) -> List[PersistedBarkEvent]:
        """Convert bark events to PersistedBarkEvent objects for database persistence.

        Args:
            bark_events: List of bark event objects from detector
            audio_file_name: Name of the audio file containing these events
            target_date: Date in YYYY-MM-DD format

        Returns:
            List of PersistedBarkEvent objects
        """
        persisted_events = []

        for event in bark_events:
            # Generate unique bark ID
            bark_id = str(uuid.uuid4())

            # Extract bark type from event with enhanced detection
            bark_type = "Bark"  # Default value

            # Try to get bark type from different possible attributes
            if hasattr(event, 'triggering_classes') and event.triggering_classes:
                # Use the first (highest confidence) triggering class
                bark_type = event.triggering_classes[0]
            elif hasattr(event, 'class_name'):
                bark_type = event.class_name
            elif hasattr(event, 'bark_type'):
                bark_type = event.bark_type

            # Calculate real-world time from recording start time + bark offset
            recording_start_time = parse_audio_filename_timestamp(audio_file_name)
            if recording_start_time:
                # Add bark offset (event.start_time) to recording start time
                bark_offset = timedelta(seconds=event.start_time)
                actual_bark_time = recording_start_time + bark_offset
                realworld_time = actual_bark_time.strftime('%H:%M:%S')
            else:
                # Fallback: use audio file offset if filename parsing fails
                logger.warning(f"Could not parse timestamp from filename: {audio_file_name}, using offset time")
                realworld_time = self._format_timestamp_to_time(event.start_time)

            # Calculate timestamp within audio file with millisecond precision
            bark_audiofile_timestamp = self._format_timestamp_with_milliseconds(event.start_time)

            persisted_event = PersistedBarkEvent(
                realworld_date=target_date,
                realworld_time=realworld_time,
                bark_id=bark_id,
                bark_type=bark_type,
                est_dog_size=None,  # Optional field for future use
                audio_file_name=audio_file_name,
                bark_audiofile_timestamp=bark_audiofile_timestamp,
                confidence=float(event.confidence),
                intensity=float(getattr(event, 'intensity', 0.0))
            )

            persisted_events.append(persisted_event)

        return persisted_events

    def _convert_to_violation_objects(self, violation_reports: List[ViolationReport],
                                    all_bark_events: List[PersistedBarkEvent],
                                    target_date: str) -> List[Violation]:
        """Convert ViolationReport objects to Violation objects for new persistence layer.

        Args:
            violation_reports: List of ViolationReport objects from analysis
            all_bark_events: List of all PersistedBarkEvent objects for the date
            target_date: Date in YYYY-MM-DD format

        Returns:
            List of Violation objects
        """
        violations = []

        for report in violation_reports:
            # Generate unique violation ID
            violation_id = str(uuid.uuid4())

            # Find associated bark events for this violation based on time range
            bark_event_ids = self._find_events_for_violation(report, all_bark_events)

            violation = Violation(
                violation_id=violation_id,
                violation_type=report.violation_type,
                violation_date=target_date,
                violation_start_time=report.start_time,
                violation_end_time=report.end_time,
                bark_event_ids=bark_event_ids
            )

            violations.append(violation)

        return violations

    def _format_timestamp_to_time(self, timestamp_seconds: float) -> str:
        """Convert timestamp in seconds to HH:MM:SS format.

        Args:
            timestamp_seconds: Timestamp in seconds

        Returns:
            Time string in HH:MM:SS format
        """
        hours = int(timestamp_seconds // 3600)
        minutes = int((timestamp_seconds % 3600) // 60)
        seconds = int(timestamp_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _format_timestamp_with_milliseconds(self, timestamp_seconds: float) -> str:
        """Convert timestamp in seconds to HH:MM:SS.mmm format.

        Args:
            timestamp_seconds: Timestamp in seconds

        Returns:
            Time string in HH:MM:SS.mmm format
        """
        hours = int(timestamp_seconds // 3600)
        minutes = int((timestamp_seconds % 3600) // 60)
        seconds = timestamp_seconds % 60
        whole_seconds = int(seconds)
        milliseconds = int((seconds - whole_seconds) * 1000)
        return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"

    def _find_events_for_violation(self, violation_report: ViolationReport,
                                 all_bark_events: List[PersistedBarkEvent]) -> List[str]:
        """Find bark event IDs that correlate with a specific violation.

        Args:
            violation_report: ViolationReport containing violation time range
            all_bark_events: List of all PersistedBarkEvent objects for the date

        Returns:
            List of bark_id strings associated with this violation
        """
        # Convert violation start/end times to seconds for comparison
        violation_start_seconds = self._parse_time_to_seconds(violation_report.start_time)
        violation_end_seconds = self._parse_time_to_seconds(violation_report.end_time)

        matching_event_ids = []

        for event in all_bark_events:
            # Convert event time to seconds
            event_seconds = self._parse_time_to_seconds(event.realworld_time)

            # Check if event falls within violation time range
            if violation_start_seconds <= event_seconds <= violation_end_seconds:
                matching_event_ids.append(event.bark_id)

        return matching_event_ids

    def _parse_time_to_seconds(self, time_str: str) -> float:
        """Parse time string to seconds since midnight.

        Args:
            time_str: Time string in various formats (HH:MM:SS, HH:MM AM/PM, etc.)

        Returns:
            Seconds since midnight as float
        """
        try:
            time_str = time_str.strip()

            # Handle AM/PM format first
            if 'AM' in time_str or 'PM' in time_str:
                is_pm = 'PM' in time_str
                time_part = time_str.replace('AM', '').replace('PM', '').strip()
                parts = time_part.split(':')

                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0

                # Convert to 24-hour format
                if is_pm and hours != 12:
                    hours += 12
                elif not is_pm and hours == 12:
                    hours = 0

                return hours * 3600 + minutes * 60

            # Handle 24-hour format (HH:MM:SS, HH:MM:SS.mmm, or HH:MM)
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                seconds = float(parts[2]) if len(parts) > 2 else 0.0

                return hours * 3600 + minutes * 60 + seconds

            # Fallback: assume it's already in seconds
            return float(time_str)

        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse time string '{time_str}': {e}")
            return 0.0