# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) aka `CC` when working with code in this repository.

# Project Overview
- Purpose: This project aims to develop a "bark detector" which will use machine learing to identify the sound of one or more barking dogs and will start making a medium-quality sound recording of the barking so the user can collect evidence in order to make a formal complaint to the local governing bodies.
- Current phase/status: Feature implementation.

## Technology Approach
- The system will use Machine Learning (ML) libraries to detect barking. The development platform is an M1-based Mac and it will be deployed on a single Intel-based Mac.
- The system will start recording when the ML detector is triggered and will continue to record until 30 seconds pass without barking being detected.
- **Package Manager**: This project uses `uv` for Python package management. Always prefix Python commands with `uv run` (e.g., `uv run pytest`, `uv run python -m bark_detector`).

# Project Structure
IMPORTANT: This project uses shared planning documents so CC can track changes with the user across sessions and so CC can effectively delegate tasks to subagents.

## Core Implementation
- @ bd.py - backwards compatibility wrapper and legacy entry point (deprecated, use `uv run python -m bark_detector`)
- @ bd_original.py - original monolithic implementation prior to T2 refactoring (reference for missing features)
- @ bark_detector/ - modern modular package structure (core/, calibration/, legal/, recording/, utils/)
- @ tests/ - comprehensive test suite (45 tests covering all modules with sophisticated ML/audio mocking)
- @ install.py - cross-platform install script (Intel-Mac vs M1 Mac detection)

## Documentation, Planning and Tracking
- @ README.md - user-facing project information, installation, usage
- @ CHANGELOG.md - development change log (keep succinct)
- @ docs/backlog.md - task tracking (unplanned, planned, completed)
- @ docs/features.md - feature requirements and specifications
- @ docs/project_overview.md - project description, goals, domain knowledge
- @ docs/project_status.md - current project phase and status summary
- @ docs/bugs.md - bug details and logs
- @ docs/decisions.md - architecture decision records
- @ docs/tests.md - details of tests to implement
- @ docs/improvements.md - details of improvements to implement

## Platform Requirements
- @ requirements-apple-silicon.txt - M1 Mac dependencies
- @ requirements-intel.txt - Intel Mac dependencies  
- @ requirements-fallback.txt - fallback requirements

# Development Commands
**Important**: This project uses `uv` for package management. Always use `uv run` prefix:

- **Run application**: `uv run python -m bark_detector` (modern) or `uv run bd.py` (legacy)
- **Run tests**: `uv run pytest tests/` or `uv run pytest tests/test_calibration/ -v`
- **Install dependencies**: `uv run install.py` (automatic platform detection)
- **Add packages**: `uv add package_name`
- **Audio conversion**: `uv run python -m bark_detector --convert-all 2025-08-03`

# Progress Tracking
- Track project status in the @docs/backlog.md file. Use ASCII text only - don't use emoji.
- After a task has been completed add a short summary to @CHANGELOG.md

# Templates & Workflows
- Session Restart: Read @docs/templates/session_restart.md
- PRD Creation: Read @docs/templates/prd_template.md
- User Stories: Read @docs/templates/user_story_template.md
- Architecture Decisions: Record in @docs/decisions.md

# Common Workflow Tasks

## ID Assignment
- Assign unique IDs to any tasks marked with `?` (e.g., `I?` → `I5`)

## Document Reading Priority
- Always check @docs/backlog.md `# Tasks to Discuss & Plan` for active priorities.
- Reference @docs/features.md for existing requirements when planning
- Check @docs/bugs.md for bug details and logs

## Task Completion Updates
- Mark task complete in @docs/backlog.md (move to completed section)
- Add brief summary to @CHANGELOG.md
- Update @docs/decisions.md with reasoning for changes

# Development Workflow

## Session Startup (only if user asks for task suggestions)
- **Apply**: Document Reading Priority and ID Assignment (see Common Workflow Tasks)
- Review @docs/backlog.md `# Tasks to Discuss & Plan` section for priorities
- Check @docs/project_status.md for current state  
- Suggest 3 tasks by ID from @docs/backlog.md (e.g., "I2", "T1", "F12") and brief description

## Task Planning (for new features/improvements)
**Only when user requests new work requiring planning:**
- **Apply**: Document Reading Priority and ID Assignment (see Common Workflow Tasks)
- If missing requirements: plan the feature (ask clarifying questions if needed)
- Use @docs/templates/prd_template.md or @docs/user_story_template.md as guides
- Keep planning minimal (think MVP)
- Present plan and wait for user approval before proceeding
- Update @docs/features.md with approved requirements

## During Implementation
- Use TodoWrite tool to track multi-step tasks
- Update todo status in real-time (pending → in_progress → completed)
- For complex work: provide progress updates every 2-3 steps
- If discovering better approach: pause and ask user approval
- Document technical decisions in @docs/decisions.md

## After Completion
**Required updates after any work:**
- **Apply**: Task Completion Updates (see Common Workflow Tasks)
- If architecture changed: update @docs/project_overview.md