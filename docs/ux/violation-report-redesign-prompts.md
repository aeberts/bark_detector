# AI-Optimized Implementation Prompts

## Prompt 1: v0.dev/Claude Artifacts (Complete Summary Page)

```
Create a modern, professional bark violation report summary page with the following specifications:

LAYOUT & STRUCTURE:
- Clean, scannable design with proper visual hierarchy
- Header with report title "Barking Violation Report Summary" and date "2025-09-23"
- 4-column metrics dashboard showing: Total Violations (7), Constant (1), Intermittent (6), Total Duration (12h 15m)
- Use large, prominent numbers for key metrics

VIOLATIONS TABLE:
Create a sortable table with these columns:
- Violation # | Type | Start Time | End Time | Duration | Bark Count | Audio Files
- Sample data: Violation 1 | Constant | 10:40:53 | 10:46:42 | 5m 48s | 77 | 1 file
- Use color-coded badges: red for "Constant", orange for "Intermittent"
- Zebra striping for readability
- Make "Audio Files" column show count with download icon, not file lists

DAILY TIMELINE CHART:
- X-Y scatter plot: X-axis is time (00:00-23:59), Y-axis is bark intensity (0-1.0)
- Color coding: Red dots for constant violations, orange for intermittent, gray for normal
- Show violation periods as subtle background bands
- Include interactive hover tooltips
- Responsive design for mobile viewing

STYLING:
- Professional color scheme: Red (#DC2626), Orange (#F59E0B), Gray (#9CA3AF)
- Modern typography with proper font weights
- Clean spacing and grid layouts
- Remove any file listing sections entirely

Generate clean, production-ready code for pdf creation with the reportlab python library.
```

## Prompt 2: python reportlab (Timeline Visualization)

```
Create an interactive daily bark activity timeline chart with these exact specifications:

CHART TYPE: Scatter plot (X-Y coordinates)
- X-axis: Time of day from 00:00 to 23:59 (24-hour format)
- Y-axis: Bark intensity level from 0.0 to 1.0
- Grid lines every 2 hours on X-axis, every 0.2 on Y-axis

DATA VISUALIZATION:
- Red dots (size 4px): Barks during constant violations
- Orange dots (size 3px): Barks during intermittent violations
- Light gray dots (size 2px): Barks outside violation periods
- Add subtle colored background bands for violation time periods

SAMPLE DATA to use:
- Constant violation: 10:40-10:46 (red background, red dots)
- Intermittent violations: 07:45-09:48, 09:55-11:15, etc. (orange background, orange dots)
- Scatter random bark events throughout the day with appropriate colors

STYLING:
- Clean, professional appearance
- Color palette: #DC2626 (red), #F59E0B (orange), #9CA3AF (gray)
- Modern grid lines and axis labels
- Title: "Bark Activity Timeline - 2025-09-23"

Use reportlab pdf creation library for python.
```

## Prompt 3: React/Vue Component (Violations Table)

```
Build a violations summary table in the pdf library reportlab with these requirements:

TABLE STRUCTURE:
Columns: Violation #, Type, Start Time, End Time, Duration, Bark Count, Audio Files
Sample data for 7 violations:
1. Constant | 10:40:53 | 10:46:42 | 5m 48s | 77 barks | 1 file
2. Intermittent | 07:45:06 | 09:48:57 | 2h 3m | 579 barks | 35 files
[Include realistic data for all 7 violations]

VISUAL DESIGN:
- Color-coded type badges: Red pill for "Constant", Orange pill for "Intermittent"
- Zebra row striping (alternating white/gray backgrounds)
- Bold numbers for bark counts
- Clean, professional typography
- Hover effects on rows

FUNCTIONALITY:
- Sortable columns (click headers to sort)
- Audio Files column shows count with download icon, NOT file lists
- Responsive design (stack on mobile if needed)
- Loading states and empty states

STYLING REQUIREMENTS:
- Modern table design with proper spacing
- Color scheme: Red #DC2626, Orange #F59E0B, Gray backgrounds
- Professional appearance suitable for legal documentation
- Accessibility features (proper ARIA labels, keyboard navigation)

TECHNICAL:
- Use TypeScript if React
- Include proper prop types/interfaces
- Clean, reusable component structure
- Sample data included for demo

Generate complete code that can be used with the reportlab python library.
```

## Prompt 4: PDF Generation (Python/ReportLab)

```
Create a Python script using ReportLab to generate a professional bark violation PDF report with this improved layout:

SUMMARY PAGE STRUCTURE:
HEADER:
- Title: "Barking Violation Report Summary" (large, bold)
- Date: 2025-09-23, Report ID, Risk level badge

METRICS DASHBOARD:
- 4-column layout with large numbers:
  Total Violations: 7 | Constant: 1 | Intermittent: 6 | Duration: 12h 15m
- Use colored backgrounds and proper spacing

VIOLATIONS TABLE:
- Clean table with columns: #, Type, Start, End, Duration, Barks, Files
- Color-coded type column (red/orange cells)
- Professional table styling with borders and alternating row colors
- NO audio file lists - just counts with links

TIMELINE CHART:
- Embed a scatter plot showing bark activity over 24 hours
- X-axis: Time (00:00-23:59), Y-axis: Intensity (0-1.0)
- Red dots for constant violations, orange for intermittent
- Include proper legends and grid lines

IMPLEMENTATION:
- Use ReportLab for PDF generation
- Include matplotlib/pyplot for chart generation
- Clean, professional styling throughout
- Proper fonts (Arial/Helvetica)
- Color scheme: Red #DC2626, Orange #F59E0B, Gray accents
- Page margins and spacing optimized for printing

REMOVED ELEMENTS:
- Eliminate all "Supporting audio files:" sections from summary page
- No repetitive file name lists for the summaries 
- Streamlined, executive-summary focused design

Include sample data and complete working code for implementation with reportlab pdf library.
```