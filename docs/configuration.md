# Configuration Management

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
  "calibration": {
    "default_profile": null,
    "sensitivity_range": [0.01, 0.5],
    "calibration_steps": 20
  },
  "scheduling": {
    "auto_start": false,
    "start_time": "06:00",
    "stop_time": "19:00",
    "timezone": "local"
  },
  "legal": {
    "continuous_threshold": 300,
    "sporadic_threshold": 900,
    "sporadic_gap_threshold": 300
  }
}
```

## Configuration Sections

### Detection Parameters
- `sensitivity`: Detection sensitivity (0.01-1.0)
- `sample_rate`: Audio sample rate in Hz (must be 16000 for YAMNet)
- `chunk_size`: Audio processing chunk size in samples
- `channels`: Number of audio channels (1=mono, 2=stereo)
- `quiet_duration`: Seconds of quiet before stopping recording
- `session_gap_threshold`: Seconds gap to separate recording sessions

### Output Directories
- `recordings_dir`: Directory to save audio recordings
- `reports_dir`: Directory to save violation reports
- `logs_dir`: Directory to save log files
- `profiles_dir`: Directory to save calibration profiles

### Calibration Settings
- `default_profile`: Name of default calibration profile to load (null = use sensitivity)
- `sensitivity_range`: Min and max sensitivity for calibration sweep
- `calibration_steps`: Number of steps in calibration sweep

### Scheduling (Future Feature)
- `auto_start`: Automatically start monitoring at scheduled times
- `start_time`: Time to start monitoring (HH:MM format)
- `stop_time`: Time to stop monitoring (HH:MM format)
- `timezone`: Timezone for scheduling (local or IANA timezone)

### Legal Thresholds
- `continuous_threshold`: Continuous barking threshold in seconds (City of Kelowna: 5min = 300s)
- `sporadic_threshold`: Sporadic barking threshold in seconds (City of Kelowna: 15min = 900s)
- `sporadic_gap_threshold`: Gap threshold for sporadic detection in seconds (5min = 300s)

## File Locations

The system searches for configuration files in the following locations (in order):

1. `./config.json` (current directory)
2. `~/.bark_detector/config.json` (user home directory)
3. `/etc/bark_detector/config.json` (system-wide)

## CLI Integration

### Loading Configuration Files
```bash
# Load specific configuration file
uv run python -m bark_detector --config myconfig.json

# Use automatic file discovery (searches standard locations)
uv run python -m bark_detector

# Override config file values with CLI arguments
uv run python -m bark_detector --config myconfig.json --sensitivity 0.8
```

### Creating Configuration Files
```bash
# Create default configuration file
uv run python -m bark_detector --create-config config.json

# Create configuration in user directory
uv run python -m bark_detector --create-config ~/.bark_detector/config.json
```

## Precedence Rules

Configuration values are applied in the following order (highest to lowest precedence):

1. **CLI Arguments** - Override any config file or default values
2. **Configuration File** - Override default values
3. **System Defaults** - Built-in default values

Example:
- Config file sets `sensitivity: 0.5`
- CLI argument `--sensitivity 0.8`
- Result: Final sensitivity = 0.8 (CLI wins)

## Validation

The configuration system includes comprehensive validation:

- **Parameter Range Validation**: Ensures values are within acceptable ranges
- **Type Validation**: Confirms parameters are correct data types
- **JSON Syntax Validation**: Provides clear error messages for invalid JSON
- **File Access Validation**: Handles missing files and permission issues gracefully

### Example Validation Messages
```
Configuration parameter 'sensitivity' must be between 0.01 and 1.0, got 2.0
Invalid JSON in configuration file config.json: Expecting ',' delimiter: line 5 column 18
Configuration file not found: nonexistent.json
```

## Usage Examples

### Basic Monitoring Setup
```json
{
  "detection": {
    "sensitivity": 0.7,
    "quiet_duration": 45.0
  },
  "output": {
    "recordings_dir": "my_recordings"
  }
}
```

### High-Sensitivity Monitoring
```json
{
  "detection": {
    "sensitivity": 0.4,
    "session_gap_threshold": 5.0,
    "quiet_duration": 15.0
  },
  "output": {
    "recordings_dir": "sensitive_monitoring"
  }
}
```

### Legal Evidence Collection
```json
{
  "detection": {
    "sensitivity": 0.68
  },
  "legal": {
    "continuous_threshold": 300,
    "sporadic_threshold": 900,
    "sporadic_gap_threshold": 300
  },
  "output": {
    "reports_dir": "legal_reports"
  }
}
```

## Backward Compatibility

The configuration system maintains complete backward compatibility:
- All existing CLI workflows continue to work unchanged
- CLI-only usage remains fully supported
- No configuration file is required for basic operation

## Error Handling

The system handles configuration errors gracefully:
- **Missing Files**: Falls back to defaults with informative logging
- **Invalid JSON**: Provides specific syntax error messages
- **Invalid Parameters**: Shows parameter name, expected range, and actual value
- **Permission Issues**: Handles file access problems with clear error messages

## Integration with Existing Features

The configuration system integrates seamlessly with all existing features:
- **Calibration Profiles**: Work with both config files and CLI
- **Violation Analysis**: Uses legal thresholds from configuration
- **Audio Processing**: Respects all detection parameters
- **File Organization**: Uses configured output directories

This configuration system provides a robust foundation for complex bark detector deployments while maintaining the simplicity and flexibility of CLI usage.