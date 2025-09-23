# Source Tree

This guide highlights the directories and files that matter most when navigating the Bark Detector brownfield repository. It reflects the current layout as of September 2025 and focuses on components that influence the violation analysis refactor.

## Top-Level Layout
```
.
├── bark_detector/           # Primary application package (CLI, core detection, legal analysis)
├── docs/                    # Project documentation, PRDs, architecture notes, stories
├── tests/                   # Pytest suite organised by domain (core, legal, integration, utils)
├── recordings/              # Captured audio (WAV) organised by date or flat filenames
├── violations/              # Persisted bark events & violation JSON output
├── reports/                 # Generated human-readable violation reports
├── scripts/                 # Utility scripts for maintenance and debugging
├── samples/                 # Example audio & ground truth assets for calibration
├── config*.json             # User-defined configuration files
├── README.md                # Installation & usage instructions
├── CLAUDE.md                # Guidance for AI coding assistants
└── pyproject.toml           # Python packaging metadata driven by install.py
```

## Application Package (`bark_detector/`)
- `__main__.py` / `cli.py`: Entrypoints for CLI commands (`uv run python -m bark_detector ...`).
- `core/`: YAMNet-powered detection (`detector.py`, domain models).
- `legal/`: Evidence pipeline (`tracker.py`, `database.py`, `models.py`).
- `utils/`: Shared utilities (`config.py`, `report_generator.py`, `time_utils.py`, TensorFlow warnings suppression).
- `recording/`: Audio capture helpers (`recorder.py`, `converter.py`).
- `calibration/`: Batch and realtime calibration workflows against sample audio.

## Documentation (`docs/`)
- `architecture/`: Brownfield architecture set (component diagrams, data models, tech stack, violation algorithm).
- `stories/`: User stories and development notes (e.g., `1.9.fix-violation-detection-algorithm-bug.md`).
- `backlog.md`, `features.md`, `improvements.md`: Planning artefacts referenced during grooming.
- `violation_rules.md`: Canonical legal detection rules (keep aligned with code thresholds).

## Tests (`tests/`)
- `test_core/`: Detector, model, and quantitative validation specs.
- `test_legal/`: Violation tracking, persistence, and report generation regression suite.
- `test_integration/`: CLI-level scenarios covering configuration and command orchestration.
- `fixtures/`: Shared sample data loader utilities; real-world JSON samples live outside `tests/` in `violations/`.

## Operational Artefacts
- `violations/<date>/`: Contains `<date>_events.json` (persisted bark events) and `<date>_violations.json` (analysis output).
- `recordings/<date>/`: WAV files used during offline analysis; naming convention `bark_recording_YYYYMMDD_HHMMSS.wav`.
- `reports/`: Markdown/HTML summaries generated via `report_generator`.

## Supporting Assets
- `install.py`: Platform-aware dependency installer (TensorFlow wheel selection).
- `bd.py`, `bd_original.py`: Legacy entrypoints retained for backward compatibility and regression reference.
- `debug_*.py`: Targeted diagnostics for violation detection and event structures—useful when investigating analyser regressions.

## Maintenance Notes
- Continuous violation gap threshold is currently 10 seconds in `legal/tracker.py`; recent analysis documents (2025-09-17) propose widening this to ~33 seconds. Update `docs/violation_rules.md` and `docs/architecture` materials alongside code changes.
- Keep new modules under the existing package hierarchy—avoid introducing top-level packages without updating this source tree overview and `docs/architecture/component-architecture.md`.
