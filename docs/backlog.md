# Priority Tasks to Discuss & Plan 
- [ ] I4 Improvement: Separate log files into separate files by day. Move logs to the `logs/` folder
- [ ] I1 Improvement: Save reports to the `reports/` folder
- [ ] R1 Research: Compare PANNs-CNN14 vs YAMNet vs SemDNN & CLAP for bark detection.

# Backlog

## Tests

## Bugs
2025-08-14 16:19:57,944 - ERROR - Error: zero-dimensional arrays cannot be concatenated

## Fixed Bugs (Completed)
- [x] B6 Bug: File Calibration "Unrecognized Argument" - Fixed T2 refactor missing CLI arguments. Restored 11 missing CLI arguments including --calibrate-files, --audio-files, --ground-truth-files, --save-profile and others.
- [x] B5 Bug: BD.py exits immediately after starting the program - Fixed incomplete refactoring where monitoring loop was not implemented
- [x] B1 Bug: YAMNet Error when starting the project.
- [x] B2 Bug: Error saving violations database.
- [x] B3 Bug: Reports created with --export-violations contain incorrect references to audio files.
- [x] B4 Bug: Recordings start at confidence interval below 0.68.

## Potential Improvements & Enhancements (to be confirmed)
- [ ] I5 Improvement: Optimize YAMNet performance for longer monitoring periods
- [ ] I6 Improvement: Enhanced visualization for detection events and sessions
- [ ] I7 Improvement: Add audio quality metrics and validation
- [ ] I8 Improvement: Implement batch processing for large audio file collections
- [ ] I9 Improvement: Add configurable detection thresholds per dog breed/size
- [ ] I10 Improvement: Create web-based interface for remote monitoring

## Previously Fixed Bugs (Completed)
- [x] B1 Bug: YAMNet Error when starting the project.
- [x] B2 Bug: Error saving violations database.
- [x] B3 Bug: Reports created with --export-violations contain incorrect references to audio files.
- [x] B4 Bug: Recordings start at confidence interval below 0.68.

## Implemented Improvements (Complete)
- [x] I2 Improvement: Configure bark recorder with a configuration file supporting all current features - Implemented comprehensive JSON-based configuration system with validation, CLI integration, automatic file search, precedence handling (CLI > config file > defaults), example files, and complete test coverage (32 tests). Supports all detection parameters, output directories, calibration settings, scheduling options, and legal thresholds. Includes `--config` and `--create-config` CLI options for easy usage.
- [x] I13 Phase 1 Improvement: Improve Bark Detector Accuracy - Implemented intelligent YAMNet class filtering, reduced false positives by 54% (13→6), improved precision from 58.1% to 71.4%. Excluded problematic broad classes ("Animal", "Wild animals") while maintaining detection capability with 11 focused bark-related classes.
- [x] I1 Improvement: reduce sensitivity of the bark detector to only begin barking when the YAMNet confidence is 0.68 or higher to avoid false positives.
- [x] I11 Improvement: All recordings for a single day should go in their own folder.
- [x] I12 Improvement: Convert ground truth files from decimal seconds to HH:MM:SS.mmm format with data quality validation and conversion utilities.
- [x] I3 Improvement: Avoid flooding console with multiple bark detections per real-world bark.
- [x] I4 Improvement: Allow manual conversion of audio files from the command line

## Implemented Features (Complete)
- [x] F1 Feature: YAMNet ML-based bark detection system
- [x] F2 Feature: Audio recording management with session tracking
- [x] F3 Feature: File-based calibration with ground truth annotation
- [x] F4 Feature: Real-time calibration with spacebar feedback
- [x] F5 Feature: Profile management system for saving calibration settings
- [x] F6 Feature: Audio file conversion (M4A, MP3 to WAV)
- [x] F7 Feature: Cross-platform deployment with intelligent installer
- [x] F8 Feature: Real-time monitoring interface with console output

### Legal Evidence Features (Partially Implemented)
- [x] F9 Feature: Implement LegalViolationTracker class for bylaw violation detection
- [x] F10 Feature: Auto-flag 5-minute continuous barking violations
- [x] F11 Feature: Auto-flag 15-minute sporadic barking violations
- [ ] F12 Feature: Create PDF report generation for city submission
- [x] F13 Feature: Build multi-day evidence tracking (3-5 day periods) 
- [x] F14 Feature: Implement audio evidence packaging with metadata
- [x] F15 Feature: Generate city-compliant documentation with exact dates/times/durations

### Automation & Scheduling (Not Yet Implemented)
- [ ] F16 Feature: Implement automated scheduling system with configurable start times
- [ ] F17 Feature: Auto-start monitoring at specified times with saved profiles
- [ ] F18 Feature: Build persistent monitoring for multi-day evidence collection

### Technical Debt & Maintenance (Completed)
- [x] T2 Task: Refactor bd.py into separate modules
- [x] T3 Task: Implement error handling for TensorFlow model loading failures
- [x] T8 Task: Implement comprehensive project testing plan with 4-phase approach covering core detection, legal compliance, and integration testing (38/38 tests passing)
- [x] T9 Task: Implement tests of the bark detector using sample audio and ground truth files - Created comprehensive sample-based testing infrastructure using real audio recordings with precise ground truth annotations. Implemented SampleDataLoader and DetectionEvaluator with 1-second tolerance windows and 0.65+ confidence thresholds. Added 12 comprehensive tests covering individual sample accuracy, multi-sample analysis, confidence threshold compliance, false positive monitoring, and regression protection. System achieves 77.6% F1 score overall with 100% precision and 63.3% recall across all samples. All 123 tests passing.
- [x] T10 Task: Enhanced legal and analysis module test coverage - Fixed violation analysis system to use advanced YAMNet bark detection instead of simple file duration checks. Added comprehensive sporadic violation detection (15+ minutes across multiple sessions within 5-minute gaps). Fixed all test mocks to properly integrate with enhanced bark detector API. All 111 tests passing with full violation analysis integration coverage.

### Technical Debt & Maintenance (Remaining)
- [ ] T4 Task: Add comprehensive unit tests for calibration system
- [ ] T5 Task: Add logging configuration management
- [ ] T6 Task: Create automated deployment scripts for different platforms
- [ ] T7 Task: Add performance monitoring and metrics collection