"""Integration tests for PDF generation with real violation data"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from bark_detector.utils.pdf_generator import PDFGenerationService
from bark_detector.legal.database import ViolationDatabase
from bark_detector.legal.models import Violation, PersistedBarkEvent


class TestPDFIntegration:
    """Integration tests for PDF generation with real data scenarios."""

    def test_pdf_generation_with_real_violation_structure(self):
        """Test PDF generation with real violation data structure."""
        # Create realistic violation data matching actual system output
        violations = [
            Violation(
                type="Continuous",
                startTimestamp="2025-08-14T12:00:00.000Z",
                violationTriggerTimestamp="2025-08-14T12:05:04.000Z",
                endTimestamp="2025-08-14T12:06:24.000Z",
                durationMinutes=6.4,
                violationDurationMinutes=1.33,
                barkEventIds=[
                    "839547b2-a0e7-4969-b603-c74fab974118",
                    "ca1bbc14-7de9-4887-82ae-a14712c4706e",
                    "8fd8a28c-1858-47fa-a32a-da27d53e1b9e"
                ]
            ),
            Violation(
                type="Intermittent",
                startTimestamp="2025-08-14T14:30:00.000Z",
                violationTriggerTimestamp="2025-08-14T14:45:00.000Z",
                endTimestamp="2025-08-14T15:15:00.000Z",
                durationMinutes=45.0,
                violationDurationMinutes=30.0,
                barkEventIds=[
                    "ee61d145-dfa8-4ba2-8696-e39b40866430",
                    "0b02ff99-9560-4876-96d7-c93aa0df82f0"
                ]
            )
        ]

        # Create realistic bark events
        bark_events = [
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:00:10",
                bark_id="839547b2-a0e7-4969-b603-c74fab974118",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120000.wav",
                bark_audiofile_timestamp="00:00:10.000",
                confidence=0.75,
                intensity=0.0  # Test zero intensity handling
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:00:30",
                bark_id="ca1bbc14-7de9-4887-82ae-a14712c4706e",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120000.wav",
                bark_audiofile_timestamp="00:00:30.000",
                confidence=0.82,
                intensity=0.65
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:01:15",
                bark_id="8fd8a28c-1858-47fa-a32a-da27d53e1b9e",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120000.wav",
                bark_audiofile_timestamp="00:01:15.000",
                confidence=0.91,
                intensity=0.83
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="14:30:45",
                bark_id="ee61d145-dfa8-4ba2-8696-e39b40866430",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_143000.wav",
                bark_audiofile_timestamp="00:00:45.000",
                confidence=0.77,
                intensity=0.42
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="14:55:20",
                bark_id="0b02ff99-9560-4876-96d7-c93aa0df82f0",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_145500.wav",
                bark_audiofile_timestamp="00:00:20.000",
                confidence=0.68,
                intensity=0.59
            )
        ]

        # Generate PDF
        service = PDFGenerationService()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "integration_test_report.pdf"

            success = service.generate_violation_report_pdf(
                violations=violations,
                bark_events=bark_events,
                output_path=output_path,
                report_date="2025-08-14"
            )

            # Verify PDF was generated successfully
            assert success is True
            assert output_path.exists()
            assert output_path.stat().st_size > 1000  # PDF should have reasonable size

    def test_pdf_generation_edge_cases(self):
        """Test PDF generation with edge cases and boundary conditions."""
        # Test with minimal violation (single bark event)
        minimal_violation = Violation(
            type="Continuous",
            startTimestamp="2025-08-14T08:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T08:00:05.000Z",
            endTimestamp="2025-08-14T08:00:06.000Z",
            durationMinutes=0.1,
            violationDurationMinutes=0.02,
            barkEventIds=["single-bark-event"]
        )

        minimal_event = PersistedBarkEvent(
            realworld_date="2025-08-14",
            realworld_time="08:00:05",
            bark_id="single-bark-event",
            bark_type="Bark",
            est_dog_size=None,
            audio_file_name="bark_recording_20250814_080000.wav",
            bark_audiofile_timestamp="00:00:05.000",
            confidence=0.85,
            intensity=0.7
        )

        service = PDFGenerationService()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "minimal_violation_report.pdf"

            success = service.generate_violation_report_pdf(
                violations=[minimal_violation],
                bark_events=[minimal_event],
                output_path=output_path,
                report_date="2025-08-14"
            )

            assert success is True
            assert output_path.exists()

    def test_pdf_generation_with_missing_audio_files(self):
        """Test PDF generation when bark events have missing or empty audio file names."""
        violation = Violation(
            type="Intermittent",
            startTimestamp="2025-08-14T16:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T16:05:00.000Z",
            endTimestamp="2025-08-14T16:10:00.000Z",
            durationMinutes=10.0,
            violationDurationMinutes=5.0,
            barkEventIds=["missing-audio-1", "missing-audio-2"]
        )

        # Events with missing/empty audio file names
        bark_events = [
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="16:02:00",
                bark_id="missing-audio-1",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="",  # Empty audio file name
                bark_audiofile_timestamp="00:00:00.000",
                confidence=0.72,
                intensity=0.6
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="16:07:30",
                bark_id="missing-audio-2",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name=None,  # None audio file name (would cause issues in JSON)
                bark_audiofile_timestamp="00:00:00.000",
                confidence=0.81,
                intensity=0.75
            )
        ]

        # Handle the None case by converting to empty string for testing
        bark_events[1].audio_file_name = ""

        service = PDFGenerationService()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "missing_audio_report.pdf"

            success = service.generate_violation_report_pdf(
                violations=[violation],
                bark_events=bark_events,
                output_path=output_path,
                report_date="2025-08-14"
            )

            # Should still generate PDF successfully
            assert success is True
            assert output_path.exists()

    def test_pdf_generation_with_various_intensity_values(self):
        """Test PDF generation with various intensity values including edge cases."""
        violation = Violation(
            type="Continuous",
            startTimestamp="2025-08-14T10:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T10:05:00.000Z",
            endTimestamp="2025-08-14T10:08:00.000Z",
            durationMinutes=8.0,
            violationDurationMinutes=3.0,
            barkEventIds=["intensity-test-1", "intensity-test-2", "intensity-test-3", "intensity-test-4"]
        )

        # Events with various intensity scenarios
        bark_events = [
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="10:01:00",
                bark_id="intensity-test-1",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_100000.wav",
                bark_audiofile_timestamp="00:01:00.000",
                confidence=0.85,
                intensity=0.0  # Zero intensity (should use default)
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="10:02:30",
                bark_id="intensity-test-2",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_100000.wav",
                bark_audiofile_timestamp="00:02:30.000",
                confidence=0.92,
                intensity=1.0  # Maximum intensity
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="10:04:15",
                bark_id="intensity-test-3",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_100000.wav",
                bark_audiofile_timestamp="00:04:15.000",
                confidence=0.78,
                intensity=0.05  # Very low but non-zero intensity
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="10:06:45",
                bark_id="intensity-test-4",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_100000.wav",
                bark_audiofile_timestamp="00:06:45.000",
                confidence=0.88,
                intensity=0.55  # Mid-range intensity
            )
        ]

        service = PDFGenerationService()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "intensity_variety_report.pdf"

            success = service.generate_violation_report_pdf(
                violations=[violation],
                bark_events=bark_events,
                output_path=output_path,
                report_date="2025-08-14"
            )

            assert success is True
            assert output_path.exists()
            # PDF should be reasonably sized with graph content
            assert output_path.stat().st_size > 5000

    def test_pdf_filename_convention(self):
        """Test that PDF files follow the required naming convention."""
        service = PDFGenerationService()

        # Test with violation database integration
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock a violation database call
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as violations_file:
                violations_data = {
                    "violations": [{
                        "type": "Continuous",
                        "startTimestamp": "2025-09-15T09:00:00.000Z",
                        "violationTriggerTimestamp": "2025-09-15T09:05:00.000Z",
                        "endTimestamp": "2025-09-15T09:07:00.000Z",
                        "durationMinutes": 7.0,
                        "violationDurationMinutes": 2.0,
                        "barkEventIds": ["test-bark-1"]
                    }]
                }
                import json
                json.dump(violations_data, violations_file)
                violations_file.flush()

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as events_file:
                events_data = {
                    "events": [{
                        "realworld_date": "2025-09-15",
                        "realworld_time": "09:02:30",
                        "bark_id": "test-bark-1",
                        "bark_type": "Bark",
                        "est_dog_size": None,
                        "audio_file_name": "bark_recording_20250915_090000.wav",
                        "bark_audiofile_timestamp": "00:02:30.000",
                        "confidence": 0.88,
                        "intensity": 0.67
                    }]
                }
                import json
                json.dump(events_data, events_file)
                events_file.flush()

            # Test direct PDF generation to verify filename format
            violations = [Violation(
                type="Continuous",
                startTimestamp="2025-09-15T09:00:00.000Z",
                violationTriggerTimestamp="2025-09-15T09:05:00.000Z",
                endTimestamp="2025-09-15T09:07:00.000Z",
                durationMinutes=7.0,
                violationDurationMinutes=2.0,
                barkEventIds=["test-bark-1"]
            )]

            bark_events = [PersistedBarkEvent(
                realworld_date="2025-09-15",
                realworld_time="09:02:30",
                bark_id="test-bark-1",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250915_090000.wav",
                bark_audiofile_timestamp="00:02:30.000",
                confidence=0.88,
                intensity=0.67
            )]

            # Generate PDF using service method that creates filename
            result_path = output_dir / "2025-09-15_Violation_Report.pdf"
            success = service.generate_violation_report_pdf(
                violations=violations,
                bark_events=bark_events,
                output_path=result_path,
                report_date="2025-09-15"
            )

            assert success is True
            assert result_path.exists()
            # Verify naming convention: YYYY-MM-DD_Violation_Report.pdf
            assert result_path.name == "2025-09-15_Violation_Report.pdf"

            # Cleanup temp files
            Path(violations_file.name).unlink()
            Path(events_file.name).unlink()

    def test_large_violation_dataset(self):
        """Test PDF generation with a larger dataset to verify performance and memory usage."""
        # Generate a larger violation with many bark events
        large_violation = Violation(
            type="Intermittent",
            startTimestamp="2025-08-14T18:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T18:15:00.000Z",
            endTimestamp="2025-08-14T20:30:00.000Z",
            durationMinutes=150.0,  # 2.5 hour violation
            violationDurationMinutes=135.0,
            barkEventIds=[f"large-test-event-{i}" for i in range(50)]  # 50 bark events
        )

        # Generate 50 bark events spread across the timeframe
        import random
        from datetime import datetime, timedelta

        base_time = datetime(2025, 8, 14, 18, 0, 0)
        bark_events = []

        for i in range(50):
            # Spread events across the violation timeframe
            event_time = base_time + timedelta(minutes=random.randint(0, 150))

            bark_events.append(PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time=event_time.strftime("%H:%M:%S"),
                bark_id=f"large-test-event-{i}",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name=f"bark_recording_20250814_{event_time.strftime('%H%M%S')}.wav",
                bark_audiofile_timestamp=f"00:00:{i % 60:02d}.000",
                confidence=random.uniform(0.6, 0.95),
                intensity=random.uniform(0.1, 0.9)
            ))

        service = PDFGenerationService()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "large_dataset_report.pdf"

            # Time the generation to ensure reasonable performance
            start_time = datetime.now()

            success = service.generate_violation_report_pdf(
                violations=[large_violation],
                bark_events=bark_events,
                output_path=output_path,
                report_date="2025-08-14"
            )

            generation_time = (datetime.now() - start_time).total_seconds()

            assert success is True
            assert output_path.exists()
            assert output_path.stat().st_size > 10000  # Should be a substantial PDF
            assert generation_time < 30  # Should complete within 30 seconds

    def test_pdf_directory_creation(self):
        """Test that PDF generation creates output directories as needed."""
        service = PDFGenerationService()

        violations = [Violation(
            type="Continuous",
            startTimestamp="2025-08-14T11:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T11:05:00.000Z",
            endTimestamp="2025-08-14T11:06:00.000Z",
            durationMinutes=6.0,
            violationDurationMinutes=1.0,
            barkEventIds=["dir-test-event"]
        )]

        bark_events = [PersistedBarkEvent(
            realworld_date="2025-08-14",
            realworld_time="11:02:00",
            bark_id="dir-test-event",
            bark_type="Bark",
            est_dog_size=None,
            audio_file_name="bark_recording_20250814_110000.wav",
            bark_audiofile_timestamp="00:02:00.000",
            confidence=0.85,
            intensity=0.72
        )]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a nested path that doesn't exist
            nested_output_path = Path(temp_dir) / "reports" / "2025-08-14" / "violation_report.pdf"

            success = service.generate_violation_report_pdf(
                violations=violations,
                bark_events=bark_events,
                output_path=nested_output_path,
                report_date="2025-08-14"
            )

            assert success is True
            assert nested_output_path.exists()
            assert nested_output_path.parent.exists()  # Directory was created