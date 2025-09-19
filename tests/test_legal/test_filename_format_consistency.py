"""
Regression tests for filename format consistency bug fix.

This test ensures that both events and violations files use the
consistent underscore naming convention throughout the system.
"""

import pytest
import tempfile
from pathlib import Path
from bark_detector.legal.database import ViolationDatabase, PersistedBarkEvent, Violation


class TestFilenameFormatConsistency:
    """Regression tests for filename format consistency."""

    def test_violations_file_uses_underscore_format(self):
        """Test that violations file path uses underscore format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)

            # Test path generation
            test_date = '2025-09-19'
            violations_path = db._get_violations_file_path(test_date)

            # Verify underscore format
            expected_filename = f'{test_date}_violations.json'
            assert violations_path.name == expected_filename
            assert '_violations.json' in violations_path.name
            assert '-violations.json' not in violations_path.name

    def test_events_file_uses_underscore_format(self):
        """Test that events file path uses underscore format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)

            # Test path generation
            test_date = '2025-09-19'
            events_path = db._get_events_file_path(test_date)

            # Verify underscore format
            expected_filename = f'{test_date}_events.json'
            assert events_path.name == expected_filename
            assert '_events.json' in events_path.name
            assert '-events.json' not in events_path.name

    def test_both_files_use_consistent_format(self):
        """Test that both events and violations files use consistent naming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)

            test_date = '2025-09-19'
            events_path = db._get_events_file_path(test_date)
            violations_path = db._get_violations_file_path(test_date)

            # Both should use underscore format
            assert '_' in events_path.name
            assert '_' in violations_path.name

            # Neither should use dash format
            assert '-events.json' not in events_path.name
            assert '-violations.json' not in violations_path.name

            # Both should be in same directory
            assert events_path.parent == violations_path.parent

    def test_file_creation_with_correct_naming(self):
        """Test that actual file creation uses correct naming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            violations_dir = Path(temp_dir) / 'violations'
            db = ViolationDatabase(violations_dir=violations_dir)

            # Create test data
            test_date = '2025-09-19'
            test_events = [
                PersistedBarkEvent(
                    bark_id='test_001',
                    realworld_date=test_date,
                    realworld_time='14:30:15',
                    bark_type='Bark',
                    audio_file_name='test.wav',
                    bark_audiofile_timestamp='00:05:15',
                    confidence=0.85,
                    intensity=0.65,
                    est_dog_size='Medium'
                )
            ]

            test_violations = [
                Violation(
                    violation_id='violation_001',
                    violation_type='Intermittent',
                    violation_date=test_date,
                    violation_start_time='14:30:00',
                    violation_end_time='14:35:00',
                    bark_event_ids=['test_001']
                )
            ]

            # Save files
            db.save_events(test_events, test_date)
            db.save_violations_new(test_violations, test_date)

            # Verify created files use correct naming
            date_dir = violations_dir / test_date
            assert date_dir.exists()

            events_file = date_dir / f'{test_date}_events.json'
            violations_file = date_dir / f'{test_date}_violations.json'

            assert events_file.exists()
            assert violations_file.exists()

            # Verify no dash format files exist
            dash_events_file = date_dir / f'{test_date}-events.json'
            dash_violations_file = date_dir / f'{test_date}-violations.json'

            assert not dash_events_file.exists()
            assert not dash_violations_file.exists()

    def test_legacy_mode_compatibility_maintained(self):
        """Test that legacy mode still works after filename fix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_file = Path(temp_dir) / 'violations.json'

            # Create database in legacy mode
            db = ViolationDatabase(str(legacy_file))

            # Should be in legacy mode
            assert not db.use_date_structure

            # Events and violations methods should raise errors in legacy mode
            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db._get_events_file_path('2025-09-19')

            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.save_events([], '2025-09-19')

            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.load_events('2025-09-19')

            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.save_violations_new([], '2025-09-19')

            with pytest.raises(ValueError, match="only supported in date-based structure mode"):
                db.load_violations_new('2025-09-19')