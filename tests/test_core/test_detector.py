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
        assert detector.analysis_sensitivity == 0.30  # Default value
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
        bark_scores, class_details = detector._get_bark_scores(scores)
        
        assert len(bark_scores) == 5
        assert len(class_details) == 5
        assert bark_scores[0] == 0.9  # Max of dog (0.8) and bark (0.9)
        assert bark_scores[1] == 0.7  # Only bark class active
        assert bark_scores[2] == 0.0  # No bark classes active
        
        # Test class details
        assert class_details[0]['max_score'] == 0.9
        assert 'class_scores' in class_details[0]
        assert 'triggering_classes' in class_details[0]
    
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
        
        # Create bark scores above threshold (only frames 1,2,3 > 0.68)
        bark_scores = np.array([0.5, 0.75, 0.8, 0.9, 0.6])  # frames 1,2,3 above 0.68
        
        # Create mock class details for each frame
        class_details = []
        for i in range(len(bark_scores)):
            class_details.append({
                'frame': i,
                'max_score': bark_scores[i],
                'class_scores': {'Bark': bark_scores[i]},
                'triggering_classes': ['Bark']
            })
        
        # Test event extraction
        events = detector._scores_to_events(bark_scores, class_details)
        
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
        
        # Create mock class details for each frame
        class_details = []
        for i in range(len(bark_scores)):
            class_details.append({
                'frame': i,
                'max_score': bark_scores[i],
                'class_scores': {'Bark': bark_scores[i]},
                'triggering_classes': ['Bark']
            })
        
        # Test event extraction
        events = detector._scores_to_events(bark_scores, class_details)
        
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

    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_detector_initialization_with_analysis_sensitivity(self, mock_pyaudio, mock_hub_load, yamnet_class_map_file):
        """Test AdvancedBarkDetector initialization with analysis_sensitivity parameter."""
        # Mock YAMNet model
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model

        # Test custom analysis_sensitivity value
        detector = AdvancedBarkDetector(
            sensitivity=0.68,
            analysis_sensitivity=0.25,
            output_dir='test_recordings'
        )

        assert detector.sensitivity == 0.68
        assert detector.analysis_sensitivity == 0.25

    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_detect_barks_with_sensitivity_method(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test _detect_barks_in_buffer_with_sensitivity method accepts custom sensitivity."""
        # Mock YAMNet model
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor

        # Mock YAMNet inference to return controlled scores
        mock_scores = np.zeros((3, 11))  # 3 frames, 11 classes
        mock_scores[0, 5] = 0.40  # Dog class - below real-time threshold (0.68) but above analysis threshold (0.30)
        mock_scores[1, 6] = 0.50  # Bark class
        mock_scores[2, 6] = 0.75  # Bark class - above both thresholds

        mock_model.return_value = (mock_scores, None, None)
        mock_hub_load.return_value = mock_model

        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)

        # Create test audio data
        audio_chunk = np.random.random(16000).astype(np.float32)  # 1 second of audio

        # Test with real-time sensitivity (0.68) - should detect only frame 2
        events_realtime = detector._detect_barks_in_buffer_with_sensitivity(audio_chunk, 0.68)

        # Test with analysis sensitivity (0.30) - should detect frames 0, 1, and 2
        events_analysis = detector._detect_barks_in_buffer_with_sensitivity(audio_chunk, 0.30)

        # Analysis mode should detect more events than real-time mode
        assert len(events_analysis) >= len(events_realtime)

    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_real_time_detection_uses_primary_sensitivity(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test that real-time detection continues using self.sensitivity."""
        # Mock YAMNet model
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model

        # Create detector with different sensitivities
        detector = AdvancedBarkDetector(**mock_detector_config)

        # Mock the _detect_barks_in_buffer_with_sensitivity method to track calls
        detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=[])

        # Test audio data
        audio_chunk = np.random.random(16000).astype(np.float32)

        # Call real-time detection method
        detector._detect_barks_in_buffer(audio_chunk)

        # Verify it used the real-time sensitivity (0.68)
        detector._detect_barks_in_buffer_with_sensitivity.assert_called_once_with(audio_chunk, 0.68)

    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_sensitivity_threshold_application(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test that bark_scores > sensitivity logic uses correct threshold."""
        # Mock YAMNet model
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model

        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)

        # Create test scores with known values
        bark_scores = np.array([0.25, 0.45, 0.75, 0.85])  # Range of confidence scores

        # Create mock class details
        class_details = []
        for i, score in enumerate(bark_scores):
            class_details.append({
                'frame': i,
                'max_score': score,
                'class_scores': {'Bark': score},
                'triggering_classes': ['Bark']
            })

        # Test with high sensitivity (0.80) - should detect only frame 3
        events_high = detector._scores_to_events_with_sensitivity(bark_scores, class_details, 0.80)
        assert len(events_high) == 1

        # Test with medium sensitivity (0.50) - should detect frames 2 and 3
        events_medium = detector._scores_to_events_with_sensitivity(bark_scores, class_details, 0.50)
        assert len(events_medium) == 1  # Frames 2-3 will be grouped as one consecutive event

        # Test with low sensitivity (0.20) - should detect all frames
        events_low = detector._scores_to_events_with_sensitivity(bark_scores, class_details, 0.20)
        assert len(events_low) >= 1  # All frames should be detected

    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_detection_mode_differentiation(self, mock_pyaudio, mock_hub_load, mock_detector_config, yamnet_class_map_file):
        """Test that different sensitivity values are handled correctly."""
        # Mock YAMNet model
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = yamnet_class_map_file
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model

        # Create detector
        detector = AdvancedBarkDetector(**mock_detector_config)

        # Verify dual sensitivity values are set correctly
        assert detector.sensitivity == 0.68
        assert detector.analysis_sensitivity == 0.30

        # Mock the YAMNet model call to return controlled data
        mock_scores = np.zeros((3, 11))  # 3 frames, 11 classes
        mock_scores[0, 5] = 0.40  # Below real-time threshold, above analysis threshold
        mock_scores[1, 6] = 0.75  # Above both thresholds

        mock_model.return_value = (mock_scores, None, None)

        # Test audio chunk
        audio_chunk = np.random.random(16000).astype(np.float32)

        # Test real-time mode detection (higher threshold)
        events_realtime = detector._detect_barks_in_buffer_with_sensitivity(audio_chunk, detector.sensitivity)

        # Test analysis mode detection (lower threshold)
        events_analysis = detector._detect_barks_in_buffer_with_sensitivity(audio_chunk, detector.analysis_sensitivity)

        # Analysis mode should detect at least as many events as real-time mode
        assert len(events_analysis) >= len(events_realtime)

        # Verify the methods work with different sensitivity values
        low_sensitivity_events = detector._detect_barks_in_buffer_with_sensitivity(audio_chunk, 0.20)
        high_sensitivity_events = detector._detect_barks_in_buffer_with_sensitivity(audio_chunk, 0.80)

        # Lower sensitivity should detect more events
        assert len(low_sensitivity_events) >= len(high_sensitivity_events)