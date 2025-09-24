# Tech Stack

## Existing Technology Stack

Your current stack provides an excellent foundation for the enhancement:

| Category | Current Technology | Version | Usage in Enhancement | Notes |
|----------|-------------------|---------|---------------------|--------|
| **Language** | Python | 3.11.4 | PDF report generation service and enhanced CLI orchestration | No version change required - perfect compatibility |
| **Package Manager** | uv | latest | All development, testing, and deployment via `uv run` commands | Critical for maintaining cross-platform dependency management |
| **ML Framework** | TensorFlow + TensorFlow Hub | latest | No direct usage - leverages existing YAMNet results via `PersistedBarkEvent` data | Enhancement is downstream of ML processing |
| **Audio Processing** | Librosa, SoundFile | >=0.9.0 | No direct usage - operates on pre-analyzed violation data | Enhancement works with post-processed results |
| **Data Models** | Python dataclasses, typing | built-in | Extending existing `PersistedBarkEvent`, `Violation`, `ViolationReport` models | Zero model changes required |
| **Testing Framework** | pytest, pytest-mock | >=7.0.0 | New PDF generation tests integrated with existing 204-test suite | Maintains established testing patterns |
| **JSON Processing** | json (stdlib) | built-in | Reading violation data from established date-partitioned structure | Leverages existing ViolationDatabase patterns |
| **File Operations** | pathlib, os | built-in | PDF output to reports/ directory following existing patterns | Consistent with current file organization |

## New Technology Additions

Strategic additions for PDF generation capability:

| Technology | Version | Purpose | Rationale | Integration Method |
|------------|---------|---------|-----------|-------------------|
| **ReportLab** | >=4.0.4 | Professional PDF document generation | Industry standard for Python PDF creation, excellent legal document formatting capabilities | `uv add reportlab` - integrates via new `PDFReportGenerator` class |
| **matplotlib** | >=3.7.2 | Bark intensity visualization graphs | Already common in data science workflows, excellent chart generation for legal evidence | `uv add matplotlib` - used for embedded PDF charts |
| **Pillow (PIL)** | ~10.0 | Image processing for PDF graphics | Dependency of matplotlib, handles chart rendering and PDF embedding | Automatic dependency of matplotlib |

---
