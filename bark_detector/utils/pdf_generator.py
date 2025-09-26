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
            fontSize=24,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1F2937'),
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6B7280'),
            fontName='Helvetica',
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        self.styles.add(ParagraphStyle(
            name='MetricStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.white
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
        # Header Section
        story.append(Paragraph(f"Barking Violation Summary - {report_date}", self.styles['CustomTitle']))

        # Determine bark level
        total_violations = len(violations)
        bark_level = "HIGH" if total_violations >= 5 else "MEDIUM" if total_violations >= 2 else "LOW"
        bark_level_color = '#DC2626' if bark_level == 'HIGH' else '#F59E0B' if bark_level == 'MEDIUM' else '#10B981'

        header_info = f'Bark Level: <font color="{bark_level_color}"><b>{bark_level}</b></font>'
        story.append(Paragraph(header_info, self.styles['HeaderStyle']))
        story.append(Spacer(1, 15))

        # Metrics Dashboard
        constant_violations = sum(1 for v in violations if v.type == "Continuous")
        intermittent_violations = sum(1 for v in violations if v.type == "Intermittent")

        # Calculate total duration
        total_minutes = sum(violation.durationMinutes for violation in violations)
        total_hours = int(total_minutes // 60)
        remaining_minutes = int(total_minutes % 60)

        metrics_data = [
            [
                Paragraph(f"<font size='24'><b>{total_violations}</b></font><br/>Total Violations", self.styles['MetricStyle']),
                Paragraph(f"<font size='24'><b>{constant_violations}</b></font><br/>Constant", self.styles['MetricStyle']),
                Paragraph(f"<font size='24'><b>{intermittent_violations}</b></font><br/>Intermittent", self.styles['MetricStyle']),
                Paragraph(f"<font size='24'><b>{total_hours}h {remaining_minutes}m</b></font><br/>Duration", self.styles['MetricStyle'])
            ]
        ]

        metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#DC2626')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#F59E0B')),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#10B981')),
            ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#6366F1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white]),
            ('GRID', (0, 0), (-1, -1), 2, colors.white),
        ]))

        story.append(metrics_table)
        story.append(Spacer(1, 15))

        # Violations Table (moved under subtitle as requested)
        story.append(Paragraph("<b>Violation Details</b>", self.styles['Heading2']))
        story.append(Spacer(1, 8))

        table_data = [['#', 'Type', 'Start Time', 'End Time', 'Duration', 'Total Barks', 'Audio Files']]

        for i, violation in enumerate(violations):
            violation_events = self._get_violation_events(violation, bark_events)
            audio_files = self._get_audio_files_for_violation(violation_events)

            # Parse timestamps
            start_dt = datetime.fromisoformat(violation.startTimestamp.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(violation.endTimestamp.replace('Z', '+00:00'))

            # Format times
            start_time_str = start_dt.strftime("%H:%M:%S")
            end_time_str = end_dt.strftime("%H:%M:%S")

            # Format duration as hours, minutes, seconds
            total_duration_minutes = violation.durationMinutes
            duration_hours = int(total_duration_minutes // 60)
            duration_minutes = int(total_duration_minutes % 60)
            duration_seconds = int((total_duration_minutes - int(total_duration_minutes)) * 60)

            if duration_hours > 0:
                duration_str = f"{duration_hours}h {duration_minutes}m {duration_seconds}s"
            else:
                duration_str = f"{duration_minutes}m {duration_seconds}s"

            # Violation type display name and color
            violation_type = "Constant" if violation.type == "Continuous" else "Intermittent"
            type_color = '#DC2626' if violation.type == "Continuous" else '#F59E0B'

            table_data.append([
                str(i + 1),
                Paragraph(f'<font color="{type_color}"><b>{violation_type}</b></font>', self.styles['Normal']),
                start_time_str,
                end_time_str,
                duration_str,
                str(len(violation.barkEventIds)),
                f'{len(audio_files)} files'
            ])

        violations_table = Table(table_data, colWidths=[0.5*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        violations_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))

        story.append(violations_table)
        story.append(Spacer(1, 15))

        # Activity Timeline (moved to fit on same page)
        story.append(Paragraph("<b>Activity Timeline</b>", self.styles['Heading2']))
        story.append(Spacer(1, 8))

        # Create and add timeline chart with reduced size for single-page fit
        timeline_image = self._generate_activity_timeline(violations, bark_events, report_date)
        if timeline_image:
            story.append(timeline_image)

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

    def _generate_activity_timeline(
        self,
        violations: List[Violation],
        bark_events: List[PersistedBarkEvent],
        report_date: str
    ) -> Optional[Image]:
        """Generate 24-hour activity timeline chart.

        Args:
            violations: List of violations
            bark_events: List of bark events
            report_date: Report date string

        Returns:
            ReportLab Image object or None if generation fails
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.patch.set_facecolor('white')

            # Create time data points for each violation
            times = []
            intensities = []
            colors_list = []

            for violation in violations:
                # Parse start and end times
                start_dt = datetime.fromisoformat(violation.startTimestamp.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(violation.endTimestamp.replace('Z', '+00:00'))

                start_decimal = start_dt.hour + start_dt.minute/60
                end_decimal = end_dt.hour + end_dt.minute/60

                # Create multiple points across the violation duration
                duration_hours = end_decimal - start_decimal
                if duration_hours < 0:  # Handle day boundary crossing
                    duration_hours += 24

                num_points = max(3, int(duration_hours * 4))  # More points for longer violations

                for i in range(num_points):
                    time_point = start_decimal + (duration_hours * i / (num_points - 1))
                    if time_point >= 24:
                        time_point -= 24
                    times.append(time_point)

                    # Intensity based on barks per minute
                    duration_minutes = violation.durationMinutes
                    barks_per_minute = len(violation.barkEventIds) / duration_minutes if duration_minutes > 0 else 0
                    intensity = min(1.0, barks_per_minute / 10)  # Normalize to 0-1 scale
                    intensities.append(intensity)

                    # Color coding
                    if violation.type == "Continuous":
                        colors_list.append('#DC2626')  # Red
                    else:
                        colors_list.append('#F59E0B')  # Orange

            # Create bar chart instead of scatter for better visibility
            if times and intensities:
                # Create hourly bins
                hours = list(range(24))
                hourly_intensities = [0] * 24
                hourly_colors = ['#F59E0B'] * 24  # Default to orange

                # Aggregate intensities by hour
                for time_val, intensity, color in zip(times, intensities, colors_list):
                    hour = int(time_val) % 24
                    if intensity > hourly_intensities[hour]:
                        hourly_intensities[hour] = intensity
                        hourly_colors[hour] = color

                # Create bar chart
                bars = ax.bar(hours, hourly_intensities, color=hourly_colors, alpha=0.7, width=0.8)

            # Formatting
            ax.set_xlim(-0.5, 23.5)
            ax.set_ylim(0, 1.1)
            ax.set_xlabel('Time of Day (Hours)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Bark Intensity Level', fontsize=12, fontweight='bold')
            ax.set_title(f'Barking Violations for {report_date}', fontsize=14, fontweight='bold', pad=20)

            # Set time ticks
            ax.set_xticks(range(0, 24, 2))
            ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], rotation=45)

            # Grid
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_facecolor('#FAFAFA')

            # Legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#DC2626', label='Constant Violations'),
                Patch(facecolor='#F59E0B', label='Intermittent Violations')
            ]
            ax.legend(handles=legend_elements, loc='upper right', frameon=True, fancybox=True, shadow=True)

            # Tight layout
            plt.tight_layout()

            # Save to bytes buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            plt.close()

            # Create ReportLab Image with reduced size to fit single page
            img = Image(buffer, width=6.5*inch, height=2.8*inch)
            return img

        except Exception as e:
            logger.error(f"Failed to generate activity timeline: {e}")
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