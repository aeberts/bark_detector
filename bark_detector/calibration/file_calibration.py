"""File-based calibration system"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from ..core.models import CalibrationProfile, GroundTruthEvent

logger = logging.getLogger(__name__)


class FileBasedCalibration:
    """File-based calibration using ground truth timestamps."""
    
    def __init__(self, detector):
        """Initialize file-based calibration."""
        self.detector = detector
        self.test_files = []
        self.results = []
    
    def add_test_file(self, audio_path: Path, ground_truth_path: Path = None, 
                     ground_truth_events: List[GroundTruthEvent] = None):
        """Add a test file with ground truth data."""
        # Validate and potentially convert audio file
        converted_path = self._ensure_compatible_audio(audio_path)
        
        if ground_truth_path and ground_truth_path.exists():
            # Load ground truth from JSON file
            with open(ground_truth_path, 'r') as f:
                gt_data = json.load(f)
            
            events = []
            for event_data in gt_data.get('events', []):
                events.append(GroundTruthEvent(
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    description=event_data.get('description', ''),
                    confidence_expected=event_data.get('confidence_expected', 1.0)
                ))
            
        elif ground_truth_events:
            events = ground_truth_events
        else:
            # No ground truth - assume this is a negative file (no barks)
            events = []
            
        self.test_files.append({
            'audio_path': converted_path,
            'original_path': audio_path,
            'ground_truth': events,
            'is_negative': len(events) == 0
        })
        
        logger.info(f"📁 Added test file: {audio_path.name} ({len(events)} ground truth events)")
    
    def _ensure_compatible_audio(self, audio_path: Path) -> Path:
        """Ensure audio file is in compatible format (WAV, 16kHz)."""
        supported_extensions = ['.wav', '.m4a', '.mp3', '.aac', '.flac']
        
        if audio_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported audio format: {audio_path.suffix}")
        
        # If already WAV, check if it needs resampling
        if audio_path.suffix.lower() == '.wav':
            try:
                import soundfile as sf
                info = sf.info(str(audio_path))
                if info.samplerate == 16000 and info.channels == 1:
                    return audio_path  # Already in correct format
            except Exception:
                pass  # Fall through to conversion
        
        # Convert to WAV 16kHz mono
        converted_path = self._convert_audio_file(audio_path)
        return converted_path
    
    def _convert_audio_file(self, audio_path: Path) -> Path:
        """Convert audio file to WAV 16kHz mono format."""
        import librosa
        import soundfile as sf
        
        # Create converted file path
        converted_dir = audio_path.parent / 'converted'
        converted_dir.mkdir(exist_ok=True)
        converted_path = converted_dir / f"{audio_path.stem}_16khz.wav"
        
        # Skip if already converted
        if converted_path.exists():
            logger.info(f"🔄 Using existing converted file: {converted_path.name}")
            return converted_path
        
        try:
            logger.info(f"🔄 Converting {audio_path.name} to WAV 16kHz...")
            
            # Load and convert
            audio_data, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
            
            # Save as WAV
            sf.write(str(converted_path), audio_data, 16000, subtype='PCM_16')
            
            duration = len(audio_data) / 16000
            logger.info(f"✅ Converted: {converted_path.name} ({duration:.1f}s)")
            
            return converted_path
            
        except Exception as e:
            logger.error(f"❌ Failed to convert {audio_path}: {e}")
            raise
    
    def calibrate_from_files(self, audio_files: List[Path], 
                           sensitivity_range: Tuple[float, float] = (0.1, 0.9),
                           steps: int = 20) -> CalibrationProfile:
        """Calibrate detector using audio files."""
        logger.info(f"🔍 Starting file-based calibration with {len(audio_files)} files")
        
        # Add all files (assuming they have corresponding ground truth files)
        for audio_file in audio_files:
            gt_file = audio_file.with_suffix('.json')
            self.add_test_file(audio_file, gt_file if gt_file.exists() else None)
        
        if not self.test_files:
            raise ValueError("No test files added with valid ground truth")
        
        # Run sensitivity sweep
        calibration_results = self.run_sensitivity_sweep(sensitivity_range, steps)
        
        # Create calibration profile
        profile_name = f"file-calib-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        profile = CalibrationProfile(
            name=profile_name,
            sensitivity=calibration_results['optimal_sensitivity'],
            min_bark_duration=0.5,
            session_gap_threshold=10.0,
            background_noise_level=0.01,
            created_date=datetime.now().isoformat(),
            location="File-based Calibration",
            notes=f"F1={calibration_results['best_result']['f1_score']:.3f}, "
                  f"P={calibration_results['best_result']['precision']:.1%}, "
                  f"R={calibration_results['best_result']['recall']:.1%}, "
                  f"Files={len(self.test_files)}"
        )
        
        return profile
    
    def run_sensitivity_sweep(self, sensitivity_range: Tuple[float, float] = (0.01, 0.5), 
                            steps: int = 20) -> Dict:
        """Run calibration across a range of sensitivity values."""
        logger.info(f"🔍 Running sensitivity sweep: {sensitivity_range[0]:.3f} to {sensitivity_range[1]:.3f}")
        logger.info(f"📊 Testing {len(self.test_files)} files with {steps} sensitivity levels")
        
        if not self.test_files:
            raise ValueError("No test files added. Use add_test_file() first.")
        
        # Generate sensitivity values to test
        sensitivity_values = np.linspace(sensitivity_range[0], sensitivity_range[1], steps)
        
        sweep_results = []
        
        for i, sensitivity in enumerate(sensitivity_values):
            logger.info(f"🎛️  Testing sensitivity {sensitivity:.3f} ({i+1}/{steps})")
            
            # Set detector sensitivity
            original_sensitivity = self.detector.sensitivity
            self.detector.sensitivity = sensitivity
            
            # Test all files at this sensitivity
            file_results = []
            total_matches = 0
            total_false_positives = 0
            total_missed = 0
            total_ground_truth = 0
            
            for test_file in self.test_files:
                result = self._test_single_file(test_file, sensitivity)
                file_results.append(result)
                
                total_matches += result['matches']
                total_false_positives += result['false_positives']
                total_missed += result['missed']
                total_ground_truth += len(test_file['ground_truth'])
            
            # Calculate overall metrics
            precision = total_matches / max(total_matches + total_false_positives, 1)
            recall = total_matches / max(total_ground_truth, 1)
            f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
            
            sweep_result = {
                'sensitivity': sensitivity,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'total_matches': total_matches,
                'total_false_positives': total_false_positives,
                'total_missed': total_missed,
                'total_ground_truth': total_ground_truth,
                'file_results': file_results
            }
            
            sweep_results.append(sweep_result)
            logger.info(f"   Precision: {precision:.1%}, Recall: {recall:.1%}, F1: {f1_score:.3f}")
        
        # Restore original sensitivity
        self.detector.sensitivity = original_sensitivity
        
        # Find optimal sensitivity
        best_result = max(sweep_results, key=lambda x: x['f1_score'])
        
        logger.info("🎯 Calibration Results:")
        logger.info(f"  Optimal Sensitivity: {best_result['sensitivity']:.3f}")
        logger.info(f"  Best F1 Score: {best_result['f1_score']:.3f}")
        logger.info(f"  Precision: {best_result['precision']:.1%}")
        logger.info(f"  Recall: {best_result['recall']:.1%}")
        logger.info(f"  Total Ground Truth Events: {best_result['total_ground_truth']}")
        logger.info(f"  Matches: {best_result['total_matches']}")
        logger.info(f"  False Positives: {best_result['total_false_positives']}")
        logger.info(f"  Missed: {best_result['total_missed']}")
        
        return {
            'optimal_sensitivity': best_result['sensitivity'],
            'best_result': best_result,
            'all_results': sweep_results
        }
    
    def _test_single_file(self, test_file: Dict, sensitivity: float) -> Dict:
        """Test detection on a single file."""
        audio_path = test_file['audio_path']
        ground_truth = test_file['ground_truth']
        
        try:
            # Load audio file
            import librosa
            audio_data, sample_rate = librosa.load(str(audio_path), sr=16000, mono=True)
            
            # Run detection
            detected_events = self.detector._detect_barks_in_buffer(audio_data)
            
            # Match detected events to ground truth
            matches = 0
            false_positives = 0
            tolerance = 0.5  # 500ms tolerance
            
            matched_gt = set()
            
            for detected in detected_events:
                matched = False
                for i, gt in enumerate(ground_truth):
                    if i in matched_gt:
                        continue
                    
                    # Check overlap
                    if (abs(detected.start_time - gt.start_time) <= tolerance or
                        abs(detected.end_time - gt.end_time) <= tolerance or
                        (detected.start_time <= gt.start_time <= detected.end_time) or
                        (gt.start_time <= detected.start_time <= gt.end_time)):
                        matches += 1
                        matched_gt.add(i)
                        matched = True
                        break
                
                if not matched:
                    false_positives += 1
            
            missed = len(ground_truth) - matches
            
            return {
                'audio_path': str(audio_path),
                'detected_events': len(detected_events),
                'ground_truth_events': len(ground_truth),
                'matches': matches,
                'false_positives': false_positives,
                'missed': missed
            }
            
        except Exception as e:
            logger.error(f"Error testing file {audio_path}: {e}")
            return {
                'audio_path': str(audio_path),
                'detected_events': 0,
                'ground_truth_events': len(ground_truth),
                'matches': 0,
                'false_positives': 0,
                'missed': len(ground_truth),
                'error': str(e)
            }