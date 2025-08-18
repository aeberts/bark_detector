"""Tests for B9 violation report generation fix"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import csv

from bark_detector.legal.database import ViolationDatabase
from bark_detector.legal.models import ViolationReport


class TestViolationReportGeneration:
    """Test comprehensive violation report generation functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            db_path = Path(tmp.name)
        
        yield db_path
        
        # Cleanup
        if db_path.exists():
            os.unlink(db_path)
    
    @pytest.fixture
    def temp_reports_dir(self):
        """Create temporary reports directory"""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_violations(self):
        """Create sample violations for testing"""
        return [
            ViolationReport(
                date="2025-08-15",
                start_time="09:00:00",
                end_time="09:15:00",
                violation_type="Intermittent",
                total_bark_duration=900.0,
                total_incident_duration=1067.0,
                audio_files=["recordings/2025-08-15/bark_recording_20250815_090000.wav", 
                           "recordings/2025-08-15/bark_recording_20250815_091000.wav"],
                audio_file_start_times=["09:00:00", "09:10:00"],
                audio_file_end_times=["09:15:00", "09:15:00"],
                confidence_scores=[0.8, 0.9],
                peak_confidence=0.95,
                avg_confidence=0.85,
                created_timestamp="2025-08-18T10:00:00"
            ),
            ViolationReport(
                date="2025-08-15",
                start_time="14:00:00",
                end_time="14:05:00",
                violation_type="Constant",
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=["recordings/2025-08-15/bark_recording_20250815_140000.wav"],
                audio_file_start_times=["14:00:00"],
                audio_file_end_times=["14:05:00"],
                confidence_scores=[0.7],
                peak_confidence=0.8,
                avg_confidence=0.75,
                created_timestamp="2025-08-18T11:00:00"
            )
        ]
    
    def test_generate_violation_report_no_violations(self, temp_db, temp_reports_dir):
        """Test report generation when no violations exist"""
        db = ViolationDatabase(temp_db)
        
        report_dir = db.generate_violation_report("2025-08-16", "2025-08-16", temp_reports_dir)
        
        assert report_dir is None
    
    def test_generate_violation_report_with_violations(self, temp_db, temp_reports_dir, sample_violations):
        """Test complete report generation with violations"""
        db = ViolationDatabase(temp_db)
        
        # Add sample violations
        for violation in sample_violations:
            db.add_violation(violation)
        
        # Generate report
        report_dir = db.generate_violation_report("2025-08-15", "2025-08-15", temp_reports_dir)
        
        assert report_dir is not None
        assert report_dir.exists()
        assert report_dir.is_dir()
        
        # Check report files exist
        csv_files = list(report_dir.glob("*.csv"))
        txt_files = list(report_dir.glob("*_detailed.txt"))
        summary_file = report_dir / "REPORT_SUMMARY.txt"
        audio_dir = report_dir / "audio_evidence"
        
        assert len(csv_files) == 1
        assert len(txt_files) == 1
        assert summary_file.exists()
        assert audio_dir.exists()
    
    def test_csv_export_format(self, temp_db, temp_reports_dir, sample_violations):
        """Test CSV export format and content"""
        db = ViolationDatabase(temp_db)
        
        # Add sample violations
        for violation in sample_violations:
            db.add_violation(violation)
        
        # Generate report
        report_dir = db.generate_violation_report("2025-08-15", "2025-08-15", temp_reports_dir)
        
        # Check CSV content
        csv_files = list(report_dir.glob("*.csv"))
        assert len(csv_files) == 1
        
        with open(csv_files[0], 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2  # Two violations
        
        # Check first violation
        row1 = rows[0]
        assert row1['Date'] == "2025-08-15"
        assert row1['Violation Type'] == "Intermittent"
        assert row1['Total Bark Duration (min)'] == "15.0"
        assert row1['Audio Files Count'] == "2"
        assert "bark_recording_20250815_090000.wav" in row1['Audio Files']
        
        # Check second violation
        row2 = rows[1]
        assert row2['Date'] == "2025-08-15"
        assert row2['Violation Type'] == "Constant"
        assert row2['Total Bark Duration (min)'] == "5.0"
        assert row2['Audio Files Count'] == "1"
    
    def test_detailed_report_content(self, temp_db, temp_reports_dir, sample_violations):
        """Test detailed text report content"""
        db = ViolationDatabase(temp_db)
        
        # Add sample violations
        for violation in sample_violations:
            db.add_violation(violation)
        
        # Generate report
        report_dir = db.generate_violation_report("2025-08-15", "2025-08-15", temp_reports_dir)
        
        # Check detailed report content
        txt_files = list(report_dir.glob("*_detailed.txt"))
        assert len(txt_files) == 1
        
        with open(txt_files[0], 'r') as f:
            content = f.read()
        
        assert "BARK DETECTOR VIOLATION REPORT" in content
        assert "Report Period: 2025-08-15 to 2025-08-15" in content
        assert "Total Violations: 2" in content
        assert "Constant Violations: 1" in content
        assert "Intermittent Violations: 1" in content
        assert "VIOLATION #1" in content
        assert "VIOLATION #2" in content
        assert "Type: Intermittent" in content
        assert "Type: Constant" in content
    
    def test_summary_file_content(self, temp_db, temp_reports_dir, sample_violations):
        """Test summary file content"""
        db = ViolationDatabase(temp_db)
        
        # Add sample violations
        for violation in sample_violations:
            db.add_violation(violation)
        
        # Generate report
        report_dir = db.generate_violation_report("2025-08-15", "2025-08-15", temp_reports_dir)
        
        # Check summary content
        summary_file = report_dir / "REPORT_SUMMARY.txt"
        assert summary_file.exists()
        
        with open(summary_file, 'r') as f:
            content = f.read()
        
        assert "BARK DETECTOR VIOLATION REPORT SUMMARY" in content
        assert "Report Period: 2025-08-15 to 2025-08-15" in content
        assert "Total Violations: 2" in content
        assert "Constant Violations: 1" in content
        assert "Intermittent Violations: 1" in content
        assert "Total Bark Duration: 20.0 minutes" in content
        assert "2025-08-15: 2 violation(s)" in content
    
    @patch('shutil.copy2')
    def test_audio_file_copying(self, mock_copy, temp_db, temp_reports_dir, sample_violations):
        """Test audio file copying functionality"""
        db = ViolationDatabase(temp_db)
        
        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            # Add sample violations
            for violation in sample_violations:
                db.add_violation(violation)
            
            # Generate report
            report_dir = db.generate_violation_report("2025-08-15", "2025-08-15", temp_reports_dir)
            
            # Check that copy was called for each audio file
            assert mock_copy.call_count == 3  # Total audio files in sample violations
    
    def test_date_range_reports(self, temp_db, temp_reports_dir):
        """Test report generation for date ranges"""
        db = ViolationDatabase(temp_db)
        
        # Add violations for different dates
        violation1 = ViolationReport(
            date="2025-08-15", start_time="09:00:00", end_time="09:15:00",
            violation_type="Intermittent", total_bark_duration=900.0,
            total_incident_duration=1067.0, audio_files=["test1.wav"],
            audio_file_start_times=["09:00:00"], audio_file_end_times=["09:15:00"],
            confidence_scores=[0.8], peak_confidence=0.9, avg_confidence=0.8,
            created_timestamp="2025-08-18T10:00:00"
        )
        
        violation2 = ViolationReport(
            date="2025-08-16", start_time="10:00:00", end_time="10:15:00",
            violation_type="Constant", total_bark_duration=600.0,
            total_incident_duration=600.0, audio_files=["test2.wav"],
            audio_file_start_times=["10:00:00"], audio_file_end_times=["10:15:00"],
            confidence_scores=[0.75], peak_confidence=0.8, avg_confidence=0.75,
            created_timestamp="2025-08-18T11:00:00"
        )
        
        db.add_violation(violation1)
        db.add_violation(violation2)
        
        # Generate report for date range
        report_dir = db.generate_violation_report("2025-08-15", "2025-08-16", temp_reports_dir)
        
        assert report_dir is not None
        assert "2025-08-15_to_2025-08-16" in report_dir.name
        
        # Check that both violations are included
        csv_files = list(report_dir.glob("*.csv"))
        with open(csv_files[0], 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        dates = [row['Date'] for row in rows]
        assert "2025-08-15" in dates
        assert "2025-08-16" in dates