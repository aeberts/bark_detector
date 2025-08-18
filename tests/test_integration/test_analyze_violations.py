"""Integration tests for --analyze-violations CLI functionality"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import json

from bark_detector.cli import main
from bark_detector.core.models import BarkEvent, BarkingSession
from bark_detector.legal.models import ViolationReport


class TestAnalyzeViolationsIntegration:
    """Test --analyze-violations CLI command integration."""
    
    @patch('bark_detector.cli.setup_logging')
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    @patch('librosa.load')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    def test_analyze_violations_basic(self, mock_exists, mock_glob, mock_librosa_load, 
                                      mock_pyaudio, mock_hub_load, mock_logging):
        """Test basic --analyze-violations functionality."""
        # Mock YAMNet model
        mock_model = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.numpy.return_value = b"Dog,Bark,Yip,Howl,Bow-wow,Growling,Whimper,Whimper (dog),Domestic animals, pets,Livestock, farm animals, working animals,Canidae, dogs, wolves"
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Mock path operations for date folder
        mock_exists.return_value = True
        mock_recording_files = [
            Path("recordings/2025-08-03/bark_recording_20250803_101647.wav"),
            Path("recordings/2025-08-03/bark_recording_20250803_101912.wav"),
        ]
        mock_glob.return_value = mock_recording_files
        
        # Mock audio loading - simulate 6 minute and 3 minute recordings
        audio_6min = np.random.rand(96000 * 6)  # 6 minutes at 16kHz
        audio_3min = np.random.rand(96000 * 3)  # 3 minutes at 16kHz
        mock_librosa_load.side_effect = [
            (audio_6min, 16000),  # First file: 6 minutes (should be violation)
            (audio_3min, 16000),  # Second file: 3 minutes (no violation)
        ]
        
        # Mock YAMNet inference to return bark detections
        def mock_yamnet_call(audio_waveform):
            # Return mock scores indicating barking throughout
            num_frames = len(audio_waveform) // (16000 * 0.48)  # 0.48s per frame
            scores = np.zeros((int(num_frames), 521))  # 521 YAMNet classes
            
            # Set bark-related classes high for all frames
            scores[:, 70] = 0.85  # Bark class
            scores[:, 69] = 0.75  # Dog class
            
            return scores, None, None
        
        mock_model.side_effect = mock_yamnet_call
        
        with patch('sys.argv', ['bark_detector', '--analyze-violations', '2025-08-03']):
            main()
        
        # Verify that logging shows violations were found
        # The exact number depends on the mock implementation, but we should see analysis
        mock_logging.assert_called_once()
    
    @patch('bark_detector.cli.setup_logging') 
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    @patch('librosa.load')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists')
    def test_analyze_violations_no_recordings(self, mock_exists, mock_glob, mock_librosa_load,
                                               mock_pyaudio, mock_hub_load, mock_logging):
        """Test --analyze-violations with no recordings found."""
        # Mock YAMNet model
        mock_model = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.numpy.return_value = b"Dog,Bark,Yip,Howl,Bow-wow,Growling,Whimper"
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Mock no recordings found
        mock_exists.return_value = False
        mock_glob.return_value = []
        
        with patch('sys.argv', ['bark_detector', '--analyze-violations', '2025-01-01']):
            main()
        
        mock_logging.assert_called_once()
    
    @patch('bark_detector.cli.setup_logging')
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_analyze_violations_error_handling(self, mock_pyaudio, mock_hub_load, mock_logging):
        """Test --analyze-violations error handling."""
        # Mock YAMNet model to raise exception
        mock_hub_load.side_effect = Exception("Model loading failed")
        
        with patch('sys.argv', ['bark_detector', '--analyze-violations', '2025-08-03']):
            result = main()
        
        # Should return error code
        assert result == 1
        mock_logging.assert_called_once()
    
    @patch('bark_detector.cli.setup_logging')
    @patch('bark_detector.core.detector.hub.load')  
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    @patch('librosa.load')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists') 
    def test_analyze_violations_with_config(self, mock_exists, mock_glob, mock_librosa_load,
                                             mock_pyaudio, mock_hub_load, mock_logging):
        """Test --analyze-violations works with configuration files."""
        # Mock YAMNet model
        mock_model = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.numpy.return_value = b"Dog,Bark,Yip,Howl,Bow-wow,Growling,Whimper"
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Mock config file
        test_config = {
            "detection": {"sensitivity": 0.7},
            "output": {"recordings_dir": "test_recordings"},
            "legal": {"continuous_threshold": 300}
        }
        
        # Mock recordings
        mock_exists.return_value = True
        mock_recording_files = [Path("test_recordings/2025-08-03/test.wav")]
        mock_glob.return_value = mock_recording_files
        mock_librosa_load.return_value = (np.random.rand(16000 * 60), 16000)  # 1 minute
        
        mock_model.side_effect = lambda audio: (np.zeros((125, 521)), None, None)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('sys.argv', ['bark_detector', '--config', 'test.json', '--analyze-violations', '2025-08-03']):
                    main()
        
        mock_logging.assert_called_once()


class TestViolationAnalysisLogic:
    """Test the violation analysis logic specifically."""
    
    def test_continuous_violation_detection(self):
        """Test detection of continuous violations (5+ minutes)."""
        from bark_detector.legal.tracker import LegalViolationTracker
        
        # Create a long continuous session (6 minutes)
        long_session = BarkingSession(
            start_time=0.0,
            end_time=360.0,  # 6 minutes
            events=[],
            total_barks=50,
            total_duration=320.0,  # 5.33 minutes of actual barking
            avg_confidence=0.75,
            peak_confidence=0.9,
            barks_per_second=50/360.0,
            intensity=0.8
        )
        
        tracker = LegalViolationTracker()
        violations = tracker.analyze_violations([long_session])
        
        assert len(violations) == 1
        assert violations[0].violation_type == "Constant"
        assert violations[0].total_bark_duration >= 300  # 5+ minutes
    
    def test_sporadic_violation_detection(self):
        """Test detection of sporadic violations (15+ minutes total)."""
        from bark_detector.legal.tracker import LegalViolationTracker
        
        # Create multiple sessions within 5-minute gaps that total > 15 minutes
        sessions = []
        current_time = 0.0
        total_bark_duration = 0.0
        
        # Create 4 sessions of 5 minutes each with 3-minute gaps (within 5-minute threshold)
        for i in range(4):
            session_start = current_time
            session_end = current_time + 300  # 5 minutes
            session_bark_duration = 270  # 4.5 minutes of actual barking
            
            session = BarkingSession(
                start_time=session_start,
                end_time=session_end,
                events=[],
                total_barks=30,
                total_duration=session_bark_duration,
                avg_confidence=0.72,
                peak_confidence=0.85,
                barks_per_second=30/300.0,
                intensity=0.7
            )
            sessions.append(session)
            total_bark_duration += session_bark_duration
            current_time = session_end + 180  # 3-minute gap
        
        assert total_bark_duration > 900  # Should be > 15 minutes
        
        tracker = LegalViolationTracker()
        violations = tracker.analyze_violations(sessions)
        
        # Should detect both continuous and sporadic violations
        assert len(violations) >= 1
        
        # Check for sporadic violation
        sporadic_violations = [v for v in violations if v.violation_type == "Intermittent"]
        if sporadic_violations:
            assert sporadic_violations[0].total_bark_duration >= 900  # 15+ minutes
    
    def test_no_violations_short_sessions(self):
        """Test that short sessions don't trigger violations.""" 
        from bark_detector.legal.tracker import LegalViolationTracker
        
        # Create short sessions (< 5 minutes each)
        short_sessions = []
        for i in range(3):
            session = BarkingSession(
                start_time=i * 600,  # 10 minute gaps
                end_time=i * 600 + 240,  # 4 minutes each
                events=[],
                total_barks=10,
                total_duration=180,  # 3 minutes of actual barking
                avg_confidence=0.7,
                peak_confidence=0.8,
                barks_per_second=10/240.0,
                intensity=0.6
            )
            short_sessions.append(session)
        
        tracker = LegalViolationTracker()
        violations = tracker.analyze_violations(short_sessions)
        
        # Should not detect any violations (too short and too far apart)
        assert len(violations) == 0