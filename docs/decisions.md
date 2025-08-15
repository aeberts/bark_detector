# Architecture Decision Records

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

## ADR-007: Intelligent YAMNet Class Filtering for False Positive Reduction
**Date**: 2025-08-15  
**Status**: Accepted  
**Decision**: Implement intelligent filtering to exclude problematic YAMNet classes that cause false positives while preserving bark detection capability  
**Rationale**: Background audio analysis revealed that broad classes "Animal" and "Wild animals" were causing 100% false positives from environmental sounds (birds, insects, etc.) without contributing to true bark detection. Class-level analysis showed these classes provided no value for dog bark detection but significantly increased manual review burden for city complaints.  
**Implementation**: Enhanced bark detection system with comprehensive class-level analysis, excluded classes [67] "Animal" and [103] "Wild animals", maintained 11 focused dog-specific classes, added per-class confidence scoring and false positive analysis tools.  
**Results**: Achieved 54% reduction in false positives (13→6), improved precision from 58.1% to 71.4%, maintained effective bark detection with 50% recall, reduced manual review time for legal evidence preparation.  
**Consequences**: +Significantly reduced false positive rate, +Higher precision for city complaint submission, +Comprehensive class analysis tools for ongoing optimization; -Slightly reduced recall (acceptable trade-off), -Additional complexity in class management  
**Monitoring**: Future analysis may consider excluding "Livestock, farm animals, working animals" class if false positive patterns emerge