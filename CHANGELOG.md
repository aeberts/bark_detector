# CHANGELOG

## 2025-08-18

### Major Improvements
- **Sample-Based Testing System (T9)**: Implemented comprehensive real-world testing infrastructure using actual audio recordings with precise ground truth annotations. Created SampleDataLoader and DetectionEvaluator with 1-second tolerance windows and 0.65+ confidence thresholds for practical bark detection validation. Added 12 comprehensive tests covering individual sample accuracy, multi-sample analysis, confidence threshold compliance, false positive monitoring, and regression protection. System demonstrates 77.6% F1 score overall with 100% precision and 63.3% recall across large and small dog bark samples. All 123 tests passing (added 12 new sample-based tests to existing 111-test suite).
- **Violation Analysis Enhancement**: Complete overhaul of `--analyze-violations` functionality to use advanced YAMNet bark detection instead of simple file duration analysis. Now properly analyzes audio content using ML model to detect actual bark events and create accurate barking sessions. Implemented comprehensive sporadic violation detection (15+ minutes across multiple sessions within 5-minute gaps) alongside existing continuous violation detection (5+ minutes per session). Enhanced LegalViolationTracker with _detect_sporadic_violations(), _group_sessions_for_sporadic_analysis(), and _create_sporadic_violation_report() methods.

### Bug Fixes
- Fixed failing tests caused by I13 accuracy improvements: Updated file calibration tests to mock soundfile.read instead of accessing non-existent test files, fixed detector tests to handle new _get_bark_scores() tuple return value and _scores_to_events() class_details parameter. Fixed legal violation tracker tests to properly mock advanced bark detector with required attributes and methods.

### Improvements
- **TensorFlow Debug Output Suppression**: Implemented comprehensive suppression of TensorFlow debug messages that were cluttering console output during YAMNet model loading and inference operations. Added TF_CPP_MIN_LOG_LEVEL=3, TF_ENABLE_ONEDNN_OPTS=0 environment variables, TensorFlow logger level configuration, and TensorFlow Hub warning filters across all entry points (cli.py, detector.py, bd.py). Eliminates the extensive "DEBUG INFO Executor start aborting" messages and "pkg_resources is deprecated" warnings shown during model operations. Provides clean console output while maintaining error reporting.
- I2: Implemented comprehensive JSON-based configuration system supporting all current CLI features. Added ConfigManager with validation, automatic file search paths (./config.json, ~/.bark_detector/config.json), and CLI precedence handling. Created config.json and config-example.json templates. Integrated --config and --create-config CLI options with backward compatibility. Includes 32 comprehensive tests covering configuration loading, validation, CLI integration, and error handling. System supports detection parameters, output directories, calibration settings, scheduling options, and legal thresholds with proper validation and error messages.

## 2025-08-15

### Bug Fixes
- B6: Fixed CLI arguments missing after T2 refactor. Restored 11 critical CLI arguments that were removed during modular architecture transition including --calibrate-files, --audio-files, --ground-truth-files, --save-profile, --convert-files, --convert-directory, --list-violations, --record, --duration, --create-template, --sensitivity-range, and --steps. Implemented complete handlers for all argument types using test-driven development. User's file-based calibration workflows now function correctly.

### Improvements
- I13 Phase 1: Implemented intelligent YAMNet class filtering to reduce false positives by 54%. Enhanced bark detection with comprehensive class-level analysis system that identifies problematic YAMNet classes. Excluded broad classes ("Animal", "Wild animals") that were causing environmental noise false positives. Improved precision from 58.1% to 71.4% while maintaining detection capability. Added detailed detection logging with per-class confidence scoring and false positive analysis tools for ongoing accuracy optimization.
- I12: Implemented comprehensive ground truth format conversion from decimal seconds to HH:MM:SS.mmm format. Added time conversion utilities with flexible format parsing (HH:MM:SS.mmm, MM:SS.mmm, SS.mmm), enhanced GroundTruthEvent model with dual format support and validation, created batch conversion script with data quality fixes, and updated all tests. Improved data integrity by fixing inverted timestamps and duration confusion in sample files. All 60 tests passing.

## 2025-08-14

### Major Refactoring
- T2: Completed full modular architecture refactor of bd.py (3,111 lines) into clean package structure. Created bark_detector package with core/, calibration/, legal/, recording/, and utils/ modules. Maintained 100% backwards compatibility via bd.py wrapper while providing modern `python -m bark_detector` interface. Enables easier maintenance, testing, and future development.

### Bug Fixes
- B5: Fixed critical bug where refactored bd.py exited immediately after startup. Root cause was incomplete monitoring loop implementation during T2 refactoring. Added complete PyAudio stream setup, monitoring loop with `while self.is_running`, and all supporting detection methods. Program now stays running correctly and responds to Ctrl+C for graceful shutdown.
- B6: Fixed "zero-dimensional arrays cannot be concatenated" error when pressing Ctrl+C during monitoring. Root cause was inconsistent audio data storage method (extend vs append) between original and refactored versions. Changed recording data storage to use append() and added comprehensive error handling for edge cases.

### Testing Infrastructure
- T8: Implemented comprehensive project testing plan with 4-phase approach. Created pytest infrastructure with 45/45 core tests passing covering: data models, YAMNet ML integration, legal violation detection, CLI functionality. Features sophisticated YAMNet/TensorFlow mocking, comprehensive fixtures, and end-to-end integration testing for the modular architecture.
- Fixed calibration test import paths broken by T2 modular refactoring. Updated test mocking from module-specific paths to direct library patches, resolving 5 failing file calibration tests.

### Improvements
- I11: Implemented date-based folder organization for recordings. New recordings are saved to `recordings/YYYY-MM-DD/` subdirectories while maintaining backward compatibility with existing flat structure recordings.