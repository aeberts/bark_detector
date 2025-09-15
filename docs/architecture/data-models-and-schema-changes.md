# Data Models and Schema Changes

## New Data Models

### PersistedBarkEvent

  * **Purpose**: To serve as a raw, persistent log of every individual bark event detected during an analysis run, decoupled from the final violation interpretation.
  * **Integration**: This model will be the schema for records stored in the new `[YYYY-MM-DD]_events.json` files.
  * **Key Attributes**:
      * `realworld_date`, `realworld_time`, `bark_id`, `bark_type`, `est_dog_size` (nullable for future use), `audio_file_name`, `bark_audiofile_timestamp`, **`confidence`**, **`intensity`**.

### Violation

  * **Purpose**: To logically separate the raw analysis result from the final formatted `ViolationReport`. This provides greater flexibility for debugging and filtering.
  * **Integration**: This will be the schema for records stored in the new `[YYYY-MM-DD]_violations.json` files.
  * **Key Attributes**:
      * `violation_id`, `violation_type`, `violation_date`, `violation_start_time`, `violation_end_time`, `bark_event_ids` (an array of `bark_id`s from the events file).

## Schema Integration Strategy

  * **New Files**: The system will now generate two files per day of analysis: **`[YYYY-MM-DD]_events.json`** and **`[YYYY-MM-DD]_violations.json`**.
  * **Refactored Model**: The existing `ViolationReport` model will be refactored to become a presentation-layer object, generated on-the-fly from the raw `Violation` data.
  * **Migration Strategy**: A post-deployment task will be to run `--analyze-violations` for all historical recording dates to back-populate the new data structure.

-----
