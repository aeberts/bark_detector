# Formal Barking Violation Rules

## 1. Introduction

This document contains the official, solidified rules for detecting barking violations. It serves as the single source of truth for all technical design and implementation. The rules defined herein are based on the legal requirements of the City of Kelowna bylaw and have been clarified to remove ambiguity.

## 2. Core Analysis Principles

Violation detection is not performed in real-time. The process is as follows:
1.  An audio recording is captured based on initial sound detection.
2.  The recording is analyzed to identify every individual bark, generating a list of "bark events" with precise start timestamps.
3.  The violation analysis logic processes this list of timestamped events to determine if a violation has occurred.

All rules are based on the time elapsed **between the start timestamps** of consecutive bark events.

## 3. Violation Definitions

### 3.1. Continuous Violation

A **Continuous Violation** occurs when a session of sustained barking lasts for **5 minutes or more**.

-   **Session Definition:** A "Continuous Barking Session" is a sequence of two or more bark events.
-   **Session Continuation:** The session continues as long as the time gap between the start of one bark event and the start of the next consecutive event is **less than 10 seconds**.
-   **Session End:** The session ends if the time gap between consecutive bark events is **10 seconds or greater**.
-   **Violation Trigger:** A violation is triggered the moment the total duration of the session (i.e., `timestamp_of_current_event - timestamp_of_first_event_in_session`) reaches or exceeds 5 minutes.

### 3.2. Sporadic Violation

A **Sporadic Violation** occurs when a session of intermittent barking lasts for **15 minutes or more**.

-   **Session Definition:** A "Sporadic Barking Session" is a sequence of two or more bark events.
-   **Session Continuation:** The session continues as long as the time gap between the start of one bark event and the start of the next consecutive event is **less than 5 minutes**.
-   **Session End:** The session ends if the time gap between consecutive bark events is **5 minutes or greater**.
-   **Violation Trigger:** A violation is triggered the moment the total duration of the session (i.e., `timestamp_of_current_event - timestamp_of_first_event_in_session`) reaches or exceeds 15 minutes.

**Note:** It is possible for a single bark event to be part of both a Continuous Violation and a Sporadic Violation.

## 4. Out of Scope Violations

### 4.1. Disturbance Violation

The bylaw regarding barking "in any manner that disturbs the peace, quiet, rest, enjoyment or comfort of people" is inherently subjective. As there are no objective, measurable criteria provided, this violation is **out of scope** for automatic detection. Documenting and arguing this type of disturbance is left to the user's discretion when submitting evidence to the authorities.

**Note (2025-09-17 analysis):** Real-world persisted bark events show 90th-percentile inter-bark gaps around 18–33 seconds. To keep constant violations (≥5 minutes) detectable while remaining below the 60-second ceiling, plan to raise the continuous gap threshold from 10 seconds to roughly 33 seconds (or make it configurable in that range).
