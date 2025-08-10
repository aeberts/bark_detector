# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) aka `CC` when working with code in this repository.

# Project Overview
- Purpose: This project aims to develop a "bark detector" which will use machine learing to identify the sound of one or more barking dogs and will start making a medium-quality sound recording of the barking so the user can collect evidence in order to make a formal complaint to the local governing bodies.
- Current phase/status: Feature implementation.

## Technology Approach
- The system will use Machine Learning (ML) libraries to detect barking. The development platform is an M1-based Mac and it will be deployed on a single Intel-based Mac.
- The system will start recording when the ML detector is triggered and will continue to record until 30 seconds pass without barking being detected.

# Project Structure
IMPORTANT: This project uses shared planning documents so CC can track changes with the user across sessions and so CC can effectively delegate tasks to subagents.

- @ bd.py - main implementation file.
- @ install.py - custom install script which detects installation platform (Intel-Mac or M1 Mac)
- @ README.md - User-facing information about the project, installation, how to run the program, configuration, usage examples, additional notes.
- @ CHANGELOG.md - Record of development changes. Keep updates to this file as succinct as possible.
- @ docs/project_overview.md - project description, goals, background, domain notes, references.
- @ docs/features.md - feature requirements and specs.
- @ docs/backlog.md - Unplanned tasks, Planned tasks and features (including status), completed tasks
- @ docs/bugs.md - Additional notes about bugs mentioned in backlog.md
- @ requirements-apple-silicon.txt - M1 Mac package requirements for installation
- @ requirements-fallback.txt - Fallback requirements if the other requirements files do not load
- @ requirements-intel.txt - Intel-Mac package requirements for installation

# Progress Tracking
- Track project status in the @docs/backlog.md file

# Templates & Workflows
- PRD Creation: Read @docs/templates/prd_template.md
- User Stories: Read @docs/templates/user_story_template.md  
- Session Restart: Read @docs/templates/session_restart.md
- Architecture Decisions: Record in @docs/decisions.md

# Development Workflow

## Session Startup
1. Check @docs/project_status.md for current state
2. Review @docs/backlog.md for active priorities

## Plan and Review

First read and understand the planning documents @docs/project_status.md, @docs/project_overview.md, @docs/features.md, @docs/backlog.md, @docs/bugs.md

## Before Carrying out User Requests:
- Always start in plan mode.
- Check `@docs/project_status.md`, `@docs/backlog.md`, and suggest a task to work on next. Suggest two other task options.
- Next, check `@docs/features.md` to see if requirements have been created for the task you have been asked to work on.
- If there are no details in `@docs/features.md` or the other planning documents for the task, plan the feature (ask the user clarifying questions if necessary) and record any relevant discussions and decisions to the requirements or specification for that feature in `docs/features.md` using @docs/templates/prd_template.md, @docs/templates/user_story_template.md as necessary.
- Don't overplan - think MVP.
- Once you have presented the plan, stop and wait for the user to approve it. Do not continue until the user has approved the plan.
- Once the plan has been approved, write a summary of any plans, requirements, specifications and decisions to the relevant planning documents.

## While implementing
- Update the plan as you work if necessary. If during research or planning you find a better solution, stop and ask the user before carrying out this plan. 
- Record any changes to the plan in the planning documents as necessary.

## After completing work

- After completing work, update the relevant planning documents with:
    - Task completion status (@docs/backlog.md, @docs/features.md, @docs/project_status.md, @CHANGELOG.md)
    - New decisions made (@docs/decisions.md)
    - Any changes to architecture or approach (@docs/project_overview.md)
    - Notes for future collaboration (@docs/backlog.md - append to the `# Features to Discuss & Plan` section)