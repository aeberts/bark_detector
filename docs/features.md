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
- Maintain audio quality during conversion
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

## PLANNED FEATURE: Bylaw Violation Detection
### User Requirements
- Automatically detect when barking meets City of Kelowna bylaw violation criteria
- Flag incidents that can be used as legal evidence
### Specifications
- **Status**: Not yet implemented in current codebase
- Auto-flag 5-minute continuous barking violations
- Auto-flag 15-minute sporadic barking violations within a legal session
- Uses Gap Threshold Hierarchy rules defined in project_overview.md (5-minute legal gap threshold)
- Will implement LegalViolationTracker class for violation detection

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