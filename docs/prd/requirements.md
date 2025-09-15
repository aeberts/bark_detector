# Requirements

## Functional

1.  **FR1**: The violation analysis process MUST analyze audio recordings in chronological order based on their filename timestamps to ensure accurate session and violation tracking.
2.  **FR2**: The enhanced report generation module MUST source its data from a persistent and structured data store (e.g., the `violations/` JSON database) instead of parsing application logs.
3.  **FR3**: Each bark event listed in a detailed violation report MUST be accurately correlated with its source audio file and include a precise `HH:MM:SS.mmm` timestamp of its offset from the start of that file.
4.  **FR4**: The summary violation report's total violation count for a given day MUST match the number of detailed violation reports generated for that same day.
5.  **FR5**: The dual configuration systems (`config.json` and the calibration `profiles`) MUST be consolidated into a single, unified configuration mechanism to eliminate ambiguity.
6.  **FR6**: The system MUST provide a single, robust command (`--violation-report`) for generating evidence reports. This command will first automatically run the violation analysis process on the source audio files to populate a structured database, and then generate the human-readable report from that database, ensuring data integrity and decoupling the process from fragile log parsing.

## Non-Functional

1.  **NFR1**: The refactored analysis and reporting pipeline must not introduce significant performance degradation; processing time for a given day's recordings should be comparable to the previous implementation.
2.  **NFR2**: The system MUST maintain its ability to install and run correctly on both Apple Silicon (ARM) and Intel (x86_64) macOS platforms.
3.  **NFR3**: The violation detection logic MUST continue to adhere to the established definitions for "Constant" and "Intermittent" barking as defined in the `docs/project_overview.md` file.

## Compatibility Requirements

1.  **CR1**: All existing Command-Line Interface (CLI) commands, such as `--analyze-violations` and `--violation-report`, MUST remain functional, even if their underlying implementation is completely overhauled.
2.  **CR2**: The structure of existing data models (`BarkEvent`, `BarkingSession`, `ViolationReport`) SHOULD NOT be altered unless a change is critical for fixing the reporting bugs.
3.  **CR3**: The system MUST remain compatible with the existing calibration workflows and ground truth file formats.