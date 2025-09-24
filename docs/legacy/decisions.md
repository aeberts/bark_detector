# ⚠️ LEGACY DOCUMENT - DEPRECATED ⚠️

**STATUS**: This document has been SUPERSEDED by BMad Method documentation
**REPLACEMENT**: Use `docs/brownfield-architecture.md` for current architectural decisions
**DO NOT USE**: This pre-BMad ADR format conflicts with current BMad documentation standards
**DATE ARCHIVED**: 2025-09-24

---

## BMad Method Migration Guide

This decisions.md was part of pre-BMad architecture decision tracking that has been replaced by:

- **Current Architecture**: Comprehensive documentation in `docs/brownfield-architecture.md`
- **Epic-Driven Architecture**: Architectural decisions captured in epic planning (`docs/prd/`)
- **Story-Level Decisions**: Technical decisions documented in BMad stories (`docs/stories/`)
- **Living Documentation**: Architecture maintained as part of ongoing BMad workflow

**For Current Work**:
- Architecture questions → Reference `docs/brownfield-architecture.md`
- New architectural decisions → Document in relevant epics/stories
- Technical constraints → See brownfield architecture document

---

# ARCHIVED: Architecture Decision Records

## ADR-001: YAMNet for Bark Detection
**Date**: 2025-07-28  
**Status**: Accepted  
**Decision**: Use Google's YAMNet neural network model for audio classification  
**Rationale**: Pre-trained on large dataset, handles diverse audio environments, TensorFlow Hub integration  
**Consequences**: +Good accuracy, +Fast inference; -Requires TensorFlow, -16kHz audio preprocessing needed

## ADR-002: 16kHz Audio Processing  
**Date**: 2025-07-29  
**Status**: Accepted  
**Decision**: Standardize on 16kHz WAV format for all audio processing  
**Rationale**: YAMNet requirement, good balance of quality vs file size for evidence collection  
**Consequences**: +Consistent processing, +ML model compatibility; -Requires audio conversion step

## ADR-003: Gap Threshold Hierarchy
**Date**: 2025-08-01  
**Status**: Accepted  
**Decision**: Use 10-second gaps for recording sessions, 5-minute gaps for legal violations  
**Rationale**: Balances storage efficiency with legal evidence requirements for City of Kelowna  
**Consequences**: +Clear violation boundaries, +Efficient storage; -Complex session logic

## ADR-004: Single-File Architecture (bd.py)
**Date**: 2025-07-30  
**Status**: Under Review  
**Decision**: Initially implement all functionality in single bd.py file  
**Rationale**: Rapid prototyping, simple deployment, easier debugging  
**Consequences**: +Fast development, +Simple deployment; -Hard to maintain, -Poor separation of concerns  
**Note**: Refactoring to modules planned for maintainability

## ADR-005: JSON-Based Configuration
**Date**: 2025-08-02  
**Status**: Proposed  
**Decision**: Move to JSON configuration file for all settings  
**Rationale**: Better user experience, persistent settings, easier profile management  
**Consequences**: +User-friendly, +Persistent config; -Additional file management

## ADR-006: Comprehensive Testing Infrastructure
**Date**: 2025-08-14  
**Status**: Accepted  
**Decision**: Implement pytest-based testing with sophisticated mocking for ML components  
**Rationale**: Ensure reliability of bark detection system, legal compliance features, and modular architecture. Enable confident refactoring and feature development without breaking existing functionality.  
**Consequences**: +High test coverage (38 core tests), +Reliable CI/CD pipeline, +Safe refactoring; -Additional development overhead for test maintenance  
**Technical Details**: Uses unittest.mock for YAMNet/TensorFlow simulation, comprehensive fixtures for data models, integration testing for CLI workflows

## ADR-008: JSON-Based Configuration System
**Date**: 2025-08-18  
**Status**: Accepted  
**Decision**: Implement comprehensive JSON-based configuration system to replace CLI-only parameter management  
**Rationale**: Users needed persistent configuration storage to avoid complex CLI commands for repeated operations. The CLI-only approach was becoming unwieldy with 20+ parameters across detection, calibration, output, scheduling, and legal features. Configuration files enable better user experience and reproducible setups.  
**Implementation**: Created ConfigManager with structured JSON configuration organized into logical sections (detection, output, calibration, scheduling, legal). Implemented automatic file search in standard locations, CLI integration with `--config` and `--create-config` options, parameter validation with helpful error messages, and complete precedence handling (CLI > config file > defaults).  
**Technical Details**: Uses dataclass-based configuration structure with validation, supports all existing CLI parameters, maintains 100% backward compatibility, includes comprehensive test coverage (32 tests), and provides example configuration templates with documentation.  
**Benefits**: +Simplified user workflows for complex setups, +Persistent configuration storage, +Better organization of related parameters, +Template generation for new users, +Comprehensive validation with clear error messages, +Maintains full CLI flexibility  
**Consequences**: +Significantly improved user experience, +Easier configuration management, +Better support for different use cases; -Additional complexity in configuration loading system, -Need to maintain parallel CLI and config file parameter handling  
**Future Considerations**: Configuration system provides foundation for future features like automated scheduling and profile-based monitoring

## ADR-007: Intelligent YAMNet Class Filtering for False Positive Reduction
**Date**: 2025-08-15  
**Status**: Accepted  
**Decision**: Implement intelligent filtering to exclude problematic YAMNet classes that cause false positives while preserving bark detection capability  
**Rationale**: Background audio analysis revealed that broad classes "Animal" and "Wild animals" were causing 100% false positives from environmental sounds (birds, insects, etc.) without contributing to true bark detection. Class-level analysis showed these classes provided no value for dog bark detection but significantly increased manual review burden for city complaints.  
**Implementation**: Enhanced bark detection system with comprehensive class-level analysis, excluded classes [67] "Animal" and [103] "Wild animals", maintained 11 focused dog-specific classes, added per-class confidence scoring and false positive analysis tools.  
**Results**: Achieved 54% reduction in false positives (13→6), improved precision from 58.1% to 71.4%, maintained effective bark detection with 50% recall, reduced manual review time for legal evidence preparation.  
**Consequences**: +Significantly reduced false positive rate, +Higher precision for city complaint submission, +Comprehensive class analysis tools for ongoing optimization; -Slightly reduced recall (acceptable trade-off), -Additional complexity in class management  
**Monitoring**: Future analysis may consider excluding "Livestock, farm animals, working animals" class if false positive patterns emerge

## ADR-009: ML-Based Violation Analysis Integration
**Date**: 2025-08-18  
**Status**: Accepted  
**Decision**: Integrate advanced YAMNet bark detection into violation analysis system instead of simple file duration checks  
**Problem**: The original `--analyze-violations` functionality used simplistic file duration analysis (files >5 minutes = violation) rather than analyzing actual audio content. This approach was unreliable because it couldn't distinguish between actual barking and silent files, background noise, or other non-bark audio content. Legal evidence collection requires accurate detection of actual barking events to meet City of Kelowna bylaw requirements.  
**Rationale**: Legal evidence must be based on actual bark detection rather than assumptions. The advanced YAMNet bark detection system (with 54% false positive reduction) was already implemented but not integrated into violation analysis. Users needed accurate violation reports based on real audio content analysis for city complaint submissions.  
**Implementation**: Completely rewrote `LegalViolationTracker.analyze_recordings_for_date()` to use advanced bark detection pipeline: load audio files → YAMNet ML analysis → bark event detection → session creation using gap threshold hierarchy → violation detection (continuous: 5+ min sessions, sporadic: 15+ min across multiple sessions within 5-min gaps) → comprehensive violation reports with metadata.  
**Technical Details**: Added `_events_to_sessions()`, `_create_session_from_events()`, `_detect_sporadic_violations()`, `_group_sessions_for_sporadic_analysis()`, and `_create_sporadic_violation_report()` methods. Enhanced test coverage with proper detector mocking for all integration scenarios.  
**Results**: Violation analysis now uses same advanced ML model as real-time detection, providing accurate bark event detection with confidence scores, proper session grouping based on gap thresholds, comprehensive sporadic violation detection (15+ minutes across sessions), and detailed metadata for legal evidence submission.  
**Benefits**: +Accurate audio content analysis rather than file duration guessing, +Consistent detection quality between real-time and post-processing modes, +Comprehensive sporadic violation detection meeting bylaw requirements, +Detailed confidence scoring and metadata for legal evidence, +Full integration test coverage ensuring reliability  
**Consequences**: +Much more accurate violation detection for legal evidence, +Consistent ML-based analysis across all system components, +Better legal compliance with city requirements; -Increased processing time for violation analysis (acceptable for accuracy gain), -More complex integration testing requirements  
**Legal Impact**: System now provides reliable evidence that can withstand legal scrutiny, with actual bark detection rather than file duration assumptions, supporting City of Kelowna complaint requirements for exact times, durations, and proof of barking incidents