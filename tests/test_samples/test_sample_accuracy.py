"""Core accuracy tests using real sample audio files and ground truth data"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from bark_detector.core.detector import AdvancedBarkDetector
from bark_detector.core.models import BarkEvent
from tests.fixtures.sample_data_loader import SampleDataLoader, DetectionEvaluator


class TestSampleBasedAccuracy:
    """Test bark detection accuracy using real sample audio and ground truth"""
    
    @pytest.fixture
    def sample_loader(self):
        """Create sample data loader fixture"""
        return SampleDataLoader()
    
    @pytest.fixture 
    def evaluator(self):
        """Create detection evaluator with reasonable tolerance"""
        # 1-second tolerance for practical bark detection evaluation
        return DetectionEvaluator(tolerance_seconds=1.0, min_confidence=0.65)
    
    @pytest.fixture
    def detector(self):
        """Create properly mocked detector for testing"""
        with patch('bark_detector.core.detector.hub.load') as mock_hub_load:
            with patch('builtins.open', mock_open(read_data="index,mid,display_name\n0,/m/0bt9lr,Dog\n1,/m/0jbk,Bark\n2,/m/0k4j,Yip")):
                # Mock YAMNet model
                mock_model = MagicMock()
                mock_tensor = MagicMock()
                mock_tensor.numpy.return_value = b"test_class_map.csv"
                mock_model.class_map_path.return_value = mock_tensor
                mock_hub_load.return_value = mock_model
                
                # Create detector with real-world confidence threshold
                detector = AdvancedBarkDetector(sensitivity=0.65, sample_rate=16000)
                
                # Manually set class names for testing
                detector.class_names = ["Dog", "Bark", "Yip", "Howl", "Bow-wow", "Growling", "Whimper"]
                detector.bark_class_indices = [0, 1, 2, 3, 4, 5, 6]  # All are bark-related
                
                return detector
    
    def test_sample_loader_initialization(self, sample_loader):
        """Test that sample loader can initialize and find sample files"""
        samples = sample_loader.get_available_samples()
        
        # Should find at least the two bark samples and background
        assert len(samples) >= 2, f"Expected at least 2 samples, found {len(samples)}"
        
        # Verify we have both bark samples
        sample_names = [s['name'] for s in samples]
        assert 'bark_recording_20250727_134707_bark' in sample_names
        assert 'bark_recording_20250727_141319_bark' in sample_names
    
    def test_ground_truth_loading(self, sample_loader):
        """Test loading and parsing ground truth data"""
        # Test large dog sample
        large_dog_sample = sample_loader.load_sample('bark_recording_20250727_134707_bark')
        
        assert large_dog_sample['has_ground_truth'] is True
        assert len(large_dog_sample['ground_truth_events']) == 15
        assert large_dog_sample['duration'] > 50  # Should be ~54 seconds
        
        # Verify ground truth event structure
        first_event = large_dog_sample['ground_truth_events'][0]
        assert hasattr(first_event, 'start_time')
        assert hasattr(first_event, 'end_time') 
        assert hasattr(first_event, 'description')
        assert hasattr(first_event, 'confidence_expected')
        
        # Test small dog sample
        small_dog_sample = sample_loader.load_sample('bark_recording_20250727_141319_bark')
        
        assert small_dog_sample['has_ground_truth'] is True
        assert len(small_dog_sample['ground_truth_events']) == 15
        assert small_dog_sample['duration'] > 30  # Should be ~33 seconds
    
    def test_background_sample_loading(self, sample_loader):
        """Test loading background (negative) sample"""
        try:
            background_sample = sample_loader.load_sample('background')
            assert background_sample['has_ground_truth'] is False
            assert len(background_sample['ground_truth_events']) == 0
            assert background_sample['audio_data'] is not None
        except ValueError:
            pytest.skip("Background sample not found - acceptable for basic testing")
    
    def test_detection_evaluation_metrics(self, evaluator):
        """Test detection evaluation and metrics calculation"""
        from tests.fixtures.sample_data_loader import GroundTruthEvent
        
        # Create mock detected events  
        detected_events = [
            BarkEvent(start_time=1.0, end_time=2.0, confidence=0.8),
            BarkEvent(start_time=5.0, end_time=6.0, confidence=0.7),
            BarkEvent(start_time=10.0, end_time=11.0, confidence=0.6),  # Below threshold
            BarkEvent(start_time=20.0, end_time=21.0, confidence=0.9),  # False positive
        ]
        
        # Create ground truth events
        ground_truth_events = [
            GroundTruthEvent(start_time=1.2, end_time=2.2, description="bark 1"),
            GroundTruthEvent(start_time=5.1, end_time=6.1, description="bark 2"), 
            GroundTruthEvent(start_time=15.0, end_time=16.0, description="bark 3"),  # Missed
        ]
        
        # Evaluate matches
        match_results = evaluator.match_detections_to_ground_truth(detected_events, ground_truth_events)
        
        # Should have 2 true positives (events at 1s and 5s match with tolerance)
        # 1 false positive (event at 20s), 1 false negative (event at 15s missed)
        # Event at 10s filtered out by confidence threshold
        assert len(match_results['true_positives']) == 2
        assert len(match_results['false_positives']) == 1
        assert len(match_results['false_negatives']) == 1
        
        # Calculate metrics
        metrics = evaluator.calculate_metrics(match_results)
        assert metrics['precision'] == 2/3  # 2 TP / (2 TP + 1 FP)
        assert metrics['recall'] == 2/3     # 2 TP / (2 TP + 1 FN)
        assert metrics['f1_score'] == 2/3   # 2 * (2/3 * 2/3) / (2/3 + 2/3)
    
    def test_large_dog_sample_detection(self, sample_loader, detector, evaluator):
        """Test detection accuracy on large dog bark sample"""
        # Load sample data (using real audio file)
        sample = sample_loader.load_sample('bark_recording_20250727_134707_bark')
        
        # Mock YAMNet inference to return realistic bark detections
        def mock_yamnet_inference(audio_waveform):
            # Simulate YAMNet returning scores for the known bark events
            # Create scores array with detections roughly matching ground truth timing
            num_frames = len(audio_waveform) // (16000 * 0.48)  # YAMNet frame rate
            scores = np.zeros((int(num_frames), 521))
            
            # Add bark detections at approximate ground truth locations  
            ground_truth = sample['ground_truth_events']
            for gt_event in ground_truth:
                # Convert time to frame index
                frame_start = int(gt_event.start_time / 0.48)
                frame_end = int(gt_event.end_time / 0.48)
                
                if frame_end < scores.shape[0]:
                    # Set bark-related class scores high for this event (using indices that match our mock)
                    scores[frame_start:frame_end+1, 1] = 0.85  # Bark class (index 1 in our mock)
                    scores[frame_start:frame_end+1, 0] = 0.75  # Dog class (index 0 in our mock)
            
            # Create mock tensor that has .numpy() method
            mock_scores_tensor = MagicMock()
            mock_scores_tensor.numpy.return_value = scores
            
            return mock_scores_tensor, None, None
        
        detector.yamnet_model.side_effect = mock_yamnet_inference
        
        # Run detection on sample audio
        detected_events = detector._detect_barks_in_buffer(sample['audio_data'])
        
        # Evaluate against ground truth
        match_results = evaluator.match_detections_to_ground_truth(
            detected_events, sample['ground_truth_events']
        )
        
        metrics = evaluator.calculate_metrics(match_results)
        
        # Assert reasonable detection performance 
        # With 15 ground truth events, we should detect most of them
        assert metrics['recall'] >= 0.6, f"Recall too low: {metrics['recall']:.3f}"
        assert metrics['precision'] >= 0.6, f"Precision too low: {metrics['precision']:.3f}"
        assert metrics['f1_score'] >= 0.6, f"F1 score too low: {metrics['f1_score']:.3f}"
        
        # Should have detected some events
        assert metrics['total_detections'] > 0, "No detections found"
        assert len(detected_events) > 0, "No bark events detected"
    
    def test_small_dog_sample_detection(self, sample_loader, detector, evaluator):
        """Test detection accuracy on small dog bark sample"""
        # Load sample data (using real audio file)
        sample = sample_loader.load_sample('bark_recording_20250727_141319_bark')
        
        # Mock YAMNet inference for small dog barks
        def mock_yamnet_inference(audio_waveform):
            num_frames = len(audio_waveform) // (16000 * 0.48)
            scores = np.zeros((int(num_frames), 521))
            
            # Simulate detections for small dog barks
            ground_truth = sample['ground_truth_events']
            for gt_event in ground_truth:
                frame_start = int(gt_event.start_time / 0.48)
                frame_end = int(gt_event.end_time / 0.48)
                
                if frame_end < scores.shape[0]:
                    # Small dog barks might have slightly lower confidence
                    scores[frame_start:frame_end+1, 1] = 0.75  # Bark class (index 1)
                    scores[frame_start:frame_end+1, 0] = 0.70  # Dog class (index 0)
            
            # Create mock tensor that has .numpy() method
            mock_scores_tensor = MagicMock()
            mock_scores_tensor.numpy.return_value = scores
            
            return mock_scores_tensor, None, None
        
        detector.yamnet_model.side_effect = mock_yamnet_inference
        
        # Run detection
        detected_events = detector._detect_barks_in_buffer(sample['audio_data'])
        
        # Evaluate
        match_results = evaluator.match_detections_to_ground_truth(
            detected_events, sample['ground_truth_events']
        )
        
        metrics = evaluator.calculate_metrics(match_results)
        
        # Small dog barks should still be detected reasonably well
        # Note: Small dog barks can be more challenging to detect
        assert metrics['recall'] >= 0.4, f"Small dog recall too low: {metrics['recall']:.3f}"
        assert metrics['precision'] >= 0.4, f"Small dog precision too low: {metrics['precision']:.3f}"
        assert len(detected_events) > 0, "No small dog bark events detected"
    
    def test_background_false_positives(self, sample_loader, detector):
        """Test that background audio doesn't trigger false positives"""
        try:
            background_sample = sample_loader.load_sample('background')
        except ValueError:
            pytest.skip("Background sample not available")
        
        # Mock YAMNet to return low scores for background audio
        def mock_yamnet_inference(audio_waveform):
            num_frames = len(audio_waveform) // (16000 * 0.48)
            scores = np.zeros((int(num_frames), 521))
            
            # Background should have very low bark-related scores
            scores[:, 1] = np.random.uniform(0.0, 0.3, num_frames)  # Low bark scores (index 1)
            scores[:, 0] = np.random.uniform(0.0, 0.2, num_frames)  # Low dog scores (index 0)
            
            # Create mock tensor that has .numpy() method
            mock_scores_tensor = MagicMock()
            mock_scores_tensor.numpy.return_value = scores
            
            return mock_scores_tensor, None, None
        
        detector.yamnet_model.side_effect = mock_yamnet_inference
        
        # Run detection
        detected_events = detector._detect_barks_in_buffer(background_sample['audio_data'])
        
        # Should have very few or no detections above confidence threshold
        high_confidence_detections = [
            event for event in detected_events 
            if event.confidence >= 0.65
        ]
        
        assert len(high_confidence_detections) <= 1, f"Too many false positives in background: {len(high_confidence_detections)}"
    
    def test_confidence_threshold_filtering(self, evaluator):
        """Test that confidence threshold properly filters detections"""
        # Create events with various confidence levels
        detected_events = [
            BarkEvent(start_time=1.0, end_time=2.0, confidence=0.8),  # Above threshold
            BarkEvent(start_time=3.0, end_time=4.0, confidence=0.65), # At threshold
            BarkEvent(start_time=5.0, end_time=6.0, confidence=0.64), # Below threshold
            BarkEvent(start_time=7.0, end_time=8.0, confidence=0.3),  # Well below threshold
        ]
        
        ground_truth = []  # No ground truth needed for this test
        
        match_results = evaluator.match_detections_to_ground_truth(detected_events, ground_truth)
        
        # Only events with confidence >= 0.65 should be considered
        total_considered = (len(match_results['true_positives']) + 
                          len(match_results['false_positives']))
        
        assert total_considered == 2, f"Expected 2 events above threshold, got {total_considered}"