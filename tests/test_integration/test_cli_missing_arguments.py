"""Tests for missing CLI arguments that were removed during T2 refactor"""

import pytest
import subprocess
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock


class TestMissingCLIArguments:
    """Test CLI arguments that were present in original but missing after T2 refactor"""
    
    def test_calibrate_files_argument_recognized(self):
        """Test that --calibrate-files argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--calibrate-files", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--calibrate-files" in result.stdout
        
    def test_audio_files_argument_recognized(self):
        """Test that --audio-files argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--audio-files", "test.wav", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--audio-files" in result.stdout
        
    def test_ground_truth_files_argument_recognized(self):
        """Test that --ground-truth-files argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--ground-truth-files", "test.json", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--ground-truth-files" in result.stdout
        
    def test_create_template_argument_recognized(self):
        """Test that --create-template argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--create-template", "test.wav", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--create-template" in result.stdout
        
    def test_sensitivity_range_argument_recognized(self):
        """Test that --sensitivity-range argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--sensitivity-range", "0.1", "0.5", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--sensitivity-range" in result.stdout
        
    def test_steps_argument_recognized(self):
        """Test that --steps argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--steps", "10", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--steps" in result.stdout
        
    def test_convert_files_argument_recognized(self):
        """Test that --convert-files argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--convert-files", "test.m4a", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--convert-files" in result.stdout
        
    def test_convert_directory_argument_recognized(self):
        """Test that --convert-directory argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--convert-directory", ".", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--convert-directory" in result.stdout
        
    def test_list_violations_argument_recognized(self):
        """Test that --list-violations argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--list-violations", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--list-violations" in result.stdout
        
    def test_record_argument_recognized(self):
        """Test that --record argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--record", "test.wav", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--record" in result.stdout
        
    def test_duration_argument_recognized(self):
        """Test that --duration argument is recognized"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--duration", "5", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should not fail with "unrecognized arguments" error
        assert result.returncode == 0
        assert "--duration" in result.stdout

    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_user_specific_command_works(self, mock_pyaudio, mock_hub_load, temp_dir):
        """Test the user's specific command that was failing"""
        # Mock YAMNet model loading
        mock_model = Mock()
        mock_model.class_map_path.return_value.numpy.return_value = b'/tmp/fake_class_map.csv'
        mock_hub_load.return_value = mock_model
        
        # Create fake class map file
        class_map_content = "index,mid,display_name\n0,/m/0bt9lr,Dog\n1,/m/05tny_,Bark\n"
        class_map_path = Path("/tmp/fake_class_map.csv")
        with open(class_map_path, 'w') as f:
            f.write(class_map_content)
        
        # Create temporary audio and ground truth files
        audio_file1 = temp_dir / "test1.wav"
        audio_file2 = temp_dir / "test2.wav"
        gt_file1 = temp_dir / "test1.json"
        gt_file2 = temp_dir / "test2.json"
        
        # Create minimal WAV files (just headers)
        for audio_file in [audio_file1, audio_file2]:
            with open(audio_file, 'wb') as f:
                # Minimal WAV header
                f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00>\x00\x00\x00>\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00')
        
        # Create ground truth files
        gt_data = {
            "audio_file": str(audio_file1),
            "duration": 1.0,
            "instructions": "Timestamp format: HH:MM:SS.mmm",
            "events": [
                {
                    "start_time": "00:00:00.100",
                    "end_time": "00:00:00.500",
                    "description": "Test bark",
                    "confidence_expected": 1.0
                }
            ],
            "format_version": "2.0"
        }
        
        for gt_file in [gt_file1, gt_file2]:
            with open(gt_file, 'w') as f:
                json.dump(gt_data, f)
        
        # Test the command that was failing
        result = subprocess.run([
            "uv", "run", "python", "-m", "bark_detector",
            "--calibrate-files",
            "--audio-files", str(audio_file1), str(audio_file2),
            "--ground-truth-files", str(gt_file1), str(gt_file2),
            "--save-profile", "test-profile"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        # Should not fail with "unrecognized arguments" error
        assert "unrecognized arguments" not in result.stderr
        # Should exit gracefully (may fail due to missing model, but not due to argument parsing)
        assert result.returncode != 2  # Exit code 2 is typically argument parsing error
        
        # Cleanup
        class_map_path.unlink(missing_ok=True)