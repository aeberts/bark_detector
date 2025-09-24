# Source Tree

## Existing Project Structure (Preserved)

Your current organization provides the perfect foundation for PDF generation components:

```
bark_detector/
├── __init__.py                    # Package initialization
├── __main__.py                    # CLI entry point via python -m
├── cli.py                         # Command-line interface (Enhanced: --violation-report logic)
├── core/                          # ML detection and data models
│   ├── __init__.py
│   ├── detector.py                # YAMNet bark detection
│   └── models.py                  # BarkEvent, BarkingSession models
├── legal/                         # Legal evidence processing
│   ├── __init__.py
│   ├── database.py                # ViolationDatabase persistence
│   ├── models.py                  # PersistedBarkEvent, Violation models
│   └── tracker.py                 # LegalViolationTracker analysis
├── utils/                         # Shared utilities (Enhanced: PDF generation)
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   ├── helpers.py                 # Common utilities
│   ├── report_generator.py        # (DEPRECATED: LogBasedReportGenerator)
│   ├── tensorflow_suppression.py  # TensorFlow warning suppression
│   └── time_utils.py              # Time formatting utilities
├── recording/                     # Audio capture and conversion
├── calibration/                   # Calibration systems
```

## New File Organization

Strategic placement of PDF generation components within your established structure:

```
bark_detector/
├── utils/                         # Enhanced utilities module
│   ├── pdf_report_generator.py    # NEW: Professional PDF report generation
│   ├── chart_generator.py         # NEW: Bark intensity visualizations
│   ├── report_generator.py        # DEPRECATED: LogBasedReportGenerator (for removal)
│   └── pdf_templates.py           # NEW: PDF layout templates and formatting
├── legal/                         # No changes - existing models perfect
│   ├── database.py                # Enhanced: PDF-specific data access methods
├── cli.py                         # Enhanced: Smart --violation-report orchestration
```

## Integration Guidelines

**File Naming Consistency:**
- **snake_case naming** - Follows your established `report_generator.py`, `time_utils.py` patterns
- **Descriptive module names** - `pdf_report_generator.py` clearly indicates purpose and relationship to existing modules
- **Component-specific naming** - `chart_generator.py` follows your utilities naming convention

**Import/Export Patterns:**
```python
# Follows your established import patterns
from bark_detector.utils.pdf_report_generator import PDFReportGenerator
from bark_detector.utils.chart_generator import ChartGenerator
from bark_detector.legal.database import ViolationDatabase
from bark_detector.legal.models import Violation, PersistedBarkEvent

# Enhanced CLI integration
from bark_detector.cli import handle_violation_report_command
```

**Module Organization Principles:**
- **Single responsibility** - Each new module has focused purpose aligned with your existing architecture
- **Clear dependencies** - New modules only depend on existing stable interfaces (ViolationDatabase, models)
- **Testable isolation** - PDF generation components can be unit tested independently like existing utils/

---
