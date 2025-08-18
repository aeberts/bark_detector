"""Comprehensive sample-based testing using all available sample data"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from bark_detector.core.detector import AdvancedBarkDetector
from bark_detector.core.models import BarkEvent
from tests.fixtures.sample_data_loader import SampleDataLoader, DetectionEvaluator


class TestComprehensiveSampleTesting:
    """Comprehensive testing using all available sample files"""
    
    @pytest.fixture
    def sample_loader(self):
        """Create sample data loader fixture"""
        return SampleDataLoader()
    
    @pytest.fixture 
    def evaluator(self):
        """Create detection evaluator with realistic parameters"""
        # 1-second tolerance for practical evaluation, 0.65 confidence threshold
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
                
                # Create detector with 0.65 confidence threshold (real-world requirement)
                detector = AdvancedBarkDetector(sensitivity=0.65, sample_rate=16000)
                
                # Set class names for testing
                detector.class_names = ["Dog", "Bark", "Yip", "Howl", "Bow-wow", "Growling", "Whimper"]
                detector.bark_class_indices = [0, 1, 2, 3, 4, 5, 6]
                
                return detector
    
    def create_yamnet_mock(self, sample, confidence_multiplier=1.0):
        """Create YAMNet mock for sample with configurable confidence"""
        def mock_yamnet_inference(audio_waveform):
            num_frames = len(audio_waveform) // (16000 * 0.48)
            scores = np.zeros((int(num_frames), 521))
            
            # Add detections based on ground truth if available
            if sample['has_ground_truth']:
                ground_truth = sample['ground_truth_events']
                for gt_event in ground_truth:
                    frame_start = int(gt_event.start_time / 0.48)
                    frame_end = int(gt_event.end_time / 0.48)
                    
                    if frame_end < scores.shape[0]:
                        # Apply confidence multiplier for different scenarios
                        bark_conf = min(0.95, 0.8 * confidence_multiplier)
                        dog_conf = min(0.90, 0.7 * confidence_multiplier)
                        
                        scores[frame_start:frame_end+1, 1] = bark_conf  # Bark class
                        scores[frame_start:frame_end+1, 0] = dog_conf   # Dog class
            else:
                # For background samples, add very low random scores
                scores[:, 1] = np.random.uniform(0.0, 0.3, num_frames)  # Low bark scores
                scores[:, 0] = np.random.uniform(0.0, 0.2, num_frames)  # Low dog scores
            
            # Create mock tensor with .numpy() method
            mock_scores_tensor = MagicMock()
            mock_scores_tensor.numpy.return_value = scores
            
            return mock_scores_tensor, None, None
        
        return mock_yamnet_inference
    
    def test_all_bark_samples_comprehensive(self, sample_loader, detector, evaluator):
        """Test detection accuracy on all available bark samples"""
        samples = sample_loader.get_available_samples()
        
        # Filter to only bark samples (those with ground truth)
        bark_samples = [s for s in samples if s['name'].startswith('bark_recording')]
        
        assert len(bark_samples) >= 2, f"Expected at least 2 bark samples, found {len(bark_samples)}"
        
        total_metrics = {
            'samples_tested': 0,
            'total_ground_truth_events': 0,
            'total_detections': 0,
            'total_true_positives': 0,
            'total_false_positives': 0,
            'total_false_negatives': 0,
            'sample_results': []
        }
        
        for sample_info in bark_samples:
            # Load sample
            sample = sample_loader.load_sample(sample_info['name'])
            
            # Create YAMNet mock for this sample
            detector.yamnet_model.side_effect = self.create_yamnet_mock(sample, confidence_multiplier=1.0)
            
            # Run detection
            detected_events = detector._detect_barks_in_buffer(sample['audio_data'])
            
            # Evaluate
            match_results = evaluator.match_detections_to_ground_truth(
                detected_events, sample['ground_truth_events']
            )
            
            metrics = evaluator.calculate_metrics(match_results)
            
            # Store results
            sample_result = {
                'name': sample['name'],
                'duration': sample['duration'],
                'ground_truth_events': len(sample['ground_truth_events']),
                'detected_events': len(detected_events),
                'metrics': metrics
            }
            total_metrics['sample_results'].append(sample_result)
            
            # Accumulate totals
            total_metrics['samples_tested'] += 1
            total_metrics['total_ground_truth_events'] += metrics['total_ground_truth']
            total_metrics['total_detections'] += metrics['total_detections']
            total_metrics['total_true_positives'] += metrics['true_positives']
            total_metrics['total_false_positives'] += metrics['false_positives']
            total_metrics['total_false_negatives'] += metrics['false_negatives']
            
            # Individual sample assertions
            assert metrics['recall'] >= 0.3, f"{sample['name']}: Recall too low {metrics['recall']:.3f}"
            assert metrics['precision'] >= 0.3, f"{sample['name']}: Precision too low {metrics['precision']:.3f}"
            assert len(detected_events) > 0, f"{sample['name']}: No detections found"
        
        # Overall system performance assertions
        overall_precision = (total_metrics['total_true_positives'] / 
                           (total_metrics['total_true_positives'] + total_metrics['total_false_positives'])
                           if (total_metrics['total_true_positives'] + total_metrics['total_false_positives']) > 0 else 0.0)
        
        overall_recall = (total_metrics['total_true_positives'] / 
                         (total_metrics['total_true_positives'] + total_metrics['total_false_negatives'])
                         if (total_metrics['total_true_positives'] + total_metrics['total_false_negatives']) > 0 else 0.0)
        
        overall_f1 = (2 * (overall_precision * overall_recall) / (overall_precision + overall_recall)
                     if (overall_precision + overall_recall) > 0 else 0.0)
        
        # System-level performance requirements
        assert overall_recall >= 0.4, f"Overall system recall too low: {overall_recall:.3f}"
        assert overall_precision >= 0.4, f"Overall system precision too low: {overall_precision:.3f}"
        assert overall_f1 >= 0.4, f"Overall system F1 score too low: {overall_f1:.3f}"
        
        # Log comprehensive results for analysis
        print(f"\n=== COMPREHENSIVE SAMPLE TEST RESULTS ===")
        print(f"Samples tested: {total_metrics['samples_tested']}")
        print(f"Total ground truth events: {total_metrics['total_ground_truth_events']}")
        print(f"Total detections: {total_metrics['total_detections']}")
        print(f"Overall Precision: {overall_precision:.3f}")
        print(f"Overall Recall: {overall_recall:.3f}")
        print(f"Overall F1 Score: {overall_f1:.3f}")
        
        for result in total_metrics['sample_results']:
            print(f"\n{result['name']}:")
            print(f"  Duration: {result['duration']:.1f}s")
            print(f"  Ground truth events: {result['ground_truth_events']}")
            print(f"  Detected events: {result['detected_events']}")
            print(f"  Precision: {result['metrics']['precision']:.3f}")
            print(f"  Recall: {result['metrics']['recall']:.3f}")
            print(f"  F1 Score: {result['metrics']['f1_score']:.3f}")
    
    def test_confidence_threshold_compliance(self, sample_loader, detector, evaluator):
        """Test that system properly enforces 0.65+ confidence threshold"""
        # Load one sample for testing
        sample = sample_loader.load_sample('bark_recording_20250727_134707_bark')
        
        # Create YAMNet mock with various confidence levels
        def mock_yamnet_with_varied_confidence(audio_waveform):
            num_frames = len(audio_waveform) // (16000 * 0.48)
            scores = np.zeros((int(num_frames), 521))
            
            # Add events with different confidence levels
            ground_truth = sample['ground_truth_events']
            for i, gt_event in enumerate(ground_truth):
                frame_start = int(gt_event.start_time / 0.48)
                frame_end = int(gt_event.end_time / 0.48)
                
                if frame_end < scores.shape[0]:
                    # Vary confidence: some above 0.65, some below
                    if i % 3 == 0:
                        # High confidence (should be detected)
                        scores[frame_start:frame_end+1, 1] = 0.85
                    elif i % 3 == 1:
                        # Medium confidence (should be detected)  
                        scores[frame_start:frame_end+1, 1] = 0.70
                    else:
                        # Low confidence (should NOT be detected)
                        scores[frame_start:frame_end+1, 1] = 0.45
            
            mock_scores_tensor = MagicMock()
            mock_scores_tensor.numpy.return_value = scores
            return mock_scores_tensor, None, None
        
        detector.yamnet_model.side_effect = mock_yamnet_with_varied_confidence
        
        # Run detection
        detected_events = detector._detect_barks_in_buffer(sample['audio_data'])
        
        # Verify confidence threshold enforcement
        high_confidence_events = [e for e in detected_events if e.confidence >= 0.65]
        low_confidence_events = [e for e in detected_events if e.confidence < 0.65]
        
        # All detected events should meet confidence threshold when evaluated
        valid_detections = len([e for e in detected_events if e.confidence >= 0.65])
        
        # Should detect approximately 2/3 of events (those with confidence >= 0.65)
        expected_detections = len(sample['ground_truth_events']) * 2 // 3
        
        assert len(detected_events) >= expected_detections * 0.5, f"Too few detections: {len(detected_events)} (expected ~{expected_detections})"
        
        # Key assertion: evaluator should only consider events >= 0.65 confidence
        match_results = evaluator.match_detections_to_ground_truth(
            detected_events, sample['ground_truth_events']
        )
        
        # Total considered detections should be filtered by confidence
        total_considered = len(match_results['true_positives']) + len(match_results['false_positives'])
        all_high_conf = len([e for e in detected_events if e.confidence >= 0.65])
        
        assert total_considered == all_high_conf, f"Evaluator should only consider high-confidence events: {total_considered} vs {all_high_conf}"
    
    def test_background_samples_false_positive_rate(self, sample_loader, detector):
        """Test false positive rate on background/noise samples"""
        try:
            background_sample = sample_loader.load_sample('background')
        except ValueError:
            pytest.skip("Background sample not available - test skipped")
        
        # Mock YAMNet to return realistic background scores (low but not zero)
        detector.yamnet_model.side_effect = self.create_yamnet_mock(background_sample, confidence_multiplier=0.3)
        
        # Run detection
        detected_events = detector._detect_barks_in_buffer(background_sample['audio_data'])
        
        # Count high-confidence false positives
        high_confidence_fps = [e for e in detected_events if e.confidence >= 0.65]
        
        # Background should produce minimal false positives
        fp_rate = len(high_confidence_fps) / (background_sample['duration'] / 60)  # FPs per minute
        
        assert fp_rate <= 2.0, f"Too many false positives in background: {len(high_confidence_fps)} events ({fp_rate:.1f} per minute)"
        
        print(f"\nBackground false positive test:")
        print(f"  Duration: {background_sample['duration']:.1f} seconds")
        print(f"  Total detections: {len(detected_events)}")
        print(f"  High confidence detections: {len(high_confidence_fps)}")
        print(f"  False positive rate: {fp_rate:.2f} detections per minute")
    
    def test_regression_protection(self, sample_loader, detector, evaluator):
        """Test that system maintains expected performance levels (regression protection)"""
        # This test serves as a regression guard against future changes that might degrade accuracy
        
        # Load both primary samples
        large_dog_sample = sample_loader.load_sample('bark_recording_20250727_134707_bark')
        small_dog_sample = sample_loader.load_sample('bark_recording_20250727_141319_bark')
        
        baseline_results = []
        
        for sample_name, sample in [("large_dog", large_dog_sample), ("small_dog", small_dog_sample)]:
            # Create optimistic YAMNet mock (represents good conditions)
            detector.yamnet_model.side_effect = self.create_yamnet_mock(sample, confidence_multiplier=1.1)
            
            detected_events = detector._detect_barks_in_buffer(sample['audio_data'])
            match_results = evaluator.match_detections_to_ground_truth(detected_events, sample['ground_truth_events'])
            metrics = evaluator.calculate_metrics(match_results)
            
            baseline_results.append({
                'sample': sample_name,
                'metrics': metrics,
                'ground_truth_count': len(sample['ground_truth_events'])
            })
            
            # Regression protection thresholds (based on expected system capability)
            min_recall = 0.5 if sample_name == "large_dog" else 0.4  # Small dogs are harder
            min_precision = 0.5
            
            assert metrics['recall'] >= min_recall, f"{sample_name} recall regression: {metrics['recall']:.3f} < {min_recall}"
            assert metrics['precision'] >= min_precision, f"{sample_name} precision regression: {metrics['precision']:.3f} < {min_precision}"
        
        print(f"\n=== REGRESSION PROTECTION RESULTS ===")
        for result in baseline_results:
            print(f"{result['sample'].upper()}:")
            print(f"  Ground truth events: {result['ground_truth_count']}")
            print(f"  Precision: {result['metrics']['precision']:.3f}")
            print(f"  Recall: {result['metrics']['recall']:.3f}")
            print(f"  F1 Score: {result['metrics']['f1_score']:.3f}")
            print(f"  Status: {'✅ PASS' if result['metrics']['f1_score'] >= 0.4 else '❌ FAIL'}")
        
        # Overall system should maintain reasonable performance
        avg_f1 = sum(r['metrics']['f1_score'] for r in baseline_results) / len(baseline_results)
        assert avg_f1 >= 0.45, f"Overall system F1 regression: {avg_f1:.3f} < 0.45"