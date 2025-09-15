# Bark Detector Brownfield Enhancement PRD

## Intro Project Analysis and Context

### Existing Project Overview

* **Analysis Source**: This analysis is based on the previously generated Brownfield Architecture Document and the comprehensive project details you provided.
* **Current Project State**: The project is a modular Python application that uses the YAMNet ML model to detect dog barking, record audio evidence, and analyze it against local bylaws. It has recently been refactored from a single script into a package structure but suffers from critical bugs in its violation analysis and reporting features.

### Available Documentation Analysis

The Brownfield Architecture Document created previously provides a solid foundation. Key available documentation includes:

* [x] Tech Stack Documentation
* [x] Source Tree/Architecture
* [x] Coding Standards (Inferred from code and docs)
* [x] API Documentation (CLI commands)
* [ ] External API Documentation (TensorFlow Hub is used but not explicitly documented)
* [ ] UX/UI Guidelines (N/A for this service)
* [x] Technical Debt Documentation

### Enhancement Scope Definition

* **Enhancement Type**:
    * [x] Major Feature Modification
    * [x] Bug Fix and Stability Improvements
* **Enhancement Description**: This project aims to fix and improve the core functionality for analyzing recorded audio and generating accurate, reliable violation reports suitable for submission as evidence to the Regional Dog Control Okanagan (RDCO).
* **Impact Assessment**:
    * [x] Significant Impact (substantial existing code changes)

### Goals and Background Context

* **Goals**:
    * Reliably generate accurate violation reports from recorded audio.
    * Ensure bark events in reports correctly correlate to timestamps within the specific audio files.
    * Fix the discrepancy between the bark analyzer and the enhanced report generator.
    * Improve the brittleness of the current log-parsing-based reporting system.
* **Background Context**: The primary goal is to collect legally viable evidence of barking incidents for submission to the RDCO. The current system fails to do this reliably due to critical bugs in the analysis and reporting pipeline, which undermines the entire purpose of the application. This enhancement will address these failures to make the system functional and trustworthy.

### Change Log

| Change | Date | Version | Description | Author |
| :--- | :--- | :--- | :--- | :--- |
| Initial Draft | 2025-09-14 | 0.1 | Initial draft of the Brownfield PRD based on project analysis. | John (PM) |

---
## Requirements

### Functional

1.  **FR1**: The violation analysis process MUST analyze audio recordings in chronological order based on their filename timestamps to ensure accurate session and violation tracking.
2.  **FR2**: The enhanced report generation module MUST source its data from a persistent and structured data store (e.g., the `violations/` JSON database) instead of parsing application logs.
3.  **FR3**: Each bark event listed in a detailed violation report MUST be accurately correlated with its source audio file and include a precise `HH:MM:SS.mmm` timestamp of its offset from the start of that file.
4.  **FR4**: The summary violation report's total violation count for a given day MUST match the number of detailed violation reports generated for that same day.
5.  **FR5**: The dual configuration systems (`config.json` and the calibration `profiles`) MUST be consolidated into a single, unified configuration mechanism to eliminate ambiguity.
6.  **FR6**: The system MUST provide a single, robust command (`--violation-report`) for generating evidence reports. This command will first automatically run the violation analysis process on the source audio files to populate a structured database, and then generate the human-readable report from that database, ensuring data integrity and decoupling the process from fragile log parsing.

### Non-Functional

1.  **NFR1**: The refactored analysis and reporting pipeline must not introduce significant performance degradation; processing time for a given day's recordings should be comparable to the previous implementation.
2.  **NFR2**: The system MUST maintain its ability to install and run correctly on both Apple Silicon (ARM) and Intel (x86_64) macOS platforms.
3.  **NFR3**: The violation detection logic MUST continue to adhere to the established definitions for "Constant" and "Intermittent" barking as defined in the `docs/project_overview.md` file.

### Compatibility Requirements

1.  **CR1**: All existing Command-Line Interface (CLI) commands, such as `--analyze-violations` and `--violation-report`, MUST remain functional, even if their underlying implementation is completely overhauled.
2.  **CR2**: The structure of existing data models (`BarkEvent`, `BarkingSession`, `ViolationReport`) SHOULD NOT be altered unless a change is critical for fixing the reporting bugs.
3.  **CR3**: The system MUST remain compatible with the existing calibration workflows and ground truth file formats.

---
## Technical Constraints and Integration Requirements

### Existing Technology Stack
*(Confirmed)* The system will continue to be built on Python 3.11, using TensorFlow/YAMNet for ML, PyAudio for audio I/O, and `uv` for package management.

### Integration Approach

#### Data Persistence Strategy
Per your input, the `--analyze-violations` command will now generate two structured files in the `violations/[YYYY-MM-DD]/` directory with the date prepended to the filename:

1.  **`[YYYY-MM-DD]_events.json`**: This file will contain the raw, unprocessed log of every individual bark event detected in the audio files for that day.
2.  **`[YYYY-MM-DD]_violations.json`**: This file will contain the final, interpreted list of bylaw violations that were derived from the data in the events file.

The schema for each record in `[YYYY-MM-DD]_events.json` will be:
* `realworld_date`: The date of the event (e.g., "2025-09-14").
* `realworld_time`: The precise time of the event (e.g., "18:22:15.123").
* `bark_id`: A unique identifier for the event.
* `bark_type`: The specific YAMNet class that triggered the detection (e.g., "Bark", "Howl", "Yip").
* `est_dog_size`: We will include this field and populate it with `null` for now, marking it as a target for a future feature improvement.
* `audio_file_name`: The name of the `.wav` file containing the bark.
* `bark_audiofile_timestamp`: The precise `HH:MM:SS.mmm` offset of the event from the start of the audio file.

#### API (Internal Logic) Integration Strategy
The `--violation-report` command will be updated with the following intelligent workflow:
1.  When a user runs `--violation-report [DATE]`, the system will first check if a `[YYYY-MM-DD]_violations.json` analysis file already exists for that date.
2.  **If the file does not exist**, it will automatically trigger the `--analyze-violations` logic for that date first.
3.  Once the analysis is complete, the system will generate the human-readable report from the `violations.json` file.

#### Testing Integration Strategy
New integration tests will be added to the `pytest` suite to validate the complete, end-to-end workflow and confirm that the data correlation bugs have been resolved.

### Code Organization and Standards
* **File Structure Approach**: The `--enhanced-violation-report` command and its `LogBasedReportGenerator` will be removed. All analysis logic will be consolidated and refactored within `bark_detector/legal/tracker.py` and `bark_detector/legal/database.py`. The `cli.py` will be updated to reflect the new command logic.
* **Documentation Standards**: The `README.md` and `docs/features.md` must be updated to reflect the single, unified reporting command.

### Deployment and Operations
* **Post-Deployment Task**: After deployment, a one-time analysis of all historical recordings should be performed using the updated `--analyze-violations` command to populate the new `violations/` database.

### Risk Assessment and Mitigation
* **Technical Risk**: The "smart" `--violation-report` command could have a long runtime if it triggers a first-time analysis of many recordings.
    * **Mitigation**: The CLI must provide clear feedback to the user (e.g., "Analysis for [DATE] not found. Running analysis now...") to manage expectations.
* **Integration Risk**: The refactored violation logic in `LegalViolationTracker` could contain errors.
    * **Mitigation**: This will be mitigated by writing a comprehensive suite of new integration tests to validate the end-to-end process.

---
## Epic and Story Structure

### Epic Approach
This enhancement will be structured as a **single, comprehensive epic**. The rationale is that all required tasks are highly interdependent and must be completed together to deliver the final user value: a trustworthy, end-to-end evidence generation system.

---
## Epic 1: Violation Reporting System Overhaul (Final)

**Epic Goal**: To refactor the violation analysis and reporting pipeline to be reliable, accurate, and robust. This will deliver a single, intuitive command-line interface for generating legally viable evidence for RDCO complaints, resolving all known data correlation bugs.

**Integration Requirements**: The refactored system must read source audio from the `recordings/` directory, write its analysis results to the `violations/` directory using the new date-stamped, dual-file (`_events.json`, `_violations.json`) format, and correctly integrate with the existing `pytest` testing infrastructure.

### Story 1.1: Refactor Data Persistence Layer
* **As a** system maintainer,
    **I want** the `ViolationDatabase` module to read from and write to a date-partitioned folder structure,
    **so that** violation and event data is stored in a robust, portable, and easily managed format.
* **Acceptance Criteria**:
    1.  The `ViolationDatabase` class can correctly save `[YYYY-MM-DD]_events.json` and `[YYYY-MM-DD]_violations.json` files to a `violations/[YYYY-MM-DD]/` directory.
    2.  The class can correctly load data from this new structure.
    3.  **The `CHANGELOG.md` and `docs/features.md` are updated to reflect the new data persistence strategy.**
* **Integration Verification**:
    1.  Existing unit tests for the `ViolationDatabase` that are unrelated to file paths must still pass.

### Story 1.2: Refactor Violation Analysis Engine
* **As a** system maintainer,
    **I want** the `LegalViolationTracker` to use the refactored `ViolationDatabase` to save its analysis results,
    **so that** all detected bark events and identified violations are persisted to the new structured JSON files.
* **Acceptance Criteria**:
    1.  `LegalViolationTracker` saves all detected raw bark events to the correct `[YYYY-MM-DD]_events.json` file.
    2.  It saves all identified bylaw violations to the correct `[YYYY-MM-DD]_violations.json` file.
    3.  **The `CHANGELOG.md` is updated with a summary of the refactor.**
* **Integration Verification**:
    1.  The refactored tracker must produce analysis results for a sample audio file that are demonstrably more accurate than the old, buggy implementation.

### Story 1.3: Update the `--analyze-violations` Command
* **As a** user,
    **I want** to run the `--analyze-violations` command,
    **so that** it uses the refactored `LegalViolationTracker` to generate accurate, persisted analysis files.
* **Acceptance Criteria**:
    1.  Running `uv run python -m bark_detector --analyze-violations [DATE]` executes the new analysis workflow.
    2.  The correct `_events.json` and `_violations.json` files are created in the `violations/[DATE]/` directory.
    3.  **The `README.md` and `CHANGELOG.md` are updated to reflect the changes to this command.**
* **Integration Verification**:
    1.  The command must handle cases where the source `recordings/` directory for a given date does not exist.

### Story 1.4: Deprecate Legacy Reporting Code
* **As a** system maintainer,
    **I want** to remove the old `--enhanced-violation-report` command and its underlying log-parsing logic,
    **so that** the codebase contains only a single, reliable reporting workflow.
* **Acceptance Criteria**:
    1.  The `--enhanced-violation-report` argument is removed from `bark_detector/cli.py`.
    2.  The `LogBasedReportGenerator` class is deleted from `bark_detector/utils/report_generator.py`.
    3.  **The `CHANGELOG.md` and relevant docs are updated to note the removal of the legacy feature.**
* **Integration Verification**:
    1.  Removing the old code must not impact the functionality of the `--analyze-violations` command.

### Story 1.5: Implement New Database-Driven Report Generator
* **As a** system maintainer,
    **I want** a new report generation module that creates human-readable output from the reliable `_violations.json` and `_events.json` files,
    **so that** reports are accurate and decoupled from logs.
* **Acceptance Criteria**:
    1.  A new module can format a detailed text report from the two JSON source files.
    2.  The report correctly lists all violations and correlates each bark event to its source audio file and timestamp offset.
    3.  **The `CHANGELOG.md` and `docs/features.md` are updated to describe the new reporting engine.**
* **Integration Verification**:
    1.  The report generator must gracefully handle missing or corrupted JSON analysis files.

### Story 1.6: Implement Smart `--violation-report` Command
* **As a** user,
    **I want** to run the `--violation-report` command and have it automatically analyze the data if needed,
    **so that** I can get a complete report with a single command.
* **Acceptance Criteria**:
    1.  When run for a date with existing analysis files, the command immediately generates a report.
    2.  When run for a date without analysis files, it first triggers the analysis logic and then generates the report.
    3.  A clear message is displayed to the user when the automatic analysis is being run.
    4.  **The `README.md`, `CHANGELOG.md`, and `docs/features.md` are updated with the final usage instructions for the new, unified `--violation-report` command.**
* **Integration Verification**:
    1.  The command must function correctly for both single-day and date-range reports.