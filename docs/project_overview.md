# Project Overview

## Project Description

This project aims to develop a "bark detector" which will identify the sound of one or more barking dogs and will start making a medium-quality sound recording of the barking.

## Technology Approach

- The system will use YAMNet to detect barking on an Intel-based Mac
- The system will start recording when it detects barking and will continue to record until 30 seconds pass without any barking being detected.

## Primary Goal

The goal of this project is to be able to have enough evidence of barking that we can make a formal complaint to the City of Kelowna.

## Legal Evidence Requirements Analysis

### City of Kelowna Bylaw Violations to Detect

The City of Kelowna bylaws state that owners must not allow a dog to bark, howl, or yelp:
- **Continuously for more than 5 minutes, or**
- **Sporadically for more than 15 minutes, or**
- **In any manner that disturbs the peace, quiet, rest, enjoyment or comfort of people in the neighbourhood**

Note: The Regional District of Central Okanagan (RDCO) issue reporting site uses the terms "Intermittent". For our purposes, the term "sporadic" and it's variants should be considered a synonym for "intermitent" and its variants. The terms "continuously" and its variants should be considered a synonym for the term "constant" and its variants.

### Specific Violations We Target

1. **Continuous Barking**: 5+ minutes of non-stop barking.
2. **Sporadic Barking**: 15+ minutes total within a time window
3. **Disturbance**: Any pattern that's clearly disruptive

### Clarification on Sporadic Violations

The City of Kelowna's definition of "sporadic violation" is vague, but our interpretation is:
- If dogs start to bark for a few seconds, then stop for a short period (a few seconds), then start up again for a few seconds over the course of 15 minutes, that would count as "sporadic" or "intermittent" barking and would count as a violation.
- The "time between barks" is open to interpretation, but a period of at least 5 minutes of quiet would "invalidate" the sporadic violation

### City of Kelowna Evidence Standards

To submit a complaint you must provide:
- **4+ separate instances** over a 3-5 day period (unless severe)
- **Exact dates, times and durations** of the barking episodes
- **Audio recordings** as proof.
- **Documentation** suitable for city submission.
- Regional District of Central Okanagan (RDCO) Issue reporting site: https://requests.rdco.com/?type=barking

####  RDCO Issue Reporting Instructions (from site):

"Cite at least 4 dates and times to demonstrate that there is an on going issue and not a one off incident. You are required to have exact times and duration of barking to have a valid complaint. If the exact time is not given, the ticket could be dismissed. The officer assigned to the file will be in touch with you when the complaint file has been completed. Including any owner or occupier information (if known). Time format hh:mm am|pm include leading 0. Example: 02:30pm"

Incident Reports must include:
- Date
- Start time
- End time
- Intermittent? (Yes / No)
- Constant? (Yes / No)
- Dog Visible? (Yes / No)
- Additional details to support your case (text box)
- Upload your Attachments section:
-- Include images or documents to help your case.
-- Acceptable file types: jpg, png, gif, pdf, mp3, mp4

## Key Definitions & Business Rules

### Gap Threshold Hierarchy

**Recording Sessions (10-second gaps)**
- Groups individual barks into audio recordings for file management and storage efficiency
- Handles short pauses between barks within the same incident
- More than 30 secs of quiet = stop recording. 

**Legal Sporadic Sessions (5-minute gaps)**
- Groups recording sessions for bylaw violation detection.
- 5+ minutes of quiet = new legal incident starts.
- Critical for determining legal violation boundaries.

### Legal Logic Example

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

## Key Dependencies

- `tensorflow`: Core machine learning framework for YAMNet
- `tensorflow-hub`: Access to pre-trained YAMNet model
- `librosa`: Advanced audio processing and analysis
- `soundfile`: Audio file reading/writing
- `pyaudio`: Real-time audio input/output
- `numpy`: Numerical computing for audio data
- `scipy`: Scientific computing for signal processing

## Deployment

- **Source Control**: Python source is synced to the execution environment via git
- **GitHub repo**: https://github.com/aeberts/bark_detector.git
- **Cross-Platform Support**: 
  - Apple Silicon Macs (M1, M2, M3)
  - Intel-based Macs
  - Linux systems
- **Installation**: Intelligent installer (`install.py`) with automatic platform detection and TensorFlow optimization
- **Development Platform**: M1 based Mac Laptop
- **Primary Target**: Intel-based Mac Laptop