"""Integration tests for the CLI violation report functionality"""

import pytest
import tempfile
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from bark_detector.legal.models import Violation, PersistedBarkEvent
from bark_detector.utils.pdf_generator import PDFGenerationService


class TestCLIViolationReport:
    """Test CLI violation report functionality"""

    @pytest.fixture
    def mock_detector(self):
        """Mock detector with analyze_violations_for_date method"""
        mock = Mock()
        mock.analyze_violations_for_date = Mock()
        return mock

    @pytest.fixture
    def sample_violations(self):
        """Sample violation data for testing"""
        return [
            Violation(
                type="Continuous",
                startTimestamp="2025-01-15T10:00:00Z",
                violationTriggerTimestamp="2025-01-15T10:05:00Z",
                endTimestamp="2025-01-15T10:05:30Z",
                durationMinutes=5.5,
                violationDurationMinutes=0.5,
                barkEventIds=["bark-1", "bark-2", "bark-3"]
            )
        ]

    @pytest.fixture
    def sample_bark_events(self):
        """Sample bark event data for testing"""
        return [
            PersistedBarkEvent(
                realworld_date="2025-01-15",
                realworld_time="10:00:00",
                bark_id="bark-1",
                bark_type="bark",
                confidence=0.85,
                intensity=0.7,
                audio_file_name="recording_20250115_100000.wav"
            ),
            PersistedBarkEvent(
                realworld_date="2025-01-15",
                realworld_time="10:02:30",
                bark_id="bark-2",
                bark_type="bark",
                confidence=0.92,
                intensity=0.8,
                audio_file_name="recording_20250115_100000.wav"
            )
        ]

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_with_existing_analysis(self, mock_detector_class, tmp_path):
        """Test violation report generation when analysis file already exists"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        # Setup test directory structure
        violations_dir = tmp_path / "violations" / "2025-01-15"
        violations_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = tmp_path / "reports"

        # Create existing violations file
        violations_data = [{
            "type": "Continuous",
            "startTimestamp": "2025-01-15T10:00:00Z",
            "violationTriggerTimestamp": "2025-01-15T10:05:00Z",
            "endTimestamp": "2025-01-15T10:05:30Z",
            "durationMinutes": 5.5,
            "violationDurationMinutes": 0.5,
            "barkEventIds": ["bark-1", "bark-2"]
        }]

        violations_file = violations_dir / "2025-01-15_violations.json"
        with open(violations_file, 'w') as f:
            json.dump(violations_data, f)

        # Create existing events file
        events_data = [{
            "realworld_date": "2025-01-15",
            "realworld_time": "10:00:00",
            "bark_id": "bark-1",
            "bark_type": "bark",
            "confidence": 0.85,
            "intensity": 0.7,
            "audio_file_name": "recording_20250115_100000.wav"
        }]

        events_file = violations_dir / "2025-01-15_events.json"
        with open(events_file, 'w') as f:
            json.dump(events_data, f)

        # Mock PDF generation service
        with patch('bark_detector.cli.PDFGenerationService') as mock_pdf_service_class:
            mock_pdf_service = Mock()
            mock_pdf_service_class.return_value = mock_pdf_service

            expected_pdf_path = reports_dir / "2025-01-15_Violation_Report.pdf"
            mock_pdf_service.generate_pdf_from_date.return_value = expected_pdf_path

            # Mock path exists to simulate successful PDF creation
            with patch.object(Path, 'exists') as mock_exists:
                mock_exists.return_value = True

                # Mock sys.argv and run CLI
                test_args = ['bark_detector', '--violation-report', '2025-01-15']

                with patch('sys.argv', test_args), \
                     patch('bark_detector.cli.Path') as mock_path_class:

                    # Setup Path mocking
                    mock_path_class.side_effect = lambda p: Path(str(tmp_path / p)) if isinstance(p, str) and not p.startswith('/') else Path(p)

                    with patch('bark_detector.cli.logger') as mock_logger:
                        result = main()

                        # Verify no analysis was triggered (file already existed)
                        mock_detector.analyze_violations_for_date.assert_not_called()

                        # Verify PDF generation was called
                        mock_pdf_service.generate_pdf_from_date.assert_called_once()

                        # Verify success messages
                        assert any("PDF violation report generated" in str(call) for call in mock_logger.info.call_args_list)

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_with_automatic_analysis(self, mock_detector_class, tmp_path, sample_violations):
        """Test violation report generation when analysis is run automatically"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.analyze_violations_for_date.return_value = sample_violations

        # Setup test directory structure (no existing violations file)
        violations_dir = tmp_path / "violations" / "2025-01-15"
        violations_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = tmp_path / "reports"

        # Mock PDF generation service
        with patch('bark_detector.cli.PDFGenerationService') as mock_pdf_service_class:
            mock_pdf_service = Mock()
            mock_pdf_service_class.return_value = mock_pdf_service

            expected_pdf_path = reports_dir / "2025-01-15_Violation_Report.pdf"
            mock_pdf_service.generate_pdf_from_date.return_value = expected_pdf_path

            # Mock path exists to simulate successful PDF creation
            with patch.object(Path, 'exists') as mock_exists:
                mock_exists.return_value = True

                test_args = ['bark_detector', '--violation-report', '2025-01-15']

                with patch('sys.argv', test_args), \
                     patch('bark_detector.cli.Path') as mock_path_class:

                    # Setup Path mocking
                    mock_path_class.side_effect = lambda p: Path(str(tmp_path / p)) if isinstance(p, str) and not p.startswith('/') else Path(p)

                    with patch('bark_detector.cli.logger') as mock_logger:
                        result = main()

                        # Verify analysis was triggered
                        mock_detector.analyze_violations_for_date.assert_called_once_with('2025-01-15')

                        # Verify PDF generation was called
                        mock_pdf_service.generate_pdf_from_date.assert_called_once()

                        # Verify automatic analysis message was logged
                        assert any("Automatically running violation analysis" in str(call) for call in mock_logger.info.call_args_list)
                        assert any("Analysis complete. Found 1 violations" in str(call) for call in mock_logger.info.call_args_list)

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_no_violations_found(self, mock_detector_class, tmp_path):
        """Test violation report when no violations are found"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.analyze_violations_for_date.return_value = []  # No violations

        # Setup test directory structure (no existing violations file)
        violations_dir = tmp_path / "violations" / "2025-01-15"
        violations_dir.mkdir(parents=True, exist_ok=True)

        test_args = ['bark_detector', '--violation-report', '2025-01-15']

        with patch('sys.argv', test_args), \
             patch('bark_detector.cli.Path') as mock_path_class:

            # Setup Path mocking
            mock_path_class.side_effect = lambda p: Path(str(tmp_path / p)) if isinstance(p, str) and not p.startswith('/') else Path(p)

            with patch('bark_detector.cli.logger') as mock_logger:
                result = main()

                # Verify analysis was triggered
                mock_detector.analyze_violations_for_date.assert_called_once_with('2025-01-15')

                # Verify appropriate message for no violations
                assert any("No violations found for 2025-01-15. Skipping PDF generation" in str(call) for call in mock_logger.info.call_args_list)

                # Should return 0 (success) even with no violations
                assert result == 0

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_invalid_date_format(self, mock_detector_class):
        """Test violation report with invalid date format"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        test_args = ['bark_detector', '--violation-report', 'invalid-date']

        with patch('sys.argv', test_args):
            with patch('bark_detector.cli.logger') as mock_logger:
                result = main()

                # Should not trigger analysis with invalid date
                mock_detector.analyze_violations_for_date.assert_not_called()

                # Should log error message
                assert any("Invalid date format" in str(call) for call in mock_logger.error.call_args_list)

                # Should return error code
                assert result == 1

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_analysis_failure(self, mock_detector_class, tmp_path):
        """Test violation report when analysis fails"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.analyze_violations_for_date.return_value = None  # Analysis failure

        # Setup test directory structure (no existing violations file)
        violations_dir = tmp_path / "violations" / "2025-01-15"
        violations_dir.mkdir(parents=True, exist_ok=True)

        test_args = ['bark_detector', '--violation-report', '2025-01-15']

        with patch('sys.argv', test_args), \
             patch('bark_detector.cli.Path') as mock_path_class:

            # Setup Path mocking
            mock_path_class.side_effect = lambda p: Path(str(tmp_path / p)) if isinstance(p, str) and not p.startswith('/') else Path(p)

            with patch('bark_detector.cli.logger') as mock_logger:
                result = main()

                # Verify analysis was triggered
                mock_detector.analyze_violations_for_date.assert_called_once_with('2025-01-15')

                # Should log failure message
                assert any("Failed to run violation analysis" in str(call) for call in mock_logger.error.call_args_list)

                # Should return error code
                assert result == 1

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_enhanced_violation_report_deprecation_warning(self, mock_detector_class):
        """Test that enhanced violation report shows deprecation warning"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        test_args = ['bark_detector', '--enhanced-violation-report', '2025-01-15']

        with patch('sys.argv', test_args):
            with patch('bark_detector.cli.logger') as mock_logger:
                # This will likely fail due to missing dependencies, but we only care about the warning
                try:
                    result = main()
                except:
                    pass  # Ignore other failures, we only want to test the deprecation warning

                # Check that deprecation warnings were logged
                warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
                assert any("DEPRECATION WARNING" in call for call in warning_calls)
                assert any("enhanced-violation-report is deprecated" in call for call in warning_calls)
                assert any("use --violation-report YYYY-MM-DD instead" in call for call in warning_calls)

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_pdf_generation_failure(self, mock_detector_class, tmp_path, sample_violations):
        """Test violation report when PDF generation fails"""
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.analyze_violations_for_date.return_value = sample_violations

        # Setup test directory structure
        violations_dir = tmp_path / "violations" / "2025-01-15"
        violations_dir.mkdir(parents=True, exist_ok=True)

        # Mock PDF generation service to return None (failure)
        with patch('bark_detector.cli.PDFGenerationService') as mock_pdf_service_class:
            mock_pdf_service = Mock()
            mock_pdf_service_class.return_value = mock_pdf_service
            mock_pdf_service.generate_pdf_from_date.return_value = None  # PDF generation failure

            test_args = ['bark_detector', '--violation-report', '2025-01-15']

            with patch('sys.argv', test_args), \
                 patch('bark_detector.cli.Path') as mock_path_class:

                # Setup Path mocking
                mock_path_class.side_effect = lambda p: Path(str(tmp_path / p)) if isinstance(p, str) and not p.startswith('/') else Path(p)

                with patch('bark_detector.cli.logger') as mock_logger:
                    result = main()

                    # Verify analysis was triggered
                    mock_detector.analyze_violations_for_date.assert_called_once_with('2025-01-15')

                    # Verify PDF generation was attempted
                    mock_pdf_service.generate_pdf_from_date.assert_called_once()

                    # Should log failure message
                    assert any("Failed to generate PDF report" in str(call) for call in mock_logger.error.call_args_list)

                    # Should return error code
                    assert result == 1