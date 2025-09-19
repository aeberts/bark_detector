"""Tests for date-based violation database structure (I17 improvement)"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from bark_detector.legal.database import ViolationDatabase
from bark_detector.legal.models import ViolationReport, PersistedBarkEvent, Violation


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
            expected_path = violations_dir / '2025-08-15' / '2025-08-15_violations.json'
            
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
            expected_file = expected_dir / '2025-08-15_violations.json'
            
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
            
            violations_file = date_dir / f'{test_date}_violations.json'
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
            
            violations_file = date_dir / f'{test_date}_violations.json'
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
            violations_file = violations_dir / '2025-08-15' / '2025-08-15_violations.json'
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


class TestPersistedBarkEvent:
    """Test suite for PersistedBarkEvent model serialization/deserialization."""
    
    def test_bark_event_creation(self):
        """Test basic PersistedBarkEvent creation."""
        event = PersistedBarkEvent(
            realworld_date="2025-08-15",
            realworld_time="06:25:30",
            bark_id="bark_20250815_062530_001",
            bark_type="Bark",
            est_dog_size=None,
            audio_file_name="bark_recording_20250815_062530.wav",
            bark_audiofile_timestamp="00:00:15.267",
            confidence=0.824,
            intensity=0.375
        )
        
        assert event.realworld_date == "2025-08-15"
        assert event.bark_id == "bark_20250815_062530_001"
        assert event.confidence == 0.824
        assert event.est_dog_size is None
    
    def test_bark_event_to_dict(self):
        """Test PersistedBarkEvent to_dict serialization."""
        event = PersistedBarkEvent(
            realworld_date="2025-08-15",
            realworld_time="06:25:30",
            bark_id="bark_20250815_062530_001",
            bark_type="Bark",
            est_dog_size="Medium",
            audio_file_name="bark_recording_20250815_062530.wav",
            bark_audiofile_timestamp="00:00:15.267",
            confidence=0.824,
            intensity=0.375
        )
        
        data = event.to_dict()
        
        assert isinstance(data, dict)
        assert data['realworld_date'] == "2025-08-15"
        assert data['bark_id'] == "bark_20250815_062530_001"
        assert data['est_dog_size'] == "Medium"
        assert data['confidence'] == 0.824
    
    def test_bark_event_from_dict(self):
        """Test PersistedBarkEvent from_dict deserialization."""
        data = {
            'realworld_date': "2025-08-15",
            'realworld_time': "06:25:30",
            'bark_id': "bark_20250815_062530_001",
            'bark_type': "Bark",
            'est_dog_size': None,
            'audio_file_name': "bark_recording_20250815_062530.wav",
            'bark_audiofile_timestamp': "00:00:15.267",
            'confidence': 0.824,
            'intensity': 0.375
        }
        
        event = PersistedBarkEvent.from_dict(data)
        
        assert event.realworld_date == "2025-08-15"
        assert event.bark_id == "bark_20250815_062530_001"
        assert event.confidence == 0.824
        assert event.est_dog_size is None
    
    def test_bark_event_json_serialization(self):
        """Test PersistedBarkEvent JSON serialization and deserialization."""
        original_event = PersistedBarkEvent(
            realworld_date="2025-08-15",
            realworld_time="06:25:30",
            bark_id="bark_20250815_062530_001",
            bark_type="Howl",
            est_dog_size="Large",
            audio_file_name="bark_recording_20250815_062530.wav",
            bark_audiofile_timestamp="00:00:15.267",
            confidence=0.924,
            intensity=0.675
        )
        
        # Convert to JSON and back
        json_str = original_event.to_json()
        restored_event = PersistedBarkEvent.from_json(json_str)
        
        assert restored_event.realworld_date == original_event.realworld_date
        assert restored_event.bark_id == original_event.bark_id
        assert restored_event.bark_type == original_event.bark_type
        assert restored_event.est_dog_size == original_event.est_dog_size
        assert restored_event.confidence == original_event.confidence


class TestViolation:
    """Test suite for Violation model serialization/deserialization."""
    
    def test_violation_creation(self):
        """Test basic Violation creation."""
        violation = Violation(
            violation_id="violation_20250815_001",
            violation_type="Constant",
            violation_date="2025-08-15",
            violation_start_time="06:25:00",
            violation_end_time="06:30:00",
            bark_event_ids=["bark_20250815_062530_001", "bark_20250815_062535_002"]
        )
        
        assert violation.violation_id == "violation_20250815_001"
        assert violation.violation_type == "Constant"
        assert len(violation.bark_event_ids) == 2
    
    def test_violation_to_dict(self):
        """Test Violation to_dict serialization."""
        violation = Violation(
            violation_id="violation_20250815_001",
            violation_type="Intermittent",
            violation_date="2025-08-15",
            violation_start_time="06:25:00",
            violation_end_time="06:45:00",
            bark_event_ids=["bark_001", "bark_002", "bark_003"]
        )
        
        data = violation.to_dict()
        
        assert isinstance(data, dict)
        assert data['violation_id'] == "violation_20250815_001"
        assert data['violation_type'] == "Intermittent"
        assert len(data['bark_event_ids']) == 3
    
    def test_violation_from_dict(self):
        """Test Violation from_dict deserialization."""
        data = {
            'violation_id': "violation_20250815_001",
            'violation_type': "Constant",
            'violation_date': "2025-08-15",
            'violation_start_time': "06:25:00",
            'violation_end_time': "06:30:00",
            'bark_event_ids': ["bark_001", "bark_002"]
        }
        
        violation = Violation.from_dict(data)
        
        assert violation.violation_id == "violation_20250815_001"
        assert violation.violation_type == "Constant"
        assert len(violation.bark_event_ids) == 2
    
    def test_violation_json_serialization(self):
        """Test Violation JSON serialization and deserialization."""
        original_violation = Violation(
            violation_id="violation_20250815_002",
            violation_type="Intermittent",
            violation_date="2025-08-15",
            violation_start_time="07:15:00",
            violation_end_time="07:35:00",
            bark_event_ids=["bark_001", "bark_002", "bark_003", "bark_004"]
        )
        
        # Convert to JSON and back
        json_str = original_violation.to_json()
        restored_violation = Violation.from_json(json_str)
        
        assert restored_violation.violation_id == original_violation.violation_id
        assert restored_violation.violation_type == original_violation.violation_type
        assert restored_violation.bark_event_ids == original_violation.bark_event_ids


class TestNewDatabaseMethods:
    """Test suite for new ViolationDatabase methods (save_events, load_events, etc.)."""
    
    def test_events_file_path_generation(self):
        """Test _get_events_file_path generates correct date-based paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Test path generation
            test_date = '2025-08-15'
            expected_path = violations_dir / '2025-08-15' / '2025-08-15_events.json'
            
            result_path = db._get_events_file_path(test_date)
            assert result_path == expected_path
    
    def test_events_file_path_legacy_mode_error(self):
        """Test _get_events_file_path raises error in legacy mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_file = Path(temp_dir) / 'legacy.json'
            db = ViolationDatabase(legacy_file)
            
            with pytest.raises(ValueError, match="Events files are only supported in date-based structure mode"):
                db._get_events_file_path('2025-08-15')
    
    def test_save_events_creates_directory_and_file(self):
        """Test save_events creates directory structure and saves events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test events
            events = [
                PersistedBarkEvent(
                    realworld_date="2025-08-15",
                    realworld_time="06:25:30",
                    bark_id="bark_001",
                    bark_type="Bark",
                    est_dog_size=None,
                    audio_file_name="test.wav",
                    bark_audiofile_timestamp="00:00:15.267",
                    confidence=0.824,
                    intensity=0.375
                ),
                PersistedBarkEvent(
                    realworld_date="2025-08-15",
                    realworld_time="06:25:35",
                    bark_id="bark_002",
                    bark_type="Howl",
                    est_dog_size="Large",
                    audio_file_name="test.wav",
                    bark_audiofile_timestamp="00:00:20.500",
                    confidence=0.912,
                    intensity=0.680
                )
            ]
            
            # Save events
            db.save_events(events, '2025-08-15')
            
            # Verify directory and file were created
            expected_dir = violations_dir / '2025-08-15'
            expected_file = expected_dir / '2025-08-15_events.json'
            
            assert expected_dir.exists()
            assert expected_file.exists()
            
            # Verify content
            with open(expected_file, 'r') as f:
                data = json.load(f)
            
            assert len(data['events']) == 2
            assert data['metadata']['date'] == '2025-08-15'
            assert data['metadata']['total_events'] == 2
            assert data['events'][0]['bark_id'] == 'bark_001'
            assert data['events'][1]['bark_id'] == 'bark_002'
    
    def test_load_events_reads_from_file(self):
        """Test load_events correctly reads events from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test data manually
            test_date = '2025-08-15'
            date_dir = violations_dir / test_date
            date_dir.mkdir(parents=True)
            
            test_data = {
                'events': [
                    {
                        'realworld_date': "2025-08-15",
                        'realworld_time': "06:25:30",
                        'bark_id': "bark_001",
                        'bark_type': "Bark",
                        'est_dog_size': None,
                        'audio_file_name': "test.wav",
                        'bark_audiofile_timestamp': "00:00:15.267",
                        'confidence': 0.824,
                        'intensity': 0.375
                    }
                ],
                'metadata': {
                    'date': test_date,
                    'total_events': 1
                }
            }
            
            events_file = date_dir / f'{test_date}_events.json'
            with open(events_file, 'w') as f:
                json.dump(test_data, f)
            
            # Load and verify
            events = db.load_events(test_date)
            
            assert len(events) == 1
            assert events[0].bark_id == "bark_001"
            assert events[0].bark_type == "Bark"
            assert events[0].confidence == 0.824
    
    def test_save_violations_new_creates_directory_and_file(self):
        """Test save_violations_new creates directory structure and saves violations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test violations
            violations = [
                Violation(
                    violation_id="violation_001",
                    violation_type="Constant",
                    violation_date="2025-08-15",
                    violation_start_time="06:25:00",
                    violation_end_time="06:30:00",
                    bark_event_ids=["bark_001", "bark_002"]
                )
            ]
            
            # Save violations
            db.save_violations_new(violations, '2025-08-15')
            
            # Verify directory and file were created
            expected_dir = violations_dir / '2025-08-15'
            expected_file = expected_dir / '2025-08-15_violations.json'
            
            assert expected_dir.exists()
            assert expected_file.exists()
            
            # Verify content
            with open(expected_file, 'r') as f:
                data = json.load(f)
            
            assert len(data['violations']) == 1
            assert data['metadata']['date'] == '2025-08-15'
            assert data['violations'][0]['violation_id'] == 'violation_001'
    
    def test_load_violations_new_reads_from_file(self):
        """Test load_violations_new correctly reads violations from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create test data manually
            test_date = '2025-08-15'
            date_dir = violations_dir / test_date
            date_dir.mkdir(parents=True)
            
            test_data = {
                'violations': [
                    {
                        'violation_id': "violation_001",
                        'violation_type': "Intermittent",
                        'violation_date': "2025-08-15",
                        'violation_start_time': "06:25:00",
                        'violation_end_time': "06:45:00",
                        'bark_event_ids': ["bark_001", "bark_002", "bark_003"]
                    }
                ],
                'metadata': {
                    'date': test_date,
                    'total_violations': 1
                }
            }
            
            violations_file = date_dir / f'{test_date}_violations.json'
            with open(violations_file, 'w') as f:
                json.dump(test_data, f)
            
            # Load and verify
            violations = db.load_violations_new(test_date)
            
            assert len(violations) == 1
            assert violations[0].violation_id == "violation_001"
            assert violations[0].violation_type == "Intermittent"
            assert len(violations[0].bark_event_ids) == 3
    
    def test_save_events_empty_list(self):
        """Test save_events handles empty list gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Save empty list - should not create files
            db.save_events([], '2025-08-15')
            
            events_file = violations_dir / '2025-08-15' / '2025-08-15_events.json'
            assert not events_file.exists()
    
    def test_save_violations_new_empty_list(self):
        """Test save_violations_new handles empty list gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Save empty list - should not create files
            db.save_violations_new([], '2025-08-15')
            
            violations_file = violations_dir / '2025-08-15' / '2025-08-15_violations.json'
            assert not violations_file.exists()
    
    def test_load_events_nonexistent_file(self):
        """Test load_events returns empty list for nonexistent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Load from nonexistent file
            events = db.load_events('2025-08-15')
            
            assert events == []
    
    def test_load_violations_new_nonexistent_file(self):
        """Test load_violations_new returns empty list for nonexistent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Load from nonexistent file
            violations = db.load_violations_new('2025-08-15')
            
            assert violations == []
    
    def test_methods_raise_error_in_legacy_mode(self):
        """Test new methods raise appropriate errors in legacy mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_file = Path(temp_dir) / 'legacy.json'
            db = ViolationDatabase(legacy_file)
            
            # All new methods should raise ValueError in legacy mode
            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.save_events([], '2025-08-15')
            
            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.load_events('2025-08-15')
            
            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.save_violations_new([], '2025-08-15')
            
            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.load_violations_new('2025-08-15')


class TestBackwardCompatibility:
    """Test suite to ensure existing ViolationDatabase API contracts remain functional."""
    
    def test_existing_violation_report_workflow_still_works(self):
        """Test that existing ViolationReport-based workflows continue to function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create ViolationReport using existing pattern
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
            
            # Existing API should still work
            db.add_violation(violation)
            retrieved = db.get_violations_by_date('2025-08-15')
            
            assert len(retrieved) == 1
            assert retrieved[0].date == '2025-08-15'
    
    def test_legacy_save_violations_method_still_works(self):
        """Test that the existing save_violations() method still functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)
            
            # Create violation and add to database
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
            
            db.violations.append(violation)
            
            # Legacy save_violations() should work
            db.save_violations()
            
            # Should be saved to date-based structure
            violations_file = violations_dir / '2025-08-15' / '2025-08-15_violations.json'
            assert violations_file.exists()
    
    def test_dual_mode_support_maintained(self):
        """Test that dual-mode support (legacy vs date-based) is maintained."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test legacy mode
            legacy_file = Path(temp_dir) / 'legacy.json'
            legacy_db = ViolationDatabase(legacy_file)
            assert legacy_db.use_date_structure is False
            
            # Test date-based mode
            violations_dir = Path(temp_dir) / 'violations'
            date_db = ViolationDatabase(violations_dir=violations_dir)
            assert date_db.use_date_structure is True