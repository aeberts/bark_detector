# Epic and Story Structure

## Epic Approach
This enhancement will be structured as a **single, comprehensive epic**. The rationale is that all required tasks are highly interdependent and must be completed together to deliver the final user value: a trustworthy, end-to-end evidence generation system.

---
# Epic 1: Violation Reporting System Overhaul (Final)

**Epic Goal**: To refactor the violation analysis and reporting pipeline to be reliable, accurate, and robust. This will deliver a single, intuitive command-line interface for generating legally viable evidence for RDCO complaints, resolving all known data correlation bugs.

**Integration Requirements**: The refactored system must read source audio from the `recordings/` directory, write its analysis results to the `violations/` directory using the new date-stamped, dual-file (`_events.json`, `_violations.json`) format, and correctly integrate with the existing `pytest` testing infrastructure.

## Story 1.1: Refactor Data Persistence Layer
* **As a** system maintainer,
    **I want** the `ViolationDatabase` module to read from and write to a date-partitioned folder structure,
    **so that** violation and event data is stored in a robust, portable, and easily managed format.
* **Acceptance Criteria**:
    1.  The `ViolationDatabase` class can correctly save `[YYYY-MM-DD]_events.json` and `[YYYY-MM-DD]_violations.json` files to a `violations/[YYYY-MM-DD]/` directory.
    2.  The class can correctly load data from this new structure.
    3.  **The `CHANGELOG.md` and `docs/features.md` are updated to reflect the new data persistence strategy.**
* **Integration Verification**:
    1.  Existing unit tests for the `ViolationDatabase` that are unrelated to file paths must still pass.

## Story 1.2: Refactor Violation Analysis Engine
* **As a** system maintainer,
    **I want** the `LegalViolationTracker` to use the refactored `ViolationDatabase` to save its analysis results,
    **so that** all detected bark events and identified violations are persisted to the new structured JSON files.
* **Acceptance Criteria**:
    1.  `LegalViolationTracker` saves all detected raw bark events to the correct `[YYYY-MM-DD]_events.json` file.
    2.  It saves all identified bylaw violations to the correct `[YYYY-MM-DD]_violations.json` file.
    3.  **The `CHANGELOG.md` is updated with a summary of the refactor.**
* **Integration Verification**:
    1.  The refactored tracker must produce analysis results for a sample audio file that are demonstrably more accurate than the old, buggy implementation.

## Story 1.3: Update the `--analyze-violations` Command
* **As a** user,
    **I want** to run the `--analyze-violations` command,
    **so that** it uses the refactored `LegalViolationTracker` to generate accurate, persisted analysis files.
* **Acceptance Criteria**:
    1.  Running `uv run python -m bark_detector --analyze-violations [DATE]` executes the new analysis workflow.
    2.  The correct `_events.json` and `_violations.json` files are created in the `violations/[DATE]/` directory.
    3.  **The `README.md` and `CHANGELOG.md` are updated to reflect the changes to this command.**
* **Integration Verification**:
    1.  The command must handle cases where the source `recordings/` directory for a given date does not exist.

## Story 1.4: Deprecate Legacy Reporting Code
* **As a** system maintainer,
    **I want** to remove the old `--enhanced-violation-report` command and its underlying log-parsing logic,
    **so that** the codebase contains only a single, reliable reporting workflow.
* **Acceptance Criteria**:
    1.  The `--enhanced-violation-report` argument is removed from `bark_detector/cli.py`.
    2.  The `LogBasedReportGenerator` class is deleted from `bark_detector/utils/report_generator.py`.
    3.  **The `CHANGELOG.md` and relevant docs are updated to note the removal of the legacy feature.**
* **Integration Verification**:
    1.  Removing the old code must not impact the functionality of the `--analyze-violations` command.

## Story 1.5: Implement New Database-Driven Report Generator
* **As a** system maintainer,
    **I want** a new report generation module that creates human-readable output from the reliable `_violations.json` and `_events.json` files,
    **so that** reports are accurate and decoupled from logs.
* **Acceptance Criteria**:
    1.  A new module can format a detailed text report from the two JSON source files.
    2.  The report correctly lists all violations and correlates each bark event to its source audio file and timestamp offset.
    3.  **The `CHANGELOG.md` and `docs/features.md` are updated to describe the new reporting engine.**
* **Integration Verification**:
    1.  The report generator must gracefully handle missing or corrupted JSON analysis files.

## Story 1.6: Implement Smart `--violation-report` Command
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