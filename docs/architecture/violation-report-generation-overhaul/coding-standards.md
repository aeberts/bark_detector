# Coding Standards

## Existing Standards Compliance

**Code Style:**
- **PEP 8 compliance** - Following your established formatting in existing utils/ and legal/ modules
- **Type hints** - Comprehensive typing annotations matching your legal/models.py patterns
- **Docstring standards** - Google-style docstrings consistent with existing ViolationDatabase and detector modules
- **Variable naming** - snake_case naming following your established patterns

**Linting Rules:**
- **Import organization** - Follow your established patterns (standard library, third-party, local imports)
- **Line length** - 88-character limit matching your existing code formatting
- **Function complexity** - Keep functions focused and testable like existing utils/ modules

**Testing Patterns:**
- **pytest framework** - Integrate with your existing 204-test suite architecture
- **Mock usage** - Use pytest-mock for external dependencies like existing TensorFlow mocking
- **Test organization** - Follow your established `test_utils/test_*.py` structure

**Documentation Style:**
- **Inline comments** - Minimal, focused on complex business logic like existing legal violation detection
- **Module docstrings** - Clear purpose statements following your established patterns
- **API documentation** - Type hints and docstrings sufficient for developer understanding

## Enhancement-Specific Standards

### PDF Generation Code Organization
```python
"""Professional PDF report generation for legal evidence collection.

This module provides PDF generation capabilities for bark detector violation
reports, replacing the deprecated LogBasedReportGenerator with professional
legal document formatting.
"""

from typing import List, Optional, Path
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

class PDFReportGenerator:
    """Generates professional PDF violation reports for legal evidence.

    Integrates with existing ViolationDatabase to consume violation data
    and produce legal-quality PDF reports for RDCO complaint submission.
    """
```

### Error Handling Standards
```python
# Follow existing error handling patterns from ViolationDatabase
class PDFGenerationError(Exception):
    """Exception raised when PDF generation fails."""
    pass

def generate_report(self, date: str) -> Path:
    """Generate PDF report with comprehensive error handling."""
    try:
        violations = self.violation_database.load_violations_new(date)
        events = self.violation_database.load_events(date)

        if not violations:
            logger.warning(f"No violations found for {date}")
            return self._generate_empty_report(date)

        return self._create_pdf_report(violations, events, date)

    except Exception as e:
        logger.error(f"PDF generation failed for {date}: {e}")
        raise PDFGenerationError(f"Cannot generate PDF report: {e}") from e
```

## Critical Integration Rules

**Existing API Compatibility:**
- **No changes to ViolationDatabase interfaces** - PDF generation consumes existing methods without modification
- **CLI signature preservation** - `--violation-report YYYY-MM-DD` maintains identical user interface
- **Configuration integration** - Use existing ConfigManager patterns for PDF generation settings

**Database Integration:**
- **Read-only data access** - PDF generation never modifies violation or event data
- **Error handling alignment** - Follow ViolationDatabase error patterns for missing/corrupt data
- **Transaction safety** - No database transactions required, purely file-based operations

**Error Handling:**
- **Graceful degradation** - PDF generation failures fall back to existing text report generation
- **User-friendly messages** - Error messages provide clear guidance for troubleshooting
- **Logging consistency** - Use established logger patterns from existing modules

---
