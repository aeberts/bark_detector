# Features

## FEATURE: YAMNet ML-Based Bark Detection
### User Requirements
- Accurately detect barking sounds using machine learning
- Minimize false positives from other household sounds
- Work reliably across different dog breeds and barking patterns
### Specifications
- Uses Google's YAMNet neural network model from TensorFlow Hub
- Analyzes audio in real-time with confidence scoring
- Supports sensitivity adjustment for different environments
- 16kHz audio processing optimized for YAMNet requirements
- Cross-platform compatibility (M1 Mac, Intel Mac, Linux)
- **Enhanced Class Filtering**: Intelligent filtering of YAMNet's 521 audio classes to focus on 11 dog-specific classes while excluding problematic broad categories
- **False Positive Reduction**: 54% reduction in false positives through class-level analysis and selective exclusion of environmental noise classes
- **Detailed Detection Analysis**: Per-class confidence scoring and triggering class identification for ongoing accuracy optimization

## FEATURE: Audio Recording Management
### User Requirements
- Record high-quality audio of barking incidents
- Manage storage efficiently for extended monitoring periods
- Start/stop recording based on bark detection
### Specifications
- Records 16kHz WAV format audio for ML compatibility
- Automatic recording start when barking detected above sensitivity threshold
- Continues recording until 30 seconds pass without detected barking
- Session-based file organization with timestamps
- Configurable output directory and file naming

## FEATURE: Calibration System
### User Requirements
- Fine-tune detection sensitivity for specific environments
- Validate detection accuracy with known bark samples
- Save calibration settings for reuse
### Specifications
- **File-based Calibration**: Process pre-recorded audio files with ground truth annotations
- **Real-time Calibration**: Interactive calibration with spacebar feedback during live monitoring
- **Performance Metrics**: F1 score, precision, recall calculation for calibration validation
- **Sensitivity Adjustment**: Dynamic sensitivity tuning based on calibration results
- **Profile Management**: Save and load calibration profiles for different environments
- **Enhanced Class Analysis**: Comprehensive breakdown of which YAMNet classes contribute to true vs false positives
- **False Positive Identification**: Automatic analysis of environmental noise sources and problematic class recommendations
- **Background Audio Profiling**: Analysis of non-bark audio to identify and exclude noise-generating classes

## FEATURE: Configuration Management
### User Requirements
- Persistent configuration storage for all bark detector settings
- Easy management of complex parameter sets without long CLI commands
- Support for multiple configuration profiles for different use cases
- CLI override capability for quick adjustments
### Specifications
- **Status**: Fully implemented
- **JSON-based Configuration**: Complete configuration system using structured JSON files
- **Automatic File Discovery**: Searches standard locations (./config.json, ~/.bark_detector/config.json, /etc/bark_detector/config.json)
- **Comprehensive Parameter Support**: All CLI parameters available in config files organized by functional area
- **Configuration Sections**:
  - `detection`: Sensitivity, sample rate, thresholds, audio processing parameters
  - `output`: Directory paths for recordings, reports, logs, profiles
  - `calibration`: Default profiles, sensitivity ranges, calibration steps
  - `scheduling`: Auto-start settings, time windows, timezone configuration
  - `legal`: Bylaw violation thresholds for continuous and sporadic detection
- **CLI Integration**: `--config <file>` to load configuration, `--create-config <file>` to generate templates
- **Precedence Handling**: CLI arguments override config file values override system defaults
- **Validation System**: Comprehensive parameter validation with helpful error messages
- **Template Generation**: Automatic creation of example configuration files with documentation
- **Backward Compatibility**: All existing CLI workflows continue to work unchanged
- **Error Handling**: Graceful handling of missing files, invalid JSON, parameter validation failures

## FEATURE: Profile Management  
### User Requirements
- Save detection settings for different monitoring scenarios
- Quick switching between calibrated configurations
- Persistent storage of calibration results
### Specifications
- JSON-based profile storage with calibration parameters
- Named profiles for different environments (e.g., "bedroom", "backyard")
- Profile validation and error handling
- Default profile fallback system
- Integration with calibration system for automatic profile updates
- **Integration with Configuration System**: Profiles work seamlessly with new configuration management

## FEATURE: Audio File Conversion
### User Requirements
- Process existing audio recordings (Voice Memos, M4A files)
- Support common audio formats for calibration
- Maintain audio quality during conversion.
- [NEW] Manually trigger audio file conversion from command line 
    - E.g. `uv run bd.py --convert-all 2025-08-03` converts all audio files labeled 2025-08-03 to YAMNet compatible format leaving originals.
### Specifications
- Support for M4A, MP3, and other common audio formats
- Automatic conversion to 16kHz WAV for YAMNet processing
- Batch processing capabilities for multiple files
- Audio quality preservation during format conversion
- Integration with file-based calibration workflow

## FEATURE: Gap Threshold Hierarchy
### User Requirements
- Group individual barks into meaningful recording sessions
- Support legal evidence collection requirements
### Specifications
- Implements the Gap Threshold Hierarchy as defined in project_overview.md
- Uses 10-second gaps for Recording Sessions and 5-minute gaps for Legal Sporadic Sessions
- See project_overview.md for detailed legal logic examples and business rules

## FEATURE: Real-time Monitoring Interface
### User Requirements
- Visual feedback during monitoring
- Control monitoring start/stop
- Display detection events and session information
### Specifications
- Console-based interface with real-time status updates
- Session tracking with bark count and duration
- Event logging with timestamps and confidence scores
- Keyboard controls for manual recording and calibration
- Progress indicators for model loading and calibration

## FEATURE: Detection Deduplication System
### User Requirements
- Prevent console spam from multiple detections of the same real-world bark
- Provide clean, readable detection output during monitoring
- Maintain detection accuracy while reducing noise
### Specifications
- Implements detection cooldown logic to group nearby detections
- Configurable cooldown duration (default: 2-3 seconds)
- Groups overlapping/nearby detections into single reported events
- Only logs console messages for genuine new bark incidents
- Preserves all detection events for recording and calibration purposes
- Maintains backward compatibility with existing detection behavior

## FEATURE: Date-Based Recording Organization
### User Requirements
- Organize recordings by date for better file management
- Maintain easy access to daily recording collections
- Support long-term evidence collection and organization
- Preserve existing recordings without requiring migration
### Specifications
- **Directory Structure**: Creates date-based subdirectories in format `recordings/YYYY-MM-DD/`
- **Automatic Organization**: New recordings automatically saved to appropriate date folder
- **Backward Compatibility**: Maintains access to existing recordings in flat structure
- **Dual Search Logic**: File discovery searches both new date folders and legacy flat structure
- **Timestamp Preservation**: Maintains existing filename timestamp format for sorting
- **Seamless Integration**: Works transparently with violation analysis and reporting features
- **Error Handling**: Graceful handling of directory creation permissions and edge cases

## FEATURE: Advanced Bylaw Violation Detection
### User Requirements
- Automatically detect when barking meets City of Kelowna bylaw violation criteria using ML analysis
- Flag incidents that can be used as legal evidence with confidence scoring
- Analyze all audio recordings in the recordings folder for a given day for potential violations
- Create comprehensive violation reports for each violation identified with detailed metadata
### Specifications
- **Status**: Fully implemented with advanced YAMNet ML integration
- **ML-Based Analysis**: Uses advanced YAMNet bark detection to analyze actual audio content rather than simple file duration checks. Provides accurate bark event detection with confidence scores and detailed session analysis.
- **Continuous/Constant Violation Detection**: 
  - Detects individual BarkingSessions with total_duration ≥ 5 minutes (300 seconds) of actual barking
  - Uses YAMNet ML model to identify real bark events within sessions
  - Classification: Reports as "Constant" violation type with confidence metrics
- **Sporadic/Intermittent Violation Detection**: 
  - Groups BarkingSessions into Legal Sporadic Sessions using 5-minute gap threshold
  - Detects Legal Sporadic Sessions with ≥15 minutes (900 seconds) total barking duration  
  - Uses Gap Threshold Hierarchy rules defined in project_overview.md
  - Classification: Reports as "Intermittent" violation type with session grouping details
- **Advanced Post-processing Analysis**: 
  - Analyzes existing recordings using advanced bark detection pipeline
  - Loads audio files → YAMNet ML analysis → bark event detection → session creation → violation detection
  - Supports both date-based folder structure and flat file organization
  - Comprehensive error handling for corrupted or missing files
- **Detailed Violation Reports**: Each violation report includes exact dates, times, durations, violation types, confidence scores, audio file references, and metadata for legal evidence
- **CLI Integration**: Accessible via `--analyze-violations DATE` command with comprehensive logging and progress reporting
- **Comprehensive Test Coverage**: Full integration testing ensures reliability for legal evidence collection

## PLANNED FEATURE: Legal Evidence Collection
### User Requirements
- Generate documentation suitable for City of Kelowna complaint submission
- Collect evidence across multiple days as required by city bylaws
- Package audio recordings with proper metadata
### Specifications
- **Status**: Not yet implemented in current codebase
- Generate city-compliant evidence reports
- Track violations across 3-5 day periods
- Create PDF reports ready for city submission including exact dates, times, type of violation and duration.
- Organize audio evidence by incident with metadata
- Record exact dates, times, and durations of incidents

## FEATURE: Modular Architecture
### User Requirements
- Maintainable codebase with clear separation of concerns
- Reusable components for future development
- Easy testing and debugging of individual modules
- Support for both backwards compatibility and modern package structure
### Specifications
- **Status**: Fully implemented
- **Package Structure**: Clean modular architecture with bark_detector package containing core/, calibration/, legal/, recording/, and utils/ modules
- **Backwards Compatibility**: Original bd.py entry point maintained with deprecation warning
- **Modern Interface**: New `python -m bark_detector` package entry point with full CLI functionality  
- **Component Separation**: Core detection logic, data models, calibration system, legal tracking, and utilities properly separated
- **Import System**: All major classes available through package imports for external use
- **Testing Ready**: Individual modules can be tested independently
- **Maintainability**: Single responsibility principle applied throughout with ~200 lines per module vs original 3,111-line monolith

## PLANNED FEATURE: Automated Scheduling System
### User Requirements
- System should start monitoring automatically at specified times
- Save monitoring profiles for repeated use
### Specifications
- **Status**: Not yet implemented in current codebase
- Auto-start monitoring at configurable times with saved profiles
- Support saved monitoring configurations
- Enable scheduled operation for multi-day evidence collection