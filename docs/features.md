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

## PLANNED FEATURE: Bylaw Violation Detection
### User Requirements
- Automatically detect when barking meets City of Kelowna bylaw violation criteria
- Flag incidents that can be used as legal evidence
- Analyze all audio recordings in the recordings folder for a given day for potential violations
- Create a violation report for each violation identified with the following information:
    - Date of violation
    - start time
    - end time
    - Type of violation: (Intermittent? (aka sporadic) / Constant (aka continual))
    

### Specifications
- **Status**: Not yet implemented in current codebase
- **Continuous/Constant Violation Detection**: 
  - Detects individual BarkingSessions with total_duration ≥ 5 minutes (300 seconds)
  - Detects sequences of BarkingSessions with gaps ≤30 seconds that together span ≥5 minutes
  - Uses existing 10-second gap threshold (Recording Sessions) for detection
  - Classification: Reports as "Constant" violation type
- **Sporadic/Intermittent Violation Detection**: 
  - Groups BarkingSessions into Legal Sporadic Sessions using 5-minute gap threshold
  - Detects Legal Sporadic Sessions with ≥15 minutes (900 seconds) total barking duration  
  - Uses Gap Threshold Hierarchy rules defined in project_overview.md
  - Classification: Reports as "Intermittent" violation type
- **Post-processing Analysis**: Analyze existing recordings in recordings/ folder by date to reconstruct violation timeline
- **Real-time Detection**: Flag violations during live monitoring sessions
- **Violation Database**: Track violations across multiple days for city evidence requirements (4+ instances over 3-5 days)
- **RDCO Report Generation**: Generate reports with exact dates, times, durations, violation types, and associated audio file references
- **Additional Report Fields**: Include total barking duration, list of associated audio recording files, and RDCO-compliant formatting
- **Will implement enhanced LegalViolationTracker class for comprehensive violation detection and reporting**

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

## PLANNED FEATURE: Automated Scheduling System
### User Requirements
- System should start monitoring automatically at specified times
- Save monitoring profiles for repeated use
### Specifications
- **Status**: Not yet implemented in current codebase
- Auto-start monitoring at configurable times with saved profiles
- Support saved monitoring configurations
- Enable scheduled operation for multi-day evidence collection