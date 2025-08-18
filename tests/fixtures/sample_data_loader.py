"""Sample data loading utilities for real-world bark detection testing"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

import librosa
import numpy as np

logger = logging.getLogger(__name__)


class GroundTruthEvent:
    """Represents a ground truth bark event from sample data"""
    
    def __init__(self, start_time: float, end_time: float, description: str, 
                 confidence_expected: float = 1.0):
        self.start_time = start_time
        self.end_time = end_time  
        self.duration = end_time - start_time
        self.description = description
        self.confidence_expected = confidence_expected
    
    def __repr__(self):
        return f"GroundTruthEvent({self.start_time:.3f}-{self.end_time:.3f}s, '{self.description}')"


class SampleDataLoader:
    """Loads and processes sample audio files with ground truth annotations"""
    
    def __init__(self, samples_dir: Path = None):
        if samples_dir is None:
            samples_dir = Path(__file__).parent.parent.parent / "samples"
        self.samples_dir = Path(samples_dir)
        logger.debug(f"SampleDataLoader initialized with directory: {self.samples_dir}")
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse HH:MM:SS.mmm timestamp to seconds"""
        try:
            # Handle both HH:MM:SS.mmm and MM:SS.mmm formats
            parts = timestamp_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
            else:
                return float(timestamp_str)
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing timestamp '{timestamp_str}': {e}")
            return 0.0
    
    def load_ground_truth(self, ground_truth_path: Path) -> Tuple[List[GroundTruthEvent], Dict]:
        """Load ground truth events from JSON file"""
        with open(ground_truth_path, 'r') as f:
            data = json.load(f)
        
        events = []
        for event_data in data.get('events', []):
            start_time = self._parse_timestamp(event_data['start_time'])
            end_time = self._parse_timestamp(event_data['end_time'])
            
            event = GroundTruthEvent(
                start_time=start_time,
                end_time=end_time,
                description=event_data.get('description', ''),
                confidence_expected=event_data.get('confidence_expected', 1.0)
            )
            events.append(event)
        
        # Return events and metadata
        metadata = {
            'audio_file': data.get('audio_file', ''),
            'duration': data.get('duration', 0.0),
            'format_version': data.get('format_version', '1.0'),
            'total_events': len(events)
        }
        
        logger.info(f"Loaded {len(events)} ground truth events from {ground_truth_path.name}")
        return events, metadata
    
    def load_audio(self, audio_path: Path, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
        """Load audio file and resample to target sample rate"""
        try:
            audio_data, sr = librosa.load(str(audio_path), sr=target_sr)
            logger.debug(f"Loaded audio: {audio_path.name}, duration: {len(audio_data)/sr:.2f}s")
            return audio_data, sr
        except Exception as e:
            logger.error(f"Error loading audio file {audio_path}: {e}")
            raise
    
    def get_available_samples(self) -> List[Dict[str, Path]]:
        """Get list of available sample files with their ground truth"""
        samples = []
        
        # Look for ground truth files and match with audio files
        for gt_file in self.samples_dir.glob("*_ground_truth.json"):
            if gt_file.name.endswith('.json.backup'):
                continue
            
            # Extract base name to find corresponding audio file
            base_name = gt_file.name.replace('_ground_truth.json', '')
            
            # Try to find corresponding audio file
            audio_extensions = ['.wav', '.m4a', '.mp3']
            audio_file = None
            
            for ext in audio_extensions:
                potential_audio = self.samples_dir / f"{base_name}{ext}"
                if potential_audio.exists():
                    audio_file = potential_audio
                    break
            
            if audio_file:
                samples.append({
                    'name': base_name,
                    'audio_file': audio_file,
                    'ground_truth_file': gt_file
                })
            else:
                logger.warning(f"No audio file found for ground truth: {gt_file.name}")
        
        # Also check for background samples (negative examples)
        background_files = ['background.wav', 'noise.wav', 'silence.wav']
        for bg_file in background_files:
            bg_path = self.samples_dir / bg_file
            if bg_path.exists():
                samples.append({
                    'name': bg_path.stem,
                    'audio_file': bg_path,
                    'ground_truth_file': None  # No ground truth for background
                })
        
        logger.info(f"Found {len(samples)} sample files in {self.samples_dir}")
        return samples
    
    def load_sample(self, sample_name: str) -> Dict:
        """Load a complete sample with audio and ground truth"""
        samples = self.get_available_samples()
        
        for sample in samples:
            if sample['name'] == sample_name:
                result = {
                    'name': sample['name'],
                    'audio_path': sample['audio_file']
                }
                
                # Load audio
                result['audio_data'], result['sample_rate'] = self.load_audio(sample['audio_file'])
                result['duration'] = len(result['audio_data']) / result['sample_rate']
                
                # Load ground truth if available
                if sample['ground_truth_file']:
                    result['ground_truth_events'], result['metadata'] = self.load_ground_truth(sample['ground_truth_file'])
                    result['has_ground_truth'] = True
                else:
                    result['ground_truth_events'] = []
                    result['metadata'] = {}
                    result['has_ground_truth'] = False
                
                return result
        
        raise ValueError(f"Sample '{sample_name}' not found in {self.samples_dir}")


class DetectionEvaluator:
    """Evaluate bark detection results against ground truth"""
    
    def __init__(self, tolerance_seconds: float = 1.0, min_confidence: float = 0.65):
        self.tolerance = tolerance_seconds
        self.min_confidence = min_confidence
        logger.debug(f"DetectionEvaluator: tolerance={tolerance_seconds}s, min_confidence={min_confidence}")
    
    def calculate_overlap(self, detected_start: float, detected_end: float, 
                         truth_start: float, truth_end: float) -> float:
        """Calculate overlap between detected and ground truth events"""
        overlap_start = max(detected_start, truth_start)
        overlap_end = min(detected_end, truth_end)
        
        if overlap_end > overlap_start:
            overlap = overlap_end - overlap_start
            truth_duration = truth_end - truth_start
            return overlap / truth_duration if truth_duration > 0 else 0.0
        return 0.0
    
    def match_detections_to_ground_truth(self, detected_events: List, 
                                       ground_truth_events: List[GroundTruthEvent]) -> Dict:
        """Match detected events to ground truth with tolerance window"""
        results = {
            'true_positives': [],
            'false_positives': [],
            'false_negatives': [],
            'matched_pairs': []
        }
        
        # Filter detections by confidence
        valid_detections = [
            event for event in detected_events 
            if getattr(event, 'confidence', 0.0) >= self.min_confidence
        ]
        
        matched_gt_indices = set()
        matched_detection_indices = set()
        
        # Find matches
        for i, detection in enumerate(valid_detections):
            best_match = None
            best_overlap = 0.0
            best_gt_idx = -1
            
            for j, gt_event in enumerate(ground_truth_events):
                if j in matched_gt_indices:
                    continue
                
                # Check if events are within tolerance window
                time_diff = abs(detection.start_time - gt_event.start_time)
                if time_diff <= self.tolerance:
                    overlap = self.calculate_overlap(
                        detection.start_time, detection.end_time,
                        gt_event.start_time, gt_event.end_time
                    )
                    
                    if overlap > best_overlap and overlap > 0.1:  # Minimum 10% overlap
                        best_match = gt_event
                        best_overlap = overlap
                        best_gt_idx = j
            
            if best_match:
                results['true_positives'].append(detection)
                results['matched_pairs'].append((detection, best_match, best_overlap))
                matched_gt_indices.add(best_gt_idx)
                matched_detection_indices.add(i)
        
        # Unmatched detections are false positives
        for i, detection in enumerate(valid_detections):
            if i not in matched_detection_indices:
                results['false_positives'].append(detection)
        
        # Unmatched ground truth events are false negatives
        for j, gt_event in enumerate(ground_truth_events):
            if j not in matched_gt_indices:
                results['false_negatives'].append(gt_event)
        
        return results
    
    def calculate_metrics(self, match_results: Dict) -> Dict[str, float]:
        """Calculate precision, recall, and F1 score"""
        tp = len(match_results['true_positives'])
        fp = len(match_results['false_positives'])
        fn = len(match_results['false_negatives'])
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'total_detections': tp + fp,
            'total_ground_truth': tp + fn
        }