"""Audio file converter"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioFileConverter:
    """Convert audio files between formats."""
    
    def __init__(self):
        """Initialize audio file converter."""
        pass
    
    def convert_to_wav(self, input_path: Path, output_path: Path):
        """Convert audio file to WAV format."""
        # Placeholder - implementation to be moved from bd.py
        logger.debug(f"Converting {input_path} to {output_path}")