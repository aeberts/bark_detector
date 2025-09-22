# Violation Detection Algorithm Architecture

## 1. Introduction

This document provides the technical architecture and precise algorithms for detecting barking violations. It is based on the business rules defined in `docs/violation_rules.md` and serves as the official blueprint for implementation.

## 2. System Overview

The violation detection system is not a real-time process. It operates by post-processing a list of `BarkEvent` objects that have been previously generated from audio recordings.

The core design is a stateful iterative algorithm that processes a chronologically sorted list of bark events to identify violation sessions.

## 3. Data Models

### 3.1. Input: AlgorithmInputEvent

The fundamental input to the violation detection algorithm is an `AlgorithmInputEvent` object. The analysis function will expect a list of these objects, sorted by `startTimestamp`.

**IMPORTANT:** This object is constructed in memory by the application from the raw event data found in the `_events.json` files. The `startTimestamp` must be created by combining the `realworld_date` and `realworld_time` fields.

```
// Raw Event (from _events.json)
{
  "bark_id": "11b16212-8416-448e-8b67-58ae5a7e135f",
  "realworld_date": "YYYY-MM-DD",
  "realworld_time": "HH:mm:ss",
  // ... other fields
}

// Constructed AlgorithmInputEvent (for use in algorithm)
{
  "id": "11b16212-8416-448e-8b67-58ae5a7e135f", // Mapped from bark_id
  "startTimestamp": "YYYY-MM-DDTHH:mm:ss.sssZ" // ISO 8601 format
  // ... other relevant metadata can be carried over if needed
}
```

### 3.2. Output: Violation

When a violation is detected, a `Violation` object should be created.

```
// Enhanced Violation Structure
{
  "type": "Continuous" | "Sporadic",
  "startTimestamp": "YYYY-MM-DDTHH:mm:ss.sssZ",        // Timestamp of the first bark in the violation session
  "violationTriggerTimestamp": "YYYY-MM-DDTHH:mm:ss.sssZ", // Timestamp of the bark that triggered the violation detection
  "endTimestamp": "YYYY-MM-DDTHH:mm:ss.sssZ",          // Timestamp of the last bark in the violation session
  "durationMinutes": float,                             // Total duration of the entire violation session (endTimestamp - startTimestamp)
  "violationDurationMinutes": float,                    // Duration from trigger to end (endTimestamp - violationTriggerTimestamp)
  "barkEventIds": ["uuid1", "uuid2", "uuid3"]         // Array of UUIDs of all bark events in the session
}
```

### Rationale for Enhanced Structure

**Three Timestamp Approach:**
- **`startTimestamp`**: Legal compliance - when the barking incident began
- **`violationTriggerTimestamp`**: System audit trail - when the system detected it qualified as a violation
- **`endTimestamp`**: Legal compliance - when the barking incident actually ended

**Example Scenario:** 8-minute continuous violation
- `startTimestamp`: "2025-09-21T10:00:00.000Z" (first bark)
- `violationTriggerTimestamp`: "2025-09-21T10:05:00.000Z" (5-minute threshold reached)
- `endTimestamp`: "2025-09-21T10:08:00.000Z" (last bark in session)
- `durationMinutes`: 8.0 (total incident duration for legal evidence)
- `violationDurationMinutes`: 3.0 (additional barking after violation detected)

**Data Structure Improvements:**
- `barkEventIds` is now properly defined as an array of UUID strings (not concatenated string)
- Added `violationDurationMinutes` for system analytics and legal clarity
- All timestamps provide complete temporal boundaries for legal evidence collection

## 4. Core Algorithm Design

The following pseudocode describes the logic for finding all violations within a given list of bark events.

### 4.1. Continuous Violation Detection

**Constants:**
- `MAX_GAP_SECONDS = 10`
- `MIN_SESSION_MINUTES = 5`

**Pseudocode:**

```pseudocode
function findContinuousViolations(barkEvents):
  // Ensure events are sorted by startTimestamp
  if barkEvents are not sorted:
    sort barkEvents by startTimestamp

  violations = []
  if count(barkEvents) < 2:
    return violations

  // Initialize the start of a potential session
  sessionStartIndex = 0

  // Iterate through the events to find sessions
  for i from 1 to count(barkEvents) - 1:
    previousEvent = barkEvents[i-1]
    currentEvent = barkEvents[i]

    // Calculate the gap between the start of consecutive events
    gapInSeconds = currentEvent.startTimestamp - previousEvent.startTimestamp

    if gapInSeconds >= MAX_GAP_SECONDS:
      // The gap is too large, so the session is broken.
      // Reset the start of the next potential session to the current event.
      sessionStartIndex = i
      continue

    // If the gap is small enough, the session continues.
    // Check if the current session duration meets the violation criteria.
    firstEventInSession = barkEvents[sessionStartIndex]
    sessionDurationSeconds = currentEvent.startTimestamp - firstEventInSession.startTimestamp
    sessionDurationMinutes = sessionDurationSeconds / 60

    if sessionDurationMinutes >= MIN_SESSION_MINUTES:
      // A violation has occurred.
      // Check if we have already logged a violation for this session that ends at the *previous* event.
      // This prevents creating duplicate violations for every subsequent bark in an ongoing violation.
      isNewViolation = true
      if count(violations) > 0:
        lastViolation = violations[count(violations)-1]
        if lastViolation.type == "Continuous" and lastViolation.endTimestamp == previousEvent.startTimestamp:
          isNewViolation = false

      if isNewViolation:
        // Extract the IDs of all events that constitute this violation
        violationEvents = slice(algorithmInputEvents from sessionStartIndex to i)
        eventIds = map violationEvents to list of event.id

        newViolation = createViolation(
          type: "Continuous",
          startTimestamp: firstEventInSession.startTimestamp,
          violationTriggerTimestamp: currentEvent.startTimestamp,
          endTimestamp: currentEvent.startTimestamp,  // Will be updated as session continues
          durationMinutes: sessionDurationMinutes,
          violationDurationMinutes: 0.0,  // Will be updated as session continues
          barkEventIds: eventIds
        )
        add newViolation to violations

  return violations
```

### 4.2. Sporadic Violation Detection

**Constants:**
- `MAX_GAP_MINUTES = 5`
- `MIN_SESSION_MINUTES = 15`

**Pseudocode:**

```pseudocode
function findSporadicViolations(barkEvents):
  // Ensure events are sorted by startTimestamp
  if barkEvents are not sorted:
    sort barkEvents by startTimestamp

  violations = []
  if count(barkEvents) < 2:
    return violations

  // Initialize the start of a potential session
  sessionStartIndex = 0

  // Iterate through the events to find sessions
  for i from 1 to count(barkEvents) - 1:
    previousEvent = barkEvents[i-1]
    currentEvent = barkEvents[i]

    // Calculate the gap in minutes
    gapInSeconds = currentEvent.startTimestamp - previousEvent.startTimestamp
    gapInMinutes = gapInSeconds / 60

    if gapInMinutes >= MAX_GAP_MINUTES:
      // The gap is too large, session is broken.
      // Reset the start of the next potential session.
      sessionStartIndex = i
      continue

    // If the gap is small enough, the session continues.
    // Check if the current session duration meets the violation criteria.
    firstEventInSession = barkEvents[sessionStartIndex]
    sessionDurationSeconds = currentEvent.startTimestamp - firstEventInSession.startTimestamp
    sessionDurationMinutes = sessionDurationSeconds / 60

    if sessionDurationMinutes >= MIN_SESSION_MINUTES:
      // A violation has occurred.
      // Use the same logic as continuous to avoid duplicate violation entries.
      isNewViolation = true
      if count(violations) > 0:
        lastViolation = violations[count(violations)-1]
        if lastViolation.type == "Sporadic" and lastViolation.endTimestamp == previousEvent.startTimestamp:
          isNewViolation = false

      if isNewViolation:
        // Extract the IDs of all events that constitute this violation
        violationEvents = slice(algorithmInputEvents from sessionStartIndex to i)
        eventIds = map violationEvents to list of event.id

        newViolation = createViolation(
          type: "Sporadic",
          startTimestamp: firstEventInSession.startTimestamp,
          violationTriggerTimestamp: currentEvent.startTimestamp,
          endTimestamp: currentEvent.startTimestamp,  // Will be updated as session continues
          durationMinutes: sessionDurationMinutes,
          violationDurationMinutes: 0.0,  // Will be updated as session continues
          barkEventIds: eventIds
        )
        add newViolation to violations

  return violations
```

### 4.3. Violation Updating for Ongoing Sessions

**IMPORTANT**: The pseudocode above shows initial violation creation. For complete implementation, violations must be updated as sessions continue beyond the trigger point.

**Implementation Requirements:**
- When a violation is first detected, `endTimestamp` and `violationTriggerTimestamp` are the same
- As the session continues with additional bark events, update the existing violation:
  - `endTimestamp` → timestamp of the most recent bark in the session
  - `durationMinutes` → total session duration (endTimestamp - startTimestamp)
  - `violationDurationMinutes` → duration from trigger to current end
  - `barkEventIds` → include all bark event IDs in the session

**Session Continuation Logic:**
- Continue updating the same violation record until session breaks (gap threshold exceeded)
- This ensures violations capture complete temporal boundaries for legal evidence

## 5. Edge Cases & Implementation Considerations

-   **Input Sorting:** The algorithms are critically dependent on the `barkEvents` list being pre-sorted chronologically. The implementation MUST ensure this sorting before processing.
-   **Empty Event List:** The functions should gracefully handle cases where the input list of events is empty or contains only one event, returning an empty list of violations.
-   **Timestamp Precision:** All timestamp calculations should handle timezone offsets correctly and maintain millisecond precision if available. Using a robust date/time library is essential.
-   **State Management:** The provided pseudocode is a pure function approach. For a large number of events, a class-based or stateful iterator approach could be more memory-efficient, but this logic remains the same.
-   **Violation Updates:** Implementations must handle updating violation records as sessions continue beyond the initial trigger point to ensure accurate `endTimestamp` and complete `barkEventIds` arrays.
-   **Data Type Consistency:** Ensure `barkEventIds` is implemented as a proper array/list structure in the target language, not a concatenated string.
