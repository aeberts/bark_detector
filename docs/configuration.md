# Configuration Guide

This document describes the Bark Detector's comprehensive JSON-based configuration system, including the new channel-based logging features.

## Overview

The Bark Detector supports comprehensive JSON-based configuration management, allowing users to store and manage complex parameter sets without long CLI commands. The configuration system provides persistent storage, automatic file discovery, and seamless CLI integration.

## Configuration File Structure

Configuration files use JSON format organized into logical sections:

```json
{
  "detection": {
    "sensitivity": 0.68,
    "sample_rate": 16000,
    "chunk_size": 1024,
    "channels": 1,
    "quiet_duration": 30.0,
    "session_gap_threshold": 10.0
  },
  "output": {
    "recordings_dir": "recordings",
    "reports_dir": "reports",
    "logs_dir": "logs",
    "profiles_dir": "profiles"
  },
  "legal": {
    "constant_violation_duration": 300,
    "sporadic_violation_threshold": 900,
    "sporadic_gap_threshold": 300,
    "constant_gap_threshold": 10
  },
  "calibration": {
    "default_profile": null,
    "auto_calibrate": false
  }
}
```

## Output Directories

### Logs Directory Configuration

The `output.logs_dir` setting controls where the channel-based logging system stores log files:

```json
{
  "output": {
    "logs_dir": "custom_logs"
  }
}
```

**Directory Resolution Priority:**
1. Explicit CLI parameter (`--logs-dir` or function parameter)
2. Configuration file `output.logs_dir` setting
3. Default `logs/` directory

**Path Handling:**
- **Absolute paths**: Used directly (e.g., `/var/log/bark_detector`)
- **Relative paths**: Resolved relative to current working directory
- **Automatic creation**: Directories are created automatically with proper permissions

### Log File Structure

With channel-based logging enabled (default), logs are organized as:

```
{logs_dir}/
├── 2025-09-27/
│   ├── 2025-09-27_detection.log    # Real-time monitoring, calibration
│   └── 2025-09-27_analysis.log     # Analysis, reports, exports
├── 2025-09-26/
│   ├── 2025-09-26_detection.log
│   └── 2025-09-26_analysis.log
└── migration_backups/              # Legacy log backups
    └── bark_detector.log.backup.2025-09-27T12:30:45
```

### Legacy Compatibility

For backward compatibility with existing tooling, flat file logging can be enabled:

```python
# In code - disable date folders for legacy behavior
logger = setup_logging(channel='detection', use_date_folders=False)
# Creates: logs/bark_detector_detection.log
```

## Channel-Based Logging Configuration

### Channel Classifications

**Detection Channel** (real-time operations):
- Default detector startup and monitoring
- Manual recording sessions
- Calibration modes (realtime, file-based)
- Profile management
- Audio conversion utilities

**Analysis Channel** (batch operations):
- Violation analysis
- Report generation
- Data export commands
- Migration scripts

### Configuration Integration

The logging system respects configuration settings:

```json
{
  "output": {
    "logs_dir": "/var/log/bark_detector",
    "recordings_dir": "/data/recordings",
    "reports_dir": "/data/reports"
  }
}
```

**CLI Override Examples:**
```bash
# Override logs directory via CLI
uv run python -m bark_detector --config config.json --logs-dir /tmp/debug_logs

# Use configuration file with default log location
uv run python -m bark_detector --config production.json
```

## Migration from Legacy Logs

### Automatic Migration

Use the migration script to convert existing flat log files:

```bash
# Preview migration (safe, no changes)
uv run python scripts/migrate_logs_by_date.py --dry-run

# Execute migration with default settings
uv run python scripts/migrate_logs_by_date.py

# Custom migration with specific parameters
uv run python scripts/migrate_logs_by_date.py \
  --input old_system/bark_detector.log \
  --logs-dir /data/logs \
  --backup-dir /backup/logs \
  --continue-on-error
```

### Migration Features

- **Channel Classification**: Automatically sorts log entries into detection vs analysis channels
- **Backup Creation**: Creates timestamped backups before migration
- **Error Handling**: Gracefully handles malformed log entries
- **Dry Run Mode**: Preview changes before execution
- **JSON Summary**: Generates detailed migration report

### Migration Keywords

The migration script uses keyword patterns to classify log entries:

**Detection Keywords:**
- "yamnet model", "starting manual recording", "recording saved"
- "calibration", "profile", "audio conversion"
- "real-time detection", "bark detected", "session started"

**Analysis Keywords:**
- "violation analysis", "analysis complete", "violations detected"
- "PDF report", "report generated", "exporting violations"
- "violation report", "enhanced report", "CSV export"

**Default**: Unmatched entries default to detection channel

## Error Handling

### Directory Validation

The system validates directory paths and permissions:

```python
# Automatic validation includes:
# - Directory creation (with parents)
# - Write permission verification
# - Path normalization (relative to absolute)
# - Error reporting with fallback options
```

### Configuration Errors

Common configuration issues and resolutions:

1. **Invalid logs_dir**: Falls back to default `logs/` with warning
2. **Permission errors**: Reports specific permission issues
3. **Missing directories**: Automatically created with proper permissions

## Best Practices

### Production Configuration

```json
{
  "output": {
    "logs_dir": "/var/log/bark_detector",
    "recordings_dir": "/data/recordings",
    "reports_dir": "/data/reports"
  },
  "detection": {
    "sensitivity": 0.68,
    "session_gap_threshold": 10.0
  },
  "legal": {
    "constant_violation_duration": 300,
    "sporadic_violation_threshold": 900
  }
}
```

### Development Configuration

```json
{
  "output": {
    "logs_dir": "dev_logs",
    "recordings_dir": "dev_recordings",
    "reports_dir": "dev_reports"
  },
  "detection": {
    "sensitivity": 0.1,
    "session_gap_threshold": 5.0
  }
}
```

### Logging Troubleshooting

**Issue**: Logs not appearing in configured directory
- **Check**: `output.logs_dir` setting in config file
- **Verify**: Directory permissions and disk space
- **Test**: Run with explicit `--logs-dir` parameter

**Issue**: Legacy flat log files still being created
- **Check**: Application using `use_date_folders=False`
- **Verify**: CLI integration using proper logging functions
- **Update**: Ensure using `get_detection_logger()` or `get_analysis_logger()`

## Related Documentation

- [README.md](../README.md) - Basic usage and logging overview
- [CHANGELOG.md](../CHANGELOG.md) - History of logging system changes
- [docs/architecture/coding-standards.md](architecture/coding-standards.md) - Development guidelines
- [scripts/migrate_logs_by_date.py](../scripts/migrate_logs_by_date.py) - Migration utility