# Tech Stack Alignment

## Existing Technology Stack

The enhancement will be built using the project's current, established technologies.

| Category | Current Technology | Version | Usage in Enhancement | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Language** | Python | 3.11.4 | The refactored `LegalViolationTracker` and new reporting logic will be written in Python. | No version change required. |
| **Package Manager** | uv | - | Will be used to run all development, testing, and analysis commands. | Adherence to `uv run ...` is critical. |
| **ML Model** | Google YAMNet | 1 | The analysis engine will continue to use the existing detector's YAMNet predictions as the source of bark events. | The core detection logic is not being changed in this epic. |
| **Audio Processing**| Librosa, SoundFile| \>=0.9.0 | Used by the `LegalViolationTracker` to read and process audio from the `recordings/` directory for analysis. | Existing libraries are sufficient for the task. |
| **Testing** | pytest, pytest-mock| \>=7.0.0 | The existing test suite will be expanded to validate the bug fixes and new data persistence logic. | New integration tests are a key requirement for this epic. |

## New Technology Additions

No new technologies or major dependencies are required for this enhancement.

-----
