# Technical Constraints and Integration Requirements

## Existing Technology Stack
*(Confirmed)* The system will continue to be built on Python 3.11, using TensorFlow/YAMNet for ML, PyAudio for audio I/O, and `uv` for package management.

## Integration Approach

### Data Persistence Strategy
Per your input, the `--analyze-violations` command will now generate two structured files in the `violations/[YYYY-MM-DD]/` directory with the date prepended to the filename:

1.  **`[YYYY-MM-DD]_events.json`**: This file will contain the raw, unprocessed log of every individual bark event detected in the audio files for that day.
2.  **`[YYYY-MM-DD]_violations.json`**: This file will contain the final, interpreted list of bylaw violations that were derived from the data in the events file.

The schema for each record in `[YYYY-MM-DD]_events.json` will be:
* `realworld_date`: The date of the event (e.g., "2025-09-14").
* `realworld_time`: The precise time of the event (e.g., "18:22:15.123").
* `bark_id`: A unique identifier for the event.
* `bark_type`: The specific YAMNet class that triggered the detection (e.g., "Bark", "Howl", "Yip").
* `est_dog_size`: We will include this field and populate it with `null` for now, marking it as a target for a future feature improvement.
* `audio_file_name`: The name of the `.wav` file containing the bark.
* `bark_audiofile_timestamp`: The precise `HH:MM:SS.mmm` offset of the event from the start of the audio file.

### API (Internal Logic) Integration Strategy
The `--violation-report` command will be updated with the following intelligent workflow:
1.  When a user runs `--violation-report [DATE]`, the system will first check if a `[YYYY-MM-DD]_violations.json` analysis file already exists for that date.
2.  **If the file does not exist**, it will automatically trigger the `--analyze-violations` logic for that date first.
3.  Once the analysis is complete, the system will generate the human-readable report from the `violations.json` file.

### Testing Integration Strategy
New integration tests will be added to the `pytest` suite to validate the complete, end-to-end workflow and confirm that the data correlation bugs have been resolved.

## Code Organization and Standards
* **File Structure Approach**: The `--enhanced-violation-report` command and its `LogBasedReportGenerator` will be removed. All analysis logic will be consolidated and refactored within `bark_detector/legal/tracker.py` and `bark_detector/legal/database.py`. The `cli.py` will be updated to reflect the new command logic.
* **Documentation Standards**: The `README.md` and `docs/features.md` must be updated to reflect the single, unified reporting command.

## Deployment and Operations
* **Post-Deployment Task**: After deployment, a one-time analysis of all historical recordings should be performed using the updated `--analyze-violations` command to populate the new `violations/` database.

## Risk Assessment and Mitigation
* **Technical Risk**: The "smart" `--violation-report` command could have a long runtime if it triggers a first-time analysis of many recordings.
    * **Mitigation**: The CLI must provide clear feedback to the user (e.g., "Analysis for [DATE] not found. Running analysis now...") to manage expectations.
* **Integration Risk**: The refactored violation logic in `LegalViolationTracker` could contain errors.
    * **Mitigation**: This will be mitigated by writing a comprehensive suite of new integration tests to validate the end-to-end process.