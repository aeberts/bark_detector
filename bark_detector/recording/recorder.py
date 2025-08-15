"""Manual recording functionality"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ManualRecorder:
    """Manual audio recording system."""
    
    def __init__(self, output_dir: str = "recordings"):
        """Initialize manual recorder."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.debug(f"Manual recorder initialized with output dir: {output_dir}")
    
    def start_recording(self):
        """Start manual recording."""
        # Placeholder - implementation to be moved from bd.py
        logger.info("Manual recording started")
    
    def stop_recording(self):
        """Stop manual recording."""
        # Placeholder - implementation to be moved from bd.py  
        logger.info("Manual recording stopped")