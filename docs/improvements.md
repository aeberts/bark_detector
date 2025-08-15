# Improvement Plans

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