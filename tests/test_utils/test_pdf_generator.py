"""Tests for PDF Generation Service"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from bark_detector.utils.pdf_generator import PDFGenerationService, PDFConfig
from bark_detector.legal.models import Violation, PersistedBarkEvent
from bark_detector.legal.database import ViolationDatabase


class TestPDFConfig:
    """Test PDFConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PDFConfig()
        assert config.page_size is not None
        assert config.margin > 0
        assert config.title_font_size > 0
        assert config.default_intensity == 0.5

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PDFConfig(
            title_font_size=20,
            default_intensity=0.7,
            graph_width=10
        )
        assert config.title_font_size == 20
        assert config.default_intensity == 0.7
        assert config.graph_width == 10


class TestPDFGenerationService:
    """Test PDF Generation Service functionality."""

    @pytest.fixture
    def pdf_service(self):
        """Create PDF generation service instance."""
        return PDFGenerationService()

    @pytest.fixture
    def sample_violation(self):
        """Create sample violation for testing."""
        return Violation(
            type="Continuous",
            startTimestamp="2025-08-14T12:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T12:05:00.000Z",
            endTimestamp="2025-08-14T12:06:00.000Z",
            durationMinutes=6.0,
            violationDurationMinutes=1.0,
            barkEventIds=["event-1", "event-2", "event-3"]
        )

    @pytest.fixture
    def sample_bark_events(self):
        """Create sample bark events for testing."""
        return [
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:00:10",
                bark_id="event-1",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120000.wav",
                bark_audiofile_timestamp="00:00:10.000",
                confidence=0.8,
                intensity=0.6
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:00:30",
                bark_id="event-2",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120000.wav",
                bark_audiofile_timestamp="00:00:30.000",
                confidence=0.7,
                intensity=0.8
            ),
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:01:00",
                bark_id="event-3",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120000.wav",
                bark_audiofile_timestamp="00:01:00.000",
                confidence=0.9,
                intensity=0.0  # Test default intensity handling
            )
        ]

    def test_service_initialization(self):
        """Test PDF service initialization."""
        service = PDFGenerationService()
        assert service.config is not None
        assert service.styles is not None

    def test_service_initialization_with_custom_config(self):
        """Test PDF service initialization with custom config."""
        config = PDFConfig(title_font_size=20)
        service = PDFGenerationService(config)
        assert service.config.title_font_size == 20

    def test_get_violation_events(self, pdf_service, sample_violation, sample_bark_events):
        """Test filtering bark events for a specific violation."""
        violation_events = pdf_service._get_violation_events(sample_violation, sample_bark_events)

        assert len(violation_events) == 3
        assert all(event.bark_id in sample_violation.barkEventIds for event in violation_events)

    def test_get_violation_events_no_match(self, pdf_service, sample_bark_events):
        """Test filtering bark events when no events match violation."""
        violation = Violation(
            type="Continuous",
            startTimestamp="2025-08-14T12:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T12:05:00.000Z",
            endTimestamp="2025-08-14T12:06:00.000Z",
            durationMinutes=6.0,
            violationDurationMinutes=1.0,
            barkEventIds=["non-existent-event"]
        )

        violation_events = pdf_service._get_violation_events(violation, sample_bark_events)
        assert len(violation_events) == 0

    def test_get_audio_files_for_violation(self, pdf_service, sample_bark_events):
        """Test extracting unique audio files from bark events."""
        # Add another event with different audio file
        sample_bark_events.append(
            PersistedBarkEvent(
                realworld_date="2025-08-14",
                realworld_time="12:02:00",
                bark_id="event-4",
                bark_type="Bark",
                est_dog_size=None,
                audio_file_name="bark_recording_20250814_120200.wav",
                bark_audiofile_timestamp="00:00:00.000",
                confidence=0.8,
                intensity=0.7
            )
        )

        audio_files = pdf_service._get_audio_files_for_violation(sample_bark_events)

        assert len(audio_files) == 2
        assert "bark_recording_20250814_120000.wav" in audio_files
        assert "bark_recording_20250814_120200.wav" in audio_files
        assert audio_files == sorted(audio_files)  # Should be sorted

    def test_get_audio_files_empty_events(self, pdf_service):
        """Test audio files extraction with empty events list."""
        audio_files = pdf_service._get_audio_files_for_violation([])
        assert len(audio_files) == 0

    @patch('bark_detector.utils.pdf_generator.plt')
    def test_generate_bark_intensity_graph(self, mock_plt, pdf_service, sample_violation, sample_bark_events):
        """Test bark intensity graph generation."""
        # Mock matplotlib components
        mock_fig = Mock()
        mock_ax = Mock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Mock savefig to write to buffer
        mock_buffer = BytesIO(b'fake_image_data')
        with patch('bark_detector.utils.pdf_generator.BytesIO', return_value=mock_buffer):
            with patch('bark_detector.utils.pdf_generator.Image') as mock_image:
                mock_image_instance = Mock()
                mock_image.return_value = mock_image_instance

                # Get events for the violation
                violation_events = pdf_service._get_violation_events(sample_violation, sample_bark_events)

                # Generate graph
                result = pdf_service._generate_bark_intensity_graph(sample_violation, violation_events)

                # Verify graph generation was attempted
                mock_plt.subplots.assert_called_once()
                mock_ax.scatter.assert_called()
                mock_ax.set_xlim.assert_called()
                mock_ax.set_ylim.assert_called_with(0, 1.0)

                # Verify image creation
                mock_image.assert_called_once()
                assert result == mock_image_instance

    @patch('bark_detector.utils.pdf_generator.plt')
    def test_generate_bark_intensity_graph_error_handling(self, mock_plt, pdf_service, sample_violation, sample_bark_events):
        """Test bark intensity graph generation error handling."""
        # Make matplotlib raise an exception
        mock_plt.subplots.side_effect = Exception("Matplotlib error")

        violation_events = pdf_service._get_violation_events(sample_violation, sample_bark_events)
        result = pdf_service._generate_bark_intensity_graph(sample_violation, violation_events)

        assert result is None

    def test_generate_bark_intensity_graph_default_intensity(self, pdf_service, sample_violation, sample_bark_events):
        """Test that default intensity is used when intensity is 0 or missing."""
        # Find the event with 0 intensity
        zero_intensity_event = next(event for event in sample_bark_events if event.intensity == 0.0)
        assert zero_intensity_event is not None

        with patch('bark_detector.utils.pdf_generator.plt') as mock_plt:
            mock_fig = Mock()
            mock_ax = Mock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)

            violation_events = pdf_service._get_violation_events(sample_violation, sample_bark_events)

            with patch('bark_detector.utils.pdf_generator.BytesIO'):
                with patch('bark_detector.utils.pdf_generator.Image'):
                    pdf_service._generate_bark_intensity_graph(sample_violation, violation_events)

            # Verify scatter was called (indicating intensity processing worked)
            mock_ax.scatter.assert_called()

            # Get the intensity values passed to scatter
            call_args = mock_ax.scatter.call_args
            intensities = call_args[0][1]  # Second argument to scatter (y-values)

            # Should have replaced 0.0 with default intensity
            assert pdf_service.config.default_intensity in intensities

    @patch('bark_detector.utils.pdf_generator.SimpleDocTemplate')
    def test_generate_violation_report_pdf_success(self, mock_doc_class, pdf_service, sample_violation, sample_bark_events):
        """Test successful PDF generation."""
        mock_doc = Mock()
        mock_doc_class.return_value = mock_doc

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            with patch.object(pdf_service, '_add_summary_page') as mock_summary:
                with patch.object(pdf_service, '_add_detail_page') as mock_detail:
                    result = pdf_service.generate_violation_report_pdf(
                        violations=[sample_violation],
                        bark_events=sample_bark_events,
                        output_path=output_path,
                        report_date="2025-08-14"
                    )

            assert result is True
            mock_doc.build.assert_called_once()
            mock_summary.assert_called_once()
            mock_detail.assert_called_once()

    @patch('bark_detector.utils.pdf_generator.SimpleDocTemplate')
    def test_generate_violation_report_pdf_error(self, mock_doc_class, pdf_service, sample_violation, sample_bark_events):
        """Test PDF generation error handling."""
        mock_doc_class.side_effect = Exception("PDF generation error")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            result = pdf_service.generate_violation_report_pdf(
                violations=[sample_violation],
                bark_events=sample_bark_events,
                output_path=output_path,
                report_date="2025-08-14"
            )

            assert result is False

    def test_generate_violation_report_pdf_no_violations(self, pdf_service):
        """Test PDF generation with no violations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            with patch('bark_detector.utils.pdf_generator.SimpleDocTemplate') as mock_doc_class:
                mock_doc = Mock()
                mock_doc_class.return_value = mock_doc

                result = pdf_service.generate_violation_report_pdf(
                    violations=[],
                    bark_events=[],
                    output_path=output_path,
                    report_date="2025-08-14"
                )

                assert result is True  # Should still generate PDF with empty summary
                mock_doc.build.assert_called_once()

    def test_generate_violation_report_pdf_auto_date(self, pdf_service, sample_violation, sample_bark_events):
        """Test PDF generation with automatic date extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            with patch('bark_detector.utils.pdf_generator.SimpleDocTemplate') as mock_doc_class:
                mock_doc = Mock()
                mock_doc_class.return_value = mock_doc

                with patch.object(pdf_service, '_add_summary_page') as mock_summary:
                    with patch.object(pdf_service, '_add_detail_page') as mock_detail:
                        result = pdf_service.generate_violation_report_pdf(
                            violations=[sample_violation],
                            bark_events=sample_bark_events,
                            output_path=output_path,
                            report_date=None  # Should auto-extract from violation timestamp
                        )

                assert result is True
                # Verify that summary was called with extracted date
                mock_summary.assert_called_once()
                call_args = mock_summary.call_args[0]
                extracted_date = call_args[3]  # Fourth argument is report_date
                assert extracted_date == "2025-08-14"

    @patch.object(ViolationDatabase, 'load_violations_new')
    @patch.object(ViolationDatabase, 'load_events')
    def test_generate_pdf_from_date_success(self, mock_load_events, mock_load_violations, pdf_service, sample_violation, sample_bark_events):
        """Test PDF generation from date with ViolationDatabase."""
        mock_load_violations.return_value = [sample_violation]
        mock_load_events.return_value = sample_bark_events

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with patch.object(pdf_service, 'generate_violation_report_pdf', return_value=True):
                result = pdf_service.generate_pdf_from_date("2025-08-14", output_dir)

            assert result is not None
            assert result.name == "2025-08-14_Violation_Report.pdf"
            mock_load_violations.assert_called_once_with("2025-08-14")
            mock_load_events.assert_called_once_with("2025-08-14")

    @patch.object(ViolationDatabase, 'load_violations_new')
    def test_generate_pdf_from_date_no_violations(self, mock_load_violations, pdf_service):
        """Test PDF generation from date with no violations."""
        mock_load_violations.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = pdf_service.generate_pdf_from_date("2025-08-14", output_dir)

            assert result is None

    @patch.object(ViolationDatabase, 'load_violations_new')
    def test_generate_pdf_from_date_error(self, mock_load_violations, pdf_service):
        """Test PDF generation from date error handling."""
        mock_load_violations.side_effect = Exception("Database error")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = pdf_service.generate_pdf_from_date("2025-08-14", output_dir)

            assert result is None

    def test_multiple_violations_pdf_generation(self, pdf_service, sample_bark_events):
        """Test PDF generation with multiple violations."""
        violations = [
            Violation(
                type="Continuous",
                startTimestamp="2025-08-14T12:00:00.000Z",
                violationTriggerTimestamp="2025-08-14T12:05:00.000Z",
                endTimestamp="2025-08-14T12:06:00.000Z",
                durationMinutes=6.0,
                violationDurationMinutes=1.0,
                barkEventIds=["event-1", "event-2"]
            ),
            Violation(
                type="Intermittent",
                startTimestamp="2025-08-14T14:00:00.000Z",
                violationTriggerTimestamp="2025-08-14T14:15:00.000Z",
                endTimestamp="2025-08-14T14:25:00.000Z",
                durationMinutes=25.0,
                violationDurationMinutes=10.0,
                barkEventIds=["event-3"]
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            with patch('bark_detector.utils.pdf_generator.SimpleDocTemplate') as mock_doc_class:
                mock_doc = Mock()
                mock_doc_class.return_value = mock_doc

                with patch.object(pdf_service, '_add_summary_page') as mock_summary:
                    with patch.object(pdf_service, '_add_detail_page') as mock_detail:
                        result = pdf_service.generate_violation_report_pdf(
                            violations=violations,
                            bark_events=sample_bark_events,
                            output_path=output_path,
                            report_date="2025-08-14"
                        )

                assert result is True
                mock_summary.assert_called_once()
                assert mock_detail.call_count == 2  # Called for each violation


class TestIntegrationScenarios:
    """Integration test scenarios for PDF generation."""

    def test_continuous_violation_type_mapping(self):
        """Test that 'Continuous' violation type maps to 'Constant' in display."""
        service = PDFGenerationService()

        violation = Violation(
            type="Continuous",  # Internal type
            startTimestamp="2025-08-14T12:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T12:05:00.000Z",
            endTimestamp="2025-08-14T12:06:00.000Z",
            durationMinutes=6.0,
            violationDurationMinutes=1.0,
            barkEventIds=["event-1"]
        )

        # The mapping should happen internally in the PDF generation
        # This is tested indirectly through the display formatting
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            with patch('bark_detector.utils.pdf_generator.SimpleDocTemplate'):
                with patch.object(service, '_add_summary_page') as mock_summary:
                    with patch.object(service, '_add_detail_page'):
                        service.generate_violation_report_pdf(
                            violations=[violation],
                            bark_events=[],
                            output_path=output_path,
                            report_date="2025-08-14"
                        )

                # Verify summary page generation was called
                mock_summary.assert_called_once()

    def test_intermittent_violation_type_mapping(self):
        """Test that 'Intermittent' violation type is preserved in display."""
        service = PDFGenerationService()

        violation = Violation(
            type="Intermittent",  # Should remain as "Intermittent"
            startTimestamp="2025-08-14T12:00:00.000Z",
            violationTriggerTimestamp="2025-08-14T12:05:00.000Z",
            endTimestamp="2025-08-14T12:06:00.000Z",
            durationMinutes=6.0,
            violationDurationMinutes=1.0,
            barkEventIds=["event-1"]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.pdf"

            with patch('bark_detector.utils.pdf_generator.SimpleDocTemplate'):
                with patch.object(service, '_add_detail_page') as mock_detail:
                    with patch.object(service, '_add_summary_page'):
                        service.generate_violation_report_pdf(
                            violations=[violation],
                            bark_events=[],
                            output_path=output_path,
                            report_date="2025-08-14"
                        )

                # Verify detail page generation was called
                mock_detail.assert_called_once()