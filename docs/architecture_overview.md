# Bark Detector Brownfield Architecture Document

## Introduction

[cite\_start]This document captures the CURRENT STATE of the Bark Detector codebase, a Python-based application designed for the legal evidence collection of dog barking incidents[cite: 1]. It serves as a reference for AI agents working on enhancements, bug fixes, and maintenance by documenting what EXISTS, including its refactored modular architecture, known technical debt, real-world patterns, and critical bugs related to violation analysis and reporting.

### Document Scope

This documentation is focused on providing the necessary context for AI agents to perform the following future tasks:

  * Documenting and implementing new features.
  * Reviewing and fixing existing bugs, particularly in the bark analysis and enhanced report generation modules.
  * Performing Quality Assurance on the architecture and command-line interface.
  * Refining requirements based on the existing `docs/` folder.

### Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-09-14 | 1.0 | Initial brownfield analysis and documentation | Winston (Architect) |

-----

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

  * **Main Entry Points**: `bark_detector/__main__.py` (modern package), `bd.py` (legacy wrapper).
  * **Core Detection Logic**: `bark_detector/core/detector.py` (Contains the `AdvancedBarkDetector` class which handles YAMNet model interaction and real-time audio processing).
  * **Violation Analysis**: `bark_detector/legal/tracker.py` (The "bark analyzer" which implements bylaw logic).
  * **Violation Database**: `bark_detector/legal/database.py` (Handles persistence of violation data).
  * **Report Generation**: `bark_detector/utils/report_generator.py` (The "enhanced violation report" generator).
  * **Data Models**: `bark_detector/core/models.py`, `bark_detector/legal/models.py`.
  * **Configuration**: `config.json` (Primary configuration), `bark_detector/calibration/profiles.py` (Handles sensitivity profiles).
  * **Command-Line Interface**: `bark_detector/cli.py`.

-----

## High Level Architecture

### Technical Summary

[cite\_start]The Bark Detector is a modular Python 3.11 application designed to run on macOS (both Apple Silicon and Intel)[cite: 1]. [cite\_start]It uses the YAMNet machine learning model via TensorFlow Hub for real-time audio classification to detect dog barking[cite: 1]. [cite\_start]Upon detection, it records audio evidence and analyzes it against City of Kelowna bylaws to identify and document violations for formal complaints[cite: 1]. [cite\_start]The system recently underwent a significant refactoring from a single monolithic script (`bd_original.py`) into a modern package structure (`bark_detector/`) to improve maintainability and testability[cite: 1].

### Actual Tech Stack

| Category | Technology | Version / Details | Notes |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.11.4 | Specified in `.python-version`. |
| **Package Manager** | uv | - | Used for all Python commands (e.g., `uv run ...`). |
| **ML Framework** | TensorFlow | 2.12.0 (Intel), 2.12.0 (macOS) | Handled by `install.py` for platform-specific builds. |
| **ML Model** | Google YAMNet | 1 | Loaded from TensorFlow Hub for audio classification. |
| **Audio I/O** | PyAudio | \>=0.2.11 | For real-time microphone input. |
| **Audio Processing** | Librosa, SoundFile | \>=0.9.0, \>=0.10.0 | For audio analysis, format conversion, and resampling. |
| **Numerical** | NumPy | \>=1.20.0 | For audio data manipulation. |
| **Testing** | pytest, pytest-mock | \>=7.0.0, \>=3.10.0 | Comprehensive test suite with ML mocking. |

### Repository Structure Reality Check

  * **Type**: Single repository containing the entire application.
  * [cite\_start]**Package Manager**: `uv` is used for managing Python dependencies[cite: 1].
  * [cite\_start]**Notable**: The project contains a significant `docs/` folder that acts as the source of truth for requirements, decisions, and status, intended for use by both humans and AI agents[cite: 1].

-----

## Source Tree and Module Organization

### Project Structure (Actual)

```
bark_detector/
├── bark_detector/          # Main application package
│   ├── core/               # Core detection logic and data models
│   ├── calibration/        # Sensitivity calibration and profiling
│   ├── legal/              # Violation analysis and reporting
│   ├── recording/          # Audio recording and file management
│   └── utils/              # Helper functions, config management
├── docs/                   # Project documentation (backlog, features, decisions)
├── scripts/                # Utility and migration scripts
├── tests/                  # Pytest test suite
├── samples/                # Sample audio and ground truth files for testing
├── config.json             # Main configuration file
├── install.py              # Cross-platform dependency installer
└── bd.py                   # Legacy entry point wrapper
```

### Key Modules and Their Purpose

  * **`bark_detector.core.detector`**: The primary engine containing the `AdvancedBarkDetector` class. It manages real-time audio streaming, interfacing with the YAMNet model, and triggering recording sessions.
  * **`bark_detector.legal.tracker`**: The "bark analyzer." It implements the logic for identifying "Constant" and "Intermittent" violations based on City of Kelowna bylaws by analyzing `BarkingSession` objects.
  * **`bark_detector.utils.report_generator`**: The "enhanced report generator." It parses application logs to create human-readable violation reports with detailed timestamp correlations.
  * **`bark_detector.calibration`**: Modules for tuning the detector's sensitivity using either real-time feedback or pre-recorded audio files with ground truth annotations.
  * **`install.py`**: A critical script that handles the platform-specific installation of TensorFlow for Intel vs. Apple Silicon (ARM) Macs.

-----

## Data Models and APIs

### Data Models

The system relies on several key data classes defined in `bark_detector/core/models.py` and `bark_detector/legal/models.py`:

  * `BarkEvent`: Represents a single, continuous bark sound with start/end times, confidence, and intensity.
  * `BarkingSession`: A collection of `BarkEvent`s grouped together, separated by short periods of silence (default \< 10 seconds).
  * `ViolationReport`: The final output object representing a bylaw violation, containing formatted dates, times, durations, and references to audio evidence files.

### API Specifications

The project is a command-line application. Its public API is the set of commands defined in `bark_detector/cli.py`. It does not expose any REST or web-based APIs.

-----

## Technical Debt and Known Issues

### Critical Technical Debt

1.  **Dual Configuration System**: The project uses both a `config.json` file and a separate "profiles" system for managing detector sensitivity. This creates confusion and should be consolidated. [cite\_start]The `docs/backlog.md` identifies this as a task (`T12`) for future review[cite: 1].
2.  **Brittle Reporting Pipeline**: The enhanced report generation relies on parsing log files, which has proven to be a brittle approach. A more robust solution, potentially using a lightweight database for events, is needed. [cite\_start]The user noted this as a key area for future improvement[cite: 1].

### Workarounds and Gotchas

  * [cite\_start]**Platform-Specific Installation**: The `install.py` script is a critical workaround to handle different TensorFlow dependencies on Apple Silicon vs. Intel Macs[cite: 1]. Standard `pip install` from a single requirements file will not work.
  * **YAMNet Class Filtering**: The system's accuracy heavily relies on excluding broad YAMNet classes like "Animal" to reduce false positives from environmental noise. [cite\_start]This is a crucial, non-obvious convention[cite: 1].
  * **TensorFlow Cache Corruption**: The YAMNet model cache can become corrupted, requiring manual deletion of the `tfhub_modules` directory to resolve model loading errors (`docs/bugs.md`).

### Known Bugs

  * **Bark Analyzer & Report Discrepancies**: There is a critical disconnect between the violation analysis (`--analyze-violations`) and the enhanced report generation (`--enhanced-violation-report`). [cite\_start]They can produce different conclusions for the same date due to bugs in file ordering and timestamp correlation[cite: 1].
  * **Incorrect Timestamp Correlation**: The enhanced reports fail to correctly identify which audio file a bark occurred in and at what specific time within that file. [cite\_start]This is the highest priority bug to fix as it undermines the project's primary goal[cite: 1].

-----

## Development and Deployment

### Local Development Setup

[cite\_start]Setup is managed via `uv` and the custom `install.py` script, which handles platform detection[cite: 1].

1.  `uv venv`
2.  `uv run install.py`
3.  `uv run python -m bark_detector`

### Build and Deployment Process

  * **Build**: There is no formal build process; it is an interpreted Python application.
  * [cite\_start]**Deployment**: Deployment is a manual process involving syncing the source code to the target Intel Mac and running the `install.py` script to set up the environment[cite: 1].

-----

## Testing Reality

### Current Test Coverage

The project has a robust test suite in the `tests/` directory, created as part of the T2 refactoring effort. It includes:

  * Over 45 tests covering core logic, legal violation rules, and the CLI (`docs/tests.md`).
  * Sophisticated mocking of TensorFlow/YAMNet to allow for testing without model downloads.
  * A sample-based testing system (`tests/test_samples/`) that validates detection against real audio files with ground truth annotations (`docs/sample_based_testing.md`).

### Running Tests

```bash
uv run pytest tests/
```

[cite\_start][cite: 1]

-----

## Future AI Task Impact Areas

Based on the requested future work, AI agents will need to focus on the following areas:

  * **Fixing Violation Analysis & Reporting**: This will require deep modifications to `bark_detector/legal/tracker.py`, `database.py`, and `utils/report_generator.py`. A potential solution involves creating a lightweight database to store bark events in real-time, decoupling analysis from fragile log parsing.
  * **QA and Streamlining the CLI**: This will involve reviewing and refactoring `bark_detector/cli.py` and addressing the dual configuration issue in `bark_detector/utils/config.py` and `bark_detector/calibration/profiles.py`.
  * **Implementing New Features**: This will likely involve creating new user stories and epics based on the `docs/` folder and then modifying the core detector logic in `bark_detector/core/detector.py` and the CLI in `bark_detector/cli.py`.

-----

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

  * [cite\_start]**Run application**: `uv run python -m bark_detector` [cite: 1]
  * [cite\_start]**Run tests**: `uv run pytest tests/` [cite: 1]
  * [cite\_start]**Install dependencies**: `uv run install.py` [cite: 1]
  * **Analyze Violations**: `uv run python -m bark_detector --analyze-violations YYYY-MM-DD`
  * **Generate Report**: `uv run python -m bark_detector --violation-report START_DATE END_DATE`