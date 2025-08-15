#!/usr/bin/env python3
"""
Ground Truth Format Conversion Script

Converts ground truth files from decimal seconds to HH:MM:SS.mmm format
and fixes data quality issues.

Usage:
    uv run scripts/convert_ground_truth_format.py [directory]
    uv run scripts/convert_ground_truth_format.py samples/
    uv run scripts/convert_ground_truth_format.py --dry-run samples/
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bark_detector.core.models import GroundTruthEvent, seconds_to_timestamp, detect_timestamp_format

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def validate_and_fix_ground_truth_data(data: Dict[str, Any], audio_file_path: Path) -> Dict[str, Any]:
    """Validate and fix ground truth data quality issues.
    
    Args:
        data: Ground truth data dictionary
        audio_file_path: Path to the audio file for duration validation
        
    Returns:
        Fixed ground truth data
    """
    fixed_data = data.copy()
    events = data.get('events', [])
    audio_duration = data.get('duration', None)
    
    logger.info(f"  Processing {len(events)} events...")
    
    fixed_events = []
    issues_found = 0
    
    for i, event in enumerate(events):
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        
        # Detect and convert formats
        try:
            start_format = detect_timestamp_format(start_time)
            end_format = detect_timestamp_format(end_time)
            
            # Convert to float for validation
            if start_format == "seconds":
                start_seconds = float(start_time)
            else:
                from bark_detector.core.models import timestamp_to_seconds
                start_seconds = timestamp_to_seconds(start_time)
                
            if end_format == "seconds":
                end_seconds = float(end_time)
            else:
                from bark_detector.core.models import timestamp_to_seconds
                end_seconds = timestamp_to_seconds(end_time)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"  Event {i+1}: Invalid timestamp format - {e}")
            issues_found += 1
            continue
        
        # Fix common issues
        fixed = False
        
        # Issue 1: start_time >= end_time (swap or fix duration)
        if start_seconds >= end_seconds:
            # Check if end_time looks like a duration instead of end timestamp
            duration = end_seconds
            if 0 < duration < 10:  # Reasonable bark duration (0-10 seconds)
                end_seconds = start_seconds + duration
                logger.info(f"  Event {i+1}: Fixed duration format (start={start_seconds:.3f}s, duration={duration:.3f}s -> end={end_seconds:.3f}s)")
                fixed = True
            else:
                logger.warning(f"  Event {i+1}: Invalid timestamps (start={start_seconds:.3f}s >= end={end_seconds:.3f}s) - skipping")
                issues_found += 1
                continue
        
        # Issue 2: Negative timestamps
        if start_seconds < 0 or end_seconds < 0:
            logger.warning(f"  Event {i+1}: Negative timestamps - skipping")
            issues_found += 1
            continue
        
        # Issue 3: Events beyond audio duration
        if audio_duration and end_seconds > audio_duration:
            logger.warning(f"  Event {i+1}: Event extends beyond audio duration ({end_seconds:.3f}s > {audio_duration:.3f}s) - skipping")
            issues_found += 1
            continue
        
        # Issue 4: Very short events (< 0.01s)
        if (end_seconds - start_seconds) < 0.01:
            logger.warning(f"  Event {i+1}: Very short event ({end_seconds - start_seconds:.3f}s) - skipping")
            issues_found += 1
            continue
        
        # Create fixed event in new format
        fixed_event = {
            'start_time': seconds_to_timestamp(start_seconds),
            'end_time': seconds_to_timestamp(end_seconds),
            'description': event.get('description', ''),
            'confidence_expected': event.get('confidence_expected', 1.0)
        }
        
        fixed_events.append(fixed_event)
        
        if fixed:
            issues_found += 1
    
    fixed_data['events'] = fixed_events
    logger.info(f"  Result: {len(fixed_events)} valid events, {issues_found} issues fixed/removed")
    
    return fixed_data


def convert_ground_truth_file(file_path: Path, dry_run: bool = False) -> bool:
    """Convert a single ground truth file to new format.
    
    Args:
        file_path: Path to the ground truth JSON file
        dry_run: If True, don't write changes to disk
        
    Returns:
        True if conversion was successful
    """
    logger.info(f"Converting: {file_path.name}")
    
    try:
        # Load existing data
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Get audio file path for validation
        audio_file = data.get('audio_file', '')
        if audio_file:
            audio_path = file_path.parent / Path(audio_file).name
        else:
            audio_path = file_path.with_suffix('.wav')  # Assume same name with .wav
        
        # Validate and fix data
        fixed_data = validate_and_fix_ground_truth_data(data, audio_path)
        
        # Update metadata
        fixed_data['instructions'] = "Timestamp format: HH:MM:SS.mmm"
        fixed_data['format_version'] = "2.0"
        
        if not dry_run:
            # Create backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if not backup_path.exists():
                with open(backup_path, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"  Backup created: {backup_path.name}")
            
            # Write fixed data
            with open(file_path, 'w') as f:
                json.dump(fixed_data, f, indent=2)
            logger.info(f"  ✅ Converted successfully")
        else:
            logger.info(f"  ✅ Would convert (dry run)")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Failed to convert: {e}")
        return False


def find_ground_truth_files(directory: Path) -> List[Path]:
    """Find all ground truth JSON files in directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of ground truth file paths
    """
    patterns = [
        "*_ground_truth.json",
        "*_gt.json", 
        "*groundtruth.json"
    ]
    
    files = []
    for pattern in patterns:
        files.extend(directory.glob(pattern))
    
    return sorted(list(set(files)))  # Remove duplicates and sort


def main():
    parser = argparse.ArgumentParser(description="Convert ground truth files to HH:MM:SS.mmm format")
    parser.add_argument('directory', nargs='?', default='samples/', 
                       help='Directory containing ground truth files (default: samples/)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Find directory
    directory = Path(args.directory)
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 1
    
    # Find ground truth files
    gt_files = find_ground_truth_files(directory)
    if not gt_files:
        logger.warning(f"No ground truth files found in {directory}")
        return 0
    
    logger.info(f"Found {len(gt_files)} ground truth files")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    # Convert each file
    success_count = 0
    for file_path in gt_files:
        if convert_ground_truth_file(file_path, dry_run=args.dry_run):
            success_count += 1
        print()  # Add blank line between files
    
    # Summary
    logger.info(f"Conversion complete: {success_count}/{len(gt_files)} files processed successfully")
    
    if success_count < len(gt_files):
        return 1
    return 0


if __name__ == "__main__":
    exit(main())