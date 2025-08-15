# CHANGELOG

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