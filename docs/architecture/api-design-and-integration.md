# API Design and Integration

## API Integration Strategy

The primary strategy is to simplify the user-facing CLI by deprecating the redundant `--enhanced-violation-report` command and consolidating all reporting functionality into a single, intelligent `--violation-report` command.

## Modified CLI Commands

  * **`--analyze-violations [DATE]`**: This command's role is clarified as the primary data-generation tool, performing deep analysis of audio files and populating the `_events.json` and `_violations.json` files.
  * **`--violation-report [START_DATE] [END_DATE]`**: This becomes the single, primary command for users to get a report. It will now automatically trigger the analysis if the required data for the requested date(s) is not found.
  * **`--enhanced-violation-report`**: This command will be **deprecated and removed**.
