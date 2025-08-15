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