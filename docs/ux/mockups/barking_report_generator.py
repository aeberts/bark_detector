import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
import io
import numpy as np

# Sample data extracted from the original report
violations_data = [
    {"id": 1, "type": "Constant", "start": "10:40:53", "end": "10:46:42", "duration": "5m 48s", "barks": 77, "files": 1},
    {"id": 2, "type": "Intermittent", "start": "07:45:06", "end": "09:48:57", "duration": "123m 50s", "barks": 579, "files": 38},
    {"id": 3, "type": "Intermittent", "start": "09:55:39", "end": "11:15:23", "duration": "79m 44s", "barks": 461, "files": 33},
    {"id": 4, "type": "Intermittent", "start": "13:05:08", "end": "13:28:27", "duration": "23m 18s", "barks": 74, "files": 12},
    {"id": 5, "type": "Intermittent", "start": "13:34:07", "end": "16:34:29", "duration": "180m 22s", "barks": 1099, "files": 68},
    {"id": 6, "type": "Intermittent", "start": "16:39:56", "end": "16:59:53", "duration": "19m 56s", "barks": 127, "files": 7},
    {"id": 7, "type": "Intermittent", "start": "17:05:04", "end": "17:41:27", "duration": "36m 22s", "barks": 97, "files": 14}
]

def create_timeline_chart():
    """Create a professional timeline chart showing bark activity over 24 hours"""
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('white')
    
    # Create time data points for each violation
    times = []
    intensities = []
    colors_list = []
    
    for violation in violations_data:
        # Parse start and end times
        start_hour = int(violation["start"].split(":")[0])
        start_min = int(violation["start"].split(":")[1])
        end_hour = int(violation["end"].split(":")[0])
        end_min = int(violation["end"].split(":")[1])
        
        start_decimal = start_hour + start_min/60
        end_decimal = end_hour + end_min/60
        
        # Create multiple points across the violation duration
        duration_hours = end_decimal - start_decimal
        num_points = max(3, int(duration_hours * 4))  # More points for longer violations
        
        for i in range(num_points):
            time_point = start_decimal + (duration_hours * i / (num_points - 1))
            times.append(time_point)
            
            # Intensity based on barks per minute
            duration_minutes = duration_hours * 60
            barks_per_minute = violation["barks"] / duration_minutes if duration_minutes > 0 else 0
            intensity = min(1.0, barks_per_minute / 10)  # Normalize to 0-1 scale
            intensities.append(intensity)
            
            # Color coding
            if violation["type"] == "Constant":
                colors_list.append('#DC2626')  # Red
            else:
                colors_list.append('#F59E0B')  # Orange
    
    # Create scatter plot
    scatter = ax.scatter(times, intensities, c=colors_list, s=60, alpha=0.7, edgecolors='white', linewidth=0.5)
    
    # Formatting
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel('Time of Day (Hours)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Bark Intensity Level', fontsize=12, fontweight='bold')
    ax.set_title('24-Hour Barking Activity Timeline', fontsize=14, fontweight='bold', pad=20)
    
    # Set time ticks
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 25, 2)], rotation=45)
    
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
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plt.close()
    
    return buffer

def create_pdf_report():
    """Generate the professional PDF report"""
    doc = SimpleDocTemplate(
        "barking_violation_report.pdf",
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=12,
        textColor=colors.HexColor('#1F2937'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#6B7280'),
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    metric_style = ParagraphStyle(
        'MetricStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        alignment=TA_CENTER,
        textColor=colors.white
    )
    
    # Story elements
    story = []
    
    # Header Section
    story.append(Paragraph("Barking Violation Report Summary", title_style))
    
    header_info = f"""
    <b>Date:</b> 2025-09-23 | <b>Report ID:</b> BVR-20250923-001 | 
    <b>Risk Level:</b> <font color='#DC2626'>HIGH RISK</font>
    """
    story.append(Paragraph(header_info, header_style))
    story.append(Spacer(1, 20))
    
    # Metrics Dashboard
    total_violations = len(violations_data)
    constant_violations = sum(1 for v in violations_data if v["type"] == "Constant")
    intermittent_violations = sum(1 for v in violations_data if v["type"] == "Intermittent")
    
    # Calculate total duration
    total_minutes = sum([
        int(v["duration"].split("m")[0]) + 
        (int(v["duration"].split("m")[1].replace("s", "").strip()) / 60) 
        for v in violations_data
    ])
    total_hours = int(total_minutes // 60)
    remaining_minutes = int(total_minutes % 60)
    
    metrics_data = [
        [
            Paragraph(f"<font size='24'><b>{total_violations}</b></font><br/>Total Violations", metric_style),
            Paragraph(f"<font size='24'><b>{constant_violations}</b></font><br/>Constant", metric_style),
            Paragraph(f"<font size='24'><b>{intermittent_violations}</b></font><br/>Intermittent", metric_style),
            Paragraph(f"<font size='24'><b>{total_hours}h {remaining_minutes}m</b></font><br/>Duration", metric_style)
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
    story.append(Spacer(1, 30))
    
    # Violations Table
    story.append(Paragraph("<b>Violation Details</b>", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    table_data = [['#', 'Type', 'Start Time', 'End Time', 'Duration', 'Total Barks', 'Audio Files']]
    
    for v in violations_data:
        type_color = '#DC2626' if v["type"] == "Constant" else '#F59E0B'
        table_data.append([
            str(v["id"]),
            Paragraph(f'<font color="{type_color}"><b>{v["type"]}</b></font>', styles['Normal']),
            v["start"],
            v["end"],
            v["duration"],
            str(v["barks"]),
            f'{v["files"]} files'
        ])
    
    violations_table = Table(table_data, colWidths=[0.5*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    violations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
    ]))
    
    story.append(violations_table)
    story.append(Spacer(1, 30))
    
    # Timeline Chart
    story.append(Paragraph("<b>Activity Timeline</b>", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Create and add chart
    chart_buffer = create_timeline_chart()
    chart_image = Image(chart_buffer, width=7*inch, height=3.5*inch)
    story.append(chart_image)
    
    # Build PDF
    doc.build(story)
    print("Report generated successfully: barking_violation_report.pdf")

if __name__ == "__main__":
    create_pdf_report()
