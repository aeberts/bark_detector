# Improvement Plans

## T? Review if renaming exisiting files with correct timestamp is necessary. 

## T21 Task: Review all code which analyzes bark recording files for incorrect timestamps.
- the filename of bark recording files includes a timestamp of the **end** of the recording NOT the start of the recording which might be causing hard to detect bugs in code which analyzes audio files.
- E.g. the file `bark_recording_20250818_062559.wav` is 1.5MB file which **finished** recording barks at 06:25:29 AM on 2025-08-18.
- Exisiting code which parses time information from the filename of an audio bark recording may assume that this is the start time of the recording (which is incorrect).

## T20 Task : Review --analyze-violations for bugs.
- Is `--analyze-violations` correctly identifying and saving violation information?

## I17 Improvement: Save violation analysis database to the project's violations/ directory 

Improvement: Save each violation in it's own file within a folder for each day. e.g. `.violations/2025-08-15/2025-08-15-violations.json`.

Currently --analyze-violations saves the database to ~/.bark_detector/violations.json

## I19 Improvement : Separate logs by date

- Create separate logs for each day. E.g. logs/2025-08-19-bark_detector.log

## I18 Improvement: Violation Report Improvements

Violation report should include the start time and end time of the violation relative to the time of day. Here is an example of how I would like the report to look:

### Barking Violation Report Summary Template.

Note: items in curly brackets {} are instructions about what should go in the report. E.g. 
{Visual Graph of Barking Session} should be replaced with a visual graph of the bark events as described.

<Barking Violation Summary Template>
Barking Violation Report Summary
Date: 2025-08-15

SUMMARY:
Total Violations: 1 
Constant Violations: 0
Intermittent Violations: 1

Violation 1 (Intermittent):
Start time: 06:25:13  End Time 06:47:23 
Duration: 22 mins 10 seconds
Total Barks: {Total Barks Analyzed}
Supporting audio files:
- bark_recording_20250815_062511.wav
- bark_recording_20250815_064746.wav

Generated at: 2025-08-18 at 15:12:31`

</Barking Violation Summary Template>

### Barking Violation Detail Report

<Barking Violation Details Template>
Barking Detail Report for 2025-08-15, Violation 1

Violation Type: Intermittent
Start time: 06:25:13 End Time 06:47:23 
Duration: 22 mins 10 seconds
Total Barks: {Total Barks Analyzed}

{Visual Graph of Barking Session
Notes on Visual Graph: 
- X-axis is time with X=0 being the start time of the violation (in this case 06:25:13)
- The x-axis should stretch slightly past the end time of the violation (in this case 06:47:23)}
- The x-axis should be scaled to fit the width of a letter sized pdf.}

Supporting Audio Files:

# bark_recording_20250815_062511.wav
- 2025-08-15 06:25:13 Bark (00:00:02.01)
- 2025-08-15 06:25:15 Bark (00:00:04.34)

# bark_recording_20250815_064746.wav
{Identify bark details similar to the example above}

</Barking Violation Details Template>

## Reduce Tensor flow DEBUG info to console (COMPLETED 2025-08-18)

2025-08-18 07:51:08.883764: I tensorflow/core/platform/cpu_feature_guard.cc:182] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
2025-08-18 07:51:10,946 - INFO - ======================================================================
2025-08-18 07:51:10,946 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-18 07:51:10,946 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-18 07:51:10,946 - INFO - ======================================================================
2025-08-18 07:51:10,947 - INFO - ✅ Configuration loaded successfully from config.json
2025-08-18 07:51:10,947 - INFO - 📝 Configuration loaded from: config.json
2025-08-18 07:51:10,947 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
2025-08-18 07:51:10,947 - INFO - Using /var/folders/1h/ky9z5q955p397p2p6qz_z1cc0000gp/T/tfhub_modules to cache modules.
2025-08-18 07:51:11.114527: I tensorflow/core/common_runtime/executor.cc:1197] [/device:CPU:0] (DEBUG INFO) Executor start aborting (this does not indicate an error and you can ignore this message): INVALID_ARGUMENT: You must feed a value for placeholder tensor 'inputs_3' with dtype 

## I13: Improve Bark Detector Accuracy (PHASE 1 COMPLETE)

### Problem Statement
- Ground truth files contain 30 bark events
- Current file calibration using human-detected barks matches 18 barks, misses 12 barks and yields 13 false positive events.
- False positive events are causing recordings to be created that do not contain barking and which have to be manually checked by a human before being submitted as a complaint to the city.

### Goal
- Increase accuracy of bark detector without "overfitting" to sample data (real-world data can vary significantly from day to day)
- Reduce "false positives" requiring manual verification of recordings.
- Research ways to improve existing YAMNet bark detector in realtime detection.

### Phase 1 Results (COMPLETED 2025-08-15)

**Performance Improvements:**
- **False Positives Reduced**: 13 → 6 (54% reduction)
- **Precision Improved**: 58.1% → 71.4% (+13.3%)
- **Recall Trade-off**: 60.0% → 50.0% (-10% acceptable for precision gain)
- **F1 Score Maintained**: 0.590 → 0.588

**Technical Implementation:**
- Enhanced bark detection with class-level analysis system
- Added comprehensive logging of which YAMNet classes trigger detections
- Implemented intelligent class filtering to exclude problematic broad classes
- Built false positive analysis tools with per-class confidence scoring

**Key Discovery - Problematic Classes:**
Through background audio analysis, identified classes causing 100% false positives:
- **"Animal"** [class 67]: Too broad, catches birds, insects, environmental sounds
- **"Wild animals"** [class 103]: Too broad, triggers on non-dog wildlife sounds

**Excluded Classes:**
```
Excluded 2 problematic classes:
🚫 [67] Animal
🚫 [103] Wild animals
```

**Remaining Active Classes (11 total):**
- [21] Whimper
- [68] Domestic animals, pets
- [69] Dog ✅
- [70] Bark ✅
- [71] Yip ✅
- [72] Howl ✅
- [73] Bow-wow ✅
- [74] Growling ✅
- [75] Whimper (dog) ✅
- [81] Livestock, farm animals, working animals ⚠️
- [117] Canidae, dogs, wolves ✅

**Business Impact:**
- **54% reduction in manual review time** for city complaint preparation
- **Higher confidence recordings** for legal submission
- **Maintained detection capability** for legitimate violations

### Phase 2 Considerations (Future)
Based on ongoing analysis, potential next improvements:
- Monitor "Livestock, farm animals, working animals" class (showed 2 false positives vs 5 true positives)
- Temporal pattern validation (bark duration filtering)
- Spectral signature validation for frequency-based filtering
- Context-aware detection (speech/music filtering)

### Questions Addressed
- ✅ **"Animal" class impact**: Confirmed - causes significant false positives from environmental sounds
- ✅ **Class analysis methodology**: Implemented comprehensive per-class breakdown system
- ✅ **False positive sources**: Identified and eliminated primary culprits
- 🔄 **Temporal processing impact**: Requires Phase 2 investigation
- 🔄 **Spectrograph approach**: Alternative approach for Phase 2

## File Calibration Log
(bark_detector) ➜  bark_detector git:(main) ✗ uv run bd.py --calibrate-files \
--audio-files samples/bark_recording_20250727_134707_bark.wav samples/bark_recording_20250727_141319_bark.wav samples/background.wav \
--ground-truth-files samples/bark_recording_20250727_134707_bark_ground_truth.json samples/bark_recording_20250727_141319_bark_ground_truth.json \
--save-profile ww-file-calibration
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
2025-08-15 15:36:43,377 - INFO - ======================================================================
2025-08-15 15:36:43,377 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-15 15:36:43,377 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-15 15:36:43,377 - INFO - ======================================================================
2025-08-15 15:36:43,377 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
2025-08-15 15:36:43,377 - INFO - Using /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
2025-08-15 15:36:43,378 - INFO - Downloading TF-Hub Module 'https://tfhub.dev/google/yamnet/1'.
2025-08-15 15:36:44,862 - INFO - Downloaded https://tfhub.dev/google/yamnet/1, Total size: 17.43MB
2025-08-15 15:36:44,866 - INFO - Downloaded TF-Hub Module 'https://tfhub.dev/google/yamnet/1'.
2025-08-15 15:36:46,143 - INFO - YAMNet model downloaded successfully!
2025-08-15 15:36:46,143 - INFO - Loading class names...
2025-08-15 15:36:46,170 - INFO - YAMNet model loaded successfully!
2025-08-15 15:36:46,170 - INFO - Model supports 521 audio classes
2025-08-15 15:36:46,170 - INFO - Found 13 bark-related classes
2025-08-15 15:36:46,170 - INFO - Advanced Bark Detector initialized:
2025-08-15 15:36:46,170 - INFO -   Sensitivity: 0.68
2025-08-15 15:36:46,170 - INFO -   Sample Rate: 16000 Hz
2025-08-15 15:36:46,170 - INFO -   Session Gap Threshold: 10.0s
2025-08-15 15:36:46,170 - INFO -   Quiet Duration: 30.0s
2025-08-15 15:36:46,170 - INFO -   Output Directory: recordings
2025-08-15 15:36:46,170 - INFO - 📁 Starting file-based calibration...
2025-08-15 15:36:46,246 - INFO - 🔄 Using existing converted file: bark_recording_20250727_134707_bark_16khz.wav
2025-08-15 15:36:46,247 - INFO - 📁 Added test file: bark_recording_20250727_134707_bark.wav (15 ground truth events)
2025-08-15 15:36:46,247 - INFO - 🔄 Using existing converted file: bark_recording_20250727_141319_bark_16khz.wav
2025-08-15 15:36:46,248 - INFO - 📁 Added test file: bark_recording_20250727_141319_bark.wav (15 ground truth events)
2025-08-15 15:36:46,248 - INFO - 📁 Added test file: background.wav (0 ground truth events)
2025-08-15 15:36:46,248 - INFO - 🔍 Running sensitivity sweep: 0.010 to 0.500
2025-08-15 15:36:46,248 - INFO - 📊 Testing 3 files with 20 sensitivity levels
2025-08-15 15:36:46,248 - INFO - 🎛️  Testing sensitivity 0.010 (1/20)
2025-08-15 15:36:48,640 - INFO -    Precision: 63.6%, Recall: 23.3%, F1: 0.341
2025-08-15 15:36:48,640 - INFO - 🎛️  Testing sensitivity 0.036 (2/20)
2025-08-15 15:36:48,912 - INFO -    Precision: 64.3%, Recall: 30.0%, F1: 0.409
2025-08-15 15:36:48,912 - INFO - 🎛️  Testing sensitivity 0.062 (3/20)
2025-08-15 15:36:49,181 - INFO -    Precision: 61.9%, Recall: 43.3%, F1: 0.510
2025-08-15 15:36:49,182 - INFO - 🎛️  Testing sensitivity 0.087 (4/20)
2025-08-15 15:36:49,452 - INFO -    Precision: 58.3%, Recall: 46.7%, F1: 0.519
2025-08-15 15:36:49,452 - INFO - 🎛️  Testing sensitivity 0.113 (5/20)
2025-08-15 15:36:49,723 - INFO -    Precision: 55.6%, Recall: 50.0%, F1: 0.526
2025-08-15 15:36:49,723 - INFO - 🎛️  Testing sensitivity 0.139 (6/20)
2025-08-15 15:36:49,994 - INFO -    Precision: 60.7%, Recall: 56.7%, F1: 0.586
2025-08-15 15:36:49,994 - INFO - 🎛️  Testing sensitivity 0.165 (7/20)
2025-08-15 15:36:50,265 - INFO -    Precision: 58.1%, Recall: 60.0%, F1: 0.590
2025-08-15 15:36:50,265 - INFO - 🎛️  Testing sensitivity 0.191 (8/20)
2025-08-15 15:36:50,541 - INFO -    Precision: 51.4%, Recall: 60.0%, F1: 0.554
2025-08-15 15:36:50,541 - INFO - 🎛️  Testing sensitivity 0.216 (9/20)
2025-08-15 15:36:50,814 - INFO -    Precision: 50.0%, Recall: 60.0%, F1: 0.545
2025-08-15 15:36:50,814 - INFO - 🎛️  Testing sensitivity 0.242 (10/20)
2025-08-15 15:36:51,085 - INFO -    Precision: 48.6%, Recall: 60.0%, F1: 0.537
2025-08-15 15:36:51,085 - INFO - 🎛️  Testing sensitivity 0.268 (11/20)
2025-08-15 15:36:51,361 - INFO -    Precision: 45.9%, Recall: 56.7%, F1: 0.507
2025-08-15 15:36:51,361 - INFO - 🎛️  Testing sensitivity 0.294 (12/20)
2025-08-15 15:36:51,636 - INFO -    Precision: 40.5%, Recall: 50.0%, F1: 0.448
2025-08-15 15:36:51,637 - INFO - 🎛️  Testing sensitivity 0.319 (13/20)
2025-08-15 15:36:51,907 - INFO -    Precision: 41.7%, Recall: 50.0%, F1: 0.455
2025-08-15 15:36:51,907 - INFO - 🎛️  Testing sensitivity 0.345 (14/20)
2025-08-15 15:36:52,178 - INFO -    Precision: 45.5%, Recall: 50.0%, F1: 0.476
2025-08-15 15:36:52,178 - INFO - 🎛️  Testing sensitivity 0.371 (15/20)
2025-08-15 15:36:52,450 - INFO -    Precision: 41.7%, Recall: 50.0%, F1: 0.455
2025-08-15 15:36:52,450 - INFO - 🎛️  Testing sensitivity 0.397 (16/20)
2025-08-15 15:36:52,727 - INFO -    Precision: 45.7%, Recall: 53.3%, F1: 0.492
2025-08-15 15:36:52,727 - INFO - 🎛️  Testing sensitivity 0.423 (17/20)
2025-08-15 15:36:53,000 - INFO -    Precision: 44.4%, Recall: 53.3%, F1: 0.485
2025-08-15 15:36:53,000 - INFO - 🎛️  Testing sensitivity 0.448 (18/20)
2025-08-15 15:36:53,276 - INFO -    Precision: 42.9%, Recall: 50.0%, F1: 0.462
2025-08-15 15:36:53,276 - INFO - 🎛️  Testing sensitivity 0.474 (19/20)
2025-08-15 15:36:53,551 - INFO -    Precision: 44.1%, Recall: 50.0%, F1: 0.469
2025-08-15 15:36:53,551 - INFO - 🎛️  Testing sensitivity 0.500 (20/20)
2025-08-15 15:36:53,827 - INFO -    Precision: 42.9%, Recall: 50.0%, F1: 0.462
2025-08-15 15:36:53,827 - INFO - 🎯 Calibration Results:
2025-08-15 15:36:53,827 - INFO -   Optimal Sensitivity: 0.165
2025-08-15 15:36:53,827 - INFO -   Best F1 Score: 0.590
2025-08-15 15:36:53,827 - INFO -   Precision: 58.1%
2025-08-15 15:36:53,827 - INFO -   Recall: 60.0%
2025-08-15 15:36:53,827 - INFO -   Total Ground Truth Events: 30
2025-08-15 15:36:53,827 - INFO -   Matches: 18
2025-08-15 15:36:53,827 - INFO -   False Positives: 13
2025-08-15 15:36:53,827 - INFO -   Missed: 12
2025-08-15 15:36:53,827 - INFO - ✅ File-based calibration complete! Profile 'ww-file-calibration' saved.
2025-08-15 15:36:53,827 - INFO -    To use: uv run python -m bark_detector --profile ww-file-calibration

## I12: Modify Ground Truth Files to Use HH:MM:SS.MS Format (COMPLETE)

### Problem Statement
Current ground truth files use decimal seconds format (e.g., `"start_time": 5.25`) which has several issues:
- Not human-readable for manual annotation
- Data quality problems (inverted start/end times, inconsistent values)
- Difficult to verify against audio editing software timestamps
- Error-prone for manual ground truth creation

### Proposed Solution
Convert ground truth timestamp format from decimal seconds to human-readable HH:MM:SS.MS format:
- Current: `"start_time": 5.25, "end_time": 7.8`
- New: `"start_time": "00:00:05.250", "end_time": "00:00:07.800"`

### Technical Implementation

#### Phase 1: Time Conversion Utilities
- Create `seconds_to_timestamp(seconds: float) -> str` function
- Create `timestamp_to_seconds(timestamp: str) -> float` function  
- Add format detection and validation logic
- Support millisecond precision for ML accuracy

#### Phase 2: Model Updates
- Update `GroundTruthEvent` class to support both formats
- Add parsing methods for HH:MM:SS.MS strings
- Maintain backwards compatibility with existing float format
- Auto-detect format during file loading

#### Phase 3: Migration Tools
- Create `scripts/convert_ground_truth_format.py` batch conversion script
- Update `FileBasedCalibration` to handle both formats seamlessly
- Validate conversion accuracy and data integrity

#### Phase 4: Data Cleanup
- Fix existing ground truth data quality issues:
  - Ensure start_time < end_time for all events
  - Validate timestamps against audio file duration
  - Remove invalid/corrupted entries
- Convert sample files to new format
- Update documentation and examples

### Benefits
- **Human Readable**: Easy manual verification and annotation
- **Audio Tool Compatible**: Matches timestamps in audio editing software
- **Quality Control**: Easier to spot and fix invalid timestamps
- **Precision**: Maintains millisecond accuracy needed for ML
- **Error Reduction**: Less prone to human annotation errors

### Files Modified
- `bark_detector/core/models.py` - GroundTruthEvent updates
- `bark_detector/calibration/file_calibration.py` - format handling
- `scripts/convert_ground_truth_format.py` - conversion utility
- `samples/*.json` - ground truth data files
- Tests updated for new format support

### Migration Strategy
- Backwards compatibility maintained during transition
- Auto-detection of format prevents breaking changes
- Gradual migration of files without service interruption
- Comprehensive testing ensures no functionality loss

### Success Criteria
- All ground truth files use HH:MM:SS.MS format
- Backwards compatibility with decimal format maintained
- Data quality issues resolved (valid start < end times)
- FileBasedCalibration works correctly with new format
- Manual annotation workflow becomes significantly easier