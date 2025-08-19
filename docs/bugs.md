# B10 Bug: --enhanced-violation-report TypeError on Intel Mac (RESOLVED - 2025-08-18)

## Resolution

**Root Cause**: The `--enhanced-violation-report` command failed on Intel Mac with TypeError "unsupported type for timedelta seconds component: str" when attempting to parse violation timestamps. The legal violation models return time strings in HH:MM AM/PM format, but the enhanced report generator was trying to use them directly as numeric seconds in timedelta calculations.

**Solution**: Implemented robust multi-format datetime parsing for legal violation timestamps:
- Added support for multiple timestamp formats: 12-hour AM/PM ("6:25 AM"), 24-hour ("20:47:39"), full datetime strings ("2025-08-15 20:47:39"), and time-only formats
- Implemented comprehensive format detection and fallback parsing logic
- Added comprehensive error handling to gracefully skip violations with invalid timestamp formats
- Enhanced test coverage with validation for multiple timestamp formats and error scenarios

**Technical Details**: The legal ViolationReport model stores start_time and end_time as strings in various formats, but the enhanced report generator expected numeric seconds. Fixed by implementing format detection and parsing with multiple datetime patterns including "%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M:%S", and others.

**Files Modified**:
- `bark_detector/utils/report_generator.py`: Fixed timestamp parsing in create_violations_from_bark_events()
- `tests/test_utils/test_report_generator.py`: Added tests for string timestamp handling and error cases

**Status**: ✅ Bug fixed - `--enhanced-violation-report` now works correctly on all platforms with proper timestamp parsing.

## Original Bug Report

Error occurred on Intel Mac during enhanced violation report generation:
```
2025-08-18 19:13:58,711 - ERROR - Enhanced violation report failed: unsupported type for timedelta seconds component: str
TypeError: unsupported type for timedelta seconds component: str
```

# B? Bug: --enhanced-violation-report timestamp correlation issues (RESOLVED - 2025-08-18)

## Resolution

**Root Cause**: Timestamp correlation issues were caused by using hardcoded 30-minute audio file duration estimates instead of actual audio file lengths, leading to incorrect bark-to-audio-file correlations.

**Solution**: Implemented comprehensive fixes to the I18 enhanced violation report system:
- **Accurate Audio Duration**: Replaced 30-minute estimates with actual audio file duration reading using soundfile library
- **Real Violation Detection**: Integrated actual LegalViolationTracker algorithms instead of placeholder logic
- **Comprehensive Testing**: Added 60+ tests covering all components with realistic scenarios
- **Robust Error Handling**: Added graceful handling of missing files, corrupted data, and edge cases

**Technical Improvements**:
- Audio file correlation now validates bark timestamps against actual file duration bounds
- Violation detection uses same gap threshold hierarchy and legal criteria as main system
- Enhanced log parsing with millisecond precision timestamp extraction
- Proper integration between log-based bark events and existing violation infrastructure

**Status**: ✅ All timestamp correlation issues resolved with comprehensive testing validation.

## Original Issues Identified:

### Incorrect time stamps for barks 
- Barks do not appear in the audio files at the times indicated in the detailed report. 
- 2025-08-15 06:24:56 BARK (00:00:15.267) - NO BARK HERE
- 2025-08-15 06:25:00 BARK (00:00:19.168) - NO BARK HERE

### Incorrect labeling of barks:

`bark_recording_20250815_062441.wav` is 30 seconds long so it would be impossible for there to be barks at the following time stamps:

- 2025-08-15 06:25:14 BARK (00:00:33.007)
- 2025-08-15 06:25:17 BARK (00:00:36.142)
- 2025-08-15 06:25:21 BARK (00:00:40.692)
- 2025-08-15 06:25:26 BARK (00:00:45.032)
- 2025-08-15 06:25:28 BARK (00:00:47.984)
- etc...


# B9 BUG: --violation-report is not outputting reports (RESOLVED - 2025-08-18)

## Resolution

**Root Cause**: The `--violation-report` CLI command was only logging violation information to the console without creating any actual report files. Users expected comprehensive report generation but received only console output.

**Solution**: Implemented comprehensive report generation system in ViolationDatabase:
- Added `generate_violation_report()` method for complete report creation
- Reports created in `reports/` directory with date-based organization
- Report structure includes:
  - **Executive Summary** (REPORT_SUMMARY.txt) - High-level overview with statistics
  - **Detailed Analysis** (detailed.txt) - Complete violation breakdown with metadata
  - **Machine-readable Data** (CSV) - Structured data for further analysis
  - **Audio Evidence** (audio_evidence/ folder) - Copies of all referenced audio files
- Enhanced CLI to use new report generation and provide user feedback
- Addresses I16 improvement requirement for organized report storage

**Features Implemented**:
- Date-based report folder naming: `Violation_Report_YYYY-MM-DD_timestamp`
- Audio file copying with intelligent path resolution (date folders, flat structure)
- Comprehensive error handling for missing audio files
- Multi-format output for different use cases (legal, technical, archival)
- Violation statistics and summaries for quick assessment

**Files Modified**:
- `bark_detector/legal/database.py`: Added comprehensive report generation methods
- `bark_detector/cli.py`: Enhanced CLI to utilize new report generation
- `tests/test_legal/test_report_generation.py`: Comprehensive test coverage

**Status**: ✅ Bug fixed - `--violation-report` now creates comprehensive, organized reports with all supporting evidence files.

## Original Bug Report

--violation-report appears to exit without errors but no report is actually created. While we work on this bug we should add the following improvement: Save violation reports to the `reports/` directory organized into folders by day e.g. `Violation Report 2025-08-18`. The bark recording files which are referenced in the violation report should be copied to the corresponding violations folder.

## Reproduction Steps and Output

(bark_detector) ➜  bark_detector git:(main) ✗ uv run python -m bark_detector --violation-report 2025-08-15 2025-08-15

2025-08-18 14:56:04,722 - INFO - ======================================================================
2025-08-18 14:56:04,722 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-18 14:56:04,722 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-18 14:56:04,723 - INFO - ======================================================================
2025-08-18 14:56:04,723 - INFO - Loading configuration from: config.json
2025-08-18 14:56:04,723 - INFO - ✅ Configuration loaded successfully from config.json
2025-08-18 14:56:04,723 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
2025-08-18 14:56:04,723 - INFO - Using /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
2025-08-18 14:56:05,942 - INFO - YAMNet model downloaded successfully!
2025-08-18 14:56:05,942 - INFO - Loading class names...
2025-08-18 14:56:05,948 - INFO - 🚫 Excluding problematic class: [ 67] Animal
2025-08-18 14:56:05,948 - INFO - 🚫 Excluding problematic class: [103] Wild animals
2025-08-18 14:56:05,948 - INFO - 📊 Excluded 2 problematic classes to reduce false positives
2025-08-18 14:56:05,948 - INFO - 📋 Detected bark-related classes:
2025-08-18 14:56:05,948 - INFO -     1. [ 21] Whimper
2025-08-18 14:56:05,948 - INFO -     2. [ 68] Domestic animals, pets
2025-08-18 14:56:05,948 - INFO -     3. [ 69] Dog
2025-08-18 14:56:05,948 - INFO -     4. [ 70] Bark
2025-08-18 14:56:05,948 - INFO -     5. [ 71] Yip
2025-08-18 14:56:05,948 - INFO -     6. [ 72] Howl
2025-08-18 14:56:05,948 - INFO -     7. [ 73] Bow-wow
2025-08-18 14:56:05,948 - INFO -     8. [ 74] Growling
2025-08-18 14:56:05,949 - INFO -     9. [ 75] Whimper (dog)
2025-08-18 14:56:05,949 - INFO -    10. [ 81] Livestock, farm animals, working animals
2025-08-18 14:56:05,949 - INFO -    11. [117] Canidae, dogs, wolves
2025-08-18 14:56:05,949 - INFO - YAMNet model loaded successfully!
2025-08-18 14:56:05,949 - INFO - Model supports 521 audio classes
2025-08-18 14:56:05,949 - INFO - Found 11 bark-related classes
2025-08-18 14:56:05,949 - INFO - Advanced Bark Detector initialized:
2025-08-18 14:56:05,949 - INFO -   Sensitivity: 0.68
2025-08-18 14:56:05,949 - INFO -   Sample Rate: 16000 Hz
2025-08-18 14:56:05,949 - INFO -   Session Gap Threshold: 10.0s
2025-08-18 14:56:05,949 - INFO -   Quiet Duration: 30.0s
2025-08-18 14:56:05,949 - INFO -   Output Directory: recordings
2025-08-18 14:56:05,949 - INFO - 📋 Found 1 violations from 2025-08-15 to 2025-08-15:
2025-08-18 14:56:05,949 - INFO -   1. 2025-08-15 - Intermittent
2025-08-18 14:56:05,949 - INFO -      Duration: 24.9min, Files: 458

# B8 BUG: --analyze-violations creates duplicate violations when run multiple times for same date (RESOLVED - 2025-08-18)

## Resolution

**Root Cause**: ViolationDatabase.add_violation() was appending violations without checking for existing data, causing duplicates when --analyze-violations was run multiple times for the same date.

**Solution**: Implemented comprehensive duplicate detection and user choice system:
- Added `has_violations_for_date()` method to check for existing violations
- Added `remove_violations_for_date()` method to clean up existing data
- Added `add_violations_for_date()` method with overwrite option
- Enhanced LegalViolationTracker with interactive parameter for user prompts
- When duplicates detected, users get three options:
  - [o] Overwrite existing violations with new analysis
  - [k] Keep existing violations (abort analysis)  
  - [a] Add new violations alongside existing ones
- Non-interactive mode defaults to overwrite for testing compatibility

**Files Modified**:
- `bark_detector/legal/database.py`: Added duplicate detection methods
- `bark_detector/legal/tracker.py`: Added interactive user prompt system
- `tests/test_legal/test_duplicate_prevention.py`: Comprehensive test coverage

**Status**: ✅ Bug fixed - duplicate violations are now prevented with user control over handling existing data.

## Original Bug Report

--analyze-violations output:
2025-08-18 14:35:24,180 - INFO - Total sessions for 2025-08-15: 464
2025-08-18 14:35:24,181 - INFO - Detected 1 violations for 2025-08-15
2025-08-18 14:35:24,181 - INFO -   Intermittent violation: 0:00:00 - 0:17:47 (24.9min barking)
2025-08-18 14:35:24,203 - INFO - 💾 Saved 1 violations to database
2025-08-18 14:35:24,204 - INFO - ✅ Found 1 violations for 2025-08-15
2025-08-18 14:35:24,204 - INFO -   📅 Violation 1: Intermittent
2025-08-18 14:35:24,204 - INFO -      Duration: 24.9 minutes
2025-08-18 14:35:24,204 - INFO -      Audio files: 458 files
2025-08-18 14:35:24,204 - INFO -      Confidence: 0.802

--violation-report output:
2025-08-18 14:39:32,942 - INFO - 📋 Found 2 violations from 2025-08-15 to 2025-08-15:
2025-08-18 14:39:32,942 - INFO -   1. 2025-08-15 - Intermittent
2025-08-18 14:39:32,942 - INFO -      Duration: 24.9min, Files: 458
2025-08-18 14:39:32,942 - INFO -   2. 2025-08-15 - Intermittent
2025-08-18 14:39:32,942 - INFO -      Duration: 24.9min, Files: 458

This appears to happen when --analyze-violations is run more than 1 time for the period. My guess is that --analyze-violations is appending the same analysis data without checking if the analysis has already been done.

--analyze-violations should check if data already exists for the requested day and should ask the user if they want to re-run the analysis for the specified period or abort and keep the existing data in the database.

# BUG: --violation-report not finding violations created with --analyze-violations

# Reproduction Steps

- Run analysis with `uv run python -m bark_detector --analyze-violations 2025-08-15`
- <analysis completes with 1 violation recorded>
- Run violation report with `uv run python -m bark_detector --violation-report 2025-08-15 2025-08-15`

Output: 
2025-08-18 14:13:24,273 - INFO - 📋 No violations found from 2025-08-15 to 2025-08-15

# BUG: Fix failing tests (RESOLVED - 2025-08-18)

## Root Cause Analysis

**Problem**: Five tests were failing after the I13 bark detector accuracy improvements that changed internal API signatures.

**Root Causes**:
1. **File calibration tests**: Tests were trying to read actual audio files ('test.wav') that don't exist in test environment
2. **Detector tests**: `_get_bark_scores()` method now returns a tuple `(scores, class_details)` instead of just scores
3. **Event conversion tests**: `_scores_to_events()` method now requires `class_details` parameter for enhanced analysis

**Solutions**:
1. **Fixed file calibration tests**:
   - Added `@patch('soundfile.read')` to mock audio file reading in `test_sensitivity_sweep` and `test_calibration_profile_creation`
   - Provided mock audio data instead of trying to read non-existent files

2. **Fixed detector API tests**:
   - Updated `test_get_bark_scores` to handle tuple return value and test class_details
   - Updated `test_scores_to_events` and `test_scores_to_events_with_gaps` to provide required `class_details` parameter
   - Created proper mock class_details structures matching the new API

**Files Modified**:
- `tests/test_calibration/test_file_calibration.py`: Added soundfile mocking for file-based tests
- `tests/test_core/test_detector.py`: Updated API calls to match new method signatures

**Status**: ✅ All tests fixed - 104 tests now passing with comprehensive coverage of enhanced bark detection features

## Original Test Output

# BUG: File Calibration "Unrecognized Argument --calibrate-files" (RESOLVED)

## Bug Repro Steps

(bark_detector) ➜  bark_detector git:(main) uv run bd.py --calibrate-files \
--audio-files samples/bark_recording_20250727_134707_bark.wav samples/bark_recording_20250727_141319_bark.wav samples/background.wav \
--ground-truth-files samples/bark_recording_20250727_134707_bark_ground_truth.json samples/bark_recording_20250727_141319_bark_ground_truth.json \
--save-profile ww-file-calibration
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
usage: bd.py [-h] [--sensitivity SENSITIVITY] [--output-dir OUTPUT_DIR] [--profile PROFILE] [--save-profile SAVE_PROFILE] [--list-profiles] [--calibrate CALIBRATE] [--calibrate-realtime]
             [--analyze-violations ANALYZE_VIOLATIONS] [--violation-report START_DATE END_DATE] [--export-violations EXPORT_VIOLATIONS] [--convert-all CONVERT_ALL] [--list-convertible LIST_CONVERTIBLE]
             [--manual-record]
bd.py: error: unrecognized arguments: --calibrate-files --audio-files samples/bark_recording_20250727_134707_bark.wav samples/bark_recording_20250727_141319_bark.wav samples/background.wav --ground-truth-files samples/bark_recording_20250727_134707_bark_ground_truth.json samples/bark_recording_20250727_141319_bark_ground_truth.json
(bark_detector) ➜  bark_detector git:(main) 

# BUG: Error Saving recording: ERROR - Error: zero-dimensional arrays cannot be concatenated (RESOLVED - 2025-08-14)

## Root Cause Analysis

**Problem**: NumPy concatenation error occurs when pressing Ctrl+C during bark detection monitoring, preventing final recording from being saved.

**Root Cause**: Inconsistency in how audio data is stored in `self.recording_data` between the original and refactored versions:

1. **Original Implementation**: Uses `self.recording_data.append(audio_data)` - creates a list of NumPy arrays
2. **Refactored Implementation**: Uses `self.recording_data.extend(audio_data)` - flattens arrays into a flat list of samples
3. **Problem**: When `np.concatenate()` is called on a flat list of samples instead of a list of arrays, NumPy fails with "zero-dimensional arrays cannot be concatenated"

**Solution**:
- **Line 247**: Changed `self.recording_data.extend(audio_data)` to `self.recording_data.append(audio_data)`
- **Line 497**: Added robust error handling and edge case protection in `save_recording()`
- **Safety Checks**: Added validation for empty recordings, single chunks, and concatenation errors

**Files Modified**:
- `/Users/zand/dev/bark_detector/bark_detector/core/detector.py`: Fixed data storage method and added comprehensive error handling

**Status**: ✅ Bug fixed - recordings now save successfully during normal operation and when interrupted with Ctrl+C

## Original Error Log:
Found in log after pressing Control+C:
2025-08-14 16:19:57,944 - ERROR - Error: zero-dimensional arrays cannot be concatenated

# BUG: BD.py exits immediately after starting the program. (RESOLVED - 2025-08-14)

## Root Cause Analysis

**Problem**: The refactored `bd.py` exited immediately after displaying startup messages, despite showing "Bark detection monitoring started..."

**Root Cause**: The `start_monitoring()` method in the refactored `AdvancedBarkDetector` class was a placeholder that only logged a message and immediately returned with `pass`. It lacked the actual monitoring loop implementation that was present in the original 3,111-line file.

**Solution**: 
- Extracted complete monitoring loop implementation from `bd_original.py`
- Added PyAudio stream setup and audio callback methods
- Implemented the `while self.is_running: time.sleep(0.1)` loop to keep program alive
- Added all supporting methods: `_detect_barks_in_buffer()`, `_get_bark_scores()`, `save_recording()`, etc.
- Proper cleanup and Ctrl+C handling with graceful shutdown

**Status**: ✅ Fixed - Program now stays running during monitoring and properly handles keyboard interrupts.

## Original Error Output:

(bark_detector) ➜  bark_detector git:(main) ✗ uv run bd.py
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
2025-08-14 15:50:02,319 - INFO - ======================================================================
2025-08-14 15:50:02,319 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-14 15:50:02,319 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-14 15:50:02,319 - INFO - ======================================================================
2025-08-14 15:50:02,319 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
2025-08-14 15:50:02,319 - INFO - Using /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
2025-08-14 15:50:03,517 - INFO - YAMNet model downloaded successfully!
2025-08-14 15:50:03,518 - INFO - Loading class names...
2025-08-14 15:50:03,524 - INFO - YAMNet model loaded successfully!
2025-08-14 15:50:03,524 - INFO - Model supports 521 audio classes
2025-08-14 15:50:03,524 - INFO - Found 13 bark-related classes
2025-08-14 15:50:03,524 - INFO - Advanced Bark Detector initialized:
2025-08-14 15:50:03,524 - INFO -   Sensitivity: 0.68
2025-08-14 15:50:03,524 - INFO -   Sample Rate: 16000 Hz
2025-08-14 15:50:03,524 - INFO -   Session Gap Threshold: 10.0s
2025-08-14 15:50:03,524 - INFO -   Quiet Duration: 30.0s
2025-08-14 15:50:03,524 - INFO -   Output Directory: recordings
2025-08-14 15:50:03,524 - INFO - 🐕 Starting bark detection...
2025-08-14 15:50:03,524 - INFO - 🎛️ Sensitivity: 0.68
2025-08-14 15:50:03,524 - INFO - Press Ctrl+C to stop
2025-08-14 15:50:03,524 - INFO - Bark detection monitoring started...
(bark_detector) ➜  bark_detector git:(main)  # Program exited immediately here

# BUG: Recordings start at confidence interval below 0.68 (IDENTIFIED - Root Cause Found)

## Root Cause Analysis

**Problem**: When using saved calibration profiles with `--profile`, recordings start at confidence levels below the intended 0.68 threshold.

**Root Cause**: Saved calibration profiles contain old sensitivity values (e.g., 0.19) that override the new 0.68 default setting. The profile loading system works as designed, but existing profiles were calibrated before the 0.68 sensitivity change.

**Evidence from log analysis**:
- Line 18: System correctly initializes with sensitivity 0.68 ✅
- Line 24: Profile `woofy-world-file-calib` loads with sensitivity 0.19052631578947368 ❌
- Line 28: Final effective sensitivity becomes 0.191 (profile overrides default)
- Lines 34-40: Barks detected at confidence 0.287, 0.336, 0.196, 0.426, 0.291 (all below 0.68)

**Reproduction**: 
- Run `uv run bd.py --profile woofy-world-file-calib` 
- Profile overrides 0.68 default with old calibrated value (~0.19)
- System records barks at confidence levels below 0.68

**Fix Required**: Profile system needs to enforce minimum sensitivity of 0.68 to prevent old profiles from using outdated low-sensitivity values.

## Bug Report

(bark-detector) ➜  bark_detector git:(main) uv run bd.py --profile woofy-world-file-calib
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
2025-08-11 07:45:50,346 - INFO - ======================================================================
2025-08-11 07:45:50,347 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-11 07:45:50,347 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-11 07:45:50,347 - INFO - ======================================================================
2025-08-11 07:45:50,349 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
Downloading YAMNet model2025-08-11 07:45:50,349 - INFO - Using /var/folders/1h/ky9z5q955p397p2p6qz_z1cc0000gp/T/tfhub_modules to cache modules.
2025-08-11 07:45:53,380 - INFO - YAMNet model downloaded successfully!
2025-08-11 07:45:53,381 - INFO - Loading class names...
2025-08-11 07:45:53,394 - INFO - YAMNet model loaded successfully!
2025-08-11 07:45:53,395 - INFO - Model supports 521 audio classes
2025-08-11 07:45:53,395 - INFO - Found 13 bark-related classes
2025-08-11 07:45:53,395 - INFO - Advanced Bark Detector initialized:
2025-08-11 07:45:53,395 - INFO -   Sensitivity: 0.68
2025-08-11 07:45:53,395 - INFO -   Sample Rate: 16000 Hz
2025-08-11 07:45:53,395 - INFO -   Session Gap Threshold: 10.0s
2025-08-11 07:45:53,395 - INFO -   Quiet Duration: 30.0s
2025-08-11 07:45:53,395 - INFO -   Output Directory: recordings
2025-08-11 07:45:53,395 - INFO - 📂 Profile loaded: woofy-world-file-calib
2025-08-11 07:45:53,395 - INFO -   Sensitivity: 0.19052631578947368
2025-08-11 07:45:53,396 - INFO -   Notes: File-based calibration: F1=0.333, P=31.4%, R=35.5%, Files=3
2025-08-11 07:45:53,396 - INFO - 🐕 Starting bark detection...
2025-08-11 07:45:53,396 - INFO - 📂 Using profile: woofy-world-file-calib
2025-08-11 07:45:53,396 - INFO - 🎛️ Sensitivity: 0.191
2025-08-11 07:45:53,396 - INFO - Press Ctrl+C to stop
2025-08-11 07:45:53,396 - INFO - Starting Advanced YAMNet Bark Detector...
2025-08-11 07:45:53,464 - INFO - Advanced bark detector started successfully!
2025-08-11 07:45:53,465 - INFO - Monitoring for barking sounds with comprehensive analysis...
2025-08-11 07:45:53,465 - INFO - Press Ctrl+C to stop
2025-08-11 07:45:54,784 - INFO - 🐕 BARK DETECTED! Confidence: 0.287, Intensity: 0.190, Duration: 0.48s
2025-08-11 07:45:54,785 - INFO - Starting recording session...
2025-08-11 07:45:57,030 - INFO - 🐕 BARK DETECTED! Confidence: 0.336, Intensity: 0.147, Duration: 0.48s
2025-08-11 07:45:59,584 - INFO - 🐕 BARK DETECTED! Confidence: 0.604, Intensity: 0.274, Duration: 0.48s
2025-08-11 07:46:02,278 - INFO - 🐕 BARK DETECTED! Confidence: 0.196, Intensity: 0.141, Duration: 0.48s
2025-08-11 07:46:04,785 - INFO - 🐕 BARK DETECTED! Confidence: 0.426, Intensity: 0.185, Duration: 0.96s
2025-08-11 07:46:07,525 - INFO - 🐕 BARK DETECTED! Confidence: 0.291, Intensity: 0.130, Duration: 0.48s
^C2025-08-11 07:46:09,969 - INFO - Received interrupt signal...
2025-08-11 07:46:09,970 - INFO - Stopping bark detector...
2025-08-11 07:46:09,970 - INFO - Saving final recording...
2025-08-11 07:46:09,973 - INFO - Analyzing complete recording...
2025-08-11 07:46:10,045 - INFO - 🐕 BARK DETECTED! Confidence: 0.522, Intensity: 0.222, Duration: 0.96s
2025-08-11 07:46:10,061 - INFO - Recording Analysis Complete:
2025-08-11 07:46:10,061 - INFO -   Total Events: 3
2025-08-11 07:46:10,061 - INFO -   Sessions: 1
2025-08-11 07:46:10,061 - INFO -   Total Bark Duration: 10.1s (66.2%)
2025-08-11 07:46:10,061 - INFO -   Average Confidence: 0.528
2025-08-11 07:46:10,062 - INFO -   Average Intensity: 0.229
2025-08-11 07:46:10,062 - INFO -   Session 1: 3 barks, 0.2 barks/sec, intensity: 0.229
2025-08-11 07:46:10,062 - INFO - Recording saved: recordings/bark_recording_20250811_074609.wav (Duration: 15.2s)
2025-08-11 07:46:10,062 - INFO - Session Summary - Start: 2025-08-11 07:45:54, End: 2025-08-11 07:46:10, Duration: 15.3s, Barks: 98, Avg Confidence: 0.396, Peak Confidence: 0.925
2025-08-11 07:46:10,190 - INFO - Bark detector stopped.

# BUG: Reports created with --export-violations contain incorrect references to audio files. (RESOLVED)

Details: Reports created with --export-violations contain incorrect references to audio files.

Repro steps:
- generate analysis with `uv run bd.py --violation-report 2025-08-03 2025-08-03`
- generate csv file with `uv run bd.py --export-violations woofy-world-2025-08-03.csv`

Result: 
- The csv file refers to files that don't exist in the recordings folder.
- Example from `woofy-world-2025-08-03-B.csv`:
    - row 2 and row 3 refer to audio file `bark_recording_20250803_093711.wav` that does not exist in the recordings folder.

# ERROR Saving violations database (RESOLVED)

## Resolution

**Root Cause**: NumPy float32 data types from YAMNet model predictions cannot be directly serialized to JSON.

**Solution**: Added `convert_numpy_types()` utility function to convert NumPy data types to native Python types before JSON serialization.

**Files Modified**:
- Added `convert_numpy_types()` function to handle NumPy type conversion
- Updated `ViolationDatabase.save_violations()` method to convert types before serialization  
- Updated `LegalViolationTracker._create_violation_report()` to ensure native Python types

**Status**: ✅ Bug fixed - violations database now saves successfully without JSON serialization errors.

## Original Error Output:

(bark_detector) ➜  bark_detector git:(main) ✗ uv run bd.py --analyze-violations 2025-08-02
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
2025-08-03 11:03:12,469 - INFO - ======================================================================
2025-08-03 11:03:12,469 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-03 11:03:12,469 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-03 11:03:12,469 - INFO - ======================================================================
2025-08-03 11:03:12,469 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
Downloading YAMNet model2025-08-03 11:03:12,469 - INFO - Using /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
2025-08-03 11:03:14,005 - INFO - YAMNet model downloaded successfully!
2025-08-03 11:03:14,005 - INFO - Loading class names...
2025-08-03 11:03:14,038 - INFO - YAMNet model loaded successfully!
2025-08-03 11:03:14,039 - INFO - Model supports 521 audio classes
2025-08-03 11:03:14,039 - INFO - Found 13 bark-related classes
2025-08-03 11:03:14,039 - INFO - Advanced Bark Detector initialized:
2025-08-03 11:03:14,039 - INFO -   Sensitivity: 0.05
2025-08-03 11:03:14,039 - INFO -   Sample Rate: 16000 Hz
2025-08-03 11:03:14,039 - INFO -   Session Gap Threshold: 10.0s
2025-08-03 11:03:14,039 - INFO -   Quiet Duration: 30.0s
2025-08-03 11:03:14,039 - INFO -   Output Directory: recordings
2025-08-03 11:03:14,039 - INFO - 🔍 Analyzing recordings for violations on 2025-08-02
2025-08-03 11:03:14,042 - INFO - Found 8 recording files for 2025-08-02
2025-08-03 11:03:14,042 - INFO - Analyzing recording: bark_recording_20250802_060706.wav
2025-08-03 11:03:19,211 - INFO - Found 238 bark events in 6 sessions from bark_recording_20250802_060706.wav
2025-08-03 11:03:19,214 - INFO - Analyzing recording: bark_recording_20250802_062045.wav
2025-08-03 11:03:20,958 - INFO - Found 139 bark events in 3 sessions from bark_recording_20250802_062045.wav
2025-08-03 11:03:20,960 - INFO - Analyzing recording: bark_recording_20250802_062159.wav
2025-08-03 11:03:21,045 - INFO - Found 3 bark events in 2 sessions from bark_recording_20250802_062159.wav
2025-08-03 11:03:21,045 - INFO - Analyzing recording: bark_recording_20250802_062233.wav
2025-08-03 11:03:21,124 - INFO - Found 5 bark events in 2 sessions from bark_recording_20250802_062233.wav
2025-08-03 11:03:21,124 - INFO - Analyzing recording: bark_recording_20250802_062410.wav
2025-08-03 11:03:21,304 - INFO - Found 18 bark events in 1 sessions from bark_recording_20250802_062410.wav
2025-08-03 11:03:21,304 - INFO - Analyzing recording: bark_recording_20250802_062525.wav
2025-08-03 11:03:21,414 - INFO - Found 9 bark events in 2 sessions from bark_recording_20250802_062525.wav
2025-08-03 11:03:21,414 - INFO - Analyzing recording: bark_recording_20250802_062724.wav
2025-08-03 11:03:21,667 - INFO - Found 22 bark events in 3 sessions from bark_recording_20250802_062724.wav
2025-08-03 11:03:21,667 - INFO - Analyzing recording: bark_recording_20250802_074046.wav
2025-08-03 11:03:32,213 - INFO - Found 261 bark events in 4 sessions from bark_recording_20250802_074046.wav
2025-08-03 11:03:32,219 - INFO - Total sessions for 2025-08-02: 23
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,221 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,221 - INFO - Detected 6 violations for 2025-08-02
2025-08-03 11:03:32,221 - INFO -   Constant violation: 6:07 AM - 6:19 AM (11.1min barking)
2025-08-03 11:03:32,221 - INFO -   Constant violation: 6:21 AM - 6:33 AM (9.9min barking)
2025-08-03 11:03:32,221 - INFO -   Constant violation: 6:26 AM - 6:32 AM (5.2min barking)
2025-08-03 11:03:32,221 - INFO -   Intermittent violation: 6:07 AM - 6:34 AM (32.2min barking)
2025-08-03 11:03:32,221 - INFO -   Constant violation: 7:43 AM - 8:53 AM (67.2min barking)
2025-08-03 11:03:32,221 - INFO -   Intermittent violation: 7:40 AM - 8:53 AM (68.3min barking)
2025-08-03 11:03:32,221 - INFO - ✅ Found 6 violations:
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:07 AM - 6:19 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 11.1min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:21 AM - 6:33 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 9.9min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:26 AM - 6:32 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 5.2min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:07 AM - 6:34 AM
2025-08-03 11:03:32,221 - INFO -      Type: Intermittent, Duration: 32.2min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 7:43 AM - 8:53 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 67.2min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 7:40 AM - 8:53 AM
2025-08-03 11:03:32,221 - INFO -      Type: Intermittent, Duration: 68.3min

# YAMNet Error when starting the project (RESOLVED)

## Resolution

**Root Cause**: Corrupted TensorFlow Hub cache files
**Solution**: Clear the TensorFlow Hub cache directory and restart the application

```bash
# Remove the corrupted cache
rm -rf /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules

# Or more generally (finds user-specific temp folders)
rm -rf /tmp/tfhub_modules
find /var/folders -name "tfhub_modules" -type d 2>/dev/null | xargs rm -rf
```

After clearing the cache, the bark detector will automatically re-download the YAMNet model on the next startup.

**Status**: This troubleshooting information has been added to README.md and project_overview.md for future reference.

## Error Output:
  Downloading YAMNet model2025-08-03 06:49:46,918 - INFO - Using 
  /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
  2025-08-03 06:49:46,920 - ERROR - Error loading YAMNet model: Trying to load a model of 
  incompatible/unknown type. '/var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules/9616fd04ec2
  360621642ef9455b84f4b668e219e' contains neither 'saved_model.pb' nor 'saved_model.pbtxt'.
  Traceback (most recent call last):
    File "/Users/zand/dev/bark_detector/bd.py", line 1897, in <module>
      main()
    File "/Users/zand/dev/bark_detector/bd.py", line 1714, in main
      detector = AdvancedBarkDetector(**config)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/zand/dev/bark_detector/bd.py", line 929, in __init__
      self._load_yamnet_model()
    File "/Users/zand/dev/bark_detector/bd.py", line 966, in _load_yamnet_model
      self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/module_v2.py",
   line 107, in load
      raise ValueError("Trying to load a model of incompatible/unknown type. "
  ValueError: Trying to load a model of incompatible/unknown type. '/var/folders/8x/yr8h7zks5r98fq1rs4n9
  ythc0000gn/T/tfhub_modules/9616fd04ec2360621642ef9455b84f4b668e219e' contains neither 'saved_model.pb'
   nor 'saved_model.pbtxt'.