"""Manual recording mode for capturing calibration samples"""

import sys
import time
import select
import termios
import tty
import wave
import logging
from pathlib import Path

import pyaudio

logger = logging.getLogger(__name__)


class ManualRecorder:
    """Manual recording mode for capturing calibration samples."""
    
    def __init__(self, detector, output_path: Path):
        self.detector = detector
        self.output_path = Path(output_path)
        self.sample_rate = 16000
        self.channels = 1
        self.format = pyaudio.paInt16
        self.chunk_size = 1024
        
        # Audio recording
        self.audio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        
        # Terminal settings for non-blocking input
        self.original_settings = None
        
    def start_recording(self):
        """Start manual recording session."""
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎙️  Manual Recording Mode")
        logger.info(f"Output: {self.output_path}")
        logger.info(f"Format: WAV 16kHz Mono (YAMNet compatible)")
        logger.info("")
        logger.info("Controls:")
        logger.info("  [SPACE] - Start/Stop recording")
        logger.info("  [ESC] or [Q] - Finish and save")
        logger.info("  [Ctrl+C] - Cancel without saving")
        logger.info("")
        logger.info("Press SPACE to start recording...")
        
        # Setup audio
        self._setup_audio()
        
        # Setup keyboard
        self._setup_keyboard()
        
        try:
            self._recording_loop()
        except KeyboardInterrupt:
            logger.info("\\n❌ Recording cancelled by user")
        finally:
            self._cleanup()
            
    def _setup_audio(self):
        """Initialize PyAudio."""
        self.audio = pyaudio.PyAudio()
        
    def _setup_keyboard(self):
        """Setup non-blocking keyboard input."""
        if sys.platform != 'win32':
            self.original_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
    
    def _restore_keyboard(self):
        """Restore original keyboard settings."""
        if sys.platform != 'win32' and self.original_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
    
    def _get_key(self):
        """Get keyboard input without blocking."""
        if sys.platform == 'win32':
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                return key.decode('utf-8') if isinstance(key, bytes) else key
        else:
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                return key
        return None
    
    def _recording_loop(self):
        """Main recording loop."""
        running = True
        
        while running:
            key = self._get_key()
            
            if key:
                if key == ' ':  # Space - toggle recording
                    if self.is_recording:
                        self._stop_recording()
                    else:
                        self._start_recording()
                        
                elif key in ['\\x1b', 'q', 'Q']:  # ESC or Q - finish
                    if self.is_recording:
                        self._stop_recording()
                    self._save_recording()
                    running = False
                    
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
    
    def _start_recording(self):
        """Start audio recording."""
        if self.is_recording:
            return
            
        logger.info("🔴 Recording started... Press SPACE to stop")
        
        self.frames = []
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        self.is_recording = True
    
    def _stop_recording(self):
        """Stop audio recording."""
        if not self.is_recording:
            return
            
        logger.info("⏹️  Recording stopped. Press SPACE to record more, or ESC/Q to finish")
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for recording."""
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _save_recording(self):
        """Save recorded audio to file."""
        if not self.frames:
            logger.info("❌ No audio recorded")
            return
            
        try:
            # Combine all frames
            audio_data = b''.join(self.frames)
            
            # Save as WAV file
            with wave.open(str(self.output_path), 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            # Calculate duration
            duration = len(audio_data) / (self.sample_rate * self.channels * 2)  # 2 bytes per sample
            
            logger.info(f"✅ Recording saved: {self.output_path}")
            logger.info(f"   Duration: {duration:.1f} seconds")
            logger.info(f"   Format: WAV 16kHz Mono")
            logger.info("")
            logger.info("💡 To use this file for calibration:")
            logger.info(f"   1. Create ground truth: python -m bark_detector --create-template {self.output_path}")
            logger.info(f"   2. Edit the ground truth JSON file with bark timestamps")
            logger.info(f"   3. Run calibration: python -m bark_detector --calibrate {self.output_path.parent}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save recording: {e}")
    
    def _cleanup(self):
        """Clean up resources."""
        if self.is_recording:
            self._stop_recording()
            
        if self.audio:
            self.audio.terminate()
            
        self._restore_keyboard()