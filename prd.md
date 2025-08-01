# Bark Detector - Product Requirements Document

This project aims to develop a "bark detector" which will identify the sound of one or more barking dogs and will start making a medium-quality sound recording of the barking.

- The system will use a simple "decibel threashold" approach to detect barking (no machine learning will be done on the device).
- The system will continue recording until 30 seconds pass without sounds occuring above the decibel threashold.

## Project Goals

The goal of this project is to be able to have enough evidence of barking that we can make a formal complaint to the City of Kelowna. 

The City of Kelowna bylaws state that:
```
Owners must not allow a dog to bark, howl, or yelp:
    •    Continuously for more than 5 minutes, or
    •    Sporadically for more than 15 minutes, or
    •    In any manner that disturbs the peace, quiet, rest, enjoyment or comfort of people in the neighbourhood

To submit a complaint you must record at least 4 separate instances including exact dates, times and durations of the barking episodes (over a 3-5 day period, unless it's severe).
```
## **Legal Evidence Requirements Analysis:**

### **Bylaw Violations to Detect:**
1. **Continuous Barking**: 5+ minutes non-stop barking
2. **Sporadic Barking**: 15+ minutes total within a time window (what window? 1 hour? 1 day?)
3. **Disturbance**: Any pattern that's clearly disruptive

### Clarification on "Sporadic violations":
The City of Kelowna's definition of "sporadic violation is vague but the interpretation we will use is:
- if dogs start to bark for a few seconds then stop for a short period (let say a few seconds) then start up again for a few seconds over the course of 15 mins then that would count as a violation.
- The "time between barks" is open to interpretation but a period of at least 5 minutes of quiet would "invalidate" the sporadic violation.

### **City of Kelowna Evidence Standards:**
- **4+ separate instances** over 3-5 days
- **A record of the exact dates/times/durations of the incidents**
- **Audio recordings** as proof
- **Documentation** suitable for city submission

# Feature Descriptions

## **📏 Gap Threshold Hierarchy:**

### **Recording Sessions** (10-second gaps)
- Groups individual barks into audio recordings
- For file management and storage efficiency

### **Legal Sporadic Sessions** (5-minute gaps) 
- Groups recording sessions for bylaw violation detection
- 5+ minutes of quiet = new legal incident starts

## **🏛️ Legal Logic Example:**

```
Timeline: Dogs bark intermittently over 20 minutes (sporadic session)

0:00:00 ████ bark 2min ████ 
0:00:02 ░░ quiet 30sec ░░
0:02:30 ██ bark 1min ██
0:03:30 ░░░ quiet 90sec ░░░  
0:05:00 ████ bark 3min ████
0:08:00 ░░ quiet 45sec ░░
0:08:45 ██████ bark 4min ██████
0:12:45 ░░ quiet 30sec ░░
0:13:15 ████████ bark 5min ████████
0:18:15 ░░░░░░ quiet 6min ░░░░░░  ← 5+ min gap ENDS sporadic session
0:24:15 ██ new incident ██

Result: ONE sporadic violation (15 minutes total barking in first session)
```

## Legal Evidence Collection Features

### **Legal Evidence Features**

### **Bylaw violation detection**: Auto-flag 5min continuous / 15min sporadic

#### **Violation Detection Algorithm Example:**
```python
class LegalViolationTracker:
    def __init__(self):
        self.current_sporadic_session = None
        self.sporadic_start_time = None
        self.total_bark_duration_in_session = 0
        self.legal_gap_threshold = 300  # 5 minutes
        
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

- **Evidence reports**: Generate city-compliant documentation
- **Scheduling system**: Auto-start at 6:20am with saved profile

### **Legal Evidence Advanced Features**
- **Multi-day evidence collection**: Track violations across 3-5 days
- **Report generation**: PDF reports ready for city submission
- **Audio evidence packaging**: Organized by incident with metadata