# Front-End Specification: Enhanced Report Design

## Page 1: Executive Summary (Redesigned)

### Header Section
```yaml
Title: "Barking Violation Report Summary"
Subtitle: "Date: 2025-09-23"
Report ID: Auto-generated timestamp
Status Badge: Violations: (High/Medium/Low with color coding)
```

### Key Metrics Dashboard
```yaml
Layout: 4-column grid
Metrics:
  - Total Violations: 7 (large, prominent number)
  - Constant Violations: 1 (red accent)
  - Intermittent Violations: 6 (orange accent)
Visual Treatment: Large numbers, colored backgrounds, icon indicators
```

### Violations Summary Table
```yaml
Columns:
  - Violation
  - Type (Constant/Intermittent with color badges (constant=red, intermittent=orange))
  - Start Time (HH:MM:SS format)
  - End Time (HH:MM:SS format)
  - Duration (human-readable: "2h 15m")
  - Total Barks (bold numbers)
  - Audio Files Count (linked to absolute path to recordings folder)

Styling:
  - Zebra striping for readability
  - Color-coded type column (red/orange badges)
  - Compact, scannable format
```

### Daily Timeline Visualization
```yaml
Chart Type: Scatter plot (X-Y coordinates)
X-Axis: Time of day (06:00 to 20:00)
Y-Axis: Bark intensity level (0-1.0)
Data Points:
  - Vertical Red line: Barks during constant violations
  - Vertical Orange line: Barks during intermittent violations
  - Vertical Gray line: Barks outside violations
  - Line length: Proportional to bark intensity score

Visual Features:
  - Grid lines every 2 hours
  - Violation period backgrounds (subtle colored bands)
  - Legend explaining color coding
```

### Elements to Remove
- Supporting audio file lists (moved to detail pages only)
- Remove Repetitive violation descriptions
- Reduce excessive whitespace and text walls

### CSS Framework Requirements
```css
/* Color Palette */
:root {
  --constant-violation: #DC2626; /* Red */
  --intermittent-violation: #F59E0B; /* Orange */
  --normal-activity: #9CA3AF; /* Gray */
  --high-risk: #EF4444;
  --medium-risk: #F59E0B;
  --low-risk: #10B981;
}
```

### Typography 

```
/* Typography Hierarchy */
.metric-large { font-size: 2.5rem; font-weight: 700; }
.violation-table th { font-weight: 600; }
.badge { border-radius: 0.375rem; padding: 0.25rem 0.5rem; }
```