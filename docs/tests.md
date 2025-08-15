# Test T9 Implementation Plan

  1. Task Analysis

  Task: T9 - Implement test of the bark detector using sample audio and ground truth files from the @samples/ folder

  Current State Analysis:
  - ✅ @samples/ folder exists with real bark recordings and ground truth JSON files
  - ✅ FileBasedCalibration system already implemented in bark_detector.calibration.file_calibration
  - ✅ Comprehensive test infrastructure exists (45 tests currently passing)
  - ❌ No integration test using actual sample files from @samples/ folder
  - ❌ Ground truth data has formatting issues (inconsistent timestamps)

  Gap: The existing tests use mocked data, but there's no test that validates the bark detector against real sample
  audio files.

  2. Technical Planning

  Implementation Steps:

  Step 1: Fix Sample Ground Truth Data

  - Clean up inconsistent timestamps in existing ground truth JSON files
  - Validate ground truth events against audio file durations
  - Ensure proper start_time < end_time relationships

  Step 2: Create Integration Test Module

  - New file: tests/test_integration/test_sample_validation.py
  - Test class: TestSampleAudioValidation
  - Use real sample files from @samples/ folder (not mocked)

  Step 3: Implement Core Test Functions

  - Test bark detection accuracy against ground truth
  - Test file-based calibration using sample data
  - Test detection metrics (precision, recall, F1 score)
  - Test audio file loading and processing pipeline

  Step 4: Add Test Utilities

  - Helper function to load and validate sample ground truth
  - Utility to compare detected events vs ground truth with tolerance
  - Performance metrics calculation utilities

  Key Dependencies:

  - Existing FileBasedCalibration system
  - Real YAMNet model (or sophisticated mock)
  - Sample audio files in @samples/ folder
  - Ground truth JSON validation

  Files to Modify/Create:

  - Create: tests/test_integration/test_sample_validation.py
  - Fix: samples/bark_recording_*_ground_truth.json files
  - Update: tests/conftest.py (add sample file fixtures)

  3. Implementation Strategy

  Phase 1: Data Preparation

  1. Fix ground truth JSON files with correct timestamps
  2. Add validation for ground truth data integrity
  3. Create fixtures for sample file access in tests

  Phase 2: Core Integration Test

  1. Implement test using real sample audio files
  2. Load actual YAMNet model (with proper timeout/error handling)
  3. Compare detector output against ground truth annotations
  4. Validate detection accuracy meets minimum thresholds

  Phase 3: Extended Validation

  1. Test multiple sample files
  2. Test calibration workflow using samples
  3. Test edge cases (background noise, multiple barks)
  4. Performance benchmarking

  Architectural Decisions:

  - Real vs Mock: Use real audio files and YAMNet model for integration test
  - Test Isolation: Keep sample validation separate from unit tests
  - Performance: Add timeout controls for model loading
  - Validation Tolerance: Use reasonable time tolerance (±0.5s) for event matching

  4. Expected Test Structure

  class TestSampleAudioValidation:
      def test_sample_bark_detection_accuracy(self):
          """Test detection accuracy on real sample files"""

      def test_file_based_calibration_with_samples(self):
          """Test calibration using sample ground truth"""

      def test_background_noise_filtering(self):
          """Test background.wav produces no false positives"""

      def test_detection_metrics_meet_thresholds(self):
          """Ensure F1 score > 0.8 on sample data"""

  5. Success Criteria

  - ✅ Integration test runs with real sample audio files
  - ✅ Detection accuracy > 80% F1 score on sample data
  - ✅ Background noise file produces minimal false positives
  - ✅ Ground truth data is clean and validated
  - ✅ Test completes within reasonable time (< 30 seconds)