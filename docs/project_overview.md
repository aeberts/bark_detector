# Project Overview

## Project Description

This project aims to develop a "bark detector" which will identify the sound of one or more barking dogs and will start making a medium-quality sound recording of the barking.

## Technology Approach

- The system will use a simple "decibel threshold" approach to detect barking (no machine learning will be done on the device)
- The system will continue recording until 30 seconds pass without sounds occurring above the decibel threshold
- Designed to run on a Raspberry Pi for embedded deployment
- Uses Python with sounddevice and numpy libraries for real-time audio processing

## Primary Goal

The goal of this project is to be able to have enough evidence of barking that we can make a formal complaint to the City of Kelowna.

## Legal Evidence Requirements Analysis

### City of Kelowna Bylaw Violations to Detect

The City of Kelowna bylaws state that owners must not allow a dog to bark, howl, or yelp:
- **Continuously for more than 5 minutes, or**
- **Sporadically for more than 15 minutes, or**
- **In any manner that disturbs the peace, quiet, rest, enjoyment or comfort of people in the neighbourhood**

### Specific Violations We Target

1. **Continuous Barking**: 5+ minutes non-stop barking
2. **Sporadic Barking**: 15+ minutes total within a time window
3. **Disturbance**: Any pattern that's clearly disruptive

### Clarification on Sporadic Violations

The City of Kelowna's definition of "sporadic violation" is vague, but our interpretation is:
- If dogs start to bark for a few seconds, then stop for a short period (a few seconds), then start up again for a few seconds over the course of 15 minutes, that counts as a violation
- The "time between barks" is open to interpretation, but a period of at least 5 minutes of quiet would "invalidate" the sporadic violation

### City of Kelowna Evidence Standards

To submit a complaint you must provide:
- **4+ separate instances** over a 3-5 day period (unless severe)
- **Exact dates, times and durations** of the barking episodes
- **Audio recordings** as proof
- **Documentation** suitable for city submission

## Key Definitions & Business Rules

### Gap Threshold Hierarchy

**Recording Sessions (10-second gaps)**
- Groups individual barks into audio recordings for file management and storage efficiency
- Handles short pauses between barks within the same incident

**Legal Sporadic Sessions (5-minute gaps)**
- Groups recording sessions for bylaw violation detection
- 5+ minutes of quiet = new legal incident starts
- Critical for determining legal violation boundaries

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

- `pyaudio`: For audio input/output (Pi-compatible)
- `numpy`: For numerical processing of audio data
- `sounddevice`: For audio processing

## Deployment

- Python source is synced to the execution environment via git
- GitHub repo: https://github.com/aeberts/bark_detector.git
- Target platform: Raspberry Pi