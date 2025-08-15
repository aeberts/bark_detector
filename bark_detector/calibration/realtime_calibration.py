"""Real-time calibration with human feedback"""

import sys
import time
import select
import termios
import tty
import logging
from datetime import datetime

from ..core.models import BarkEvent, CalibrationProfile

logger = logging.getLogger(__name__)


class CalibrationMode:
    """Real-time calibration with human feedback."""
    
    def __init__(self, detector, duration_minutes: int = 10):
        self.detector = detector
        self.duration_seconds = duration_minutes * 60
        self.start_time = time.time()
        
        # Feedback tracking
        self.human_marks = []
        self.system_detections = []
        self.sensitivity_history = []
        
        # Terminal settings for non-blocking input
        self.original_settings = None
        self.is_calibrating = False
        
    def start_calibration(self):
        """Start real-time calibration mode."""
        logger.info("🎯 Starting Real-Time Calibration Mode")
        logger.info(f"Duration: {self.duration_seconds/60:.1f} minutes")
        logger.info("Instructions:")
        logger.info("  [SPACE] - Mark when you hear a bark")
        logger.info("  [ESC] - Finish calibration early")
        logger.info("  [Q] - Quit without saving")
        logger.info("")
        
        # Setup non-blocking keyboard input
        self._setup_keyboard()
        self.is_calibrating = True
        
        # Start calibration loop
        try:
            return self._calibration_loop()
        finally:
            self._cleanup_keyboard()
            
    def _setup_keyboard(self):
        """Setup non-blocking keyboard input."""
        if sys.platform != 'win32':
            try:
                self.original_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
            except Exception as e:
                logger.warning(f"Could not setup keyboard input: {e}")
                self.original_settings = None
    
    def _cleanup_keyboard(self):
        """Restore original keyboard settings."""
        if sys.platform != 'win32' and self.original_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
            except Exception as e:
                logger.warning(f"Could not restore keyboard settings: {e}")
    
    def _check_keyboard_input(self):
        """Check for keyboard input without blocking."""
        if sys.platform == 'win32':
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                return key.decode('utf-8') if isinstance(key, bytes) else key
        else:
            if self.original_settings is None:
                return None
                
            try:
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    return key
            except Exception:
                pass
        return None
    
    def _calibration_loop(self):
        """Main calibration loop."""
        last_status_update = time.time()
        last_optimization = time.time()
        
        while self.is_calibrating:
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Check if calibration time is up
            if elapsed >= self.duration_seconds:
                logger.info("⏰ Calibration time completed")
                break
            
            # Check for keyboard input
            key = self._check_keyboard_input()
            if key:
                if key == ' ':  # Spacebar
                    self._mark_human_bark(current_time)
                elif key == '\x1b':  # ESC
                    logger.info("🛑 Calibration ended by user")
                    break
                elif key.lower() == 'q':
                    logger.info("❌ Calibration cancelled")
                    return None
            
            # Update status every 5 seconds
            if current_time - last_status_update >= 5.0:
                self._show_status(elapsed)
                last_status_update = current_time
            
            # Auto-optimize sensitivity every 30 seconds
            if current_time - last_optimization >= 30.0:
                self._auto_optimize_sensitivity()
                last_optimization = current_time
            
            time.sleep(0.1)
        
        # Generate calibration results
        return self._generate_calibration_results()
    
    def _mark_human_bark(self, timestamp: float):
        """Record human bark marking."""
        relative_time = timestamp - self.start_time
        self.human_marks.append(relative_time)
        logger.info(f"👤 Human marked bark at {relative_time:.1f}s")
    
    def record_system_detection(self, bark_event: BarkEvent):
        """Record system detection (called by detector)."""
        detection_time = time.time() - self.start_time
        self.system_detections.append({
            'time': detection_time,
            'confidence': bark_event.confidence,
            'intensity': getattr(bark_event, 'intensity', 0.5),
            'duration': bark_event.end_time - bark_event.start_time
        })
    
    def _show_status(self, elapsed: float):
        """Show calibration status."""
        remaining = (self.duration_seconds - elapsed) / 60
        human_count = len(self.human_marks)
        system_count = len(self.system_detections)
        
        # Calculate match rate
        matches, false_pos, missed = self._calculate_matches()
        match_rate = matches / max(human_count, 1) * 100
        
        # Clear screen and show status
        print(f"\r\033[K🎯 Calibration: {elapsed/60:.1f}m / {self.duration_seconds/60:.1f}m remaining", end="")
        print(f"\r\033[K📊 Human: {human_count} | System: {system_count} | Match: {match_rate:.0f}% | Sensitivity: {self.detector.sensitivity:.3f}")
        print(f"\r\033[K✅ Matches: {matches} | ❌ False+: {false_pos} | ❓ Missed: {missed}")
        
    def _calculate_matches(self, tolerance: float = 3.0):
        """Calculate matches between human marks and system detections."""
        matches = 0
        false_positives = 0
        
        # Find matches (system detection within tolerance of human mark)
        matched_detections = set()
        
        for human_time in self.human_marks:
            for i, detection in enumerate(self.system_detections):
                if i in matched_detections:
                    continue
                if abs(detection['time'] - human_time) <= tolerance:
                    matches += 1
                    matched_detections.add(i)
                    break
        
        # Count false positives (unmatched detections)
        false_positives = len(self.system_detections) - len(matched_detections)
        
        # Count missed (unmatched human marks)
        missed = len(self.human_marks) - matches
        
        return matches, false_positives, missed
    
    def _auto_optimize_sensitivity(self):
        """Automatically adjust sensitivity based on feedback."""
        if len(self.human_marks) < 2 or len(self.system_detections) < 2:
            return
        
        matches, false_pos, missed = self._calculate_matches()
        
        # Calculate current performance
        precision = matches / max(len(self.system_detections), 1)
        recall = matches / max(len(self.human_marks), 1)
        
        # Adjust sensitivity
        current_sensitivity = self.detector.sensitivity
        new_sensitivity = current_sensitivity
        
        if false_pos > missed:
            # Too many false positives - decrease sensitivity
            new_sensitivity = current_sensitivity * 0.9
        elif missed > false_pos:
            # Missing too many - increase sensitivity  
            new_sensitivity = current_sensitivity * 1.1
        
        # Clamp to reasonable range
        new_sensitivity = max(0.01, min(1.0, new_sensitivity))
        
        if abs(new_sensitivity - current_sensitivity) > 0.005:
            self.detector.sensitivity = new_sensitivity
            self.sensitivity_history.append({
                'time': time.time() - self.start_time,
                'sensitivity': new_sensitivity,
                'precision': precision,
                'recall': recall
            })
            logger.info(f"🎛️ Auto-adjusted sensitivity: {current_sensitivity:.3f} → {new_sensitivity:.3f}")
    
    def _generate_calibration_results(self):
        """Generate final calibration results."""
        matches, false_pos, missed = self._calculate_matches()
        
        precision = matches / max(len(self.system_detections), 1)
        recall = matches / max(len(self.human_marks), 1)
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        
        results = {
            'optimal_sensitivity': self.detector.sensitivity,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'human_marks': len(self.human_marks),
            'system_detections': len(self.system_detections),
            'matches': matches,
            'false_positives': false_pos,
            'missed': missed,
            'calibration_duration': time.time() - self.start_time
        }
        
        logger.info("🎯 Calibration Results:")
        logger.info(f"  Optimal Sensitivity: {results['optimal_sensitivity']:.3f}")
        logger.info(f"  Precision: {precision:.1%} (accuracy of detections)")
        logger.info(f"  Recall: {recall:.1%} (% of barks caught)")
        logger.info(f"  F1 Score: {f1_score:.3f} (overall performance)")
        
        return results
    
    def create_calibration_profile(self, results: dict, name: str = None) -> CalibrationProfile:
        """Create a calibration profile from results."""
        if name is None:
            name = f"realtime-calib-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile = CalibrationProfile(
            name=name,
            sensitivity=results['optimal_sensitivity'],
            min_bark_duration=0.5,
            session_gap_threshold=10.0,
            background_noise_level=0.01,
            created_date=datetime.now().isoformat(),
            location="Real-time Calibration",
            notes=f"F1={results['f1_score']:.3f}, P={results['precision']:.1%}, "
                  f"R={results['recall']:.1%}, Duration={results['calibration_duration']/60:.1f}m"
        )
        
        return profile