# Bark Recording Migration Scripts

This directory contains one-time migration scripts for fixing bark recording filename timestamps.

## Problem Statement

Due to the T21 bug fix, existing bark recording files have END timestamps in their filenames instead of START timestamps. This causes incorrect bark-to-audio-file correlation in analysis tools and legal evidence collection.

## Scripts

### 1. `rename_recordings_to_start_timestamps.py`

**Purpose**: Migrates bark recording files from END timestamps to START timestamps.

**Features**:
- ✅ **Reversible operations** via JSON log file
- ✅ **Space efficient** (no file copying)
- ✅ **Dry-run mode** for safe testing
- ✅ **Comprehensive error handling**
- ✅ **Progress reporting** for large file sets
- ✅ **Cross-platform** compatibility

**Usage**:
```bash
# Preview changes (RECOMMENDED FIRST STEP)
python scripts/rename_recordings_to_start_timestamps.py --dry-run

# Execute the migration (saves log to logs/YYYY-MM-DD-recording-rename.log)
python scripts/rename_recordings_to_start_timestamps.py

# Custom recordings directory
python scripts/rename_recordings_to_start_timestamps.py --recordings-dir /path/to/recordings

# Custom log file location
python scripts/rename_recordings_to_start_timestamps.py --log-file migration-2025-08-25.log

# Process in smaller batches
python scripts/rename_recordings_to_start_timestamps.py --batch-size 50

# Continue processing despite individual file errors
python scripts/rename_recordings_to_start_timestamps.py --continue-on-error
```

### 2. `rollback_recording_renames.py`

**Purpose**: Reverses changes made by the migration script using the JSON log file.

**Usage**:
```bash
# Preview rollback actions (RECOMMENDED)
python scripts/rollback_recording_renames.py --log-file logs/2025-08-25-recording-rename.log --dry-run

# Execute rollback
python scripts/rollback_recording_renames.py --log-file logs/2025-08-25-recording-rename.log

# Rollback only successful renames (skip failed operations)
python scripts/rollback_recording_renames.py --log-file logs/migration.log --only-successful
```

## Migration Process

### Step 1: Backup (Optional but Recommended)
While the scripts are reversible via JSON logs, consider backing up critical recordings:
```bash
# Create backup of most important recordings
cp -r recordings/2025-08-15 recordings/2025-08-15.backup
```

### Step 2: Dry Run
Always start with a dry run to preview changes:
```bash
python scripts/rename_recordings_to_start_timestamps.py --dry-run
```

This will:
- Show all proposed filename changes
- Generate a log file in `logs/` directory (e.g., `logs/2025-08-25-recording-rename.log`)
- Report statistics (total files, expected changes, errors)

### Step 3: Review Results
Examine the dry-run output and log file to verify the changes look correct.

### Step 4: Execute Migration
```bash
python scripts/rename_recordings_to_start_timestamps.py
```

This will rename all files and create a comprehensive JSON log for rollback.

### Step 5: Verify Results
Test a few recordings with analysis tools to ensure timestamps are now correct:
```bash
# Test enhanced violation report
python -m bark_detector --enhanced-violation-report 2025-08-15
```

## Log File Format

The migration creates a detailed JSON log file with this structure:

```json
{
  "migration_info": {
    "timestamp": "2025-08-25T11:57:59.780611",
    "recordings_dir": "recordings",
    "dry_run": false,
    "total_files": 1362,
    "successful_renames": 1320,
    "errors": 2,
    "skipped": 40
  },
  "renames": [
    {
      "original_path": "recordings/2025-08-02/bark_recording_20250802_060706.wav",
      "new_path": "recordings/2025-08-02/bark_recording_20250802_054119.wav",
      "original_timestamp": "2025-08-02T06:07:06",
      "calculated_start": "2025-08-02T05:41:19.120000",
      "audio_duration": 1546.88,
      "status": "success"
    }
  ],
  "errors": [...],
  "skipped": [...]
}
```

## Safety Features

### Atomic Operations
- Each file rename is atomic (complete or rollback)
- No partial states or corrupted filenames

### Comprehensive Logging
- Every operation is logged with full metadata
- Rollback capability for all successful operations
- Error tracking for failed operations

### Validation Checks
- Audio file readability verification
- Timestamp parsing validation
- Filename conflict detection and resolution
- Directory permission checks

### Error Handling
- Continue processing despite individual failures
- Graceful handling of corrupted files
- Clear error messages and recovery suggestions

## Deployment on Intel Mac

To deploy these scripts to the production Intel Mac:

1. **Copy scripts**:
   ```bash
   scp scripts/rename_recordings_to_start_timestamps.py user@intel-mac:/path/to/bark_detector/scripts/
   scp scripts/rollback_recording_renames.py user@intel-mac:/path/to/bark_detector/scripts/
   ```

2. **Run dry-run remotely**:
   ```bash
   ssh user@intel-mac "cd /path/to/bark_detector && python scripts/rename_recordings_to_start_timestamps.py --dry-run"
   ```

3. **Review results and execute**:
   ```bash
   ssh user@intel-mac "cd /path/to/bark_detector && python scripts/rename_recordings_to_start_timestamps.py"
   ```

## Troubleshooting

### Common Issues

**"File not found" errors**: 
- Ensure the recordings directory path is correct
- Check file permissions

**"Duration read failed" errors**:
- Some audio files may be corrupted
- Use `--continue-on-error` to skip problematic files

**Filename conflicts**:
- Script automatically resolves conflicts by adding microseconds
- Review the log file for conflict resolution details

### Recovery

If something goes wrong:
1. **Stop the migration**: Press Ctrl+C (script saves progress)
2. **Review the log file**: Check what was completed successfully
3. **Rollback if needed**: Use the rollback script with the log file
4. **Fix the issue**: Address the root cause
5. **Resume**: Re-run the migration (it will skip already-processed files)

## Performance

**Typical Performance**:
- ~50-100 files per second on modern hardware
- 1,362 files processed in approximately 1-2 minutes
- Memory usage: ~50MB (processes files in batches)

**Large Datasets**:
- Use `--batch-size` to control memory usage
- Progress reporting every 50 files
- Interruptible with Ctrl+C (saves progress)