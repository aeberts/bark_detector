"""Tests for channel-specific logging functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from bark_detector.utils.helpers import (
    setup_logging, get_detection_logger, get_analysis_logger,
    _resolve_logs_directory, _validate_directory_path, _generate_log_filename
)
from bark_detector.utils.config import BarkDetectorConfig, OutputConfig
from bark_detector.cli import determine_logging_channel


class TestChannelSpecificLogging:
    """Test channel-specific logging functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logging_detection_channel(self):
        """Test setup_logging with detection channel creates correct filename."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path)

        logger = setup_logging(
            channel='detection',
            config=config,
            use_date_folders=True
        )

        # Check that today's detection log file was created
        today = datetime.now().strftime('%Y-%m-%d')
        expected_file = self.temp_path / today / f"{today}_detection.log"
        assert expected_file.exists()

    def test_setup_logging_analysis_channel(self):
        """Test setup_logging with analysis channel creates correct filename."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path)

        logger = setup_logging(
            channel='analysis',
            config=config,
            use_date_folders=True
        )

        # Check that today's analysis log file was created
        today = datetime.now().strftime('%Y-%m-%d')
        expected_file = self.temp_path / today / f"{today}_analysis.log"
        assert expected_file.exists()

    def test_setup_logging_minimal_mode(self):
        """Test setup_logging in minimal mode for startup."""
        logger = setup_logging(minimal=True)

        # Should return a logger without creating files
        assert logger is not None
        # No files should be created in minimal mode

    def test_get_detection_logger(self):
        """Test get_detection_logger helper function."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path)

        logger = get_detection_logger(config)

        # Check that detection log file was created
        today = datetime.now().strftime('%Y-%m-%d')
        expected_file = self.temp_path / today / f"{today}_detection.log"
        assert expected_file.exists()

    def test_get_analysis_logger(self):
        """Test get_analysis_logger helper function."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path)

        logger = get_analysis_logger(config)

        # Check that analysis log file was created
        today = datetime.now().strftime('%Y-%m-%d')
        expected_file = self.temp_path / today / f"{today}_analysis.log"
        assert expected_file.exists()

    def test_legacy_flat_file_mode(self):
        """Test backward compatibility with flat file mode."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path)

        logger = setup_logging(
            channel='detection',
            config=config,
            use_date_folders=False
        )

        # Should create flat file in logs directory
        expected_file = self.temp_path / "bark_detector.log"
        assert expected_file.exists()

    def test_legacy_flat_file_mode_analysis(self):
        """Test backward compatibility with flat file mode for analysis."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path)

        logger = setup_logging(
            channel='analysis',
            config=config,
            use_date_folders=False
        )

        # Should create flat file in logs directory
        expected_file = self.temp_path / "bark_detector_analysis.log"
        assert expected_file.exists()


class TestLogsDirectoryResolution:
    """Test 3-tier priority resolution for logs directory."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_explicit_parameter_priority(self):
        """Test explicit logs_dir parameter has highest priority."""
        config = BarkDetectorConfig()
        config.output.logs_dir = "config_logs"

        explicit_dir = str(self.temp_path / "explicit_logs")
        result = _resolve_logs_directory(explicit_dir, config)

        assert "explicit_logs" in result

    def test_config_parameter_priority(self):
        """Test config.output.logs_dir has second priority."""
        config = BarkDetectorConfig()
        config_dir = str(self.temp_path / "config_logs")
        config.output.logs_dir = config_dir

        result = _resolve_logs_directory(None, config)

        assert "config_logs" in result

    def test_default_fallback_priority(self):
        """Test default 'logs' directory as fallback."""
        result = _resolve_logs_directory(None, None)
        assert result == "logs"

    def test_config_without_logs_dir(self):
        """Test config object without logs_dir attribute."""
        config = Mock()
        config.output = Mock()
        config.output.logs_dir = None

        result = _resolve_logs_directory(None, config)
        assert result == "logs"


class TestPathValidation:
    """Test path validation functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_absolute_path_validation(self):
        """Test validation of absolute paths."""
        abs_path = str(self.temp_path / "absolute_logs")
        result = _validate_directory_path(abs_path)

        assert Path(result).is_absolute()
        assert Path(result).exists()

    def test_relative_path_validation(self):
        """Test validation of relative paths."""
        # Create a temporary subdirectory for relative path testing
        rel_dir = "relative_logs"
        with patch('pathlib.Path.cwd', return_value=self.temp_path):
            result = _validate_directory_path(rel_dir)

        expected_path = self.temp_path / rel_dir
        assert str(expected_path) == result
        assert expected_path.exists()

    def test_invalid_directory_path(self):
        """Test validation with invalid directory path."""
        invalid_path = "/nonexistent/root/path/that/cannot/be/created"

        with pytest.raises(ValueError, match="Invalid logs directory"):
            _validate_directory_path(invalid_path)


class TestFilenameGeneration:
    """Test log filename generation."""

    def test_channel_filename_with_date_folders(self):
        """Test filename generation with date folders enabled."""
        today = datetime.now().strftime('%Y-%m-%d')

        # Test detection channel
        result = _generate_log_filename('detection', None, True)
        assert result == f"{today}_detection.log"

        # Test analysis channel
        result = _generate_log_filename('analysis', None, True)
        assert result == f"{today}_analysis.log"

    def test_legacy_filename_without_date_folders(self):
        """Test filename generation with date folders disabled (legacy mode)."""
        # Test detection channel (legacy default)
        result = _generate_log_filename('detection', None, False)
        assert result == "bark_detector.log"

        # Test analysis channel
        result = _generate_log_filename('analysis', None, False)
        assert result == "bark_detector_analysis.log"

    def test_custom_filename_override(self):
        """Test custom filename override."""
        custom_name = "custom_log.log"

        result = _generate_log_filename('detection', custom_name, True)
        assert result == custom_name

        result = _generate_log_filename('analysis', custom_name, False)
        assert result == custom_name


class TestChannelDetermination:
    """Test CLI channel determination logic."""

    def test_analysis_commands_detection(self):
        """Test that analysis commands are detected correctly."""
        # Mock args object with analysis command
        args = Mock()
        args.analyze_violations = True
        args.violation_report = False
        args.export_violations = False
        args.list_violations = False
        args.enhanced_violation_report = False

        result = determine_logging_channel(args)
        assert result == 'analysis'

    def test_detection_commands_default(self):
        """Test that non-analysis commands default to detection."""
        # Mock args object without analysis commands
        args = Mock()
        args.analyze_violations = False
        args.violation_report = False
        args.export_violations = False
        args.list_violations = False
        args.enhanced_violation_report = False

        result = determine_logging_channel(args)
        assert result == 'detection'

    def test_multiple_analysis_commands(self):
        """Test multiple analysis commands still return analysis."""
        args = Mock()
        args.analyze_violations = True
        args.violation_report = True
        args.export_violations = False
        args.list_violations = False
        args.enhanced_violation_report = False

        result = determine_logging_channel(args)
        assert result == 'analysis'

    def test_violation_report_command(self):
        """Test violation report command is classified as analysis."""
        args = Mock()
        args.analyze_violations = False
        args.violation_report = True
        args.export_violations = False
        args.list_violations = False
        args.enhanced_violation_report = False

        result = determine_logging_channel(args)
        assert result == 'analysis'


class TestConfigurationIntegration:
    """Test configuration integration with logging."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_logs_dir_respected(self):
        """Test that config.output.logs_dir is properly respected."""
        config = BarkDetectorConfig()
        custom_logs_dir = str(self.temp_path / "custom_logs")
        config.output.logs_dir = custom_logs_dir

        logger = setup_logging(channel='detection', config=config)

        # Check that log was created in custom directory
        today = datetime.now().strftime('%Y-%m-%d')
        expected_file = Path(custom_logs_dir) / today / f"{today}_detection.log"
        assert expected_file.exists()

    def test_explicit_logs_dir_overrides_config(self):
        """Test that explicit logs_dir parameter overrides config."""
        config = BarkDetectorConfig()
        config.output.logs_dir = str(self.temp_path / "config_logs")

        explicit_logs_dir = str(self.temp_path / "explicit_logs")

        logger = setup_logging(
            channel='detection',
            config=config,
            logs_dir=explicit_logs_dir
        )

        # Check that log was created in explicit directory, not config directory
        today = datetime.now().strftime('%Y-%m-%d')
        expected_file = Path(explicit_logs_dir) / today / f"{today}_detection.log"
        assert expected_file.exists()

        # Config directory should not be used
        config_file = Path(config.output.logs_dir) / today / f"{today}_detection.log"
        assert not config_file.exists()


class TestErrorHandling:
    """Test error handling in logging setup."""

    def test_invalid_logs_dir_fallback(self):
        """Test handling of invalid logs directory with fallback."""
        # This test would need to be implemented with proper error handling
        # in the actual logging setup that allows graceful fallback
        pass

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        # This test would simulate permission errors
        # and verify appropriate error messages
        pass