# Features

## FEATURE: Gap Threshold Hierarchy
### User Requirements
- System needs to group individual barks into manageable recordings for storage efficiency
- System must detect legal violations by grouping related barking incidents
### Specifications
- Implements the Gap Threshold Hierarchy as defined in project_overview.md
- Uses 10-second gaps for Recording Sessions and 5-minute gaps for Legal Sporadic Sessions
- See project_overview.md for detailed legal logic examples and business rules

## FEATURE: Bylaw Violation Detection
### User Requirements
- Automatically detect when barking meets City of Kelowna bylaw violation criteria
- Flag incidents that can be used as legal evidence
### Specifications
- Auto-flag 5-minute continuous barking violations
- Auto-flag 15-minute sporadic barking violations within a legal session
- Uses Gap Threshold Hierarchy rules defined in project_overview.md (5-minute legal gap threshold)
- Implements violation detection algorithm using LegalViolationTracker class

### Violation Detection Algorithm Implementation
```python
class LegalViolationTracker:
    def __init__(self):
        self.current_sporadic_session = None
        self.sporadic_start_time = None
        self.total_bark_duration_in_session = 0
        self.legal_gap_threshold = 300  # 5 minutes (see project_overview.md)
        
    def process_recording_session(self, session):
        gap_since_last = session.start_time - self.last_bark_time
        
        if gap_since_last > self.legal_gap_threshold:
            # 5+ minute gap - start new legal session
            self._check_sporadic_violation()  # Check if previous session was violation
            self._start_new_sporadic_session(session)
        else:
            # Continue current sporadic session
            self.total_bark_duration_in_session += session.total_bark_duration
            
    def _check_sporadic_violation(self):
        if self.total_bark_duration_in_session >= 900:  # 15 minutes
            self._log_sporadic_violation()
```

## FEATURE: Legal Evidence Collection
### User Requirements
- Generate documentation suitable for City of Kelowna complaint submission
- Collect evidence across multiple days as required by city bylaws
- Package audio recordings with proper metadata
### Specifications
- Generate city-compliant evidence reports
- Track violations across 3-5 day periods
- Create PDF reports ready for city submission
- Organize audio evidence by incident with metadata
- Record exact dates, times, and durations of incidents

### Evidence Management System
- **File Organization**: Recordings organized by legal incidents with metadata
- **Multi-day Collection**: Evidence collection across 3-5 day periods as required by bylaws
- **Report Generation**: PDF reports formatted for City of Kelowna submission including exact dates, times, and durations
- **Audio Packaging**: Audio evidence packaged with proper documentation for legal submission

## FEATURE: Automated Scheduling System
### User Requirements
- System should start monitoring automatically at specified times
- Save monitoring profiles for repeated use
### Specifications
- Auto-start monitoring at 6:20am with saved profile
- Support saved monitoring configurations
- Enable scheduled operation for multi-day evidence collection

## FEATURE: Audio Recording Management
### User Requirements
- Record medium-quality audio of barking incidents
- Manage storage efficiently for extended monitoring periods
### Specifications
- Use decibel threshold approach for bark detection (no machine learning)
- Continue recording until 30 seconds pass without sounds above threshold
- Organize recordings by legal incidents
- Maintain audio quality suitable for legal evidence

### Audio Processing Architecture
- **Detection Method**: Simple decibel threshold approach (no machine learning on device)
- **Real-time Processing**: Uses sounddevice and numpy libraries
- **Platform**: Raspberry Pi compatible for embedded deployment
- **Recording Logic**: Start recording when sound exceeds threshold, continue until 30 seconds of quiet
- **Quality**: Medium-quality audio suitable for legal evidence