"""Legal violation tracker for bylaw compliance"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List
from .models import ViolationReport, LegalSporadicSession
from ..core.models import BarkingSession

logger = logging.getLogger(__name__)


class LegalViolationTracker:
    """Track and analyze bark events for legal violation detection."""
    
    def __init__(self):
        """Initialize the legal violation tracker."""
        self.violations = []
        self.sessions = []
    
    def analyze_violations(self, sessions: List[BarkingSession]) -> List[ViolationReport]:
        """Analyze barking sessions for legal violations."""
        violations = []
        
        for session in sessions:
            # Check for continuous violations (5+ minutes)
            if session.total_duration >= 300:  # 5 minutes
                violations.append(self._create_violation_report(session, "Constant"))
            
            # For sporadic violations, we'd need to group sessions
            # This is a simplified implementation
            
        return violations
    
    def analyze_recordings_for_date(self, recordings_dir: Path, target_date: str, detector) -> List[ViolationReport]:
        """
        Analyze recordings for a specific date and detect bylaw violations.
        
        Args:
            recordings_dir: Path to recordings directory
            target_date: Date string in YYYY-MM-DD format
            detector: Detector instance to use for analysis
            
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
        
        # For now, return a simplified analysis
        violations = []
        total_duration = 0
        
        for recording_file in date_recordings:
            # Get file duration (simplified)
            try:
                import librosa
                audio_data, sr = librosa.load(str(recording_file), sr=None)
                duration = len(audio_data) / sr
                total_duration += duration
                
                # Simple rule: if any recording is longer than 5 minutes, it's a violation
                if duration >= 300:  # 5 minutes
                    violation = ViolationReport(
                        date=target_date,
                        start_time="Unknown",  # Would need analysis to determine
                        end_time="Unknown",
                        violation_type="Constant",
                        total_bark_duration=duration,
                        total_incident_duration=duration,
                        audio_files=[str(recording_file)],
                        audio_file_start_times=["00:00:00"],
                        audio_file_end_times=[f"{int(duration//3600):02d}:{int((duration%3600)//60):02d}:{int(duration%60):02d}"],
                        confidence_scores=[0.68],  # Default
                        peak_confidence=0.68,
                        avg_confidence=0.68,
                        created_timestamp=datetime.now().isoformat()
                    )
                    violations.append(violation)
                    
            except Exception as e:
                logger.warning(f"Could not analyze {recording_file}: {e}")
        
        logger.info(f"Analysis complete: {len(violations)} violations detected")
        logger.info(f"Total recording duration: {total_duration/60:.1f} minutes")
        
        return violations
    
    def _create_violation_report(self, session: BarkingSession, violation_type: str) -> ViolationReport:
        """Create a violation report from a barking session."""
        from datetime import datetime
        
        return ViolationReport(
            date=datetime.now().strftime('%Y-%m-%d'),
            start_time="Unknown",
            end_time="Unknown", 
            violation_type=violation_type,
            total_bark_duration=session.total_duration,
            total_incident_duration=session.total_duration,
            audio_files=[str(session.source_file)] if session.source_file else [],
            audio_file_start_times=["00:00:00"],
            audio_file_end_times=["00:00:00"],
            confidence_scores=[session.avg_confidence],
            peak_confidence=session.peak_confidence,
            avg_confidence=session.avg_confidence,
            created_timestamp=datetime.now().isoformat()
        )
    
    def track_session(self, session: BarkingSession):
        """Track a barking session for violation analysis."""
        self.sessions.append(session)
        logger.debug(f"Tracked session: {len(session.events)} bark events")