# Tech Stack

This document summarises the technologies currently in use for the Bark Detector brownfield project. It consolidates information scattered across `README.md`, `CLAUDE.md`, and the architecture bundle so new contributors can understand the operational context quickly.

## Runtime & Languages
- **Primary language**: Python 3.11.4 (project supports >=3.9,<3.12; documentation and tooling standardise on 3.11.4).
- **Execution environment**: Cross-platform macOS (Apple Silicon & Intel) and Linux. Development occurs on Apple Silicon; production deployment currently targets an Intel Mac mini-class device.

## Core Frameworks & Libraries
| Area | Technology | Notes |
| --- | --- | --- |
| Machine learning | TensorFlow (tensorflow-macos / tensorflow) + TensorFlow Hub | Provides the YAMNet model used for bark classification. Downloads are cached per README guidance. |
| Audio analysis | Librosa, SoundFile, PyAudio | Librosa/SoundFile handle offline file analysis; PyAudio powers live capture when running the detector interactively. |
| Numerical compute | NumPy, SciPy | Support signal processing and ML pre/post-processing steps. |
| Domain models | Python `dataclasses`, `typing` | Models such as `PersistedBarkEvent`, `Violation`, and `BarkingSession`. |

## Application Structure
- **Core detection**: `bark_detector/core/detector.py` orchestrates audio capture and YAMNet inference.
- **Legal analysis**: `bark_detector/legal/tracker.py` and `bark_detector/legal/database.py` convert bark events into legally-formatted violations and persist JSON artefacts.
- **Reporting**: `bark_detector/utils/report_generator.py` turns persisted data into human-readable evidence packs.
- **CLI**: `bark_detector/cli.py` exposes worker commands such as `--analyze-violations`.

## Tooling & Package Management
- **Dependency manager**: `uv` (per `README.md` and `CLAUDE.md`). All Python commands, including tests, are executed via `uv run ...`.
- **Testing**: `pytest`, `pytest-mock`, `pytest-cov` for targeted regression coverage. Real-world JSON fixtures in `violations/` complement unit tests.
- **Linters/formatters**: No enforced tool presently, but `uv` makes it straightforward to add `ruff` or `black` if required.

## Data & Persistence
- **Event storage**: JSON files in `violations/<date>/<date>_events.json` and `_violations.json` managed by `ViolationDatabase`.
- **Audio artefacts**: WAV recordings stored under `recordings/` (date-stamped directories or flat layout).
- **Reports**: Generated artefacts land in `reports/`.

## External Services & Integrations
- **TensorFlow Hub**: Remote fetch of the YAMNet model on first run. Developers may need to clear `~/tensorflow_hub` cache when upgrading.
- **No other external APIs**: All processing is local to comply with evidence handling requirements.

## Operational Constraints
- Legal rules require accurate timestamps; all tooling must preserve sample rate and wall-clock calculations.
- Continuous violation detection currently uses a 10-second inter-bark gap threshold in code (`bark_detector/legal/tracker.py`). A 2025-09-17 analysis recommends expanding this tolerance (~33 seconds); update both code and documentation together when the decision is finalised.
- Platform-specific TensorFlow wheels force us to maintain the `install.py` workflow; avoid adding dependencies that complicate Apple Silicon vs Intel parity without justification.

## Related Documents
- `docs/architecture/tech-stack-alignment.md` – table of technologies for the latest legal-analysis epic.
- `docs/configuration.md` – canonical configuration keys and defaults.
- `docs/architecture/component-architecture.md` – illustrates interactions among CLI, tracker, database, and reporter modules.
