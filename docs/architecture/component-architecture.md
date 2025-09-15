# Component Architecture

## Modified Components

  * **`bark_detector/cli.py` (Orchestration Layer)**: Will be updated to house the "smart" logic for the consolidated `--violation-report` command and remove the deprecated command.
  * **`bark_detector/legal/tracker.py` (Analysis Engine)**: Will be refactored to be the sole engine for analysis, responsible for processing audio and persisting results via the `ViolationDatabase`.
  * **`bark_detector/legal/database.py` (Persistence Layer)**: Will be enhanced to manage all read/write operations for the new `_events.json` and `_violations.json` files.
  * **`bark_detector/utils/report_generator.py` (Reporting Layer)**: Will be refactored to read data exclusively from the `ViolationDatabase`, completely decoupling it from application logs.

## Component Interaction Diagram

```mermaid
sequenceDiagram
    actor User
    participant CLI as cli.py
    participant DB as database.py
    participant Tracker as tracker.py
    participant Reporter as report_generator.py

    User->>CLI: uv run ... --violation-report 2025-09-15
    CLI->>DB: Check for '2025-09-15_violations.json'
    DB-->>CLI: File not found
    CLI->>User: "Analysis not found. Running now..."
    CLI->>Tracker: analyze_date('2025-09-15')
    Tracker->>DB: save_events([...])
    Tracker->>DB: save_violations([...])
    CLI->>Reporter: generate_report('2025-09-15')
    Reporter->>DB: load_violations('2025-09-15')
    Reporter->>DB: load_events('2025-09-15')
    DB-->>Reporter: Violation & Event Data
    Reporter-->>CLI: Formatted Report Text
    CLI-->>User: Display Report
```

-----
