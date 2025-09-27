"""Simple integration tests for the CLI violation report functionality"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock
import sys
import os

# Get the root directory for running CLI commands
ROOT_DIR = Path(__file__).parent.parent.parent


class TestCLIViolationReportSimple:
    """Simple CLI violation report tests"""

    def test_cli_help_shows_violation_report_option(self):
        """Test that CLI help shows the violation report option"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR
        )

        assert result.returncode == 0
        assert "--violation-report" in result.stdout
        assert "Generate PDF violation report" in result.stdout

    def test_cli_violation_report_invalid_date_format(self):
        """Test CLI with invalid date format returns error"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--violation-report", "invalid-date"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR
        )

        # Should exit with error code
        assert result.returncode == 1
        # Should contain date format error message
        assert "Invalid date format" in result.stderr or "Invalid date format" in result.stdout

    def test_enhanced_violation_report_shows_deprecation_warning(self):
        """Test that enhanced violation report shows deprecation warning"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--enhanced-violation-report", "2025-01-15"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            timeout=10  # Timeout to avoid hanging
        )

        # The command might fail due to missing log files, but we should see deprecation warning
        output = result.stdout + result.stderr
        assert "DEPRECATION WARNING" in output
        assert "enhanced-violation-report is deprecated" in output
        assert "use --violation-report YYYY-MM-DD instead" in output


@pytest.mark.unit
class TestCLIArgumentParsing:
    """Unit tests for argument parsing logic"""

    def test_violation_report_parser_integration(self):
        """Test that the CLI argument parser correctly handles violation-report"""
        from bark_detector.cli import parse_arguments

        # Mock sys.argv for the test
        test_args = ["bark_detector", "--violation-report", "2025-01-15"]

        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
            assert args.violation_report == "2025-01-15"

    def test_enhanced_violation_report_parser_integration(self):
        """Test that the CLI argument parser correctly handles enhanced-violation-report"""
        from bark_detector.cli import parse_arguments

        # Mock sys.argv for the test
        test_args = ["bark_detector", "--enhanced-violation-report", "2025-01-15"]

        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
            assert args.enhanced_violation_report == "2025-01-15"


@pytest.mark.unit
class TestViolationReportLogic:
    """Unit tests for the core violation report logic"""

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_date_validation(self, mock_detector):
        """Test that violation report validates date format correctly"""
        from bark_detector.cli import main

        # Mock detector
        mock_detector_instance = Mock()
        mock_detector.return_value = mock_detector_instance

        # Test with invalid date format
        test_args = ["bark_detector", "--violation-report", "invalid-date"]

        with patch.object(sys, 'argv', test_args):
            # We need to patch the logger at the module level, not the setup_logging result
            with patch('bark_detector.cli.setup_logging') as mock_setup_logging:
                mock_logger = Mock()
                mock_setup_logging.return_value = mock_logger

                result = main()

                # Should return error code
                assert result == 1

                # Should have called error logging (test passes if the error was logged)
                assert mock_logger.error.called

    @patch('bark_detector.cli.AdvancedBarkDetector')
    def test_violation_report_empty_results_handling(self, mock_detector):
        """Test that violation report handles empty results gracefully"""
        from bark_detector.cli import main

        # Mock detector to return empty violations
        mock_detector_instance = Mock()
        mock_detector_instance.analyze_violations_for_date.return_value = []
        mock_detector.return_value = mock_detector_instance

        test_args = ["bark_detector", "--violation-report", "2025-01-15"]

        with patch.object(sys, 'argv', test_args):
            # Mock all the service dependencies to focus on the logic
            with patch('bark_detector.legal.database.ViolationDatabase') as mock_viol_db, \
                 patch('bark_detector.utils.pdf_generator.PDFGenerationService') as mock_pdf_service, \
                 patch('pathlib.Path') as mock_path_class:

                # Setup the mock path for the violations file
                mock_violation_file = Mock()
                mock_violation_file.exists.return_value = False

                # Create mock for Path() calls
                mock_violations_dir = Mock()
                mock_violations_dir.__truediv__ = Mock(side_effect=lambda x: Mock(__truediv__=Mock(return_value=mock_violation_file)))
                mock_reports_dir = Mock()
                mock_reports_dir.mkdir = Mock()

                def path_side_effect(path_str):
                    if path_str == 'violations':
                        return mock_violations_dir
                    elif path_str == 'reports':
                        return mock_reports_dir
                    return Mock()

                mock_path_class.side_effect = path_side_effect

                with patch('bark_detector.cli.setup_logging') as mock_setup_logging:
                    mock_logger = Mock()
                    mock_setup_logging.return_value = mock_logger

                    result = main()

                    # Should return success code (0) even with no violations
                    assert result == 0

                    # Should have logged info messages
                    assert mock_logger.info.called

    def test_enhanced_violation_report_deprecation_warning_unit(self):
        """Test deprecation warning logic for enhanced violation report"""
        from bark_detector.cli import main

        test_args = ["bark_detector", "--enhanced-violation-report", "2025-01-15"]

        with patch.object(sys, 'argv', test_args):
            # Mock other dependencies to avoid errors, we only care about deprecation warning
            with patch('bark_detector.cli.AdvancedBarkDetector'), \
                 patch('bark_detector.utils.report_generator.LogBasedReportGenerator'), \
                 patch('datetime.datetime') as mock_datetime:

                # Configure datetime mock to return proper date object
                from datetime import date
                mock_datetime.strptime.return_value.date.return_value = date(2025, 1, 15)

                # Use setup_logging mock to capture the logger warnings
                with patch('bark_detector.cli.setup_logging') as mock_setup_logging:
                    mock_logger = Mock()
                    mock_setup_logging.return_value = mock_logger

                    try:
                        result = main()
                    except:
                        pass  # Ignore other errors, we only want to test the warning

                    # Check that deprecation warnings were logged
                    warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
                    assert any("DEPRECATION WARNING" in call for call in warning_calls)
                    assert any("enhanced-violation-report is deprecated" in call for call in warning_calls)
                    assert any("use --violation-report YYYY-MM-DD instead" in call for call in warning_calls)