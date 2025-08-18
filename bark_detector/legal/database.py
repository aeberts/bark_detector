"""Violation database management"""

import json
import logging
import csv
import shutil
import os
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from .models import ViolationReport
from ..utils.helpers import convert_numpy_types

logger = logging.getLogger(__name__)


class ViolationDatabase:
    """Manages collection and persistence of violation reports."""
    
    def __init__(self, db_path: Path = None):
        """Initialize violation database."""
        if db_path is None:
            db_path = Path.home() / '.bark_detector' / 'violations.json'
        
        self.db_path = db_path
        self.violations: List[ViolationReport] = []
        self._load_violations()
    
    def _load_violations(self):
        """Load existing violations from database file."""
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
    
    def save_violations(self):
        """Save violations to database file."""
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
    
    def add_violation(self, violation: ViolationReport):
        """Add a violation report to the database."""
        self.violations.append(violation)
        self.save_violations()
    
    def remove_violations_for_date(self, date: str):
        """Remove all violations for a specific date."""
        initial_count = len(self.violations)
        self.violations = [v for v in self.violations if v.date != date]
        removed_count = initial_count - len(self.violations)
        if removed_count > 0:
            self.save_violations()
            logger.info(f"🗑️ Removed {removed_count} existing violations for {date}")
        return removed_count
    
    def has_violations_for_date(self, date: str) -> bool:
        """Check if violations exist for a specific date."""
        return any(v.date == date for v in self.violations)
    
    def get_violations_by_date_range(self, start_date: str, end_date: str) -> List[ViolationReport]:
        """Get violations within date range (YYYY-MM-DD format)."""
        return [
            v for v in self.violations 
            if start_date <= v.date <= end_date
        ]
    
    def get_violations_by_date(self, date: str) -> List[ViolationReport]:
        """Get violations for specific date (YYYY-MM-DD format)."""
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
        
        for violation in violations:
            self.violations.append(violation)
        
        if violations:
            self.save_violations()
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