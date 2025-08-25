#!/usr/bin/env python3
"""
Migrate bark recording files from END timestamps to START timestamps.

This script renames existing bark recording files to use the correct START timestamp
instead of the END timestamp that was previously used. This ensures accurate
bark-to-audio-file correlation in analysis tools and legal evidence collection.

Usage:
    python scripts/rename_recordings_to_start_timestamps.py [options]
    
    # Dry run to preview changes
    python scripts/rename_recordings_to_start_timestamps.py --dry-run
    
    # Execute the migration
    python scripts/rename_recordings_to_start_timestamps.py
    
    # Rollback using log file
    python scripts/rollback_recording_renames.py --log-file 2025-08-23-recording-rename.log

Features:
- Reversible operations via JSON log file
- Space efficient (no file copying)
- Dry-run mode for safe testing
- Comprehensive error handling
- Progress reporting for large file sets
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

# Import audio processing library
try:
    import soundfile as sf
except ImportError:
    print("Error: soundfile library not found. Please install with: pip install soundfile")
    sys.exit(1)


class RecordingMigrator:
    """Handles migration of bark recording files from END to START timestamps."""
    
    def __init__(self, recordings_dir: str, log_file: str, dry_run: bool = False, 
                 batch_size: int = 100, continue_on_error: bool = False):
        """Initialize the migrator."""
        self.recordings_dir = Path(recordings_dir)
        self.log_file = Path(log_file)
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.continue_on_error = continue_on_error
        
        # Migration tracking
        self.migration_log = {
            "migration_info": {
                "timestamp": datetime.now().isoformat(),
                "recordings_dir": str(self.recordings_dir),
                "dry_run": dry_run,
                "total_files": 0,
                "successful_renames": 0,
                "errors": 0,
                "skipped": 0
            },
            "renames": [],
            "errors": [],
            "skipped": []
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def find_recording_files(self) -> List[Path]:
        """Find all bark recording files in the directory."""
        self.logger.info(f"Scanning for bark recording files in {self.recordings_dir}")
        
        recording_files = []
        
        # Pattern for bark recording files
        pattern = re.compile(r'bark_recording_\d{8}_\d{6}\.wav$')
        
        # Search recursively for recording files
        for root, dirs, files in os.walk(self.recordings_dir):
            for file in files:
                if pattern.match(file):
                    recording_files.append(Path(root) / file)
        
        self.logger.info(f"Found {len(recording_files)} bark recording files")
        return sorted(recording_files)
    
    def get_audio_duration(self, file_path: Path) -> Optional[float]:
        """Get the duration of an audio file in seconds."""
        try:
            with sf.SoundFile(str(file_path)) as audio_file:
                frames = len(audio_file)
                sample_rate = audio_file.samplerate
                duration = frames / sample_rate
                return duration
        except Exception as e:
            self.logger.warning(f"Could not read audio duration for {file_path}: {e}")
            return None
    
    def parse_filename_timestamp(self, filename: str) -> Optional[datetime]:
        """Parse timestamp from bark recording filename."""
        # Pattern: bark_recording_YYYYMMDD_HHMMSS.wav
        pattern = r'bark_recording_(\d{8})_(\d{6})\.wav'
        match = re.search(pattern, filename)
        
        if match:
            try:
                date_str = match.group(1)  # YYYYMMDD
                time_str = match.group(2)  # HHMMSS
                
                # Parse date
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                
                # Parse time
                hour = int(time_str[:2])
                minute = int(time_str[2:4])
                second = int(time_str[4:6])
                
                return datetime(year, month, day, hour, minute, second)
            except ValueError as e:
                self.logger.warning(f"Invalid timestamp format in {filename}: {e}")
                return None
        
        return None
    
    def calculate_start_timestamp(self, end_timestamp: datetime, duration: float) -> datetime:
        """Calculate the start timestamp from end timestamp and duration."""
        return end_timestamp - timedelta(seconds=duration)
    
    def generate_new_filename(self, old_path: Path, start_timestamp: datetime) -> Path:
        """Generate new filename with START timestamp."""
        # Format: bark_recording_YYYYMMDD_HHMMSS.wav
        new_filename = f"bark_recording_{start_timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
        return old_path.parent / new_filename
    
    def check_filename_conflict(self, new_path: Path) -> bool:
        """Check if the new filename already exists."""
        return new_path.exists()
    
    def rename_file_with_logging(self, old_path: Path, new_path: Path, 
                                 duration: float, old_timestamp: datetime, 
                                 new_timestamp: datetime) -> bool:
        """Rename file and log the operation."""
        try:
            if self.dry_run:
                self.logger.info(f"DRY-RUN: Would rename {old_path.name} -> {new_path.name}")
                status = "dry_run_success"
            else:
                # Perform atomic rename
                old_path.rename(new_path)
                self.logger.info(f"Renamed: {old_path.name} -> {new_path.name}")
                status = "success"
            
            # Log the successful rename
            rename_entry = {
                "original_path": str(old_path),
                "new_path": str(new_path),
                "original_timestamp": old_timestamp.isoformat(),
                "calculated_start": new_timestamp.isoformat(),
                "audio_duration": round(duration, 2),
                "status": status
            }
            
            self.migration_log["renames"].append(rename_entry)
            self.migration_log["migration_info"]["successful_renames"] += 1
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to rename {old_path}: {e}"
            self.logger.error(error_msg)
            
            error_entry = {
                "original_path": str(old_path),
                "error": str(e),
                "status": "rename_failed"
            }
            
            self.migration_log["errors"].append(error_entry)
            self.migration_log["migration_info"]["errors"] += 1
            
            return False
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single recording file."""
        # Get audio duration
        duration = self.get_audio_duration(file_path)
        if duration is None:
            error_entry = {
                "original_path": str(file_path),
                "error": "Could not read audio duration",
                "status": "duration_read_failed"
            }
            self.migration_log["errors"].append(error_entry)
            self.migration_log["migration_info"]["errors"] += 1
            return False
        
        # Parse the END timestamp from filename
        end_timestamp = self.parse_filename_timestamp(file_path.name)
        if end_timestamp is None:
            error_entry = {
                "original_path": str(file_path),
                "error": "Could not parse timestamp from filename",
                "status": "timestamp_parse_failed"
            }
            self.migration_log["errors"].append(error_entry)
            self.migration_log["migration_info"]["errors"] += 1
            return False
        
        # Calculate the START timestamp
        start_timestamp = self.calculate_start_timestamp(end_timestamp, duration)
        
        # Generate new filename
        new_path = self.generate_new_filename(file_path, start_timestamp)
        
        # Check for filename conflicts
        if self.check_filename_conflict(new_path) and not self.dry_run:
            # Handle conflict by adding microseconds
            microseconds = int((duration % 1) * 1000000)
            start_timestamp = start_timestamp.replace(microsecond=microseconds)
            new_path = self.generate_new_filename(file_path, start_timestamp)
            
            # If still conflicts, skip this file
            if self.check_filename_conflict(new_path):
                skip_entry = {
                    "original_path": str(file_path),
                    "reason": f"Filename conflict: {new_path.name} already exists",
                    "status": "filename_conflict"
                }
                self.migration_log["skipped"].append(skip_entry)
                self.migration_log["migration_info"]["skipped"] += 1
                return False
        
        # If the timestamps are the same (already correct), skip
        if file_path.name == new_path.name:
            skip_entry = {
                "original_path": str(file_path),
                "reason": "File already has correct timestamp",
                "status": "already_correct"
            }
            self.migration_log["skipped"].append(skip_entry)
            self.migration_log["migration_info"]["skipped"] += 1
            return True
        
        # Perform the rename
        return self.rename_file_with_logging(
            file_path, new_path, duration, end_timestamp, start_timestamp
        )
    
    def save_migration_log(self):
        """Save the migration log to JSON file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.migration_log, f, indent=2)
            self.logger.info(f"Migration log saved to {self.log_file}")
        except Exception as e:
            self.logger.error(f"Failed to save migration log: {e}")
    
    def run_migration(self):
        """Run the complete migration process."""
        self.logger.info("Starting bark recording filename migration")
        self.logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        self.logger.info(f"Recordings directory: {self.recordings_dir}")
        self.logger.info(f"Log file: {self.log_file}")
        
        # Find all recording files
        recording_files = self.find_recording_files()
        
        if not recording_files:
            self.logger.info("No bark recording files found to migrate")
            return
        
        self.migration_log["migration_info"]["total_files"] = len(recording_files)
        
        # Process files in batches
        processed = 0
        for i in range(0, len(recording_files), self.batch_size):
            batch = recording_files[i:i + self.batch_size]
            
            self.logger.info(f"Processing batch {i//self.batch_size + 1} "
                           f"({len(batch)} files)")
            
            for file_path in batch:
                success = self.process_file(file_path)
                processed += 1
                
                if not success and not self.continue_on_error:
                    self.logger.error("Stopping migration due to error")
                    break
                
                # Progress update every 50 files
                if processed % 50 == 0:
                    self.logger.info(f"Progress: {processed}/{len(recording_files)} files processed")
        
        # Final summary
        info = self.migration_log["migration_info"]
        self.logger.info("Migration Summary:")
        self.logger.info(f"  Total files: {info['total_files']}")
        self.logger.info(f"  Successful renames: {info['successful_renames']}")
        self.logger.info(f"  Errors: {info['errors']}")
        self.logger.info(f"  Skipped: {info['skipped']}")
        
        # Save the migration log
        self.save_migration_log()
        
        if self.dry_run:
            self.logger.info("DRY-RUN completed. No files were actually renamed.")
            self.logger.info("Review the log file and run without --dry-run to execute.")
        else:
            self.logger.info("Migration completed successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate bark recording files from END to START timestamps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--recordings-dir",
        default="recordings",
        help="Path to recordings directory (default: recordings/)"
    )
    
    parser.add_argument(
        "--log-file",
        default=f"{datetime.now().strftime('%Y-%m-%d')}-recording-rename.log",
        help="Migration log file path"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing them"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Process files in batches of this size (default: 100)"
    )
    
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing other files if one fails"
    )
    
    args = parser.parse_args()
    
    # Validate recordings directory
    if not os.path.exists(args.recordings_dir):
        print(f"Error: Recordings directory '{args.recordings_dir}' does not exist")
        sys.exit(1)
    
    # Create migrator and run
    migrator = RecordingMigrator(
        recordings_dir=args.recordings_dir,
        log_file=args.log_file,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        continue_on_error=args.continue_on_error
    )
    
    try:
        migrator.run_migration()
    except KeyboardInterrupt:
        print("\nMigration interrupted by user")
        migrator.save_migration_log()
        sys.exit(1)
    except Exception as e:
        print(f"Migration failed with error: {e}")
        migrator.save_migration_log()
        sys.exit(1)


if __name__ == "__main__":
    main()