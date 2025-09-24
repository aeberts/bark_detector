# Bark Detector Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the Bark Detector codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents working on enhancements.

### Document Scope

Comprehensive documentation of entire system including ML-based bark detection, legal violation tracking, modular architecture, and cross-platform deployment patterns.

### Change Log

| Date       | Version | Description                 | Author       |
| ---------- | ------- | --------------------------- | ------------ |
| 2025-09-24 | 1.0     | Initial brownfield analysis | BMad Task    |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

- **Modern Entry**: `bark_detector/__main__.py` → `bark_detector/cli.py`
- **Legacy Entry**: `bd.py` (backwards compatibility wrapper with deprecation warnings)
- **Configuration**: `config.json`, `config-example.json`, `bark_detector/utils/config.py`
- **Core ML Detection**: `bark_detector/core/detector.py` (YAMNet integration with TensorFlow)
- **Data Models**: `bark_detector/core/models.py`
- **Legal Analysis**: `bark_detector/legal/tracker.py` (bylaw violation detection)
- **Platform Install**: `install.py` (Intel vs Apple Silicon detection and dependency management)
- **CLI Interface**: `bark_detector/cli.py` (comprehensive argument parsing and command routing)

### Deployment Critical Files

- **Cross-platform Requirements**: `requirements-apple-silicon.txt`, `requirements-intel.txt`, `requirements-fallback.txt`
- **TensorFlow Suppression**: `bark_detector/utils/tensorflow_suppression.py` (Intel Mac compatibility workaround)
- **Package Definition**: `pyproject.toml` (uv package manager configuration)

## High Level Architecture

### Technical Summary

The Bark Detector is a Python-based ML system that uses Google's YAMNet neural network model for real-time audio analysis. The system detects dog barking incidents, records evidence-quality audio, and generates legal compliance reports for municipal bylaw enforcement. Originally a 3,111-line monolithic file (`bd_original.py`), the system was refactored into a modular architecture while maintaining full backwards compatibility.

### Actual Tech Stack (from pyproject.toml/requirements)

| Category          | Technology      | Version | Notes                                    |
| ----------------- | --------------- | ------- | ---------------------------------------- |
| Runtime           | Python          | 3.9-3.11| STRICT: TensorFlow requires <3.12        |
| Package Manager   | uv              | latest  | Fast Python package installer/resolver   |
| ML Framework      | TensorFlow      | 2.12.0  | Platform-specific (macos vs standard)   |
| ML Model Hub      | TensorFlow Hub  | 0.13.0  | YAMNet pre-trained model access         |
| Audio Processing  | librosa         | 0.9-0.11| Core audio analysis and preprocessing    |
| Audio I/O         | pyaudio         | 0.2.11+ | Real-time microphone input              |
| Audio Files       | soundfile       | 0.10.0+ | WAV/M4A/MP3 file reading/writing       |
| Scientific Computing | numpy       | 1.20-1.25| Core numerical operations               |
| Scientific Computing | scipy       | 1.8-1.12 | Signal processing utilities              |
| Testing           | pytest          | 8.4.1+  | Comprehensive test suite (111+ tests)   |

### Repository Structure Reality Check

- **Type**: Modular monorepo with legacy compatibility layer
- **Package Manager**: uv (modern, fast Python package management)
- **Notable**: Maintains dual entry points for backwards compatibility; intelligent platform detection for TensorFlow variants

## Source Tree and Module Organization

### Project Structure (Actual)

```text
bark_detector/
├── bark_detector/              # Modern modular package (3.0 architecture)
│   ├── __init__.py            # Main component exports
│   ├── __main__.py            # Entry point: python -m bark_detector
│   ├── cli.py                 # Comprehensive CLI with 20+ commands
│   ├── core/                  # Core ML detection logic
│   │   ├── detector.py        # AdvancedBarkDetector (YAMNet integration)
│   │   └── models.py          # BarkEvent, BarkingSession, CalibrationProfile
│   ├── legal/                 # Bylaw violation detection
│   │   ├── tracker.py         # LegalViolationTracker (main analysis engine)
│   │   ├── database.py        # ViolationDatabase (JSON persistence)
│   │   └── models.py          # ViolationReport, LegalSession, PersistedBarkEvent
│   ├── calibration/           # Detection accuracy tuning
│   │   ├── file_calibration.py # Process pre-recorded samples with ground truth
│   │   ├── realtime_calibration.py # Interactive spacebar calibration
│   │   └── profiles.py        # Save/load calibration settings
│   ├── recording/             # Audio recording management
│   │   ├── recorder.py        # Session-based recording with gap detection
│   │   ├── converter.py       # M4A/MP3 to WAV conversion
│   │   └── manual_recorder.py # Manual recording functionality
│   └── utils/                 # Shared utilities
│       ├── config.py          # JSON configuration management
│       ├── tensorflow_suppression.py # CRITICAL: Intel Mac TF logging fixes
│       ├── time_utils.py      # Timestamp parsing and conversion
│       ├── report_generator.py # Enhanced violation reports
│       └── helpers.py         # NumPy serialization, logging setup
├── bd.py                      # LEGACY: Backwards compatibility wrapper
├── bd_original.py             # REFERENCE: Original 3,111-line monolith
├── config.json                # Primary configuration file
├── install.py                 # CRITICAL: Platform-specific dependency installer
├── recordings/                # Date-organized audio files (YYYY-MM-DD/)
├── violations/                # Date-organized violation data (JSON)
├── reports/                   # Generated violation reports
├── logs/                      # Date-organized log files
├── tests/                     # 111+ comprehensive tests
├── docs/                      # Extensive documentation (20+ files)
├── samples/                   # Test audio files with ground truth
└── scripts/                   # Migration and utility scripts
```

### Key Modules and Their Purpose

- **Core Detection**: `bark_detector/core/detector.py` - YAMNet ML model integration with dual sensitivity system (real-time: 0.68, analysis: 0.30)
- **Legal Compliance**: `bark_detector/legal/tracker.py` - City of Kelowna bylaw violation detection with configurable thresholds
- **Configuration**: `bark_detector/utils/config.py` - JSON-based configuration with CLI override precedence
- **Platform Compatibility**: `bark_detector/utils/tensorflow_suppression.py` - Critical Intel Mac TensorFlow logging workaround
- **CLI Interface**: `bark_detector/cli.py` - 800+ line comprehensive command interface with argument validation

## Data Models and APIs

### Core Data Models

Referenced from actual model files:

- **BarkEvent**: See `bark_detector/core/models.py` - Individual bark detection with confidence, intensity, timestamps
- **BarkingSession**: Groups bark events using gap thresholds (10s recording, 5min legal)
- **ViolationReport**: See `bark_detector/legal/models.py` - Legal violation structure for city complaints
- **PersistedBarkEvent**: Enhanced event model with unique IDs for forensic analysis
- **CalibrationProfile**: Saved sensitivity settings with performance metrics

### API Specifications

- **CLI Interface**: 20+ commands via `argparse` in `bark_detector/cli.py`
- **Configuration API**: JSON-based config via `ConfigManager` class
- **No REST API**: Currently CLI-only interface (potential future enhancement)

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Platform-Specific TensorFlow Complexity**: Intel Macs require extensive logging suppression due to TensorFlow debug output flooding. Workaround in `tensorflow_suppression.py` must be called BEFORE TensorFlow imports.

2. **Dual Entry Point Maintenance**: Both `bd.py` (legacy) and `python -m bark_detector` (modern) must be maintained for backwards compatibility. Legacy warnings present but not enforced.

3. **YAMNet Cache Corruption**: TensorFlow Hub model cache occasionally corrupts, requiring manual cleanup (`rm -rf /tmp/tfhub_modules`). No automatic detection/recovery implemented.

4. **Configuration Complexity**: Three-tier precedence system (CLI > config file > defaults) adds complexity to parameter handling across 20+ CLI arguments.

5. **Version Lock Dependencies**: TensorFlow 2.12.0 hard pinned due to compatibility issues; Python <3.12 required for TensorFlow compatibility.

### Workarounds and Gotchas

- **Environment Setup**: Must use `uv run` prefix for all Python commands due to package manager choice
- **TensorFlow Logging**: Aggressive suppression required on Intel Macs - see `tensorflow_suppression.py`
- **Audio Format Constraints**: YAMNet requires 16kHz WAV; automatic conversion from M4A/MP3 but quality loss possible
- **File Permissions**: Recording directories auto-created but may fail with permission issues on some systems
- **Gap Threshold Hierarchy**: Complex 10s vs 5min gap logic for recording vs legal violations - critical for legal compliance

### Migration from Monolithic Architecture

The system was refactored from a 3,111-line monolithic file (`bd_original.py`) to modular architecture. Key technical debt from this migration:

- **Incomplete Test Migration**: Some edge case behaviors may differ between old/new implementations
- **Performance Regression Potential**: Modular imports may have minimal performance impact vs monolithic
- **Backwards Compatibility Layer**: `bd.py` wrapper adds maintenance overhead

## Integration Points and External Dependencies

### External Services

| Service        | Purpose             | Integration Type | Key Files                                |
| -------------- | ------------------- | ---------------- | ---------------------------------------- |
| TensorFlow Hub | YAMNet ML Model     | HTTP Download    | `bark_detector/core/detector.py`         |
| File System    | Audio Storage       | Direct I/O       | `recordings/`, `violations/`, `reports/` |
| System Audio   | Microphone Input    | PyAudio          | `bark_detector/core/detector.py`         |
| JSON Config    | Configuration       | File System      | `config.json`, `bark_detector/utils/config.py` |

### Internal Integration Points

- **CLI to Core**: `bark_detector/cli.py` → `bark_detector/core/detector.py`
- **Detection to Legal**: `BarkEvent` → `LegalViolationTracker` → `ViolationReport`
- **Configuration Flow**: `ConfigManager` → CLI args → Detector initialization
- **Audio Pipeline**: PyAudio → YAMNet → BarkEvent → Recording/Analysis
- **Cross-Platform**: `install.py` detects platform → appropriate TensorFlow variant

### Critical Dependencies and Constraints

- **YAMNet Model**: 16kHz audio sampling rate REQUIRED
- **TensorFlow Version**: Exactly 2.12.0 due to API compatibility
- **Python Version**: 3.9-3.11 ONLY (TensorFlow constraint)
- **Audio Hardware**: Microphone required for real-time detection
- **Disk Space**: Audio recordings accumulate (WAV format, ~1MB/minute)

## Development and Deployment

### Local Development Setup

**CRITICAL**: Must use the intelligent installer to handle platform detection:

1. Clone repository
2. Run `python install.py` (detects Apple Silicon vs Intel Mac automatically)
3. Activate virtual environment: `source .venv/bin/activate` (if not using uv)
4. Use `uv run` prefix for all commands

**Known Setup Issues**:
- PyAudio may require additional system libraries on Linux
- TensorFlow Hub model downloads on first run (large download)
- Permission issues with recording directories

### Build and Deployment Process

- **No Build Step**: Pure Python, direct execution
- **Dependency Management**: `uv` package manager with `uv.lock`
- **Configuration**: Copy `config-example.json` to `config.json` and customize
- **Platform Detection**: `install.py` handles Intel vs Apple Silicon automatically
- **Testing**: `uv run pytest` (111+ tests with ML mocking)

### Package Manager Integration

```bash
# Modern development workflow
uv run python -m bark_detector                    # Start monitoring
uv run python -m bark_detector --config myconfig.json
uv run pytest tests/                             # Run all tests
uv run python install.py                         # Platform setup

# Legacy compatibility (shows deprecation warning)
uv run bd.py --profile myprofile                 # Still works
```

## Testing Reality

### Current Test Coverage

- **Unit Tests**: 111+ tests with comprehensive mocking
- **ML Model Mocking**: Sophisticated YAMNet/TensorFlow mocking for CI/CD
- **Integration Tests**: CLI command validation and end-to-end workflows
- **Sample-Based Testing**: Real audio files with ground truth annotations (77.6% F1 score)
- **Platform Testing**: Tests for both Intel and Apple Silicon requirements

### Test Architecture and Patterns

- **Framework**: pytest with extensive fixtures
- **Mocking Strategy**: Mock TensorFlow/YAMNet at API boundary, not internals
- **File Fixtures**: Uses `conftest.py` with comprehensive data model fixtures
- **CLI Testing**: `subprocess` execution of actual CLI commands
- **Sample Data**: `samples/` directory with real bark recordings and annotations

### Running Tests

```bash
uv run pytest                                   # All tests
uv run pytest tests/test_core/ -v              # Core detection tests
uv run pytest tests/test_legal/ -v             # Legal violation tests
uv run pytest tests/test_integration/ -v       # Integration tests
uv run pytest --cov=bark_detector              # Coverage report
```

### Test Quality Insights

**Strengths**:
- Comprehensive ML model mocking prevents external dependencies in CI
- Real sample-based validation with ground truth
- Cross-platform test coverage for platform-specific code

**Weaknesses**:
- No performance/load testing for extended monitoring periods
- Limited testing of TensorFlow Hub model download/cache scenarios
- Manual testing still required for actual audio hardware validation

## Integration Considerations for Future Enhancements

### Files Requiring Modification for New Features

**For Detection Enhancements**:
- `bark_detector/core/detector.py` - Core ML detection logic
- `bark_detector/core/models.py` - Data model updates
- `bark_detector/cli.py` - New CLI arguments
- `config-example.json` - Configuration templates

**For Legal/Reporting Features**:
- `bark_detector/legal/tracker.py` - Violation detection logic
- `bark_detector/legal/models.py` - Legal data structures
- `bark_detector/utils/report_generator.py` - Report formatting

**For Platform/Deployment**:
- `install.py` - New platform support
- `requirements-*.txt` - Dependency management
- `bark_detector/utils/tensorflow_suppression.py` - Platform-specific fixes

### New Files/Modules That Would Be Needed

**For Web Interface**:
- `bark_detector/web/` - New module for web API/interface
- `bark_detector/api/` - REST API endpoints
- New requirements for web frameworks

**For Mobile Integration**:
- Platform-specific audio interfaces
- Mobile app deployment configurations
- Cross-platform audio compatibility layer

### Integration Architecture Patterns

- **Configuration-Driven**: All thresholds and parameters via JSON config
- **Module Isolation**: Clear separation between ML detection, legal analysis, and I/O
- **Backwards Compatibility**: New features must maintain legacy CLI support
- **Platform Abstraction**: Platform-specific code isolated in utils/ and install.py

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

```bash
# Primary workflows
uv run python -m bark_detector                          # Start real-time monitoring
uv run python -m bark_detector --config config.json    # Use custom config
uv run python -m bark_detector --create-config test.json # Generate config template

# Analysis and reporting
uv run python -m bark_detector --analyze-violations 2025-09-24
uv run python -m bark_detector --violation-report 2025-09-24 2025-09-24
uv run python -m bark_detector --enhanced-violation-report 2025-09-24

# Calibration workflows
uv run python -m bark_detector --calibrate samples/
uv run python -m bark_detector --profile myprofile
uv run python -m bark_detector --list-profiles

# File management
uv run python -m bark_detector --convert-all 2025-09-24
uv run python -m bark_detector --list-convertible 2025-09-24

# Development and testing
uv run pytest                                           # Run full test suite
uv run pytest tests/test_core/ -v                      # Core module tests
uv run python install.py                               # Platform setup
```

### Debugging and Troubleshooting

- **Logs**: Check `logs/YYYY-MM-DD/` for date-organized application logs
- **Debug Mode**: Set `DEBUG=1` environment variable for verbose logging
- **YAMNet Cache Issues**: `rm -rf /tmp/tfhub_modules` to clear corrupted model cache
- **TensorFlow Debug Output**: Already suppressed via `tensorflow_suppression.py`
- **Configuration Validation**: Use `--create-config` to generate valid template
- **Audio Issues**: Check PyAudio installation and microphone permissions
- **Platform Issues**: Re-run `python install.py` to reinstall platform-specific dependencies

### Emergency Recovery Commands

```bash
# Reset TensorFlow model cache
rm -rf /tmp/tfhub_modules
find /var/folders -name "tfhub_modules" -type d 2>/dev/null | xargs rm -rf

# Reset configuration to defaults
uv run python -m bark_detector --create-config config.json

# Validate installation
uv run python -c "import bark_detector; print('Import successful')"

# Test core functionality without audio hardware
uv run pytest tests/test_core/test_detector.py -v
```

### Performance Monitoring

- **Memory Usage**: Monitor for TensorFlow memory leaks during extended monitoring
- **Disk Usage**: Check `recordings/` directory growth (WAV files ~1MB/minute)
- **CPU Usage**: YAMNet inference is CPU-intensive on Intel Macs
- **File Handles**: Monitor file descriptor usage with large recording sessions

This brownfield architecture document reflects the actual state of a mature, production-ready ML system with comprehensive legal compliance features, extensive test coverage, and sophisticated cross-platform deployment capabilities. The system successfully balances backwards compatibility with modern modular architecture while addressing real-world deployment challenges through intelligent platform detection and workaround implementations.