"""Tests for configuration management system"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from bark_detector.utils.config import (
    ConfigManager, BarkDetectorConfig, DetectionConfig, 
    OutputConfig, CalibrationConfig, SchedulingConfig, LegalConfig
)


class TestDetectionConfig:
    """Test detection configuration data class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = DetectionConfig()
        assert config.sensitivity == 0.68
        assert config.analysis_sensitivity == 0.30
        assert config.sample_rate == 16000
        assert config.chunk_size == 1024
        assert config.channels == 1
        assert config.quiet_duration == 30.0
        assert config.session_gap_threshold == 10.0
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = DetectionConfig(
            sensitivity=0.5,
            analysis_sensitivity=0.25,
            sample_rate=22050,
            quiet_duration=60.0
        )
        assert config.sensitivity == 0.5
        assert config.analysis_sensitivity == 0.25
        assert config.sample_rate == 22050
        assert config.quiet_duration == 60.0

    def test_analysis_sensitivity_independence(self):
        """Test that sensitivity and analysis_sensitivity can be set independently."""
        config = DetectionConfig(sensitivity=0.8, analysis_sensitivity=0.2)
        assert config.sensitivity == 0.8
        assert config.analysis_sensitivity == 0.2


class TestOutputConfig:
    """Test output configuration data class."""
    
    def test_default_values(self):
        """Test default output directory values."""
        config = OutputConfig()
        assert config.recordings_dir == "recordings"
        assert config.reports_dir == "reports"
        assert config.logs_dir == "logs"
        assert config.profiles_dir == "profiles"


class TestCalibrationConfig:
    """Test calibration configuration data class."""
    
    def test_default_values(self):
        """Test default calibration values."""
        config = CalibrationConfig()
        assert config.default_profile is None
        assert config.sensitivity_range == [0.01, 0.5]
        assert config.calibration_steps == 20
    
    def test_post_init_sensitivity_range(self):
        """Test sensitivity range initialization."""
        config = CalibrationConfig(sensitivity_range=None)
        assert config.sensitivity_range == [0.01, 0.5]


class TestLegalConfig:
    """Test legal configuration data class."""

    def test_default_values(self):
        """Test default legal configuration values."""
        config = LegalConfig()
        assert config.constant_violation_duration == 300  # 5 minutes
        assert config.intermittent_violation_duration == 900    # 15 minutes
        assert config.intermittent_gap_threshold == 300  # 5 minutes
        assert config.constant_gap_threshold == 10.0  # 10 seconds

    def test_custom_values(self):
        """Test custom legal configuration values."""
        config = LegalConfig(
            constant_violation_duration=600,  # 10 minutes
            intermittent_violation_duration=1200,   # 20 minutes
            intermittent_gap_threshold=180,  # 3 minutes
            constant_gap_threshold=15.0  # 15 seconds
        )
        assert config.constant_violation_duration == 600
        assert config.intermittent_violation_duration == 1200
        assert config.intermittent_gap_threshold == 180
        assert config.constant_gap_threshold == 15.0


class TestBarkDetectorConfig:
    """Test main configuration container."""
    
    def test_default_initialization(self):
        """Test default config initialization."""
        config = BarkDetectorConfig()
        assert isinstance(config.detection, DetectionConfig)
        assert isinstance(config.output, OutputConfig)
        assert isinstance(config.calibration, CalibrationConfig)
        assert isinstance(config.scheduling, SchedulingConfig)
        assert isinstance(config.legal, LegalConfig)
    
    def test_custom_subconfigs(self):
        """Test initialization with custom sub-configs."""
        detection = DetectionConfig(sensitivity=0.5)
        config = BarkDetectorConfig(detection=detection)
        assert config.detection.sensitivity == 0.5


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.test_config_data = {
            "detection": {
                "sensitivity": 0.75,
                "sample_rate": 16000,
                "quiet_duration": 45.0
            },
            "output": {
                "recordings_dir": "test_recordings",
                "reports_dir": "test_reports"
            },
            "calibration": {
                "calibration_steps": 15
            }
        }
    
    def test_load_config_no_file_uses_defaults(self):
        """Test loading config when no file exists uses defaults."""
        with patch.object(Path, 'exists', return_value=False):
            config = self.config_manager.load_config()
            assert config.detection.sensitivity == 0.68  # Default value
            assert config.output.recordings_dir == "recordings"
    
    def test_load_config_from_explicit_path(self):
        """Test loading config from explicit path."""
        test_path = Path("test_config.json")
        config_json = json.dumps(self.test_config_data)
        
        with patch.object(Path, 'exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=config_json)):
            config = self.config_manager.load_config(test_path)
            assert config.detection.sensitivity == 0.75
            assert config.detection.quiet_duration == 45.0
            assert config.output.recordings_dir == "test_recordings"
    
    def test_load_config_file_not_found_raises_error(self):
        """Test loading non-existent explicit config file raises error."""
        with pytest.raises(FileNotFoundError):
            self.config_manager.load_config("nonexistent.json")
    
    def test_load_config_invalid_json_raises_error(self):
        """Test loading invalid JSON raises ValueError."""
        test_path = Path("test_config.json")
        invalid_json = "{ invalid json }"
        
        with patch.object(Path, 'exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=invalid_json)):
            with pytest.raises(ValueError, match="Invalid JSON"):
                self.config_manager.load_config(test_path)
    
    def test_dict_to_config_validation(self):
        """Test configuration validation during loading."""
        # Test sensitivity validation
        invalid_data = {"detection": {"sensitivity": 2.0}}  # > 1.0
        
        with pytest.raises(ValueError, match="sensitivity.*between"):
            self.config_manager._dict_to_config(invalid_data)
    
    def test_dict_to_config_partial_data(self):
        """Test loading partial configuration data."""
        partial_data = {"detection": {"sensitivity": 0.5}}
        config = self.config_manager._dict_to_config(partial_data)
        
        # Modified value
        assert config.detection.sensitivity == 0.5
        # Default values for unspecified fields
        assert config.detection.sample_rate == 16000
        assert config.output.recordings_dir == "recordings"
    
    @patch("builtins.open", new_callable=mock_open)
    @patch.object(Path, 'mkdir')
    def test_save_config(self, mock_mkdir, mock_file):
        """Test saving configuration to file."""
        config = BarkDetectorConfig()
        config.detection.sensitivity = 0.5
        
        self.config_manager.save_config(config, "test_config.json")
        
        # Verify file operations
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once_with(Path("test_config.json"), 'w')
        
        # Verify JSON content was written
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        saved_data = json.loads(written_content)
        assert saved_data["detection"]["sensitivity"] == 0.5
    
    @patch("builtins.open", new_callable=mock_open)
    @patch.object(Path, 'mkdir')
    def test_create_default_config(self, mock_mkdir, mock_file):
        """Test creating default configuration file."""
        self.config_manager.create_default_config("default_config.json")
        
        # Verify file was created
        mock_file.assert_called_once_with(Path("default_config.json"), 'w')
        
        # Verify default values were written
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        saved_data = json.loads(written_content)
        assert saved_data["detection"]["sensitivity"] == 0.68  # Default
    
    def test_merge_cli_args_precedence(self):
        """Test that CLI args take precedence over config file."""
        config = BarkDetectorConfig()
        config.detection.sensitivity = 0.5
        config.output.recordings_dir = "config_recordings"
        
        # Mock CLI args
        class MockArgs:
            sensitivity = 0.8
            output_dir = "cli_recordings"
            profile = "test_profile"
        
        args = MockArgs()
        merged = self.config_manager.merge_cli_args(config, args)
        
        # CLI values should override config values
        assert merged.detection.sensitivity == 0.8
        assert merged.output.recordings_dir == "cli_recordings"
        assert merged.calibration.default_profile == "test_profile"
    
    def test_merge_cli_args_none_values_ignored(self):
        """Test that None CLI args don't override config values."""
        config = BarkDetectorConfig()
        config.detection.sensitivity = 0.5
        
        class MockArgs:
            sensitivity = None
            output_dir = None
            profile = None
        
        args = MockArgs()
        merged = self.config_manager.merge_cli_args(config, args)
        
        # Config values should be preserved when CLI args are None
        assert merged.detection.sensitivity == 0.5
    
    def test_validate_float_valid_range(self):
        """Test float validation with valid values."""
        result = self.config_manager._validate_float(0.5, 0.0, 1.0, "test")
        assert result == 0.5
    
    def test_validate_float_invalid_type(self):
        """Test float validation with invalid type."""
        with pytest.raises(ValueError, match="must be a number"):
            self.config_manager._validate_float("invalid", 0.0, 1.0, "test")
    
    def test_validate_float_out_of_range(self):
        """Test float validation with out of range values."""
        with pytest.raises(ValueError, match="must be between"):
            self.config_manager._validate_float(2.0, 0.0, 1.0, "test")
    
    def test_default_config_paths(self):
        """Test default configuration file search paths."""
        expected_paths = [
            Path("config.json"),
            Path.home() / ".bark_detector" / "config.json",
            Path("/etc/bark_detector/config.json")
        ]
        
        assert self.config_manager.DEFAULT_CONFIG_PATHS == expected_paths

    def test_analysis_sensitivity_default_value(self):
        """Test analysis_sensitivity defaults to 0.30 when not specified."""
        data = {"detection": {"sensitivity": 0.68}}
        config = self.config_manager._dict_to_config(data)

        assert config.detection.sensitivity == 0.68
        assert config.detection.analysis_sensitivity == 0.68  # Backward compatibility fallback

    def test_analysis_sensitivity_custom_value(self):
        """Test custom analysis_sensitivity values load correctly from config."""
        data = {
            "detection": {
                "sensitivity": 0.68,
                "analysis_sensitivity": 0.25
            }
        }
        config = self.config_manager._dict_to_config(data)

        assert config.detection.sensitivity == 0.68
        assert config.detection.analysis_sensitivity == 0.25

    def test_analysis_sensitivity_validation_range(self):
        """Test analysis_sensitivity validation with boundary testing."""
        # Valid values
        valid_data = {"detection": {"analysis_sensitivity": 0.1}}
        config = self.config_manager._dict_to_config(valid_data)
        assert config.detection.analysis_sensitivity == 0.1

        valid_data = {"detection": {"analysis_sensitivity": 1.0}}
        config = self.config_manager._dict_to_config(valid_data)
        assert config.detection.analysis_sensitivity == 1.0

        # Invalid values
        with pytest.raises(ValueError, match="analysis_sensitivity.*between"):
            invalid_data = {"detection": {"analysis_sensitivity": 0.09}}
            self.config_manager._dict_to_config(invalid_data)

        with pytest.raises(ValueError, match="analysis_sensitivity.*between"):
            invalid_data = {"detection": {"analysis_sensitivity": 1.01}}
            self.config_manager._dict_to_config(invalid_data)

    def test_backward_compatibility_analysis_sensitivity_fallback(self):
        """Test that when analysis_sensitivity not specified, it falls back to sensitivity value."""
        data = {"detection": {"sensitivity": 0.5}}
        config = self.config_manager._dict_to_config(data)

        assert config.detection.sensitivity == 0.5
        assert config.detection.analysis_sensitivity == 0.5  # Should fallback to sensitivity

    def test_config_schema_validation_dual_sensitivity(self):
        """Test JSON schema validates both sensitivity parameters correctly."""
        # Both parameters present
        data = {
            "detection": {
                "sensitivity": 0.68,
                "analysis_sensitivity": 0.30
            }
        }
        config = self.config_manager._dict_to_config(data)
        assert config.detection.sensitivity == 0.68
        assert config.detection.analysis_sensitivity == 0.30

    def test_configuration_edge_cases_analysis_sensitivity(self):
        """Test handling of null, empty, non-numeric analysis_sensitivity values."""
        # Null value should fallback to sensitivity
        data = {
            "detection": {
                "sensitivity": 0.68,
                "analysis_sensitivity": None
            }
        }
        config = self.config_manager._dict_to_config(data)
        assert config.detection.analysis_sensitivity == 0.68

        # Non-numeric value should raise error
        with pytest.raises(ValueError, match="must be a number"):
            invalid_data = {
                "detection": {
                    "sensitivity": 0.68,
                    "analysis_sensitivity": "invalid"
                }
            }
            self.config_manager._dict_to_config(invalid_data)

    def test_merge_cli_args_analysis_sensitivity(self):
        """Test CLI analysis_sensitivity parameter merging."""
        config = BarkDetectorConfig()
        config.detection.sensitivity = 0.68
        config.detection.analysis_sensitivity = 0.30

        # Mock CLI args with analysis_sensitivity
        class MockArgs:
            sensitivity = None
            analysis_sensitivity = 0.20
            output_dir = None
            profile = None

        args = MockArgs()
        merged = self.config_manager.merge_cli_args(config, args)

        # analysis_sensitivity should be overridden by CLI
        assert merged.detection.sensitivity == 0.68  # Unchanged
        assert merged.detection.analysis_sensitivity == 0.20  # From CLI

    def test_legal_config_validation_valid_values(self):
        """Test legal configuration validation with valid values."""
        config_data = {
            "legal": {
                "constant_violation_duration": 600,    # 10 minutes (valid range: 60-1800)
                "intermittent_violation_duration": 1200,     # 20 minutes (valid range: 300-7200)
                "intermittent_gap_threshold": 180   # 3 minutes (valid range: 30-1800)
            }
        }
        config_json = json.dumps(config_data)

        with patch.object(Path, 'exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=config_json)):
            config = self.config_manager.load_config("test.json")
            assert config.legal.constant_violation_duration == 600
            assert config.legal.intermittent_violation_duration == 1200
            assert config.legal.intermittent_gap_threshold == 180

    def test_legal_config_validation_invalid_values(self):
        """Test legal configuration validation with invalid values."""
        # Test constant_violation_duration too low
        config_data = {"legal": {"constant_violation_duration": 30}}  # Below min of 60
        config_json = json.dumps(config_data)

        with patch.object(Path, 'exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=config_json)):
            with pytest.raises(RuntimeError, match="constant_violation_duration.*must be between 60 and 1800"):
                self.config_manager.load_config("test.json")

        # Test intermittent_violation_duration too high
        config_data = {"legal": {"intermittent_violation_duration": 8000}}  # Above max of 7200
        config_json = json.dumps(config_data)

        with patch.object(Path, 'exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=config_json)):
            with pytest.raises(RuntimeError, match="intermittent_violation_duration.*must be between 300 and 7200"):
                self.config_manager.load_config("test.json")

    def test_legal_config_validation_non_numeric_values(self):
        """Test legal configuration validation with non-numeric values."""
        config_data = {"legal": {"constant_violation_duration": "not_a_number"}}
        config_json = json.dumps(config_data)

        with patch.object(Path, 'exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=config_json)):
            with pytest.raises(RuntimeError, match="constant_violation_duration.*must be a number"):
                self.config_manager.load_config("test.json")


class TestConfigIntegration:
    """Integration tests for configuration system."""
    
    def test_full_config_roundtrip(self, tmp_path):
        """Test full configuration save/load cycle."""
        config_file = tmp_path / "test_config.json"
        config_manager = ConfigManager()
        
        # Create custom config
        original_config = BarkDetectorConfig()
        original_config.detection.sensitivity = 0.75
        original_config.output.recordings_dir = "custom_recordings"
        original_config.legal.constant_violation_duration = 420  # 7 minutes
        
        # Save and reload
        config_manager.save_config(original_config, config_file)
        loaded_config = config_manager.load_config(config_file)
        
        # Verify all values preserved
        assert loaded_config.detection.sensitivity == 0.75
        assert loaded_config.output.recordings_dir == "custom_recordings"
        assert loaded_config.legal.constant_violation_duration == 420
        
        # Verify defaults for unmodified fields
        assert loaded_config.detection.sample_rate == 16000
        assert loaded_config.output.reports_dir == "reports"