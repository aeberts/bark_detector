# Backlog

## Bugs
- [x] Bug: YAMNet Error when starting the project.
- [x] Bug: Error saving violations database.
- [x] BUG: Reports created with --export-violations contain incorrect references to audio files.

### Current Improvements & Enhancements
- [x] Improvement: Avoid flooding console with multiple bark detections per real-world bark.
- [x] Improvement: Allow manual conversion of audio files from the command line
- [ ] Improvement: Optimize YAMNet performance for longer monitoring periods
- [ ] Improvement: Enhanced visualization for detection events and sessions
- [ ] Improvement: Add audio quality metrics and validation
- [ ] Improvement: Implement batch processing for large audio file collections
- [ ] Improvement: Add configurable detection thresholds per dog breed/size
- [ ] Improvement: Create web-based interface for remote monitoring

## Work-in-Progress and Planned Tasks

### Implemented Features (Complete)
- [x] Feature: YAMNet ML-based bark detection system
- [x] Feature: Audio recording management with session tracking
- [x] Feature: File-based calibration with ground truth annotation
- [x] Feature: Real-time calibration with spacebar feedback
- [x] Feature: Profile management system for saving calibration settings
- [x] Feature: Audio file conversion (M4A, MP3 to WAV)
- [x] Feature: Cross-platform deployment with intelligent installer
- [x] Feature: Real-time monitoring interface with console output

### Legal Evidence Features (Partially Implemented)
- [x] Feature: Implement LegalViolationTracker class for bylaw violation detection
- [x] Feature: Auto-flag 5-minute continuous barking violations
- [x] Feature: Auto-flag 15-minute sporadic barking violations
- [ ] Feature: Create PDF report generation for city submission
- [x] Feature: Build multi-day evidence tracking (3-5 day periods) 
- [x] Feature: Implement audio evidence packaging with metadata
- [x] Feature: Generate city-compliant documentation with exact dates/times/durations

### Automation & Scheduling (Not Yet Implemented)
- [ ] Feature: Implement automated scheduling system with configurable start times
- [ ] Feature: Auto-start monitoring at specified times with saved profiles
- [ ] Feature: Build persistent monitoring for multi-day evidence collection

### Technical Debt & Maintenance
- [x] Task: Implement error handling for TensorFlow model loading failures
- [ ] Task: Add comprehensive unit tests for calibration system
- [ ] Task: Add logging configuration management
- [ ] Task: Create automated deployment scripts for different platforms
- [ ] Task: Add performance monitoring and metrics collection