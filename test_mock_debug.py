#!/usr/bin/env python3
"""Debug mock detector setup"""

from unittest.mock import Mock
from bark_detector.core.models import BarkEvent

# Create mock detector exactly like test
mock_detector = Mock()
mock_detector.sample_rate = 16000
mock_detector.session_gap_threshold = 10.0
mock_detector.analysis_sensitivity = 0.30

# Mock the _detect_barks_in_buffer_with_sensitivity method
mock_bark_events = [
    BarkEvent(start_time=10.0, end_time=20.0, confidence=0.8, triggering_classes=["Bark"])
]
mock_detector._detect_barks_in_buffer_with_sensitivity = Mock(return_value=mock_bark_events)

# Test if mock has the method
print(f"Mock detector has method: {hasattr(mock_detector, '_detect_barks_in_buffer_with_sensitivity')}")
print(f"Method type: {type(mock_detector._detect_barks_in_buffer_with_sensitivity)}")

# Test calling the method directly
import numpy as np
result = mock_detector._detect_barks_in_buffer_with_sensitivity(np.array([1.0, 2.0]), 0.3)
print(f"Direct call result: {result}")
print(f"Call count: {mock_detector._detect_barks_in_buffer_with_sensitivity.call_count}")