"""Violation database management"""

import json
import logging
import csv
import shutil
import os
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from .models import ViolationReport, PersistedBarkEvent, Violation
from ..utils.helpers import convert_numpy_types

logger = logging.getLogger(__name__)


class ViolationDatabase:
    """Manages collection and persistence of violation reports."""
    
    def __init__(self, db_path_or_violations_dir: Path = None, violations_dir: Path = None):
        """Initialize violation database.
        
        Args:
            db_path_or_violations_dir: For backward compatibility - can be legacy db_path or violations_dir
            violations_dir: Explicit violations directory (when using named parameter)
        """
        # Handle backward compatibility: if first arg is provided and looks like a file, treat as legacy db_path
        if db_path_or_violations_dir is not None:
            path = Path(db_path_or_violations_dir)
            # If it has a file extension (.json), treat as legacy db_path
            if path.suffix == '.json' or (path.exists() and path.is_file()):
                # Legacy mode
                self.db_path = path
                self.violations_dir = None
                self.use_date_structure = False
            else:
                # New mode - directory for date structure
                self.violations_dir = path
                self.use_date_structure = True
                self.db_path = None
        elif violations_dir is not None:
            # Explicit violations_dir parameter
            self.violations_dir = Path(violations_dir)
            self.use_date_structure = True
            self.db_path = None
        else:
            # Default: use project-local violations/ directory
            self.violations_dir = Path.cwd() / 'violations'
            self.use_date_structure = True
            self.db_path = None
        
        self.violations: List[ViolationReport] = []
        
        if not self.use_date_structure:
            self._load_violations_legacy()
        # Date-based loading happens per-date in get_violations_by_date()
    
    def _get_violations_file_path(self, date: str) -> Path:
        """Get the file path for violations for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Path to the violations file for that date
        """
        if self.use_date_structure:
            date_dir = self.violations_dir / date
            return date_dir / f"{date}_violations.json"
        else:
            # Legacy single file mode
            return self.db_path
    
    def _get_events_file_path(self, date: str) -> Path:
        """Get the file path for events for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Path to the events file for that date
        """
        if self.use_date_structure:
            date_dir = self.violations_dir / date
            return date_dir / f"{date}_events.json"
        else:
            # Legacy mode doesn't support events files
            raise ValueError("Events files are only supported in date-based structure mode")
    
    def save_events(self, events: List[PersistedBarkEvent], date: str):
        """Save events to date-partitioned file structure.
        
        Args:
            events: List of PersistedBarkEvent objects to save
            date: Date in YYYY-MM-DD format
        """
        if not self.use_date_structure:
            raise ValueError("save_events() only supported in date-based structure mode")
        
        if not events:
            return
            
        events_file = self._get_events_file_path(date)
        
        try:
            # Create directory structure
            events_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert events to dictionaries
            events_data = {
                'events': [event.to_dict() for event in events],
                'metadata': {
                    'date': date,
                    'total_events': len(events),
                    'created_timestamp': datetime.now().isoformat()
                }
            }
            
            with open(events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            logger.debug(f"💾 Saved {len(events)} events to {events_file}")
                
        except Exception as e:
            logger.error(f"Could not save events for date {date}: {e}")
    
    def load_events(self, date: str) -> List[PersistedBarkEvent]:
        """Load events for a specific date from date-partitioned file structure.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of PersistedBarkEvent objects for that date
        """
        if not self.use_date_structure:
            raise ValueError("load_events() only supported in date-based structure mode")
        
        events_file = self._get_events_file_path(date)
        events = []
        
        try:
            if events_file.exists():
                with open(events_file, 'r') as f:
                    data = json.load(f)
                    for event_data in data.get('events', []):
                        events.append(PersistedBarkEvent.from_dict(event_data))
        except Exception as e:
            logger.warning(f"Could not load events for date {date}: {e}")
        
        return events
    
    def save_violations_new(self, violations: List[Violation], date: str):
        """Save violations to date-partitioned file structure.
        
        Args:
            violations: List of Violation objects to save
            date: Date in YYYY-MM-DD format
        """
        if not self.use_date_structure:
            raise ValueError("save_violations_new() only supported in date-based structure mode")
        
        if not violations:
            return
            
        violations_file = self._get_violations_file_path(date)
        
        try:
            # Create directory structure
            violations_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert violations to dictionaries
            violations_data = {
                'violations': [violation.to_dict() for violation in violations],
                'metadata': {
                    'date': date,
                    'total_violations': len(violations),
                    'created_timestamp': datetime.now().isoformat()
                }
            }
            
            with open(violations_file, 'w') as f:
                json.dump(violations_data, f, indent=2)
            
            logger.debug(f"💾 Saved {len(violations)} violations to {violations_file}")
                
        except Exception as e:
            logger.error(f"Could not save violations for date {date}: {e}")
    
    def load_violations_new(self, date: str) -> List[Violation]:
        """Load violations for a specific date from date-partitioned file structure.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of Violation objects for that date
        """
        if not self.use_date_structure:
            raise ValueError("load_violations_new() only supported in date-based structure mode")
        
        violations_file = self._get_violations_file_path(date)
        violations = []
        
        try:
            if violations_file.exists():
                with open(violations_file, 'r') as f:
                    data = json.load(f)
                    for violation_data in data.get('violations', []):
                        violations.append(Violation.from_dict(violation_data))
        except Exception as e:
            logger.warning(f"Could not load violations for date {date}: {e}")
        
        return violations
    
    def _load_violations_legacy(self):
        """Load existing violations from legacy single database file."""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.violations = []
                    for violation_data in data.get('violations', []):
                        # Add backward compatibility for records without new timestamp fields
                        if 'audio_file_start_times' not in violation_data:
                            violation_data['audio_file_start_times'] = ["00:00:00"] * len(violation_data.get('audio_files', []))
                        if 'audio_file_end_times' not in violation_data:
                            violation_data['audio_file_end_times'] = ["00:00:00"] * len(violation_data.get('audio_files', []))
                        
                        self.violations.append(ViolationReport(**violation_data))
        except Exception as e:
            logger.warning(f"Could not load violation database: {e}")
            self.violations = []
    
    def _load_violations_for_date(self, date: str) -> List[ViolationReport]:
        """Load violations for a specific date from date-based file structure."""
        violations_file = self._get_violations_file_path(date)
        violations = []

        try:
            if violations_file.exists():
                with open(violations_file, 'r') as f:
                    data = json.load(f)
                    for violation_data in data.get('violations', []):
                        # New-format violations (Violation model persisted as JSON)
                        if 'type' in violation_data and 'startTimestamp' in violation_data:
                            try:
                                start_dt = datetime.fromisoformat(violation_data['startTimestamp'].replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(violation_data['endTimestamp'].replace('Z', '+00:00'))
                            except (KeyError, ValueError):
                                logger.warning(f"Skipping violation with invalid timestamps in {violations_file}")
                                continue

                            start_time_str = start_dt.strftime("%I:%M %p").lstrip('0')
                            end_time_str = end_dt.strftime("%I:%M %p").lstrip('0')

                            violation_report = ViolationReport(
                                date=date,
                                start_time=start_time_str,
                                end_time=end_time_str,
                                violation_type="Constant" if violation_data.get('type') == "Continuous" else "Intermittent",
                                total_bark_duration=violation_data.get('violationDurationMinutes', 0.0) * 60.0,
                                total_incident_duration=violation_data.get('durationMinutes', 0.0) * 60.0,
                                audio_files=violation_data.get('audio_files', []),
                                audio_file_start_times=violation_data.get('audio_file_start_times', [start_time_str]),
                                audio_file_end_times=violation_data.get('audio_file_end_times', [end_time_str]),
                                confidence_scores=violation_data.get('confidence_scores', []),
                                peak_confidence=violation_data.get('peak_confidence', 0.0),
                                avg_confidence=violation_data.get('avg_confidence', 0.0),
                                created_timestamp=violation_data.get('created_timestamp', datetime.now().isoformat())
                            )

                            violations.append(violation_report)
                            continue

                        # Remove violation_id field if present (legacy compatibility)
                        if 'violation_id' in violation_data:
                            violation_data.pop('violation_id')

                        # Handle different field names between Violation and ViolationReport models
                        if 'violation_date' in violation_data:
                            violation_data['date'] = violation_data.pop('violation_date')
                        if 'violation_start_time' in violation_data:
                            violation_data['start_time'] = violation_data.pop('violation_start_time')
                        if 'violation_end_time' in violation_data:
                            violation_data['end_time'] = violation_data.pop('violation_end_time')
                        if 'bark_event_ids' in violation_data:
                            violation_data.pop('bark_event_ids')

                        violation_data.setdefault('total_bark_duration', 0.0)
                        violation_data.setdefault('total_incident_duration', 0.0)
                        violation_data.setdefault('audio_files', [])
                        violation_data.setdefault('audio_file_start_times', [])
                        violation_data.setdefault('audio_file_end_times', [])
                        violation_data.setdefault('confidence_scores', [])
                        violation_data.setdefault('peak_confidence', 0.0)
                        violation_data.setdefault('avg_confidence', 0.0)
                        violation_data.setdefault('created_timestamp', '')

                        if 'audio_file_start_times' not in violation_data:
                            violation_data['audio_file_start_times'] = ["00:00:00"] * len(violation_data.get('audio_files', []))
                        if 'audio_file_end_times' not in violation_data:
                            violation_data['audio_file_end_times'] = ["00:00:00"] * len(violation_data.get('audio_files', []))

                        violations.append(ViolationReport(**violation_data))
        except Exception as e:
            logger.warning(f"Could not load violations for date {date}: {e}")

        return violations
    
    def _save_violations_for_date(self, violations: List[ViolationReport], date: str):
        """Save violations for a specific date to date-based file structure."""
        if not violations:
            return
            
        violations_file = self._get_violations_file_path(date)
        
        try:
            # Create directory structure
            violations_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'violations': [
                    {
                        'date': v.date,
                        'start_time': v.start_time,
                        'end_time': v.end_time,
                        'violation_type': v.violation_type,
                        'total_bark_duration': convert_numpy_types(v.total_bark_duration),
                        'total_incident_duration': convert_numpy_types(v.total_incident_duration),
                        'audio_files': v.audio_files,
                        'audio_file_start_times': v.audio_file_start_times,
                        'audio_file_end_times': v.audio_file_end_times,
                        'confidence_scores': convert_numpy_types(v.confidence_scores),
                        'peak_confidence': convert_numpy_types(v.peak_confidence),
                        'avg_confidence': convert_numpy_types(v.avg_confidence),
                        'created_timestamp': v.created_timestamp
                    }
                    for v in violations
                ]
            }
            
            with open(violations_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Saved {len(violations)} violations to {violations_file}")
                
        except Exception as e:
            logger.error(f"Could not save violations for date {date}: {e}")
    
    def save_violations(self):
        """Save violations to database file (legacy method for backward compatibility)."""
        if not self.use_date_structure:
            # Legacy single file mode
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                
                data = {
                    'violations': [
                        {
                            'date': v.date,
                            'start_time': v.start_time,
                            'end_time': v.end_time,
                            'violation_type': v.violation_type,
                            'total_bark_duration': convert_numpy_types(v.total_bark_duration),
                            'total_incident_duration': convert_numpy_types(v.total_incident_duration),
                            'audio_files': v.audio_files,
                            'audio_file_start_times': v.audio_file_start_times,
                            'audio_file_end_times': v.audio_file_end_times,
                            'confidence_scores': convert_numpy_types(v.confidence_scores),
                            'peak_confidence': convert_numpy_types(v.peak_confidence),
                            'avg_confidence': convert_numpy_types(v.avg_confidence),
                            'created_timestamp': v.created_timestamp
                        }
                        for v in self.violations
                    ]
                }
                
                with open(self.db_path, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            except Exception as e:
                logger.error(f"Could not save violation database: {e}")
        else:
            # Date-based structure mode - group by date and save to separate files
            violations_by_date = {}
            for violation in self.violations:
                date = violation.date
                if date not in violations_by_date:
                    violations_by_date[date] = []
                violations_by_date[date].append(violation)
            
            for date, date_violations in violations_by_date.items():
                self._save_violations_for_date(date_violations, date)
    
    def add_violation(self, violation: ViolationReport):
        """Add a violation report to the database."""
        if self.use_date_structure:
            # In date-based mode, save directly to date-specific file
            self.add_violations_for_date([violation], violation.date, overwrite=False)
        else:
            # Legacy mode - add to in-memory list and save all
            self.violations.append(violation)
            self.save_violations()
    
    def remove_violations_for_date(self, date: str):
        """Remove all violations for a specific date."""
        if self.use_date_structure:
            violations_file = self._get_violations_file_path(date)
            removed_count = 0
            if violations_file.exists():
                existing_violations = self._load_violations_for_date(date)
                removed_count = len(existing_violations)
                try:
                    violations_file.unlink()  # Delete the file
                    logger.info(f"🗑️ Removed {removed_count} existing violations for {date}")
                except Exception as e:
                    logger.error(f"Failed to remove violations file for {date}: {e}")
                    removed_count = 0
            return removed_count
        else:
            initial_count = len(self.violations)
            self.violations = [v for v in self.violations if v.date != date]
            removed_count = initial_count - len(self.violations)
            if removed_count > 0:
                self.save_violations()
                logger.info(f"🗑️ Removed {removed_count} existing violations for {date}")
            return removed_count
    
    def has_violations_for_date(self, date: str) -> bool:
        """Check if violations exist for a specific date."""
        if self.use_date_structure:
            violations_file = self._get_violations_file_path(date)
            return violations_file.exists() and len(self._load_violations_for_date(date)) > 0
        else:
            return any(v.date == date for v in self.violations)
    
    def get_violations_by_date_range(self, start_date: str, end_date: str) -> List[ViolationReport]:
        """Get violations within date range (YYYY-MM-DD format)."""
        if self.use_date_structure:
            # Load violations from all date files in the range
            violations = []
            date_range = self._get_date_range(start_date, end_date)
            for date in date_range:
                violations.extend(self._load_violations_for_date(date))
            return violations
        else:
            return [
                v for v in self.violations 
                if start_date <= v.date <= end_date
            ]
    
    def _get_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Generate list of dates between start_date and end_date (inclusive)."""
        from datetime import datetime, timedelta
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return dates
    
    def get_violations_by_date(self, date: str) -> List[ViolationReport]:
        """Get violations for specific date (YYYY-MM-DD format)."""
        if self.use_date_structure:
            return self._load_violations_for_date(date)
        else:
            return [v for v in self.violations if v.date == date]
    
    def export_to_csv(self, output_path: Path) -> None:
        """Export violations to CSV format for RDCO submission."""
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'Date', 'Start Time', 'End Time', 'Violation Type',
                'Total Bark Duration (min)', 'Total Incident Duration (min)',
                'Audio Files', 'Audio File Start Times (Relative)', 'Audio File End Times (Relative)',
                'Peak Confidence', 'Avg Confidence'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for v in self.violations:
                writer.writerow({
                    'Date': v.date,
                    'Start Time': v.start_time,
                    'End Time': v.end_time,
                    'Violation Type': v.violation_type,
                    'Total Bark Duration (min)': f"{v.total_bark_duration / 60:.1f}",
                    'Total Incident Duration (min)': f"{v.total_incident_duration / 60:.1f}",
                    'Audio Files': '; '.join(v.audio_files),
                    'Audio File Start Times (Relative)': '; '.join(v.audio_file_start_times),
                    'Audio File End Times (Relative)': '; '.join(v.audio_file_end_times),
                    'Peak Confidence': f"{v.peak_confidence:.3f}",
                    'Avg Confidence': f"{v.avg_confidence:.3f}"
                })
    
    def add_violations_for_date(self, violations: List[ViolationReport], date: str, overwrite: bool = False):
        """Add multiple violations for a date, with optional overwrite of existing data."""
        if overwrite and self.has_violations_for_date(date):
            self.remove_violations_for_date(date)
        
        if self.use_date_structure:
            # In date-based mode, save directly to date-specific file
            existing_violations = self._load_violations_for_date(date) if not overwrite else []
            all_violations = existing_violations + violations
            self._save_violations_for_date(all_violations, date)
        else:
            # Legacy mode - add to in-memory list and save all
            for violation in violations:
                self.violations.append(violation)
            self.save_violations()
        
        if violations:
            logger.info(f"💾 Saved {len(violations)} violations to database")
    
    def generate_violation_report(self, start_date: str, end_date: str, output_dir: Path = None) -> Path:
        """Generate comprehensive violation report with audio files.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            output_dir: Base directory for reports (defaults to 'reports')
            
        Returns:
            Path to the generated report directory
        """
        if output_dir is None:
            output_dir = Path.cwd() / 'reports'
        
        violations = self.get_violations_by_date_range(start_date, end_date)
        
        if not violations:
            logger.info(f"📋 No violations found from {start_date} to {end_date} - no report generated")
            return None
        
        # Create report directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if start_date == end_date:
            report_name = f"Violation_Report_{start_date}_{timestamp}"
        else:
            report_name = f"Violation_Report_{start_date}_to_{end_date}_{timestamp}"
        
        report_dir = output_dir / report_name
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate CSV report
        csv_path = report_dir / f"{report_name}.csv"
        self._export_violations_to_csv(violations, csv_path)
        
        # Generate detailed text report
        txt_path = report_dir / f"{report_name}_detailed.txt"
        self._generate_detailed_report(violations, txt_path, start_date, end_date)
        
        # Copy audio files
        audio_dir = report_dir / "audio_evidence"
        audio_dir.mkdir(exist_ok=True)
        copied_files = self._copy_audio_files(violations, audio_dir)
        
        # Generate summary file
        summary_path = report_dir / "REPORT_SUMMARY.txt"
        self._generate_summary_file(violations, summary_path, start_date, end_date, copied_files)
        
        logger.info(f"📁 Violation report generated: {report_dir}")
        logger.info(f"📊 Report includes {len(violations)} violations and {len(copied_files)} audio files")
        
        return report_dir
    
    def _export_violations_to_csv(self, violations: List[ViolationReport], output_path: Path):
        """Export specific violations to CSV."""
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'Date', 'Start Time', 'End Time', 'Violation Type',
                'Total Bark Duration (min)', 'Total Incident Duration (min)',
                'Audio Files Count', 'Audio Files', 'Peak Confidence', 'Avg Confidence'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for v in violations:
                writer.writerow({
                    'Date': v.date,
                    'Start Time': v.start_time,
                    'End Time': v.end_time,
                    'Violation Type': v.violation_type,
                    'Total Bark Duration (min)': f"{v.total_bark_duration / 60:.1f}",
                    'Total Incident Duration (min)': f"{v.total_incident_duration / 60:.1f}",
                    'Audio Files Count': len(v.audio_files),
                    'Audio Files': '; '.join([Path(f).name for f in v.audio_files]),
                    'Peak Confidence': f"{v.peak_confidence:.3f}",
                    'Avg Confidence': f"{v.avg_confidence:.3f}"
                })
    
    def _generate_detailed_report(self, violations: List[ViolationReport], output_path: Path, start_date: str, end_date: str):
        """Generate detailed text report."""
        with open(output_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("BARK DETECTOR VIOLATION REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Report Period: {start_date} to {end_date}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Violations: {len(violations)}\n\n")
            
            # Summary by type
            constant_violations = [v for v in violations if v.violation_type == "Constant"]
            intermittent_violations = [v for v in violations if v.violation_type == "Intermittent"]
            
            f.write("VIOLATION SUMMARY:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Constant Violations: {len(constant_violations)}\n")
            f.write(f"Intermittent Violations: {len(intermittent_violations)}\n\n")
            
            # Detailed violations
            f.write("DETAILED VIOLATION LIST:\n")
            f.write("-" * 30 + "\n\n")
            
            for i, violation in enumerate(violations, 1):
                f.write(f"VIOLATION #{i}\n")
                f.write(f"Date: {violation.date}\n")
                f.write(f"Time: {violation.start_time} - {violation.end_time}\n")
                f.write(f"Type: {violation.violation_type}\n")
                f.write(f"Total Bark Duration: {violation.total_bark_duration / 60:.1f} minutes\n")
                f.write(f"Total Incident Duration: {violation.total_incident_duration / 60:.1f} minutes\n")
                f.write(f"Peak Confidence: {violation.peak_confidence:.3f}\n")
                f.write(f"Average Confidence: {violation.avg_confidence:.3f}\n")
                f.write(f"Audio Files ({len(violation.audio_files)} total):\n")
                for audio_file in violation.audio_files:
                    f.write(f"  - {Path(audio_file).name}\n")
                f.write("\n" + "-" * 50 + "\n\n")
    
    def _copy_audio_files(self, violations: List[ViolationReport], audio_dir: Path) -> List[str]:
        """Copy audio files referenced in violations to the report directory."""
        copied_files = []
        
        for violation in violations:
            for audio_file_path in violation.audio_files:
                source_path = Path(audio_file_path)
                
                # Try to find the file in recordings directory or its subdirectories
                possible_paths = [
                    source_path,  # Full path as given
                    Path.cwd() / "recordings" / source_path.name,  # Flat structure
                    Path.cwd() / "recordings" / violation.date / source_path.name,  # Date structure
                ]
                
                source_found = None
                for possible_path in possible_paths:
                    if possible_path.exists():
                        source_found = possible_path
                        break
                
                if source_found:
                    dest_path = audio_dir / source_found.name
                    try:
                        shutil.copy2(source_found, dest_path)
                        copied_files.append(source_found.name)
                        logger.debug(f"Copied audio file: {source_found.name}")
                    except Exception as e:
                        logger.warning(f"Failed to copy audio file {source_found}: {e}")
                else:
                    logger.warning(f"Audio file not found: {audio_file_path}")
        
        return copied_files
    
    def _generate_summary_file(self, violations: List[ViolationReport], summary_path: Path, 
                              start_date: str, end_date: str, copied_files: List[str]):
        """Generate executive summary file."""
        with open(summary_path, 'w') as f:
            f.write("BARK DETECTOR VIOLATION REPORT SUMMARY\n")
            f.write("=" * 45 + "\n\n")
            
            f.write(f"📅 Report Period: {start_date} to {end_date}\n")
            f.write(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n\n")
            
            f.write(f"📊 SUMMARY STATISTICS:\n")
            f.write(f"   Total Violations: {len(violations)}\n")
            
            constant_count = len([v for v in violations if v.violation_type == "Constant"])
            intermittent_count = len([v for v in violations if v.violation_type == "Intermittent"])
            f.write(f"   Constant Violations: {constant_count}\n")
            f.write(f"   Intermittent Violations: {intermittent_count}\n")
            
            total_bark_time = sum(v.total_bark_duration for v in violations)
            f.write(f"   Total Bark Duration: {total_bark_time / 60:.1f} minutes\n")
            f.write(f"   Audio Evidence Files: {len(copied_files)}\n\n")
            
            f.write("📁 REPORT CONTENTS:\n")
            f.write("   - This summary file\n")
            f.write("   - Detailed violation report (TXT format)\n")
            f.write("   - Machine-readable data (CSV format)\n")
            f.write("   - Audio evidence files (WAV format)\n\n")
            
            if violations:
                f.write("🔍 VIOLATIONS BY DATE:\n")
                dates = sorted(set(v.date for v in violations))
                for date in dates:
                    date_violations = [v for v in violations if v.date == date]
                    f.write(f"   {date}: {len(date_violations)} violation(s)\n")
            
            f.write("\n" + "=" * 45 + "\n")
            f.write("This report was generated by the Advanced YAMNet Bark Detector\n")
            f.write("For City of Kelowna bylaw violation documentation\n")
    
    def load_violations(self) -> Dict:
        """Load violations from database (for backward compatibility)."""
        return {'violations': self.violations}
