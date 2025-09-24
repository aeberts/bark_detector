"""PDF Generation Service for Violation Reports

This module provides professional PDF generation for bark violation reports,
including summary pages, detailed violation pages, and bark intensity graphs.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from io import BytesIO

# ReportLab imports for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas

# Matplotlib for graph generation
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

# Import violation data models
from ..legal.models import Violation, PersistedBarkEvent
from ..legal.database import ViolationDatabase

logger = logging.getLogger(__name__)


@dataclass
class PDFConfig:
    """Configuration for PDF generation."""
    page_size: Tuple[float, float] = letter
    margin: float = 0.75 * inch
    title_font_size: int = 16
    header_font_size: int = 14
    body_font_size: int = 12
    table_font_size: int = 10
    graph_width: int = 8
    graph_height: int = 4
    default_intensity: float = 0.5


class PDFGenerationService:
    """Service for generating professional PDF violation reports."""

    def __init__(self, config: Optional[PDFConfig] = None):
        """Initialize PDF generation service.

        Args:
            config: PDF configuration settings
        """
        self.config = config or PDFConfig()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for consistent formatting."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=self.config.title_font_size,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=self.config.header_font_size,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.black
        ))

        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=self.config.body_font_size,
            spaceAfter=6,
            alignment=TA_LEFT
        ))

    def generate_violation_report_pdf(
        self,
        violations: List[Violation],
        bark_events: List[PersistedBarkEvent],
        output_path: Path,
        report_date: Optional[str] = None
    ) -> bool:
        """Generate a complete PDF violation report.

        Args:
            violations: List of violation objects to include in the report
            bark_events: List of bark events for intensity graphs
            output_path: Path where PDF should be saved
            report_date: Date for the report (YYYY-MM-DD format)

        Returns:
            True if PDF was generated successfully, False otherwise
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine report date
            if not report_date and violations:
                # Extract date from first violation timestamp
                first_violation_time = datetime.fromisoformat(violations[0].startTimestamp.replace('Z', '+00:00'))
                report_date = first_violation_time.strftime('%Y-%m-%d')
            elif not report_date:
                report_date = datetime.now().strftime('%Y-%m-%d')

            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.config.page_size,
                topMargin=self.config.margin,
                bottomMargin=self.config.margin,
                leftMargin=self.config.margin,
                rightMargin=self.config.margin
            )

            # Build PDF content
            story = []

            # Add summary page
            self._add_summary_page(story, violations, bark_events, report_date)

            # Add page break before detail pages
            if violations:
                story.append(PageBreak())

            # Add detail pages for each violation
            for i, violation in enumerate(violations):
                violation_events = self._get_violation_events(violation, bark_events)
                self._add_detail_page(story, violation, violation_events, i + 1, report_date)

                # Add page break between violations (except for the last one)
                if i < len(violations) - 1:
                    story.append(PageBreak())

            # Build the PDF
            doc.build(story)

            logger.info(f"Successfully generated PDF report: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return False

    def _add_summary_page(
        self,
        story: List,
        violations: List[Violation],
        bark_events: List[PersistedBarkEvent],
        report_date: str
    ):
        """Add summary page to PDF story.

        Args:
            story: PDF story elements list
            violations: List of violations
            bark_events: List of bark events
            report_date: Report date string
        """
        # Title
        story.append(Paragraph("Barking Violation Report Summary", self.styles['CustomTitle']))
        story.append(Paragraph(f"Date: {report_date}", self.styles['CustomBody']))
        story.append(Spacer(1, 20))

        # Summary section
        story.append(Paragraph("SUMMARY:", self.styles['CustomHeader']))

        # Count violations by type
        total_violations = len(violations)
        constant_violations = sum(1 for v in violations if v.type == "Continuous")
        intermittent_violations = sum(1 for v in violations if v.type == "Intermittent")

        summary_data = [
            ["Total Violations:", str(total_violations)],
            ["Constant Violations:", str(constant_violations)],
            ["Intermittent Violations:", str(intermittent_violations)]
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), self.config.body_font_size),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Individual violation summaries
        for i, violation in enumerate(violations):
            violation_events = self._get_violation_events(violation, bark_events)
            audio_files = self._get_audio_files_for_violation(violation_events)

            # Parse timestamps
            start_dt = datetime.fromisoformat(violation.startTimestamp.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(violation.endTimestamp.replace('Z', '+00:00'))

            # Format times
            start_time_str = start_dt.strftime("%I:%M:%S%p").lstrip('0').lower()
            end_time_str = end_dt.strftime("%I:%M:%S%p").lstrip('0').lower()

            # Format duration
            duration_minutes = int(violation.durationMinutes)
            duration_seconds = int((violation.durationMinutes - duration_minutes) * 60)
            duration_str = f"{duration_minutes} mins {duration_seconds} seconds"

            # Violation type display name
            violation_type = "Constant" if violation.type == "Continuous" else "Intermittent"

            # Violation header
            story.append(Paragraph(f"Violation {i + 1} ({violation_type}):", self.styles['CustomHeader']))

            # Violation details
            violation_data = [
                [f"Start time: {start_time_str}  End Time: {end_time_str}"],
                [f"Duration: {duration_str}"],
                [f"Total Barks: {len(violation.barkEventIds)}"]
            ]

            # Add audio files if present
            if audio_files:
                violation_data.append(["Supporting audio files:"])
                for audio_file in audio_files:
                    violation_data.append([f"- {audio_file}"])

            violation_table = Table(violation_data, colWidths=[6*inch])
            violation_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), self.config.body_font_size),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))

            story.append(violation_table)
            story.append(Spacer(1, 15))

        # Report generated timestamp
        generated_time = datetime.now().strftime('%Y-%m-%d at %H:%M:%S')
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Report Generated: {generated_time}", self.styles['CustomBody']))

    def _add_detail_page(
        self,
        story: List,
        violation: Violation,
        violation_events: List[PersistedBarkEvent],
        violation_number: int,
        report_date: str
    ):
        """Add violation detail page to PDF story.

        Args:
            story: PDF story elements list
            violation: Violation object
            violation_events: Bark events for this violation
            violation_number: Violation number for display
            report_date: Report date string
        """
        # Title
        story.append(Paragraph(f"Barking Detail Report for {report_date}, Violation {violation_number}", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))

        # Parse timestamps
        start_dt = datetime.fromisoformat(violation.startTimestamp.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(violation.endTimestamp.replace('Z', '+00:00'))

        # Format times and duration
        start_time_str = start_dt.strftime("%I:%M:%S").lstrip('0')
        end_time_str = end_dt.strftime("%I:%M:%S").lstrip('0')
        duration_minutes = int(violation.durationMinutes)
        duration_seconds = int((violation.durationMinutes - duration_minutes) * 60)
        duration_str = f"{duration_minutes} mins {duration_seconds} seconds"

        # Violation type display name
        violation_type = "Constant" if violation.type == "Continuous" else "Intermittent"

        # Basic violation info
        info_data = [
            ["Violation Type:", violation_type],
            ["Start time:", f"{start_time_str} End Time: {end_time_str}"],
            ["Duration:", duration_str],
            ["Total Barks:", str(len(violation.barkEventIds))]
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), self.config.body_font_size),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))

        story.append(info_table)
        story.append(Spacer(1, 20))

        # Generate and add bark intensity graph
        graph_image = self._generate_bark_intensity_graph(violation, violation_events)
        if graph_image:
            story.append(graph_image)
            story.append(Spacer(1, 20))

        # Supporting audio files
        audio_files = self._get_audio_files_for_violation(violation_events)
        if audio_files:
            story.append(Paragraph("Supporting Audio Files:", self.styles['CustomHeader']))

            for audio_file in audio_files:
                story.append(Paragraph(f"- {audio_file}", self.styles['CustomBody']))

    def _generate_bark_intensity_graph(
        self,
        violation: Violation,
        violation_events: List[PersistedBarkEvent]
    ) -> Optional[Image]:
        """Generate bark intensity graph for violation.

        Args:
            violation: Violation object
            violation_events: Bark events for this violation

        Returns:
            ReportLab Image object or None if generation fails
        """
        try:
            # Parse violation timestamps
            start_dt = datetime.fromisoformat(violation.startTimestamp.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(violation.endTimestamp.replace('Z', '+00:00'))

            # Prepare data for graphing
            event_times = []
            intensities = []

            for event in violation_events:
                # Parse event timestamp
                event_dt = datetime.fromisoformat(f"{event.realworld_date}T{event.realworld_time}.000Z")

                # Convert to seconds relative to violation start
                seconds_from_start = (event_dt - start_dt).total_seconds()
                event_times.append(seconds_from_start)

                # Use event intensity or default if missing/zero
                intensity = event.intensity if event.intensity > 0 else self.config.default_intensity
                intensities.append(intensity)

            # Create the plot
            fig, ax = plt.subplots(figsize=(self.config.graph_width, self.config.graph_height))

            # Plot bark events as scatter points
            if event_times and intensities:
                ax.scatter(event_times, intensities, alpha=0.7, s=50, color='red', label='Bark Events')

                # Add trend line if we have enough points
                if len(event_times) > 2:
                    import numpy as np
                    z = np.polyfit(event_times, intensities, 1)
                    p = np.poly1d(z)
                    ax.plot(event_times, p(event_times), "r--", alpha=0.5, linewidth=1)

            # Set axis properties
            violation_duration_seconds = (end_dt - start_dt).total_seconds()
            ax.set_xlim(0, violation_duration_seconds * 1.1)  # Extend slightly past end time
            ax.set_ylim(0, 1.0)

            # Format x-axis to show time
            ax.set_xlabel('Time (seconds from violation start)', fontsize=10)
            ax.set_ylabel('Bark Intensity Level', fontsize=10)
            ax.set_title(f'Bark Intensity Over Time\n(Violation Start: {start_dt.strftime("%H:%M:%S")})', fontsize=12)

            # Add grid for readability
            ax.grid(True, alpha=0.3)

            # Save plot to BytesIO buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)

            # Create ReportLab Image
            img = Image(buffer, width=6*inch, height=3*inch)
            return img

        except Exception as e:
            logger.error(f"Failed to generate bark intensity graph: {e}")
            return None

    def _get_violation_events(
        self,
        violation: Violation,
        all_events: List[PersistedBarkEvent]
    ) -> List[PersistedBarkEvent]:
        """Get bark events associated with a specific violation.

        Args:
            violation: Violation object
            all_events: All available bark events

        Returns:
            List of bark events for this violation
        """
        violation_event_ids = set(violation.barkEventIds)
        return [event for event in all_events if event.bark_id in violation_event_ids]

    def _get_audio_files_for_violation(
        self,
        violation_events: List[PersistedBarkEvent]
    ) -> List[str]:
        """Get unique audio files associated with violation events.

        Args:
            violation_events: Bark events for violation

        Returns:
            Sorted list of unique audio file names
        """
        audio_files = set()
        for event in violation_events:
            if event.audio_file_name:
                audio_files.add(event.audio_file_name)

        return sorted(list(audio_files))

    def generate_pdf_from_date(
        self,
        violation_date: str,
        output_dir: Path,
        violation_db: Optional[ViolationDatabase] = None
    ) -> Optional[Path]:
        """Generate PDF report for a specific date.

        Args:
            violation_date: Date in YYYY-MM-DD format
            output_dir: Directory to save PDF
            violation_db: ViolationDatabase instance (optional)

        Returns:
            Path to generated PDF file or None if failed
        """
        try:
            # Initialize violation database if not provided
            if violation_db is None:
                violation_db = ViolationDatabase()

            # Load violations and events for date
            violations = violation_db.load_violations_new(violation_date)
            bark_events = violation_db.load_events(violation_date)

            if not violations:
                logger.warning(f"No violations found for date {violation_date}")
                return None

            # Generate output path
            output_path = output_dir / f"{violation_date}_Violation_Report.pdf"

            # Generate PDF
            success = self.generate_violation_report_pdf(
                violations=violations,
                bark_events=bark_events,
                output_path=output_path,
                report_date=violation_date
            )

            return output_path if success else None

        except Exception as e:
            logger.error(f"Failed to generate PDF for date {violation_date}: {e}")
            return None