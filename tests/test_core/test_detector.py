"""Tests for bark_detector.core.detector"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from bark_detector.core.detector import AdvancedBarkDetector
from bark_detector.core.models import BarkEvent


class TestAdvancedBarkDetector:
    """Test AdvancedBarkDetector class"""
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_initialization(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test basic detector initialization"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Verify initialization
        assert detector.sensitivity == 0.68
        assert detector.sample_rate == 16000
        assert detector.chunk_size == 1024
        assert detector.channels == 1
        assert detector.quiet_duration == 30.0
        assert detector.session_gap_threshold == 10.0
        assert detector.output_dir == 'test_recordings'
        
        # Verify YAMNet was loaded
        mock_hub_load.assert_called_once_with('https://tfhub.dev/google/yamnet/1')
        assert detector.yamnet_model is not None
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_yamnet_model_loading(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test YAMNet model loading and class detection"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Verify bark-related classes were found
        assert len(detector.bark_class_indices) > 0
        assert 5 in detector.bark_class_indices  # Dog class
        assert 6 in detector.bark_class_indices  # Bark class
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_get_bark_scores(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test bark score extraction from YAMNet outputs"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Create mock YAMNet scores
        scores = np.zeros((5, 11))  # 5 time frames, 11 classes (from our mock CSV)
        scores[0, 5] = 0.8  # Dog class high score
        scores[0, 6] = 0.9  # Bark class high score
        scores[1, 6] = 0.7  # Bark class medium score
        
        # Test bark score extraction
        bark_scores = detector._get_bark_scores(scores)
        
        assert len(bark_scores) == 5
        assert bark_scores[0] == 0.9  # Max of dog (0.8) and bark (0.9)
        assert bark_scores[1] == 0.7  # Only bark class active
        assert bark_scores[2] == 0.0  # No bark classes active
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_scores_to_events(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test conversion of YAMNet scores to bark events"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Create bark scores above threshold (only frames 1,2,3,4 > 0.68)
        bark_scores = np.array([0.5, 0.75, 0.8, 0.9, 0.6])  # frames 1,2,3,4 above 0.68
        
        # Test event extraction
        events = detector._scores_to_events(bark_scores)
        
        # Should create one continuous event spanning frames 1-3 (frame 4 has 0.6 < 0.68)
        assert len(events) == 1
        event = events[0]
        assert event.start_time == pytest.approx(0.48, abs=0.01)  # Frame 1 at 0.48
        assert event.end_time == pytest.approx(1.92, abs=0.01)  # Frame 3 end at (3+1)*0.48  
        assert event.confidence == pytest.approx(0.8167, abs=0.01)  # Mean of frames 1-3: (0.75+0.8+0.9)/3
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_scores_to_events_with_gaps(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test event extraction with gaps below threshold"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Create bark scores with gap below threshold (frames 0,1,4 > 0.68)
        bark_scores = np.array([0.75, 0.8, 0.5, 0.6, 0.85])  # Gap at frames 2-3
        
        # Test event extraction
        events = detector._scores_to_events(bark_scores)
        
        # Should create two separate events
        assert len(events) == 2
        
        # First event (frames 0-1)
        assert events[0].start_time == pytest.approx(0.0, abs=0.01)  # Frame 0
        assert events[0].end_time == pytest.approx(0.96, abs=0.01)  # Frame 1 end
        
        # Second event (frame 4)
        assert events[1].start_time == pytest.approx(1.92, abs=0.01)  # Frame 4
        assert events[1].end_time == pytest.approx(2.4, abs=0.01)   # Frame 4 end
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_recording_data_management(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test recording data storage and concatenation"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Test recording data starts empty
        assert detector.recording_data == []
        assert not detector.is_recording
        
        # Simulate starting recording
        detector.is_recording = True
        detector.recording_data = []
        
        # Add some audio chunks
        chunk1 = np.array([1, 2, 3, 4, 5], dtype=np.int16)
        chunk2 = np.array([6, 7, 8, 9, 10], dtype=np.int16)
        
        detector.recording_data.append(chunk1)
        detector.recording_data.append(chunk2)
        
        # Verify storage
        assert len(detector.recording_data) == 2
        assert np.array_equal(detector.recording_data[0], chunk1)
        assert np.array_equal(detector.recording_data[1], chunk2)
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    @patch('bark_detector.core.detector.os.makedirs')
    def test_save_recording(self, mock_makedirs, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file, temp_dir):
        """Test recording save functionality"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector with temp output directory
        config = mock_detector_config.copy()
        config['output_dir'] = str(temp_dir)
        detector = AdvancedBarkDetector(**config)
        
        # Set up recording data
        detector.recording_data = [
            np.array([1, 2, 3, 4], dtype=np.int16),
            np.array([5, 6, 7, 8], dtype=np.int16)
        ]
        
        # Test save recording
        with patch('bark_detector.core.detector.datetime') as mock_datetime, \
             patch('bark_detector.core.detector.wave.open') as mock_wave_open:
            mock_datetime.now.return_value.strftime.side_effect = lambda fmt: {
                "%Y%m%d_%H%M%S": "20250814_120000",
                "%Y-%m-%d": "2025-08-14"
            }[fmt]
            
            # Mock the wave file context manager
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__ = Mock(return_value=mock_wav_file)
            mock_wave_open.return_value.__exit__ = Mock(return_value=None)
            
            filepath = detector.save_recording()
            
            # Verify file was "saved" (path returned)
            assert filepath.endswith("bark_recording_20250814_120000.wav")
            # Verify wave.open was called
            mock_wave_open.assert_called_once()
    
    @patch('bark_detector.core.detector.hub.load')  
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_save_recording_edge_cases(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test save_recording edge cases"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Test empty recording data
        detector.recording_data = []
        result = detector.save_recording()
        assert result == ""
        
        # Test single empty chunk
        detector.recording_data = [np.array([], dtype=np.int16)]
        result = detector.save_recording()
        assert result == ""
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio') 
    def test_detection_deduplication(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test detection deduplication system"""
        # Mock YAMNet model with proper tensor simulation
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)
        
        # Test initial state
        assert detector.recent_detections == []
        assert detector.last_reported_bark_time == 0.0
        
        # Create mock event
        event = BarkEvent(0.0, 0.5, 0.8)
        
        # Test first detection should be reported (time gap > cooldown)
        # Use time 3.0 so that 3.0 - 0.0 = 3.0 > 2.5 (cooldown duration)
        assert detector._should_report_detection(3.0, event) == True
        assert detector.last_reported_bark_time == 3.0
        
        # Test detection within cooldown should not be reported (2.5s cooldown)
        assert detector._should_report_detection(4.0, event) == False  # 4.0 - 3.0 = 1.0 < 2.5s
        
        # Test detection after cooldown should be reported
        assert detector._should_report_detection(6.0, event) == True  # 6.0 - 3.0 = 3.0 > 2.5s cooldown