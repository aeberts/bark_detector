# Tasks to Discuss & Plan
- [ ] I2 Improvement: Configure bark recorder with a configuration file supporting all current features.
- [ ] I1 Improvement: Save reports to the `reports/` folder
- [ ] T2 Task: Refactor bd.py into separate modules
- [ ] R1 Research: Compare PANNs-CNN14 vs YAMNet vs SemDNN & CLAP for bark detection.

# Backlog

## Bugs

## Current Improvements & Enhancements
- [x] I3 Improvement: Avoid flooding console with multiple bark detections per real-world bark.
- [x] I4 Improvement: Allow manual conversion of audio files from the command line
- [ ] I5 Improvement: Optimize YAMNet performance for longer monitoring periods
- [ ] I6 Improvement: Enhanced visualization for detection events and sessions
- [ ] I7 Improvement: Add audio quality metrics and validation
- [ ] I8 Improvement: Implement batch processing for large audio file collections
- [ ] I9 Improvement: Add configurable detection thresholds per dog breed/size
- [ ] I10 Improvement: Create web-based interface for remote monitoring

## Fixed Bugs (Completed)
- [x] B1 Bug: YAMNet Error when starting the project.
- [x] B2 Bug: Error saving violations database.
- [x] B3 Bug: Reports created with --export-violations contain incorrect references to audio files.
- [x] B4 Bug: Recordings start at confidence interval below 0.68.

## Implemented Improvements (Complete)
- [x] I1 Improvement: reduce sensitivity of the bark detector to only begin barking when the YAMNet confidence is 0.68 or higher to avoid false positives.
- [x] I11 Improvement: All recordings for a single day should go in their own folder.

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

### Technical Debt & Maintenance
- [x] T3 Task: Implement error handling for TensorFlow model loading failures
- [ ] T4 Task: Add comprehensive unit tests for calibration system
- [ ] T5 Task: Add logging configuration management
- [ ] T6 Task: Create automated deployment scripts for different platforms
- [ ] T7 Task: Add performance monitoring and metrics collection