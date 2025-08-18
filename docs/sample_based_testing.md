# Sample-Based Testing Documentation

## Overview

The sample-based testing system provides real-world validation of bark detection accuracy using actual audio recordings with precise ground truth annotations. This testing approach ensures the system performs reliably with real audio data rather than relying solely on mock-based unit tests.

## Purpose

**Primary Goals:**
- **Real-world validation**: Test bark detection using actual dog barking audio samples
- **Confidence threshold verification**: Ensure 0.65+ confidence threshold is properly enforced  
- **Regression protection**: Prevent accuracy degradation during system changes
- **False positive monitoring**: Validate system performance on background/noise audio

**Key Benefits:**
- Provides confidence in real-world performance
- Uses actual ground truth data with precise timing annotations
- Tests complete end-to-end detection pipeline
- Establishes performance baselines for regression detection

## Sample Data

### Available Samples

**Bark Samples with Ground Truth:**
- `bark_recording_20250727_134707_bark.wav` (53.9s, 15 bark events)
  - Large dog barking with various intensities and patterns
  - Detailed ground truth with HH:MM:SS.mmm precision timing
- `bark_recording_20250727_141319_bark.wav` (33.4s, 15 bark events)  
  - Small dog barking with rapid, shorter bark sequences
  - Complete ground truth annotations for all events

**Background Samples:**
- `background.wav` - Environmental audio for false positive testing

### Ground Truth Format

Ground truth files use JSON format with precise timestamp annotations:

```json
{
  "audio_file": "samples/bark_recording_20250727_134707_bark.wav",
  "duration": 53.91673469387755,
  "instructions": "Timestamp format: HH:MM:SS.mmm",
  "events": [
    {
      "start_time": "00:00:00.000",
      "end_time": "00:00:00.892", 
      "description": "Large Dog barking",
      "confidence_expected": 1.0
    }
  ],
  "format_version": "2.0"
}
```

## Testing Framework

### Core Components

**SampleDataLoader** (`tests/fixtures/sample_data_loader.py`):
- Loads audio files and ground truth annotations
- Handles timestamp parsing (HH:MM:SS.mmm format)
- Provides unified interface for all sample data
- Supports both positive samples (with ground truth) and negative samples (background)

**DetectionEvaluator** (`tests/fixtures/sample_data_loader.py`):
- Compares detected events against ground truth
- Implements time-window matching with configurable tolerance (1.0 second default)
- Enforces confidence threshold filtering (0.65 minimum)
- Calculates precision, recall, and F1 score metrics

**Evaluation Parameters:**
- **Tolerance Window**: 1.0 second (allows reasonable timing variations)
- **Confidence Threshold**: 0.65 (real-world requirement for violation detection)
- **Overlap Requirement**: Minimum 10% overlap between detected and ground truth events

## Test Categories

### 1. Basic Accuracy Tests (`test_sample_accuracy.py`)

**Individual Sample Testing:**
- `test_large_dog_sample_detection()`: Tests large dog bark detection accuracy
- `test_small_dog_sample_detection()`: Tests small dog bark detection (more challenging)
- `test_background_false_positives()`: Validates low false positive rate on background audio

**Infrastructure Testing:**
- `test_sample_loader_initialization()`: Verifies sample discovery and loading
- `test_ground_truth_loading()`: Validates ground truth parsing and structure
- `test_detection_evaluation_metrics()`: Tests evaluation logic and metrics calculation

### 2. Comprehensive System Testing (`test_comprehensive_sample_testing.py`)

**Multi-Sample Analysis:**
- `test_all_bark_samples_comprehensive()`: Tests all available samples and provides detailed performance analysis
- `test_regression_protection()`: Guards against performance degradation during system changes
- `test_confidence_threshold_compliance()`: Verifies proper enforcement of 0.65+ confidence requirement

**System-Level Validation:**
- Tests overall system precision, recall, and F1 scores across all samples
- Provides detailed performance breakdowns by sample type
- Validates false positive rates on background audio

## Performance Baselines

### Current System Performance

**Overall Performance (across all samples):**
- **Precision**: 100% (no false positives detected)
- **Recall**: 63.3% (detects ~2/3 of actual bark events)  
- **F1 Score**: 77.6% (strong overall performance balance)

**By Sample Type:**
- **Large Dog Barks**: Precision 100%, Recall 86.7%, F1 92.9% ✅
- **Small Dog Barks**: Precision 100%, Recall 40.0%, F1 57.1% ✅
- **Background Audio**: <2 false positives per minute ✅

### Performance Requirements

**Minimum Acceptable Performance:**
- **Overall Recall**: ≥40% (must detect at least 40% of actual barks)
- **Overall Precision**: ≥40% (at least 40% of detections must be true barks)
- **Large Dog Recall**: ≥50% (large dog barks should be easier to detect)
- **Small Dog Recall**: ≥30% (small dog barks are more challenging)
- **False Positive Rate**: ≤2 per minute on background audio

## Usage Examples

### Running Sample-Based Tests

```bash
# Run all sample-based tests
uv run pytest tests/test_samples/ -v

# Run comprehensive testing with detailed output
uv run pytest tests/test_samples/test_comprehensive_sample_testing.py -v -s

# Run basic accuracy tests only
uv run pytest tests/test_samples/test_sample_accuracy.py -v

# Run regression protection test
uv run pytest tests/test_samples/test_comprehensive_sample_testing.py::TestComprehensiveSampleTesting::test_regression_protection -v -s
```

### Adding New Sample Data

1. **Add Audio File**: Place WAV file in `samples/` directory
2. **Create Ground Truth**: Create corresponding JSON file with `_ground_truth.json` suffix
3. **Verify Format**: Ensure timestamps use HH:MM:SS.mmm format
4. **Test Discovery**: Run `test_sample_loader_initialization` to verify sample is found

## Integration with CI/CD

### Test Organization
- **Fast Tests**: Basic infrastructure and evaluation logic tests (complete in seconds)
- **Slower Tests**: Audio processing and comprehensive analysis (complete in ~1 second per sample)
- **All Tests**: Complete sample-based testing suite adds ~12 additional tests to existing 111-test suite

### Regression Detection
The sample-based tests serve as a regression detection system:
- Automatically fail if precision/recall drop below minimum thresholds
- Provide detailed performance breakdowns for debugging accuracy issues
- Establish performance baselines for future system changes

## Troubleshooting

### Common Issues

**Sample Loading Problems:**
- Verify audio files are in correct format (WAV preferred)
- Check ground truth JSON files have correct naming convention (`*_ground_truth.json`)
- Ensure timestamp format is HH:MM:SS.mmm

**Low Accuracy Results:**
- Check confidence threshold settings (should be 0.65 for real-world use)
- Verify YAMNet mock is returning appropriate confidence scores
- Consider tolerance window (1.0 second default may need adjustment)

**Test Failures:**
- Review performance requirements - may need adjustment based on real-world observations
- Check for changes in detection algorithm that might affect accuracy
- Verify sample files haven't been corrupted or modified

## Future Enhancements

### Potential Improvements
- **Additional Sample Types**: Add more diverse bark samples (different breeds, environments)
- **Environmental Variations**: Test performance under different noise conditions
- **Temporal Analysis**: Add tests for bark sequence patterns and timing
- **Calibration Integration**: Validate sample-based testing with calibration system results

### Performance Optimization
- **Confidence Tuning**: Use sample-based results to optimize confidence thresholds
- **Class Analysis**: Analyze which YAMNet classes contribute most to accurate detection
- **Timing Precision**: Evaluate optimal tolerance windows for different use cases

---

**Note**: This testing system focuses on practical bark detection for legal violation identification. The 0.65+ confidence threshold and reasonable tolerance windows reflect real-world usage requirements rather than laboratory precision measurements.