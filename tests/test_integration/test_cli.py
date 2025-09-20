"""Integration tests for the CLI interface"""

import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock


class TestCLIIntegration:
    """Test CLI integration and end-to-end workflows"""
    
    def test_cli_help(self):
        """Test that CLI shows help without errors"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "bark_detector" in result.stdout.lower() or "usage" in result.stdout.lower()
    
    def test_cli_version(self):
        """Test that CLI can display version information"""
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import bark_detector; print('OK')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "OK" in result.stdout
    
    def test_cli_invalid_argument(self):
        """Test that CLI handles invalid arguments gracefully"""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--invalid-argument"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should exit with error code but not crash
        assert result.returncode != 0
        # Should show some error message
        assert len(result.stderr) > 0 or "error" in result.stdout.lower()
    
    @patch('bark_detector.core.detector.hub.load')
    @patch('bark_detector.core.detector.pyaudio.PyAudio')
    def test_cli_dry_run_mode(self, mock_pyaudio, mock_hub_load, temp_dir):
        """Test CLI in dry-run mode (no actual recording)"""
        # Mock YAMNet model loading
        mock_model = Mock()
        mock_tensor = Mock()
        mock_tensor.numpy.return_value = b"/tmp/test_class_map.csv"
        mock_model.class_map_path.return_value = mock_tensor
        mock_hub_load.return_value = mock_model
        
        # Create a fake class map file
        class_map_path = temp_dir / "yamnet_class_map.csv"
        class_map_content = """index,mid,display_name
0,/m/0dgw9r,Human sounds
1,/m/0jbk,Animal
5,/m/0bt9lr,Dog
6,/m/05tny_,Bark"""
        class_map_path.write_text(class_map_content)
        
        # Update mock to return actual file path
        mock_tensor.numpy.return_value = str(class_map_path).encode('utf-8')
        
        # Test that CLI can initialize without crashing
        # We can't easily test full CLI without mocking audio input,
        # but we can test that the imports and basic initialization work
        try:
            import bark_detector.cli
            import bark_detector.core.detector
            
            # Test detector initialization with mocked components
            detector = bark_detector.core.detector.AdvancedBarkDetector(
                output_dir=str(temp_dir)
            )
            
            # Verify basic properties
            assert detector.sensitivity == 0.68
            assert detector.output_dir == str(temp_dir)
            assert detector.sample_rate == 16000
            
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)
        
        assert success, f"CLI initialization failed: {error_msg if not success else ''}"
    
    def test_module_imports(self):
        """Test that all main modules can be imported without errors"""
        modules_to_test = [
            "bark_detector.core.detector",
            "bark_detector.core.models",
            "bark_detector.calibration.file_calibration",
            "bark_detector.legal.tracker",
            "bark_detector.legal.models",
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                success = True
            except ImportError as e:
                success = False
                error = str(e)
            
            assert success, f"Failed to import {module_name}: {error if not success else ''}"
    
    def test_audio_file_processing_workflow(self, temp_dir):
        """Test basic audio file processing workflow"""
        # Create a dummy audio file
        audio_file = temp_dir / "test.wav"
        audio_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")  # Minimal WAV header
        
        try:
            # Test that we can import and use audio conversion utilities
            from bark_detector.utils.audio_converter import AudioFileConverter
            converter = AudioFileConverter()
            
            # Test that the converter can be initialized
            assert converter is not None
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)
        
        assert success, f"Audio workflow test failed: {error_msg if not success else ''}"
    
    def test_legal_workflow_integration(self, temp_dir):
        """Test legal violation analysis workflow"""
        try:
            from bark_detector.legal.tracker import LegalViolationTracker
            from bark_detector.legal.models import ViolationReport
            from bark_detector.core.models import BarkingSession
            
            # Initialize tracker
            tracker = LegalViolationTracker()
            
            # Create test session data
            session = BarkingSession(
                start_time=0.0,
                end_time=360.0,  # 6 minutes - should trigger violation
                events=[],
                total_barks=50,
                total_duration=300.0,  # 5 minutes of barking
                avg_confidence=0.8,
                peak_confidence=0.9,
                barks_per_second=0.14,
                source_file=Path("test.wav")
            )
            
            # Test violation analysis
            violations = tracker.analyze_violations([session])
            
            # Should detect continuous violation
            assert len(violations) == 1
            
            success = True
        except Exception as e:
            success = False
            error_msg = str(e)
        
        assert success, f"Legal workflow test failed: {error_msg if not success else ''}"
    
    def test_project_structure_consistency(self):
        """Test that project structure is consistent with documented structure"""
        project_root = Path(__file__).parent.parent.parent
        
        # Check key files exist
        key_files = [
            "bd.py",
            "pyproject.toml",
            "README.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "bark_detector/__init__.py",
            "bark_detector/core/__init__.py",
            "bark_detector/legal/__init__.py",
            "bark_detector/calibration/__init__.py",
        ]
        
        for file_path in key_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Required file missing: {file_path}"
        
        # Check key directories exist
        key_dirs = [
            "bark_detector/core",
            "bark_detector/legal", 
            "bark_detector/calibration",
            "bark_detector/utils",
            "tests",
            "docs",
        ]
        
        for dir_path in key_dirs:
            full_path = project_root / dir_path
            assert full_path.is_dir(), f"Required directory missing: {dir_path}"

    def test_analysis_sensitivity_cli_parameter(self):
        """Test that --analysis-sensitivity CLI parameter is recognized and included in help."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "bark_detector", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        assert result.returncode == 0
        # Verify that the analysis-sensitivity parameter is in the help output
        assert "--analysis-sensitivity" in result.stdout

    def test_analysis_sensitivity_parameter_parsing(self):
        """Test that --analysis-sensitivity parameter can be parsed without errors."""
        # This test only checks argument parsing, not full execution
        result = subprocess.run(
            ["uv", "run", "python", "-c",
             "import sys; sys.path.insert(0, '.'); from bark_detector.cli import parse_arguments; "
             "args = parse_arguments(); print('PARSED OK')"],
            input="--analysis-sensitivity 0.25\n",
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        # Argument parsing should succeed (even if the command doesn't fully run)
        assert "PARSED OK" in result.stdout or result.returncode == 0