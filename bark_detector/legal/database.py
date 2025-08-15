"""Violation database management"""

import json
import logging
import csv
from typing import List, Dict
from pathlib import Path
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
    
    def load_violations(self) -> Dict:
        """Load violations from database (for backward compatibility)."""
        return {'violations': self.violations}