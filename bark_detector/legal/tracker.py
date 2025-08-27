"""Legal violation tracker for bylaw compliance"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .models import ViolationReport, LegalSporadicSession
from .database import ViolationDatabase
from ..core.models import BarkingSession

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
        
        # Analyze each recording using advanced bark detection
        all_sessions = []
        total_analyzed_duration = 0
        
        for recording_file in date_recordings:
            logger.info(f"Analyzing recording: {recording_file.name}")
            try:
                # Load and analyze audio with YAMNet
                import librosa
                audio_data, sr = librosa.load(str(recording_file), sr=detector.sample_rate)
                
                if len(audio_data) == 0:
                    logger.warning(f"Empty audio file: {recording_file}")
                    continue
                
                total_analyzed_duration += len(audio_data) / sr
                
                # Use detector's advanced bark detection
                bark_events = detector._detect_barks_in_buffer(audio_data)
                
                if not bark_events:
                    logger.debug(f"No bark events detected in {recording_file.name}")
                    continue
                
                # Convert events to sessions using gap threshold
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
        
        if not all_sessions:
            logger.info(f"No bark events detected in recordings for {target_date}")
            return []
        
        # Detect violations using session analysis
        violations = self.analyze_violations(all_sessions)
        
        # Add date context to violations
        for violation in violations:
            violation.date = target_date
        
        logger.info(f"Detected {len(violations)} violations for {target_date}")
        for i, violation in enumerate(violations, 1):
            logger.info(f"  {violation.violation_type} violation: {violation.start_time} - {violation.end_time} ({violation.total_bark_duration/60:.1f}min barking)")
        
        # Save violations to database for later retrieval by --violation-report
        if violations:
            # Check if violations already exist for this date
            if self.violation_db.has_violations_for_date(target_date):
                existing_violations = self.violation_db.get_violations_by_date(target_date)
                logger.warning(f"⚠️  Found {len(existing_violations)} existing violations for {target_date}")
                
                if self.interactive:
                    # Ask user what to do
                    print(f"\n🗓️  Existing violations found for {target_date}:")
                    for i, v in enumerate(existing_violations, 1):
                        print(f"   {i}. {v.violation_type} - {v.total_bark_duration/60:.1f}min")
                    
                    print("\n🤔 What would you like to do?")
                    print("  [o] Overwrite existing violations with new analysis")
                    print("  [k] Keep existing violations (abort analysis)")
                    print("  [a] Add new violations alongside existing ones")
                    
                    while True:
                        choice = input("\nChoice [o/k/a]: ").lower().strip()
                        if choice in ['o', 'overwrite']:
                            self.violation_db.add_violations_for_date(violations, target_date, overwrite=True)
                            break
                        elif choice in ['k', 'keep']:
                            logger.info("🚫 Analysis aborted - keeping existing violations")
                            return existing_violations  # Return existing violations, don't save new ones
                        elif choice in ['a', 'add']:
                            self.violation_db.add_violations_for_date(violations, target_date, overwrite=False)
                            logger.info("➕ Added new violations alongside existing ones")
                            break
                        else:
                            print("❌ Invalid choice. Please enter 'o', 'k', or 'a'")
                else:
                    # Non-interactive mode (for testing): default to overwrite
                    logger.info("🔄 Non-interactive mode: overwriting existing violations")
                    self.violation_db.add_violations_for_date(violations, target_date, overwrite=True)
            else:
                # No existing violations, save normally
                self.violation_db.add_violations_for_date(violations, target_date, overwrite=False)
        
        return violations
        
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