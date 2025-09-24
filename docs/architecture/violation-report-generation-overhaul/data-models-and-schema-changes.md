# Data Models and Schema Changes

## Existing Data Models (No Changes Required)

Your current data architecture already provides everything needed for professional PDF report generation:

### PersistedBarkEvent (Already Perfect)
- **Purpose:** Raw bark detection data with complete temporal and acoustic metadata
- **Integration:** PDF reports will consume this data directly from `YYYY-MM-DD_events.json` files
- **Key Attributes Available:**
  - `realworld_date`, `realworld_time`: Perfect for legal evidence timestamps
  - `bark_id`: Enables cross-referencing between events and violations
  - `bark_type`: Provides classification detail for report narratives
  - `audio_file_name`, `bark_audiofile_timestamp`: Critical for audio evidence correlation
  - `confidence`, `intensity`: Essential data for visualization graphs
  - `est_dog_size`: Future enhancement potential for report detail

### Violation (Already Comprehensive)
- **Purpose:** Legal violation records with three-timestamp architecture for compliance
- **Integration:** PDF reports consume this data from `YYYY-MM-DD_violations.json` files
- **Key Attributes Available:**
  - `type`: "Continuous" or "Intermittent" for legal classification
  - `startTimestamp`, `violationTriggerTimestamp`, `endTimestamp`: Complete temporal audit trail
  - `durationMinutes`, `violationDurationMinutes`: Pre-calculated durations for reports
  - `barkEventIds`: Links to specific bark events for detailed evidence

### ViolationReport (Presentation Layer Ready)
- **Purpose:** Formatted violation data optimized for human-readable output
- **Integration:** PDF generation will enhance this model's output formatting capabilities
- **Key Attributes Available:**
  - `date`, `start_time`, `end_time`: RDCO-compliant time formatting
  - `violation_type`: Legal classification for report headers
  - `audio_files`, `audio_file_start_times`, `audio_file_end_times`: Complete audio evidence mapping
  - `confidence_scores`, `peak_confidence`, `avg_confidence`: Statistical data for charts

## Schema Integration Strategy

**No Database Changes Required:**
Your existing date-partitioned JSON structure is ideal for PDF report generation:

- **Existing Files Consumed:**
  - `violations/YYYY-MM-DD/YYYY-MM-DD_events.json`: Raw bark event data for detailed analysis
  - `violations/YYYY-MM-DD/YYYY-MM-DD_violations.json`: Legal violation records for summary reporting
  - Audio files in `recordings/YYYY-MM-DD/`: Referenced for evidence correlation

- **New Files Generated:**
  - `reports/YYYY-MM-DD_Violation_Report.pdf`: Professional PDF output (Epic 1 requirement)
  - `reports/YYYY-MM-DD/` directory: Supporting charts and metadata (optional organization)

---
