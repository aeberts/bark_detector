# Epic 1: Violation Analysis Overhaul

**Epic Goal**: To refactor the violation analysis pipeline to be reliable and accurate for legal evidence collection, focusing on data persistence and analysis engine improvements.

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

## Stories 1.4-1.6: ~~Superseded by Epic 3~~
**Note:** The following stories have been superseded by Epic 3: Violation Report Generation Overhaul.

### ~~Story 1.4: Deprecate Legacy Reporting Code~~ [SUPERSEDED]
### ~~Story 1.5: Implement New Database-Driven Report Generator~~ [SUPERSEDED]
### ~~Story 1.6: Implement Smart `--violation-report` Command~~ [SUPERSEDED]

## Additional Bug Fix Stories (Implemented)
- **Story 1.7:** [Bug fixes - Implemented]
- **Story 1.8:** [Bug fixes - Implemented]
- **Story 1.9:** [Bug fixes - Implemented]

## Epic Status
- Stories 1.1-1.3: ✅ **COMPLETED** (Analysis pipeline refactor)
- Stories 1.4-1.6: ❌ **SUPERSEDED** (Moved to Epic 3)
- Stories 1.7-1.9: ✅ **COMPLETED** (Bug fixes)