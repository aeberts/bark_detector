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
                try:
                    # Use from_dict for better format handling and validation
                    events.append(GroundTruthEvent.from_dict(event_data))
                except ValueError as e:
                    logger.warning(f"Skipping invalid ground truth event in {ground_truth_path}: {e}")
                    continue
            
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
        
        # Run detailed class analysis at optimal sensitivity
        logger.info("")
        logger.info("🔍 Running Class Analysis for False Positive Detection...")
        class_analysis = self._analyze_false_positive_classes(best_result['sensitivity'])
        
        return {
            'optimal_sensitivity': best_result['sensitivity'],
            'best_result': best_result,
            'all_results': sweep_results,
            'class_analysis': class_analysis
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
    
    def _analyze_false_positive_classes(self, optimal_sensitivity: float) -> Dict:
        """Analyze which YAMNet classes are causing false positives at optimal sensitivity."""
        logger.info(f"🔬 Analyzing class breakdown at sensitivity {optimal_sensitivity:.3f}")
        
        # Set detector to optimal sensitivity for analysis
        original_sensitivity = self.detector.sensitivity
        self.detector.sensitivity = optimal_sensitivity
        
        try:
            false_positive_classes = {}
            true_positive_classes = {}
            background_classes = {}
            
            for test_file in self.test_files:
                analysis = self._analyze_file_classes(test_file)
                
                # Accumulate class statistics
                for class_name, count in analysis['false_positive_classes'].items():
                    false_positive_classes[class_name] = false_positive_classes.get(class_name, 0) + count
                
                for class_name, count in analysis['true_positive_classes'].items():
                    true_positive_classes[class_name] = true_positive_classes.get(class_name, 0) + count
                
                # Special handling for background file analysis
                if len(test_file['ground_truth']) == 0:  # Background file
                    for class_name, count in analysis['detected_classes'].items():
                        background_classes[class_name] = background_classes.get(class_name, 0) + count
            
            # Generate analysis report
            self._log_class_analysis_results(false_positive_classes, true_positive_classes, background_classes)
            
            return {
                'false_positive_classes': false_positive_classes,
                'true_positive_classes': true_positive_classes, 
                'background_classes': background_classes,
                'total_false_positives': sum(false_positive_classes.values()),
                'total_true_positives': sum(true_positive_classes.values()),
                'total_background_detections': sum(background_classes.values())
            }
            
        finally:
            # Restore original sensitivity
            self.detector.sensitivity = original_sensitivity
    
    def _analyze_file_classes(self, test_file: Dict) -> Dict:
        """Analyze class breakdown for a single file."""
        from ..utils.audio_converter import AudioFileConverter
        
        audio_path = test_file['audio_path'] 
        ground_truth = test_file['ground_truth']
        
        # Load and process audio
        import soundfile as sf
        audio_data, sample_rate = sf.read(audio_path)
        
        # Convert to mono if needed
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
        
        # Detect events with class information
        detected_events = self.detector._detect_barks_in_buffer(audio_data)
        
        # Classify detections as true positive or false positive
        false_positive_classes = {}
        true_positive_classes = {}
        detected_classes = {}
        
        for event in detected_events:
            # Count all detected classes
            if event.triggering_classes:
                for class_name in event.triggering_classes:
                    detected_classes[class_name] = detected_classes.get(class_name, 0) + 1
            
            # Check if this detection matches any ground truth
            is_true_positive = False
            for gt_event in ground_truth:
                if self._events_overlap(event, gt_event):
                    is_true_positive = True
                    break
            
            # Categorize by true/false positive
            if event.triggering_classes:
                target_dict = true_positive_classes if is_true_positive else false_positive_classes
                for class_name in event.triggering_classes:
                    target_dict[class_name] = target_dict.get(class_name, 0) + 1
        
        return {
            'detected_classes': detected_classes,
            'false_positive_classes': false_positive_classes,
            'true_positive_classes': true_positive_classes,
            'total_detections': len(detected_events)
        }
    
    def _log_class_analysis_results(self, false_positive_classes: Dict, 
                                   true_positive_classes: Dict, background_classes: Dict):
        """Log detailed class analysis results."""
        logger.info("📊 Class Analysis Results:")
        logger.info("")
        
        # Show false positive classes (most important)
        if false_positive_classes:
            logger.info("❌ Classes Contributing to False Positives:")
            sorted_fp = sorted(false_positive_classes.items(), key=lambda x: x[1], reverse=True)
            for class_name, count in sorted_fp:
                percentage = (count / sum(false_positive_classes.values())) * 100
                logger.info(f"   {class_name}: {count} detections ({percentage:.1f}%)")
        
        # Show background detections (environmental noise)
        if background_classes:
            logger.info("")
            logger.info("🌍 Classes Detected in Background Audio (Environmental Noise):")
            sorted_bg = sorted(background_classes.items(), key=lambda x: x[1], reverse=True)
            for class_name, count in sorted_bg:
                percentage = (count / sum(background_classes.values())) * 100 if background_classes else 0
                logger.info(f"   {class_name}: {count} detections ({percentage:.1f}%)")
        
        # Show true positive classes (good classes to keep)
        if true_positive_classes:
            logger.info("")
            logger.info("✅ Classes Contributing to True Positives (Keep These):")
            sorted_tp = sorted(true_positive_classes.items(), key=lambda x: x[1], reverse=True)
            for class_name, count in sorted_tp:
                percentage = (count / sum(true_positive_classes.values())) * 100
                logger.info(f"   {class_name}: {count} detections ({percentage:.1f}%)")
        
        # Provide recommendations
        logger.info("")
        self._provide_class_recommendations(false_positive_classes, true_positive_classes, background_classes)
    
    def _provide_class_recommendations(self, false_positive_classes: Dict, 
                                     true_positive_classes: Dict, background_classes: Dict):
        """Provide recommendations for improving accuracy."""
        logger.info("💡 Recommendations for Accuracy Improvement:")
        
        # Find classes that are only false positives (candidates for removal)
        problematic_classes = []
        for class_name, fp_count in false_positive_classes.items():
            tp_count = true_positive_classes.get(class_name, 0)
            if tp_count == 0 and fp_count > 0:
                problematic_classes.append((class_name, fp_count))
        
        if problematic_classes:
            logger.info("🚫 Consider removing these classes (only false positives):")
            for class_name, count in sorted(problematic_classes, key=lambda x: x[1], reverse=True):
                logger.info(f"   - {class_name} ({count} false positives, 0 true positives)")
        
        # Find classes with poor precision
        poor_precision_classes = []
        for class_name, fp_count in false_positive_classes.items():
            tp_count = true_positive_classes.get(class_name, 0)
            total = fp_count + tp_count
            if total > 0:
                precision = tp_count / total
                if precision < 0.5 and total >= 2:  # Less than 50% precision with at least 2 detections
                    poor_precision_classes.append((class_name, precision, total))
        
        if poor_precision_classes:
            logger.info("⚠️  Consider downweighting these classes (poor precision):")
            for class_name, precision, total in sorted(poor_precision_classes, key=lambda x: x[1]):
                logger.info(f"   - {class_name}: {precision:.1%} precision ({total} total detections)")
        
        # Environmental noise analysis
        if background_classes:
            logger.info("🌍 Environmental noise sources to filter:")
            for class_name, count in sorted(background_classes.items(), key=lambda x: x[1], reverse=True)[:3]:
                logger.info(f"   - {class_name}: {count} detections in background audio")
    
    def _events_overlap(self, detected_event, ground_truth_event, tolerance: float = 0.5) -> bool:
        """Check if a detected event overlaps with a ground truth event."""
        # Get time ranges
        det_start = detected_event.start_time
        det_end = detected_event.end_time
        gt_start = ground_truth_event.start_time
        gt_end = ground_truth_event.end_time
        
        # Check for overlap with tolerance
        overlap_start = max(det_start, gt_start - tolerance)
        overlap_end = min(det_end, gt_end + tolerance)
        
        return overlap_start < overlap_end