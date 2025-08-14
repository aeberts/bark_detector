#!/usr/bin/env python3
"""
Script to organize bark recordings into date-based subfolders.

This script moves audio files from recordings/ into date-based subdirectories
like recordings/2025-08-03/ based on the date in the filename.
"""

import os
import re
import shutil
from pathlib import Path

def extract_date_from_filename(filename):
    """
    Extract date from filename like 'bark_recording_20250803_123456.wav'
    Returns tuple (year, month, day) or None if no date found
    """
    # Match pattern: YYYYMMDD in filename
    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if date_match:
        year, month, day = date_match.groups()
        return year, month, day
    return None

def format_date_folder(year, month, day):
    """Format date components into YYYY-MM-DD folder name"""
    return f"{year}-{month}-{day}"

def is_audio_file(filename):
    """Check if file is an audio file based on extension"""
    audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg'}
    return Path(filename).suffix.lower() in audio_extensions

def organize_recordings(recordings_dir=None):
    """
    Organize recordings into date-based subfolders.
    
    Args:
        recordings_dir: Path to the recordings directory
    """
    # If no recordings_dir specified, use ../recordings relative to script location
    if recordings_dir is None:
        script_dir = Path(__file__).parent
        recordings_dir = script_dir.parent / "recordings"
    
    recordings_path = Path(recordings_dir)
    
    if not recordings_path.exists():
        print(f"Error: {recordings_dir} directory not found")
        return
    
    # Get all files in recordings directory (not subdirectories)
    files_to_organize = []
    for item in recordings_path.iterdir():
        if item.is_file() and is_audio_file(item.name):
            files_to_organize.append(item)
    
    if not files_to_organize:
        print("No audio files found to organize")
        return
    
    print(f"Found {len(files_to_organize)} audio files to organize")
    
    # Group files by date
    files_by_date = {}
    files_without_date = []
    
    for file_path in files_to_organize:
        date_parts = extract_date_from_filename(file_path.name)
        if date_parts:
            year, month, day = date_parts
            date_key = format_date_folder(year, month, day)
            if date_key not in files_by_date:
                files_by_date[date_key] = []
            files_by_date[date_key].append(file_path)
        else:
            files_without_date.append(file_path)
    
    # Report files without dates
    if files_without_date:
        print(f"\nSkipping {len(files_without_date)} files without recognizable dates:")
        for file_path in files_without_date:
            print(f"  - {file_path.name}")
    
    # Organize files by date
    total_moved = 0
    for date_folder, files in files_by_date.items():
        # Create date subdirectory
        date_dir = recordings_path / date_folder
        date_dir.mkdir(exist_ok=True)
        
        print(f"\nOrganizing {len(files)} files into {date_folder}/:")
        
        for file_path in files:
            destination = date_dir / file_path.name
            
            # Check if destination already exists
            if destination.exists():
                print(f"  - Skipping {file_path.name} (already exists in {date_folder}/)")
                continue
            
            try:
                shutil.move(str(file_path), str(destination))
                print(f"  - Moved {file_path.name}")
                total_moved += 1
            except Exception as e:
                print(f"  - Error moving {file_path.name}: {e}")
    
    print(f"\nCompleted: Moved {total_moved} files into date-based folders")
    
    # Show final organization
    print("\nFinal organization:")
    for date_folder in sorted(files_by_date.keys()):
        date_dir = recordings_path / date_folder
        if date_dir.exists():
            file_count = len(list(date_dir.glob("*.wav"))) + len(list(date_dir.glob("*.m4a")))
            print(f"  - {date_folder}/: {file_count} files")

if __name__ == "__main__":
    organize_recordings()