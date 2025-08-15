"""Pytest fixtures for bark_detector tests"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import json

from bark_detector.core.models import BarkEvent, BarkingSession, CalibrationProfile
from bark_detector.legal.models import ViolationReport


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing."""
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    samples = int(sample_rate * duration)
    
    # Generate a simple sine wave
    t = np.linspace(0, duration, samples, False)
    frequency = 440.0  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to int16 format like PyAudio
    audio_data = (audio_data * 32767).astype(np.int16)
    
    return audio_data


@pytest.fixture
def mock_yamnet_model():
    """Mock YAMNet model for testing without downloading."""
    mock_model = Mock()
    
    # Mock the model call to return fake scores, embeddings, spectrogram
    mock_scores = np.random.rand(5, 521)  # 5 time frames, 521 classes
    mock_embeddings = np.random.rand(5, 1024)  # 5 time frames, 1024 features
    mock_spectrogram = np.random.rand(5, 64)  # 5 time frames, 64 mel bins
    
    mock_model.return_value = (mock_scores, mock_embeddings, mock_spectrogram)
    
    # Mock class map path - create a mock tensor with numpy() method
    mock_tensor = Mock()
    mock_tensor.numpy.return_value = b"/tmp/yamnet_class_map.csv"
    mock_model.class_map_path.return_value = mock_tensor
    
    return mock_model


@pytest.fixture
def sample_bark_event():
    """Create a sample BarkEvent for testing."""
    return BarkEvent(
        start_time=1.0,
        end_time=1.5,
        confidence=0.75,
        intensity=0.8
    )


@pytest.fixture
def sample_barking_session():
    """Create a sample BarkingSession for testing."""
    events = [
        BarkEvent(1.0, 1.5, 0.75),
        BarkEvent(2.0, 2.3, 0.82),
        BarkEvent(3.5, 4.0, 0.68)
    ]
    
    return BarkingSession(
        start_time=1.0,
        end_time=4.0,
        events=events,
        total_barks=3,
        total_duration=1.8,  # Sum of event durations
        avg_confidence=0.75,
        peak_confidence=0.82,
        barks_per_second=1.0,  # 3 barks / 3 second session
        source_file=Path("test_recording.wav")
    )


@pytest.fixture
def sample_calibration_profile():
    """Create a sample CalibrationProfile for testing."""
    return CalibrationProfile(
        name="test_profile",
        sensitivity=0.68,
        min_bark_duration=0.5,
        session_gap_threshold=10.0,
        background_noise_level=0.01,
        created_date="2025-08-14T10:00:00",
        location="Test Environment",
        notes="Test profile for unit tests"
    )


@pytest.fixture
def sample_violation_report():
    """Create a sample ViolationReport for testing."""
    return ViolationReport(
        date="2025-08-14",
        start_time="10:00:00",
        end_time="10:05:00",
        violation_type="Constant",
        total_bark_duration=300.0,
        total_incident_duration=300.0,
        audio_files=["test_file1.wav", "test_file2.wav"],
        audio_file_start_times=["00:00:00", "02:30:00"],
        audio_file_end_times=["02:30:00", "05:00:00"],
        confidence_scores=[0.75, 0.82],
        peak_confidence=0.82,
        avg_confidence=0.785,
        created_timestamp="2025-08-14T10:00:00"
    )


@pytest.fixture
def mock_detector_config():
    """Standard configuration for AdvancedBarkDetector testing."""
    return {
        'sensitivity': 0.68,
        'sample_rate': 16000,
        'chunk_size': 1024,
        'channels': 1,
        'quiet_duration': 30.0,
        'session_gap_threshold': 10.0,
        'output_dir': 'test_recordings'
    }


@pytest.fixture
def yamnet_class_map_file(temp_dir):
    """Create a mock YAMNet class map CSV file."""
    class_map_path = temp_dir / "yamnet_class_map.csv"
    
    # Create a minimal class map with some bark-related classes
    class_map_content = """index,mid,display_name
0,/m/0dgw9r,Human sounds
1,/m/0jbk,Animal
2,/m/05zppz,Male speech
3,/m/02zsn,Female speech
4,/m/0289n,Music
5,/m/0bt9lr,Dog
6,/m/05tny_,Bark
7,/m/07rwj3x,Yip
8,/m/07sx1x9,Bow-wow
9,/m/05zc1,Bird
10,/m/01yrx,Cat"""
    
    with open(class_map_path, 'w') as f:
        f.write(class_map_content)
    
    return str(class_map_path).encode('utf-8')


@pytest.fixture
def mock_pyaudio():
    """Mock PyAudio for testing without audio hardware."""
    mock_audio = Mock()
    mock_stream = Mock()
    
    # Configure mock stream
    mock_stream.is_active.return_value = True
    mock_stream.start_stream.return_value = None
    mock_stream.stop_stream.return_value = None
    mock_stream.close.return_value = None
    
    # Configure mock audio
    mock_audio.open.return_value = mock_stream
    mock_audio.terminate.return_value = None
    mock_audio.get_sample_size.return_value = 2  # 16-bit = 2 bytes
    
    return mock_audio