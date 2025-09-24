# CLAUDE.md - BMad Method Integration
This file provides guidance to Claude Code (claude.ai/code) when working with the Bark Detector project using BMad Method workflows.

# Project Overview
- Purpose: ML-based "bark detector" for legal evidence collection using YAMNet neural network to identify dog barking and create audio recordings for formal complaints to municipal authorities (City of Kelowna/RDCO).
- Status: Feature implementation phase with modular architecture and comprehensive legal compliance system.

## BMad Method Configuration
- Core config: `.bmad-core/core-config.yaml` (drives agent behavior)
- Agent activation: Use BMad agents with `@agent-name` or `/agent-name` syntax
- Epic-driven development: BMad workflow with Story → Implementation → QA pipeline
- Project documentation: See `docs/architecture/` for comprehensive technical reference

## Technology Approach
- ML Detection: Google YAMNet neural network via TensorFlow Hub for real-time bark classification
- Platform: Cross-platform (M1 Mac development, Intel Mac deployment)
- Package Manager: **uv** for Python package management - ALWAYS prefix commands with `uv run`
- Legal Compliance: City of Kelowna bylaw violation detection (5min continuous, 15min sporadic thresholds)

# BMad-Compliant Project Structure

## Core Implementation (from docs/architecture/)
- @ bark_detector/ - Modern modular package (core/, calibration/, legal/, recording/, utils/)
- @ bd.py - Legacy entry point with deprecation warning (backwards compatibility)
- @ bd_original.py - Original 3,111-line monolith (reference for missing features)
- @ tests/ - Comprehensive test suite (111+ tests with ML/audio mocking)
- @ install.py - Cross-platform installer with Intel/Apple Silicon detection

## BMad Method Documentation Structure
- @ docs/architecture/ - **PRIMARY TECHNICAL REFERENCE** (BMad-compliant sharded architecture components)
- @ docs/archive/brownfield-architecture.md - Historical master document (archived reference)
- @ docs/prd/ - Sharded PRD epics (if configured via core-config.yaml)
- @ docs/architecture/ - Sharded architecture components (if configured)
- @ docs/stories/ - BMad story workflow (Draft → Approved → InProgress → Review → Done)
- @ .bmad-core/ - BMad templates, tasks, checklists, and agent definitions

## Legacy Documents (for historical reference only)
- @ docs/backlog.md - Pre-BMad task tracking (superseded by Epic/Story workflow)
- @ docs/templates/ - Pre-BMad templates (superseded by .bmad-core/templates/)
- @ docs/features.md, docs/bugs.md, docs/decisions.md - Historical planning documents

## Platform Requirements
- @ requirements-apple-silicon.txt - Apple Silicon Mac dependencies
- @ requirements-intel.txt - Intel Mac dependencies
- @ requirements-fallback.txt - Fallback requirements

# Development Commands (uv Package Manager)

**CRITICAL**: Always use `uv run` prefix for all Python commands:

- **Run application**: `uv run python -m bark_detector` (modern) or `uv run bd.py` (legacy)
- **Run tests**: `uv run pytest tests/` or `uv run pytest tests/test_calibration/ -v`
- **Install dependencies**: `uv run install.py` (automatic platform detection)
- **Add packages**: `uv add package_name`
- **Audio conversion**: `uv run python -m bark_detector --convert-all 2025-08-03`

# BMad Agent Workflow

## Story Creation and Implementation
1. **Story Creation**: Use BMad Scrum Master agent (`@sm`) with `*draft` command
2. **Implementation**: Use BMad Developer agent (`@dev`) following story tasks
3. **QA Review**: Use BMad QA agent (`@qa`) for review and approval
4. **Status Flow**: Draft → Approved → InProgress → Review → Done

## Epic-Driven Development
- Epic creation from sharded PRD components
- Story breakdown following BMad templates
- Sequential implementation with proper handoffs
- QA gates at story completion

# Common BMad Agent Commands

## BMad Master Commands (this agent)
- `*help` - Show available commands
- `*task {task-name}` - Execute specific BMad task
- `*create-doc {template}` - Create document from template
- `*document-project` - Comprehensive project documentation audit
- `*execute-checklist {checklist}` - Run specific checklist

## Development Workflow Integration
- **Code Changes**: Follow docs/architecture/ for module understanding
- **Testing**: 111+ test suite with sophisticated ML mocking (`uv run pytest`)
- **Configuration**: JSON-based config system with precedence (CLI > config file > defaults)
- **Legal Analysis**: YAMNet-based violation detection for municipal compliance

# Technical Constraints (from docs/architecture/)

## Hard Dependencies
- Python 3.9-3.11 (TensorFlow requirement, NOT 3.12+)
- TensorFlow 2.12.0 (platform-specific: tensorflow-macos vs tensorflow)
- YAMNet model via TensorFlow Hub (16kHz audio requirement)
- uv package manager for dependency resolution

## Platform-Specific Workarounds
- TensorFlow logging suppression utility for Intel Mac compatibility
- Separate requirements files for Apple Silicon vs Intel Macs
- YAMNet model cache corruption recovery (`rm -rf /tmp/tfhub_modules`)

# Development Workflow Best Practices

## BMad Method Compliance
- Reference docs/architecture/ for technical implementation details
- Use BMad agents for specialized workflows (SM for stories, Dev for implementation, QA for review)
- Follow Epic → Story → Implementation → QA pipeline
- Maintain story status through BMad workflow states

## Adding New Features with BMad Integration

### For New Epics:
1. **Determine Epic Number:** Check existing files in `docs/prd/epic-*.md` to find next available number
2. **Create Epic File:** Use format `docs/prd/epic-{n}-{feature-name}.md` (e.g., `epic-4-advanced-reporting.md`)
3. **Use BMad Agents:**
   - `@sm` (Scrum Master) for epic/story creation
   - `@dev` (Developer) for implementation
   - `@qa` (QA) for review and testing

### Document Organization Rules:
- **Primary Architecture:** `docs/architecture/` (BMad-compliant sharded components)
- **Individual Epics:** `docs/prd/epic-{n}-*.md` (one file per epic)
- **Stories:** `docs/stories/` (BMad story lifecycle management)
- **Archives:** `docs/archive/` (historical/deprecated documents)

### Epic Numbering Guidelines:
- Epic numbers must be sequential (1, 2, 3, 4...)
- Check existing epic files before creating new ones
- Never skip numbers (creates BMad agent confusion)
- Use descriptive but concise epic names

## Code Quality Standards
- All tests must pass: `uv run pytest tests/`
- Follow existing architectural patterns documented in docs/architecture/
- Maintain backwards compatibility via bd.py wrapper
- Use configuration system for customizable parameters

## Documentation Updates
- Update docs/architecture/ components for significant architectural changes
- Create/update stories in docs/stories/ for new features
- Use BMad templates for consistent documentation structure
- Archive legacy documents rather than modifying them

---

*This CLAUDE.md is BMad Method compliant and should be used with BMad agents for optimal workflow integration. For detailed technical reference, see docs/architecture/.*