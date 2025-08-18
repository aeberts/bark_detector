"""Tests for bark_detector.calibration.file_calibration"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import json

from bark_detector.calibration.file_calibration import FileBasedCalibration
from bark_detector.core.models import BarkEvent, GroundTruthEvent, CalibrationProfile


class TestFileBasedCalibration:
    """Test FileBasedCalibration class"""
    
    def test_initialization(self):
        """Test basic FileBasedCalibration initialization"""
        mock_detector = Mock()
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        assert calibrator.detector == mock_detector
        assert calibrator.test_files == []
        assert calibrator.results == []
    
    @patch('soundfile.info')
    def test_add_test_file_wav(self, mock_sf_info):
        """Test adding WAV test file"""
        mock_detector = Mock()
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        # Mock audio file info
        mock_info = Mock()
        mock_info.samplerate = 16000
        mock_info.channels = 1
        mock_sf_info.return_value = mock_info
        
        # Add test file
        audio_path = Path("test.wav")
        ground_truth_events = [GroundTruthEvent(1.0, 2.0, "test bark")]
        
        calibrator.add_test_file(audio_path, ground_truth_events=ground_truth_events)
        
        assert len(calibrator.test_files) == 1
        test_file = calibrator.test_files[0]
        assert test_file['original_path'] == audio_path
        assert len(test_file['ground_truth']) == 1
        assert test_file['is_negative'] == False
    
    @patch('bark_detector.calibration.file_calibration.json.load')
    def test_add_test_file_with_json_ground_truth(self, mock_json_load, temp_dir):
        """Test adding test file with JSON ground truth"""
        mock_detector = Mock()
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        # Mock ground truth JSON
        gt_data = {
            'events': [
                {'start_time': 1.0, 'end_time': 2.0, 'description': 'bark 1'},
                {'start_time': 5.0, 'end_time': 6.0, 'description': 'bark 2', 'confidence_expected': 0.9}
            ]
        }
        mock_json_load.return_value = gt_data
        
        # Create temporary files
        audio_path = temp_dir / "test.wav"
        gt_path = temp_dir / "test.json"
        
        # Mock Path.exists() and file operations
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(calibrator, '_ensure_compatible_audio', return_value=audio_path):
                with patch('builtins.open', mock_open(read_data=json.dumps(gt_data))):
                    calibrator.add_test_file(audio_path, gt_path)
        
        assert len(calibrator.test_files) == 1
        test_file = calibrator.test_files[0]
        assert len(test_file['ground_truth']) == 2
        assert test_file['ground_truth'][1].confidence_expected == 0.9
    
    @patch('librosa.load')
    def test_audio_file_conversion(self, mock_librosa_load):
        """Test audio file format conversion"""
        mock_detector = Mock()
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        # Mock audio loading
        mock_audio_data = np.random.rand(32000)  # 2 seconds at 16kHz
        mock_librosa_load.return_value = (mock_audio_data, 16000)
        
        # Test M4A file conversion
        m4a_path = Path("test.m4a")
        
        with patch('soundfile.write') as mock_sf_write:
            with patch.object(Path, 'mkdir'):
                converted_path = calibrator._convert_audio_file(m4a_path)
        
        assert converted_path.suffix == '.wav'
        assert '_16khz' in converted_path.stem
        mock_sf_write.assert_called_once()
    
    @patch('librosa.load')
    def test_single_file_detection_test(self, mock_librosa_load):
        """Test detection testing on single file"""
        mock_detector = Mock()
        mock_detector.sensitivity = 0.7
        mock_detector._detect_barks_in_buffer.return_value = [
            BarkEvent(1.2, 1.8, 0.8),  # Should match ground truth at 1.0-2.0
            BarkEvent(3.0, 3.5, 0.75)  # False positive
        ]
        
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        # Mock audio loading
        mock_audio_data = np.random.rand(64000)  # 4 seconds at 16kHz
        mock_librosa_load.return_value = (mock_audio_data, 16000)
        
        # Create test file data
        test_file = {
            'audio_path': Path("test.wav"),
            'ground_truth': [GroundTruthEvent(1.0, 2.0, "bark 1")],
            'is_negative': False
        }
        
        result = calibrator._test_single_file(test_file, 0.7)
        
        assert result['detected_events'] == 2
        assert result['ground_truth_events'] == 1
        assert result['matches'] == 1
        assert result['false_positives'] == 1
        assert result['missed'] == 0
    
    @patch('soundfile.read')
    @patch('librosa.load')
    def test_sensitivity_sweep(self, mock_librosa_load, mock_sf_read):
        """Test sensitivity parameter sweep"""
        mock_detector = Mock()
        mock_detector.sensitivity = 0.7
        
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        # Add test file
        audio_path = Path("test.wav")
        ground_truth_events = [GroundTruthEvent(1.0, 2.0, "test bark")]
        
        # Mock soundfile.read for file analysis
        mock_audio_data = np.random.rand(32000)  # 2 seconds at 16kHz
        mock_sf_read.return_value = (mock_audio_data, 16000)
        
        with patch.object(calibrator, '_ensure_compatible_audio', return_value=audio_path):
            calibrator.add_test_file(audio_path, ground_truth_events=ground_truth_events)
        
        # Mock audio loading
        mock_audio_data = np.random.rand(32000)  # 2 seconds at 16kHz
        mock_librosa_load.return_value = (mock_audio_data, 16000)
        
        # Mock detection results for different sensitivities
        def mock_detection(audio_data):
            # Return different results based on current sensitivity
            if mock_detector.sensitivity <= 0.5:
                return [BarkEvent(1.2, 1.8, 0.8), BarkEvent(3.0, 3.5, 0.4)]  # More detections at low sensitivity
            elif mock_detector.sensitivity <= 0.7:
                return [BarkEvent(1.2, 1.8, 0.8)]  # Good balance
            else:
                return []  # No detections at high sensitivity
        
        mock_detector._detect_barks_in_buffer.side_effect = mock_detection
        
        results = calibrator.run_sensitivity_sweep((0.3, 0.9), steps=3)
        
        assert 'optimal_sensitivity' in results
        assert 'best_result' in results
        assert 'all_results' in results
        assert len(results['all_results']) == 3
        
        # Best should be middle sensitivity with balanced precision/recall
        assert results['optimal_sensitivity'] == pytest.approx(0.6, abs=0.1)
        assert results['best_result']['f1_score'] > 0
    
    @patch('soundfile.read')
    @patch('librosa.load') 
    def test_calibration_profile_creation(self, mock_librosa_load, mock_sf_read):
        """Test creation of calibration profile from file analysis"""
        mock_detector = Mock()
        mock_detector.sensitivity = 0.7
        mock_detector._detect_barks_in_buffer.return_value = [BarkEvent(1.2, 1.8, 0.8)]
        
        # Mock soundfile.read for file analysis
        mock_audio_data = np.random.rand(32000)  # 2 seconds at 16kHz
        mock_sf_read.return_value = (mock_audio_data, 16000)
        
        calibrator = FileBasedCalibration(detector=mock_detector)
        
        # Mock audio loading
        mock_audio_data = np.random.rand(32000)
        mock_librosa_load.return_value = (mock_audio_data, 16000)
        
        with patch.object(calibrator, '_ensure_compatible_audio') as mock_ensure:
            mock_ensure.return_value = Path("test.wav")
            
            profile = calibrator.calibrate_from_files([Path("test.wav")])
        
        assert isinstance(profile, CalibrationProfile)
        assert profile.name.startswith('file-calib-')
        assert 0.0 <= profile.sensitivity <= 1.0
        assert profile.min_bark_duration == 0.5
        assert profile.session_gap_threshold == 10.0
        assert profile.location == "File-based Calibration"
        assert "F1=" in profile.notes