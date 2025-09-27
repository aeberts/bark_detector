"""Tests for the log migration script."""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from scripts.migrate_logs_by_date import LogMigrator, LogEntry, MigrationSummary


class TestLogMigrator:
    """Test the LogMigrator class functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.migrator = LogMigrator(logs_dir=str(self.temp_path))

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_log_line_valid(self):
        """Test parsing of valid log lines."""
        line = "2025-09-27 10:30:15,678 - INFO - Starting violation analysis for date: 2025-09-26"

        entry = self.migrator.parse_log_line(line, 1)

        assert entry is not None
        assert entry.level == "INFO"
        assert "violation analysis" in entry.message
        assert entry.timestamp.year == 2025
        assert entry.timestamp.month == 9
        assert entry.timestamp.day == 27

    def test_parse_log_line_malformed(self):
        """Test parsing of malformed log lines."""
        line = "This is not a valid log line format"

        # With continue_on_error=False (default)
        with pytest.raises(ValueError, match="Malformed log line"):
            self.migrator.parse_log_line(line, 1)

        # With continue_on_error=True (create fresh migrator)
        migrator_continue = LogMigrator(continue_on_error=True)
        entry = migrator_continue.parse_log_line(line, 1)
        assert entry is None
        assert migrator_continue.malformed_lines == 1

    def test_parse_log_line_empty(self):
        """Test parsing of empty lines."""
        entry = self.migrator.parse_log_line("", 1)
        assert entry is None

        entry = self.migrator.parse_log_line("   ", 1)
        assert entry is None

    def test_classify_by_channel_detection(self):
        """Test channel classification for detection entries."""
        detection_entries = [
            LogEntry(datetime.now(), "INFO", "YAMNet model downloaded successfully", ""),
            LogEntry(datetime.now(), "INFO", "Starting manual recording session", ""),
            LogEntry(datetime.now(), "INFO", "Calibration complete", ""),
            LogEntry(datetime.now(), "INFO", "Real-time detection started", ""),
            LogEntry(datetime.now(), "INFO", "Configuration loaded from file", ""),
        ]

        for entry in detection_entries:
            channel = self.migrator.classify_by_channel(entry)
            assert channel == 'detection', f"Entry '{entry.message}' should be detection"

    def test_classify_by_channel_analysis(self):
        """Test channel classification for analysis entries."""
        analysis_entries = [
            LogEntry(datetime.now(), "INFO", "Starting violation analysis for date: 2025-09-26", ""),
            LogEntry(datetime.now(), "INFO", "Analysis complete: 5 violations detected", ""),
            LogEntry(datetime.now(), "INFO", "PDF report generated: reports/violation_report.pdf", ""),
            LogEntry(datetime.now(), "INFO", "Enhanced report created successfully", ""),
            LogEntry(datetime.now(), "INFO", "Exporting violations to CSV", ""),
        ]

        for entry in analysis_entries:
            channel = self.migrator.classify_by_channel(entry)
            assert channel == 'analysis', f"Entry '{entry.message}' should be analysis"

    def test_classify_by_channel_default_fallback(self):
        """Test that unmatched entries default to detection channel."""
        generic_entry = LogEntry(datetime.now(), "INFO", "Some generic log message", "")

        channel = self.migrator.classify_by_channel(generic_entry)
        assert channel == 'detection'

    def test_group_by_date_and_channel(self):
        """Test grouping of entries by date and channel."""
        entries = [
            LogEntry(datetime(2025, 9, 27, 10, 0), "INFO", "YAMNet model loaded", "line1"),
            LogEntry(datetime(2025, 9, 27, 11, 0), "INFO", "Violation analysis started", "line2"),
            LogEntry(datetime(2025, 9, 28, 9, 0), "INFO", "Recording session started", "line3"),
            LogEntry(datetime(2025, 9, 28, 10, 0), "INFO", "PDF report generated", "line4"),
        ]

        grouped = self.migrator.group_by_date_and_channel(entries)

        # Check dates
        assert "2025-09-27" in grouped
        assert "2025-09-28" in grouped

        # Check channels for each date
        assert len(grouped["2025-09-27"]["detection"]) == 1
        assert len(grouped["2025-09-27"]["analysis"]) == 1
        assert len(grouped["2025-09-28"]["detection"]) == 1
        assert len(grouped["2025-09-28"]["analysis"]) == 1

    def test_create_backup(self):
        """Test backup file creation."""
        # Create a test input file
        input_file = self.temp_path / "test.log"
        input_file.write_text("Test log content")

        backup_path = self.migrator.create_backup(input_file)

        # Check backup was created
        assert backup_path.exists()
        assert backup_path.read_text() == "Test log content"
        assert "backup" in backup_path.name
        assert str(datetime.now().year) in backup_path.name

    def test_write_daily_channel_logs(self):
        """Test writing of daily channel log files."""
        entries_by_channel = {
            'detection': [
                LogEntry(datetime(2025, 9, 27, 10, 0), "INFO", "Detection message", "2025-09-27 10:00:00,000 - INFO - Detection message"),
            ],
            'analysis': [
                LogEntry(datetime(2025, 9, 27, 11, 0), "INFO", "Analysis message", "2025-09-27 11:00:00,000 - INFO - Analysis message"),
            ]
        }

        output_files = self.migrator.write_daily_channel_logs("2025-09-27", entries_by_channel)

        # Check files were created
        assert len(output_files) == 2

        detection_file = self.temp_path / "2025-09-27" / "2025-09-27_detection.log"
        analysis_file = self.temp_path / "2025-09-27" / "2025-09-27_analysis.log"

        assert detection_file.exists()
        assert analysis_file.exists()

        # Check content
        assert "Detection message" in detection_file.read_text()
        assert "Analysis message" in analysis_file.read_text()

    def test_find_legacy_log_files(self):
        """Test finding legacy log files."""
        # Create some test files
        (self.temp_path / "bark_detector.log").touch()
        (self.temp_path / "bark_detector_old.log").touch()
        (self.temp_path / "other_file.txt").touch()

        # Change to temp directory for testing
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(str(self.temp_path))
            migrator = LogMigrator()
            found_files = migrator.find_legacy_log_files()

            # Should find bark_detector files but not other files
            found_names = [f.name for f in found_files]
            assert "bark_detector.log" in found_names
            assert "bark_detector_old.log" in found_names
            assert "other_file.txt" not in found_names

        finally:
            os.chdir(old_cwd)

    def test_validate_input_file(self):
        """Test input file validation."""
        # Test with non-existent file
        non_existent = self.temp_path / "nonexistent.log"
        with pytest.raises(FileNotFoundError):
            self.migrator.validate_input_file(non_existent)

        # Test with directory instead of file
        test_dir = self.temp_path / "test_dir"
        test_dir.mkdir()
        with pytest.raises(ValueError, match="not a file"):
            self.migrator.validate_input_file(test_dir)

        # Test with valid file
        valid_file = self.temp_path / "valid.log"
        valid_file.write_text("Valid log content")
        # Should not raise exception
        self.migrator.validate_input_file(valid_file)


class TestMigrationIntegration:
    """Test end-to-end migration functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.migrator = LogMigrator(logs_dir=str(self.temp_path), verbose=False)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_migration_dry_run(self):
        """Test complete migration in dry run mode."""
        # Create sample log file
        input_file = self.temp_path / "test.log"
        log_content = """2025-09-27 10:30:15,678 - INFO - Advanced YAMNet Bark Detector v3.0
2025-09-27 10:30:16,123 - INFO - YAMNet model downloaded successfully!
2025-09-27 11:30:15,890 - INFO - Starting violation analysis for date: 2025-09-26
2025-09-27 11:32:47,456 - INFO - Analysis complete: 3 violations detected
2025-09-28 09:15:23,445 - INFO - Starting manual recording session
2025-09-28 10:45:12,234 - INFO - PDF report generated: reports/report.pdf"""

        input_file.write_text(log_content)

        # Run dry run migration
        summary = self.migrator.migrate_logs(input_file, dry_run=True)

        # Verify summary
        assert summary.total_lines_processed == 6
        assert summary.malformed_lines == 0
        assert summary.classification_stats['detection_entries'] == 3
        assert summary.classification_stats['analysis_entries'] == 3
        assert summary.date_range['earliest_date'] == '2025-09-27'
        assert summary.date_range['latest_date'] == '2025-09-28'

        # No files should be created in dry run
        assert len(summary.output_files_created) == 0

    def test_full_migration_execution(self):
        """Test complete migration execution."""
        # Create sample log file
        input_file = self.temp_path / "test.log"
        log_content = """2025-09-27 10:30:15,678 - INFO - YAMNet model loaded
2025-09-27 11:30:15,890 - INFO - Starting violation analysis
2025-09-28 09:15:23,445 - INFO - Recording session started"""

        input_file.write_text(log_content)

        # Run actual migration
        summary = self.migrator.migrate_logs(input_file, dry_run=False)

        # Verify files were created
        assert len(summary.output_files_created) > 0

        # Check specific files exist
        detection_file_27 = self.temp_path / "2025-09-27" / "2025-09-27_detection.log"
        analysis_file_27 = self.temp_path / "2025-09-27" / "2025-09-27_analysis.log"
        detection_file_28 = self.temp_path / "2025-09-28" / "2025-09-28_detection.log"

        assert detection_file_27.exists()
        assert analysis_file_27.exists()
        assert detection_file_28.exists()

        # Verify content
        assert "YAMNet model loaded" in detection_file_27.read_text()
        assert "violation analysis" in analysis_file_27.read_text()
        assert "Recording session" in detection_file_28.read_text()

        # Verify backup was created
        assert summary.backup_file
        backup_path = Path(summary.backup_file)
        assert backup_path.exists()

    def test_migration_with_malformed_lines(self):
        """Test migration with some malformed log lines."""
        input_file = self.temp_path / "test.log"
        log_content = """2025-09-27 10:30:15,678 - INFO - Valid log line
This is a malformed line without timestamp
2025-09-27 11:30:15,890 - INFO - Another valid line
Invalid line format here too
2025-09-27 12:30:15,123 - INFO - Final valid line"""

        input_file.write_text(log_content)

        # Migration with continue_on_error should handle malformed lines
        self.migrator.continue_on_error = True
        summary = self.migrator.migrate_logs(input_file, dry_run=True)

        assert summary.total_lines_processed == 5
        assert summary.malformed_lines == 2
        assert len(summary.warnings) == 2
        assert summary.classification_stats['detection_entries'] == 3

    def test_migration_summary_json_generation(self):
        """Test that migration summary JSON is properly generated."""
        input_file = self.temp_path / "test.log"
        log_content = "2025-09-27 10:30:15,678 - INFO - Test message"
        input_file.write_text(log_content)

        summary = self.migrator.migrate_logs(input_file, dry_run=False)

        # Check for summary JSON file
        summary_files = list(self.temp_path.glob("migration_summary_*.json"))
        assert len(summary_files) == 1

        # Verify JSON content
        with open(summary_files[0]) as f:
            summary_data = json.load(f)

        assert summary_data['total_lines_processed'] == 1
        assert input_file.name in summary_data['input_file']  # Backup filename includes original name
        assert 'migration_timestamp' in summary_data
        assert 'classification_stats' in summary_data


class TestChannelClassificationKeywords:
    """Test the keyword-based channel classification logic."""

    def setup_method(self):
        """Setup for each test method."""
        self.migrator = LogMigrator()

    def test_detection_keywords_classification(self):
        """Test all detection keywords are properly classified."""
        detection_messages = [
            "YAMNet model downloaded successfully",
            "Starting manual recording session",
            "Recording saved to file",
            "Calibration mode activated",
            "Profile settings loaded",
            "Audio conversion started",
            "Real-time detection initiated",
            "Bark detected at timestamp",
            "Session started successfully",
            "Configuration loaded from config.json",
            "Detector started with sensitivity 0.5",
            "Audio device initialized"
        ]

        for message in detection_messages:
            entry = LogEntry(datetime.now(), "INFO", message, "")
            channel = self.migrator.classify_by_channel(entry)
            assert channel == 'detection', f"Message '{message}' should be detection channel"

    def test_analysis_keywords_classification(self):
        """Test all analysis keywords are properly classified."""
        analysis_messages = [
            "Starting violation analysis for date 2025-09-27",
            "Analysis complete: 5 violations found",
            "Total violations detected: 3",
            "PDF report generated successfully",
            "Report generated in reports/ directory",
            "Exporting violations to CSV file",
            "Violation report created for date",
            "Enhanced report processing complete",
            "CSV export finished successfully"
        ]

        for message in analysis_messages:
            entry = LogEntry(datetime.now(), "INFO", message, "")
            channel = self.migrator.classify_by_channel(entry)
            assert channel == 'analysis', f"Message '{message}' should be analysis channel"

    def test_case_insensitive_classification(self):
        """Test that keyword matching is case-insensitive."""
        mixed_case_messages = [
            "YAMNET Model downloaded",
            "violation ANALYSIS started",
            "PDF REPORT generated",
            "audio CONVERSION complete"
        ]

        expected_channels = ['detection', 'analysis', 'analysis', 'detection']

        for message, expected in zip(mixed_case_messages, expected_channels):
            entry = LogEntry(datetime.now(), "INFO", message, "")
            channel = self.migrator.classify_by_channel(entry)
            assert channel == expected, f"Message '{message}' should be {expected} channel"