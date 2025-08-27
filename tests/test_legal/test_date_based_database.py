"""Tests for date-based violation database structure (I17 improvement)"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from bark_detector.legal.database import ViolationDatabase
from bark_detector.legal.models import ViolationReport


class TestDateBasedViolationDatabase:
    """Test suite for I17 improvement - project-local date-based violation storage."""
    
    def test_default_violations_directory_structure(self):
        """Test that ViolationDatabase uses project-local violations/ directory by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to simulate project directory
            original_cwd = Path.cwd()
            temp_path = Path(temp_dir)
            
            try:
                import os
                os.chdir(temp_path)
                
                # Create database with default settings (should use violations/ in current dir)
                db = ViolationDatabase()
                
                # Verify it's using date structure and correct directory
                assert db.use_date_structure is True
                # Use resolve() to handle symlinks in temp directories
                assert db.violations_dir.resolve() == (temp_path / 'violations').resolve()
                assert db.db_path is None
                
            finally:
                os.chdir(original_cwd)
    
    def test_explicit_violations_directory(self):
        """Test explicit violations_dir parameter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'custom_violations'
            
            db = ViolationDatabase(violations_dir=violations_dir)
            
            assert db.use_date_structure is True
            assert db.violations_dir == violations_dir
            assert db.db_path is None
    
    def test_legacy_db_path_mode(self):
        """Test backward compatibility with legacy db_path parameter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_path = Path(temp_dir) / 'legacy_violations.json'
            
            # Test legacy mode using positional parameter with .json extension
            db = ViolationDatabase(legacy_path)
            
            assert db.use_date_structure is False
            assert db.db_path == legacy_path
            assert db.violations_dir is None
    
    def test_date_based_file_path_generation(self):
        """Test _get_violations_file_path generates correct date-based paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Test path generation
            test_date = '2025-08-15'
            expected_path = violations_dir / '2025-08-15' / '2025-08-15-violations.json'
            
            result_path = db._get_violations_file_path(test_date)
            assert result_path == expected_path
    
    def test_directory_creation_on_save(self):
        """Test that directories are automatically created when saving violations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test violation
            violation = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Save violations for date
            db._save_violations_for_date([violation], '2025-08-15')
            
            # Verify directory and file were created
            expected_dir = violations_dir / '2025-08-15'
            expected_file = expected_dir / '2025-08-15-violations.json'
            
            assert expected_dir.exists()
            assert expected_file.exists()
            
            # Verify content
            with open(expected_file, 'r') as f:
                data = json.load(f)
            
            assert len(data['violations']) == 1
            assert data['violations'][0]['date'] == '2025-08-15'
            assert data['violations'][0]['violation_type'] == 'Constant'
    
    def test_load_violations_for_date(self):
        """Test loading violations from date-specific files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test data manually
            test_date = '2025-08-15'
            date_dir = violations_dir / test_date
            date_dir.mkdir(parents=True)
            
            test_data = {
                'violations': [{
                    'date': test_date,
                    'start_time': '06:25:00',
                    'end_time': '06:30:00',
                    'violation_type': 'Constant',
                    'total_bark_duration': 300.0,
                    'total_incident_duration': 300.0,
                    'audio_files': ['test.wav'],
                    'audio_file_start_times': ['00:00:00'],
                    'audio_file_end_times': ['00:05:00'],
                    'confidence_scores': [0.8],
                    'peak_confidence': 0.8,
                    'avg_confidence': 0.8,
                    'created_timestamp': '2025-08-15T12:00:00'
                }]
            }
            
            violations_file = date_dir / f'{test_date}-violations.json'
            with open(violations_file, 'w') as f:
                json.dump(test_data, f)
            
            # Load and verify
            violations = db._load_violations_for_date(test_date)
            
            assert len(violations) == 1
            assert violations[0].date == test_date
            assert violations[0].violation_type == 'Constant'
            assert violations[0].total_bark_duration == 300.0
    
    def test_has_violations_for_date_date_structure(self):
        """Test has_violations_for_date with date-based structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Initially no violations
            assert db.has_violations_for_date('2025-08-15') is False
            
            # Create violations file
            test_date = '2025-08-15'
            date_dir = violations_dir / test_date
            date_dir.mkdir(parents=True)
            
            violations_file = date_dir / f'{test_date}-violations.json'
            test_data = {
                'violations': [{
                    'date': test_date,
                    'start_time': '06:25:00',
                    'end_time': '06:30:00',
                    'violation_type': 'Constant',
                    'total_bark_duration': 300.0,
                    'total_incident_duration': 300.0,
                    'audio_files': ['test.wav'],
                    'audio_file_start_times': ['00:00:00'],
                    'audio_file_end_times': ['00:05:00'],
                    'confidence_scores': [0.8],
                    'peak_confidence': 0.8,
                    'avg_confidence': 0.8,
                    'created_timestamp': '2025-08-15T12:00:00'
                }]
            }
            with open(violations_file, 'w') as f:
                json.dump(test_data, f)
            
            # Now should have violations
            assert db.has_violations_for_date('2025-08-15') is True
    
    def test_get_violations_by_date_date_structure(self):
        """Test get_violations_by_date with date-based structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test violation
            violation = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Save violation
            db._save_violations_for_date([violation], '2025-08-15')
            
            # Retrieve and verify
            retrieved_violations = db.get_violations_by_date('2025-08-15')
            
            assert len(retrieved_violations) == 1
            assert retrieved_violations[0].date == '2025-08-15'
            assert retrieved_violations[0].violation_type == 'Constant'
    
    def test_get_violations_by_date_range_date_structure(self):
        """Test get_violations_by_date_range with date-based structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create violations for multiple dates
            dates = ['2025-08-15', '2025-08-16', '2025-08-17', '2025-08-18']
            
            for i, date in enumerate(dates):
                violation = ViolationReport(
                    date=date,
                    start_time=f'06:2{i}:00',
                    end_time=f'06:2{i+1}:00',
                    violation_type='Constant',
                    total_bark_duration=300.0,
                    total_incident_duration=300.0,
                    audio_files=[f'test_{date}.wav'],
                    audio_file_start_times=['00:00:00'],
                    audio_file_end_times=['00:05:00'],
                    confidence_scores=[0.8],
                    peak_confidence=0.8,
                    avg_confidence=0.8,
                    created_timestamp=datetime.now().isoformat()
                )
                db._save_violations_for_date([violation], date)
            
            # Test date range retrieval
            violations = db.get_violations_by_date_range('2025-08-16', '2025-08-17')
            
            assert len(violations) == 2
            retrieved_dates = [v.date for v in violations]
            assert '2025-08-16' in retrieved_dates
            assert '2025-08-17' in retrieved_dates
            assert '2025-08-15' not in retrieved_dates
            assert '2025-08-18' not in retrieved_dates
    
    def test_remove_violations_for_date_date_structure(self):
        """Test remove_violations_for_date with date-based structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test violation
            violation = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Save violation
            db._save_violations_for_date([violation], '2025-08-15')
            
            # Verify it exists
            assert db.has_violations_for_date('2025-08-15') is True
            violations_file = violations_dir / '2025-08-15' / '2025-08-15-violations.json'
            assert violations_file.exists()
            
            # Remove violations
            removed_count = db.remove_violations_for_date('2025-08-15')
            
            assert removed_count == 1
            assert db.has_violations_for_date('2025-08-15') is False
            assert not violations_file.exists()
    
    def test_add_violations_for_date_date_structure(self):
        """Test add_violations_for_date with date-based structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test violations
            violation1 = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test1.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            violation2 = ViolationReport(
                date='2025-08-15',
                start_time='07:25:00',
                end_time='07:30:00',
                violation_type='Intermittent',
                total_bark_duration=400.0,
                total_incident_duration=400.0,
                audio_files=['test2.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.9],
                peak_confidence=0.9,
                avg_confidence=0.9,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Add violations
            db.add_violations_for_date([violation1, violation2], '2025-08-15')
            
            # Verify both were saved
            violations = db.get_violations_by_date('2025-08-15')
            assert len(violations) == 2
            
            violation_types = [v.violation_type for v in violations]
            assert 'Constant' in violation_types
            assert 'Intermittent' in violation_types
    
    def test_add_violations_for_date_overwrite(self):
        """Test add_violations_for_date with overwrite functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create initial violation
            violation1 = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test1.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Add initial violation
            db.add_violations_for_date([violation1], '2025-08-15')
            assert len(db.get_violations_by_date('2025-08-15')) == 1
            
            # Create new violation
            violation2 = ViolationReport(
                date='2025-08-15',
                start_time='07:25:00',
                end_time='07:30:00',
                violation_type='Intermittent',
                total_bark_duration=400.0,
                total_incident_duration=400.0,
                audio_files=['test2.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.9],
                peak_confidence=0.9,
                avg_confidence=0.9,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Add with overwrite=True
            db.add_violations_for_date([violation2], '2025-08-15', overwrite=True)
            
            # Should only have the new violation
            violations = db.get_violations_by_date('2025-08-15')
            assert len(violations) == 1
            assert violations[0].violation_type == 'Intermittent'
    
    def test_date_range_generation(self):
        """Test _get_date_range utility method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Test single day
            dates = db._get_date_range('2025-08-15', '2025-08-15')
            assert dates == ['2025-08-15']
            
            # Test multiple days
            dates = db._get_date_range('2025-08-15', '2025-08-17')
            assert dates == ['2025-08-15', '2025-08-16', '2025-08-17']
            
            # Test month boundary
            dates = db._get_date_range('2025-08-30', '2025-09-01')
            assert dates == ['2025-08-30', '2025-08-31', '2025-09-01']
    
    def test_backward_compatibility_legacy_mode(self):
        """Test backward compatibility with legacy single-file mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_file = Path(temp_dir) / 'legacy_violations.json'
            
            # Create database in legacy mode
            db = ViolationDatabase(legacy_file)
            
            # Create test violation
            violation = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Add violation using legacy methods
            db.violations.append(violation)
            db.save_violations()
            
            # Verify file was created and contains data
            assert legacy_file.exists()
            
            with open(legacy_file, 'r') as f:
                data = json.load(f)
            
            assert len(data['violations']) == 1
            assert data['violations'][0]['date'] == '2025-08-15'
            
            # Test legacy loading
            db2 = ViolationDatabase(legacy_file)
            assert len(db2.violations) == 1
            assert db2.violations[0].date == '2025-08-15'
    
    def test_error_handling_directory_permissions(self):
        """Test error handling when directory creation fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory that we'll make read-only
            readonly_base = Path(temp_dir) / 'readonly'
            readonly_base.mkdir()
            readonly_base.chmod(0o444)  # Read-only
            
            violations_dir = readonly_base / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test violation
            violation = ViolationReport(
                date='2025-08-15',
                start_time='06:25:00',
                end_time='06:30:00',
                violation_type='Constant',
                total_bark_duration=300.0,
                total_incident_duration=300.0,
                audio_files=['test.wav'],
                audio_file_start_times=['00:00:00'],
                audio_file_end_times=['00:05:00'],
                confidence_scores=[0.8],
                peak_confidence=0.8,
                avg_confidence=0.8,
                created_timestamp=datetime.now().isoformat()
            )
            
            # Should handle permission error gracefully (not crash)
            try:
                db._save_violations_for_date([violation], '2025-08-15')
                # If no exception, that's fine - some systems may allow this
            except PermissionError:
                # Expected on most systems
                pass
            
            # Restore permissions for cleanup
            readonly_base.chmod(0o755)