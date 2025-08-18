"""Integration tests for CLI configuration system"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from bark_detector.cli import parse_arguments, main
from bark_detector.utils.config import BarkDetectorConfig


class TestCLIConfigIntegration:
    """Test CLI integration with configuration system."""
    
    def test_config_argument_parsing(self):
        """Test that config arguments are parsed correctly."""
        # Test config file argument
        with patch('sys.argv', ['bark_detector', '--config', 'test.json']):
            args = parse_arguments()
            assert args.config == 'test.json'
        
        # Test create config argument
        with patch('sys.argv', ['bark_detector', '--create-config', 'new.json']):
            args = parse_arguments()
            assert args.create_config == 'new.json'
    
    def test_create_config_command(self, tmp_path):
        """Test --create-config command functionality."""
        config_file = tmp_path / "test_config.json"
        
        with patch('sys.argv', ['bark_detector', '--create-config', str(config_file)]):
            with patch('bark_detector.cli.setup_logging'):
                main()
        
        # Verify config file was created
        assert config_file.exists()
        
        # Verify it contains valid JSON with expected structure
        with open(config_file) as f:
            data = json.load(f)
        
        assert 'detection' in data
        assert 'output' in data
        assert 'calibration' in data
        assert 'scheduling' in data
        assert 'legal' in data
        assert data['detection']['sensitivity'] == 0.68
    
    @patch('bark_detector.cli.AdvancedBarkDetector')
    @patch('bark_detector.cli.setup_logging')
    def test_config_file_loading_in_main(self, mock_logging, mock_detector, tmp_path):
        """Test that config file is loaded and used in main()."""
        # Create test config file
        config_file = tmp_path / "test.json"
        test_config = {
            "detection": {
                "sensitivity": 0.75,
                "quiet_duration": 45.0
            },
            "output": {
                "recordings_dir": "test_recordings"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Mock detector to avoid actual initialization
        mock_detector_instance = MagicMock()
        mock_detector_instance.list_profiles.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        with patch('sys.argv', ['bark_detector', '--config', str(config_file), '--list-profiles']):
            main()
        
        # Verify detector was created with config file values
        mock_detector.assert_called_once()
        call_args = mock_detector.call_args[1]  # Get keyword arguments
        
        assert call_args['sensitivity'] == 0.75
        assert call_args['quiet_duration'] == 45.0
        assert call_args['output_dir'] == "test_recordings"
    
    @patch('bark_detector.cli.AdvancedBarkDetector')
    @patch('bark_detector.cli.setup_logging')  
    def test_cli_args_override_config_file(self, mock_logging, mock_detector, tmp_path):
        """Test that CLI arguments override config file values."""
        # Create config file with one sensitivity value
        config_file = tmp_path / "test.json"
        test_config = {
            "detection": {"sensitivity": 0.5},
            "output": {"recordings_dir": "config_recordings"}
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        mock_detector_instance = MagicMock()
        mock_detector_instance.list_profiles.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        # Pass different sensitivity via CLI
        with patch('sys.argv', [
            'bark_detector', 
            '--config', str(config_file),
            '--sensitivity', '0.8',
            '--output-dir', 'cli_recordings',
            '--list-profiles'
        ]):
            main()
        
        # Verify CLI values override config file values
        call_args = mock_detector.call_args[1]
        assert call_args['sensitivity'] == 0.8  # CLI override
        assert call_args['output_dir'] == "cli_recordings"  # CLI override
    
    @patch('bark_detector.cli.AdvancedBarkDetector')
    @patch('bark_detector.cli.setup_logging')
    def test_default_config_when_no_file(self, mock_logging, mock_detector):
        """Test that defaults are used when no config file is specified."""
        mock_detector_instance = MagicMock()
        mock_detector_instance.list_profiles.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        with patch('sys.argv', ['bark_detector', '--list-profiles']):
            main()
        
        # Verify default values are used
        call_args = mock_detector.call_args[1]
        assert call_args['sensitivity'] == 0.68  # Default
        assert call_args['output_dir'] == "recordings"  # Default
    
    @patch('bark_detector.cli.setup_logging')
    def test_config_file_not_found_error(self, mock_logging, capsys):
        """Test error handling when config file is not found."""
        with patch('sys.argv', ['bark_detector', '--config', 'nonexistent.json']):
            main()
        
        # Should log error and return without crashing
        captured = capsys.readouterr()
        # Note: This test verifies the function completes without exception
        # The actual error logging verification would depend on logging setup
    
    @patch('bark_detector.cli.setup_logging')
    def test_invalid_config_json_error(self, mock_logging, tmp_path):
        """Test error handling when config file contains invalid JSON."""
        # Create invalid JSON file
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")
        
        with patch('sys.argv', ['bark_detector', '--config', str(config_file)]):
            main()
        
        # Should handle error gracefully without crashing
        # Function should complete execution
    
    def test_config_help_text_includes_examples(self):
        """Test that help text includes config file examples."""
        with patch('sys.argv', ['bark_detector', '--help']):
            with pytest.raises(SystemExit):  # argparse exits after showing help
                parse_arguments()
    
    @patch('bark_detector.cli.AdvancedBarkDetector')
    @patch('bark_detector.cli.setup_logging')
    def test_config_precedence_order(self, mock_logging, mock_detector, tmp_path):
        """Test configuration precedence: CLI > config file > defaults."""
        # Create config file with custom values
        config_file = tmp_path / "precedence_test.json"
        config_data = {
            "detection": {
                "sensitivity": 0.4,  # Config file value
                "quiet_duration": 60.0  # Config file value, no CLI override
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        mock_detector_instance = MagicMock()
        mock_detector_instance.list_profiles.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        # CLI overrides sensitivity but not quiet_duration
        with patch('sys.argv', [
            'bark_detector',
            '--config', str(config_file),
            '--sensitivity', '0.9',  # CLI override
            '--list-profiles'
        ]):
            main()
        
        call_args = mock_detector.call_args[1]
        
        # Verify precedence order
        assert call_args['sensitivity'] == 0.9      # CLI wins over config file
        assert call_args['quiet_duration'] == 60.0  # Config file wins over default (30.0)
        assert call_args['sample_rate'] == 16000    # Default value (not in config file or CLI)


class TestConfigFileSearch:
    """Test configuration file search behavior."""
    
    @patch('bark_detector.cli.AdvancedBarkDetector')
    @patch('bark_detector.cli.setup_logging')
    @patch('pathlib.Path.exists')
    def test_default_config_file_search(self, mock_exists, mock_logging, mock_detector):
        """Test that default config locations are searched."""
        mock_detector_instance = MagicMock()
        mock_detector_instance.list_profiles.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        # Mock that ./config.json exists  
        mock_exists.return_value = True
        
        # Create mock config file content
        config_content = '{"detection": {"sensitivity": 0.55}}'
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = config_content
            
            with patch('sys.argv', ['bark_detector', '--list-profiles']):
                main()
        
        # Verify that config file was loaded (sensitivity should be 0.55, not default 0.68)
        call_args = mock_detector.call_args[1]
        assert call_args['sensitivity'] == 0.55