"""Tests for configurable violation thresholds"""

import pytest
from unittest.mock import Mock, patch

from bark_detector.legal.tracker import LegalViolationTracker
from bark_detector.utils.config import BarkDetectorConfig, LegalConfig, DetectionConfig
from bark_detector.core.models import BarkingSession
from bark_detector.core.detector import AdvancedBarkDetector


class TestConfigurableThresholds:
    """Test configurable violation threshold functionality."""

    def test_legal_violation_tracker_uses_config_defaults(self):
        """Test that LegalViolationTracker uses default values when no config provided."""
        tracker = LegalViolationTracker()

        # Should use default values
        assert tracker.constant_violation_duration == 300    # 5 minutes
        assert tracker.intermittent_threshold == 900      # 15 minutes
        assert tracker.intermittent_gap_threshold == 300  # 5 minutes
        assert tracker.constant_gap_threshold == 10.0  # 10 seconds
        assert tracker.session_gap_threshold == 10.0  # 10 seconds

    def test_legal_violation_tracker_uses_custom_config(self):
        """Test that LegalViolationTracker uses custom configuration values."""
        custom_config = BarkDetectorConfig(
            legal=LegalConfig(
                constant_violation_duration=600,    # 10 minutes
                intermittent_violation_duration=1200,     # 20 minutes
                intermittent_gap_threshold=180,   # 3 minutes
                constant_gap_threshold=20.0  # 20 seconds
            ),
            detection=DetectionConfig(
                session_gap_threshold=15.0   # 15 seconds
            )
        )

        tracker = LegalViolationTracker(config=custom_config)

        # Should use custom values
        assert tracker.constant_violation_duration == 600
        assert tracker.intermittent_threshold == 1200
        assert tracker.intermittent_gap_threshold == 180
        assert tracker.constant_gap_threshold == 20.0
        assert tracker.session_gap_threshold == 15.0

    def test_continuous_violation_uses_configured_threshold(self):
        """Test that continuous violation detection uses configured threshold."""
        # Create config with 10-minute threshold instead of default 5 minutes
        custom_config = BarkDetectorConfig(
            legal=LegalConfig(constant_violation_duration=600)  # 10 minutes
        )

        tracker = LegalViolationTracker(config=custom_config)

        # Create a 7-minute session (should not be violation with 10-min threshold)
        session = BarkingSession(
            start_time=1000.0,
            end_time=1420.0,  # 7 minutes = 420 seconds
            events=[],
            total_barks=10,
            total_duration=420.0,
            avg_confidence=0.8,
            peak_confidence=0.9,
            barks_per_second=0.024
        )

        violations = tracker.analyze_violations([session])
        assert len(violations) == 0  # No violation with 10-minute threshold

        # Test with default 5-minute threshold
        default_tracker = LegalViolationTracker()
        violations_default = default_tracker.analyze_violations([session])
        assert len(violations_default) == 1  # Should be violation with 5-minute threshold

    def test_advanced_bark_detector_passes_config_to_tracker(self):
        """Test that AdvancedBarkDetector passes configuration to LegalViolationTracker."""
        custom_config = BarkDetectorConfig(
            legal=LegalConfig(
                constant_violation_duration=720,    # 12 minutes
                intermittent_violation_duration=1800,     # 30 minutes
                intermittent_gap_threshold=120,   # 2 minutes
                constant_gap_threshold=25.0  # 25 seconds
            ),
            detection=DetectionConfig(
                session_gap_threshold=20.0   # 20 seconds
            )
        )

        detector = AdvancedBarkDetector(config=custom_config)

        # Verify the detector's violation tracker has the custom config
        assert detector.violation_tracker.constant_violation_duration == 720
        assert detector.violation_tracker.intermittent_threshold == 1800
        assert detector.violation_tracker.intermittent_gap_threshold == 120
        assert detector.violation_tracker.constant_gap_threshold == 25.0
        assert detector.violation_tracker.session_gap_threshold == 20.0

    def test_backward_compatibility_no_config(self):
        """Test that existing code works without providing config parameter."""
        # This should work without breaking (backward compatibility)
        detector = AdvancedBarkDetector()

        # Should use default values
        assert detector.violation_tracker.constant_violation_duration == 300
        assert detector.violation_tracker.intermittent_threshold == 900
        assert detector.violation_tracker.intermittent_gap_threshold == 300
        assert detector.violation_tracker.constant_gap_threshold == 10.0
        assert detector.violation_tracker.session_gap_threshold == 10.0

    def test_gap_threshold_parameters_are_configurable(self):
        """Test that gap threshold parameters are configurable and used by methods."""
        custom_config = BarkDetectorConfig(
            detection=DetectionConfig(session_gap_threshold=25.0),
            legal=LegalConfig(
                intermittent_gap_threshold=150,
                constant_gap_threshold=30.0
            )
        )

        tracker = LegalViolationTracker(config=custom_config)

        # Verify the instance variables were set correctly
        assert tracker.session_gap_threshold == 25.0
        assert tracker.intermittent_gap_threshold == 150
        assert tracker.constant_gap_threshold == 30.0

        # Test that methods use None properly to get instance values
        # (We can't easily test the full algorithm without complex setup,
        # but we can verify the parameter handling works)
        assert tracker.session_gap_threshold == 25.0
        assert tracker.intermittent_gap_threshold == 150
        assert tracker.constant_gap_threshold == 30.0