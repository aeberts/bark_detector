"""Audio file converter for YAMNet-compatible format conversion"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .helpers import get_detection_logger

logger = get_detection_logger()


class AudioFileConverter:
    """Standalone audio file converter for manual command-line conversion."""
    
    def __init__(self):
        """Initialize audio file converter."""
        self.supported_extensions = ['.m4a', '.mp3', '.aac', '.flac', '.wav']
        self.target_sample_rate = 16000
        self.target_channels = 1
    
    def get_files_for_date(self, directory: Path, target_date: str) -> List[Path]:
        """
        Get all convertible audio files for a specific date.
        
        Args:
            directory: Directory to search
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            List of audio files matching the date pattern
        """
        date_parts = target_date.split('-')
        if len(date_parts) != 3:
            raise ValueError(f"Invalid date format: {target_date}. Use YYYY-MM-DD")
        
        year, month, day = date_parts
        date_pattern = f"{year}{month}{day}"
        
        convertible_files = []
        
        # Look for files matching: bark_recording_YYYYMMDD_*.[ext]
        for ext in self.supported_extensions:
            pattern = f"bark_recording_{date_pattern}_*{ext}"
            for file_path in directory.glob(pattern):
                convertible_files.append(file_path)
        
        # Also look for files that start with the date pattern
        for ext in self.supported_extensions:
            pattern = f"{date_pattern}*{ext}"
            for file_path in directory.glob(pattern):
                convertible_files.append(file_path)
        
        # Remove duplicates and sort
        convertible_files = list(set(convertible_files))
        convertible_files.sort()
        
        return convertible_files
    
    def get_convertible_files_in_directory(self, directory: Path) -> List[Path]:
        """
        Get all convertible audio files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of all convertible audio files
        """
        convertible_files = []
        
        for ext in self.supported_extensions:
            pattern = f"*{ext}"
            for file_path in directory.glob(pattern):
                # Skip already converted files
                if not file_path.name.endswith('_16khz.wav'):
                    convertible_files.append(file_path)
        
        convertible_files.sort()
        return convertible_files
    
    def is_already_converted(self, audio_path: Path) -> bool:
        """Check if a file has already been converted."""
        # Check if WAV file exists in base directory
        converted_name = f"{audio_path.stem}_16khz.wav"
        converted_path = audio_path.parent / converted_name
        
        return converted_path.exists()
    
    def convert_audio_file(self, audio_path: Path) -> Optional[Path]:
        """
        Convert a single audio file to 16kHz WAV format.
        Saves WAV in base directory and moves original to 'originals' subdirectory.
        
        Args:
            audio_path: Path to the audio file to convert
            
        Returns:
            Path to converted file, or None if conversion failed
        """
        try:
            import librosa
            import soundfile as sf
            import shutil
            
            # Check if already converted
            if self.is_already_converted(audio_path):
                logger.info(f"⏭️  Skipping {audio_path.name} (already converted)")
                converted_name = f"{audio_path.stem}_16khz.wav"
                return audio_path.parent / converted_name
            
            # Create originals directory
            originals_dir = audio_path.parent / 'originals'
            originals_dir.mkdir(exist_ok=True)
            
            # Generate output path in base directory
            converted_name = f"{audio_path.stem}_16khz.wav"
            converted_path = audio_path.parent / converted_name
            
            logger.info(f"🔄 Converting {audio_path.name} to WAV 16kHz...")
            
            # Load and convert audio
            audio_data, sample_rate = librosa.load(str(audio_path), sr=self.target_sample_rate, mono=True)
            
            # Save as WAV in base directory
            sf.write(str(converted_path), audio_data, self.target_sample_rate, subtype='PCM_16')
            
            # Move original to originals subdirectory
            original_destination = originals_dir / audio_path.name
            shutil.move(str(audio_path), str(original_destination))
            
            duration = len(audio_data) / self.target_sample_rate
            file_size_mb = converted_path.stat().st_size / (1024 * 1024)
            
            logger.info(f"✅ Converted: {converted_path.name} ({duration:.1f}s, {file_size_mb:.1f}MB)")
            logger.info(f"📁 Moved original to: originals/{audio_path.name}")
            
            return converted_path
            
        except Exception as e:
            logger.error(f"❌ Failed to convert {audio_path.name}: {e}")
            return None
    
    def convert_files_for_date(self, directory: Path, target_date: str) -> Dict[str, Any]:
        """
        Convert all audio files for a specific date.
        
        Args:
            directory: Directory containing audio files
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary with conversion results summary
        """
        logger.info(f"🔍 Finding audio files for date: {target_date}")
        
        files_to_convert = self.get_files_for_date(directory, target_date)
        
        if not files_to_convert:
            logger.info(f"📁 No audio files found for date {target_date}")
            return {
                'total_files': 0,
                'converted': 0,
                'skipped': 0,
                'failed': 0,
                'converted_files': []
            }
        
        logger.info(f"📁 Found {len(files_to_convert)} audio files for {target_date}")
        
        return self._convert_file_batch(files_to_convert)
    
    def convert_specific_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Convert specific audio files.
        
        Args:
            file_paths: List of file paths to convert
            
        Returns:
            Dictionary with conversion results summary
        """
        # Validate files exist and are convertible
        valid_files = []
        for file_path in file_paths:
            if not file_path.exists():
                logger.error(f"❌ File not found: {file_path}")
                continue
            
            if file_path.suffix.lower() not in self.supported_extensions:
                logger.error(f"❌ Unsupported format: {file_path} (supported: {', '.join(self.supported_extensions)})")
                continue
            
            valid_files.append(file_path)
        
        if not valid_files:
            logger.info("📁 No valid files to convert")
            return {
                'total_files': 0,
                'converted': 0,
                'skipped': 0,
                'failed': 0,
                'converted_files': []
            }
        
        logger.info(f"📁 Converting {len(valid_files)} files")
        return self._convert_file_batch(valid_files)
    
    def convert_directory(self, directory: Path) -> Dict[str, Any]:
        """
        Convert all convertible audio files in a directory.
        
        Args:
            directory: Directory to convert files from
            
        Returns:
            Dictionary with conversion results summary
        """
        if not directory.exists():
            logger.error(f"❌ Directory not found: {directory}")
            return {
                'total_files': 0,
                'converted': 0,
                'skipped': 0,
                'failed': 0,
                'converted_files': []
            }
        
        logger.info(f"🔍 Finding convertible files in: {directory}")
        
        files_to_convert = self.get_convertible_files_in_directory(directory)
        
        if not files_to_convert:
            logger.info(f"📁 No convertible audio files found in {directory}")
            return {
                'total_files': 0,
                'converted': 0,
                'skipped': 0,
                'failed': 0,
                'converted_files': []
            }
        
        logger.info(f"📁 Found {len(files_to_convert)} convertible files")
        return self._convert_file_batch(files_to_convert)
    
    def _convert_file_batch(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Convert a batch of files and return summary.
        
        Args:
            file_paths: List of file paths to convert
            
        Returns:
            Dictionary with conversion results
        """
        results = {
            'total_files': len(file_paths),
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'converted_files': []
        }
        
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"📄 Processing file {i}/{len(file_paths)}: {file_path.name}")
            
            if self.is_already_converted(file_path):
                results['skipped'] += 1
                logger.info(f"⏭️  Skipped {file_path.name} (already converted)")
                continue
            
            converted_path = self.convert_audio_file(file_path)
            
            if converted_path:
                results['converted'] += 1
                results['converted_files'].append(str(converted_path))
            else:
                results['failed'] += 1
        
        # Log summary
        logger.info(f"🎯 Conversion Summary:")
        logger.info(f"  📊 Total files: {results['total_files']}")
        logger.info(f"  ✅ Converted: {results['converted']}")
        logger.info(f"  ⏭️  Skipped (already converted): {results['skipped']}")
        logger.info(f"  ❌ Failed: {results['failed']}")
        
        return results