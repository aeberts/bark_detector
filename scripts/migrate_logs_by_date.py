#!/usr/bin/env python3
"""
Migrate legacy bark detector logs to channel-based daily structure.

This script transforms legacy flat log files into the new hierarchy without data loss,
leaving timestamped backups of the original files.
"""

import argparse
import json
import logging
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple, Set
from dataclasses import dataclass, asdict


class LogEntry(NamedTuple):
    """Structured representation of a log entry."""
    timestamp: datetime
    level: str
    message: str
    original_line: str


@dataclass
class MigrationSummary:
    """Summary of migration statistics and results."""
    migration_timestamp: str
    input_file: str
    backup_file: str
    total_lines_processed: int
    malformed_lines: int
    classification_stats: Dict[str, int]
    date_range: Dict[str, str]
    output_files_created: List[str]
    errors: List[str]
    warnings: List[str]


class LogMigrator:
    """Migrate legacy log files to channel-based daily structure."""

    # Channel classification keywords (case-insensitive)
    DETECTION_KEYWORDS = [
        "yamnet model", "starting manual recording", "recording saved",
        "calibration", "profile", "audio conversion",
        "real-time detection", "bark detected", "session started",
        "configuration loaded", "detector started", "audio device"
    ]

    ANALYSIS_KEYWORDS = [
        "violation analysis", "analysis complete", "violations detected",
        "pdf report", "report generated", "exporting violations",
        "violation report", "enhanced report", "csv export"
    ]

    def __init__(self, logs_dir: str = "logs", backup_dir: Optional[str] = None,
                 continue_on_error: bool = False, batch_size: int = 1000,
                 verbose: bool = False):
        """
        Initialize the log migrator.

        Args:
            logs_dir: Output logs directory
            backup_dir: Directory for backup files
            continue_on_error: Continue processing despite errors
            batch_size: Process entries in batches
            verbose: Enable verbose output
        """
        self.logs_dir = Path(logs_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else self.logs_dir / "migration_backups"
        self.continue_on_error = continue_on_error
        self.batch_size = batch_size
        self.verbose = verbose

        # Statistics
        self.total_lines = 0
        self.malformed_lines = 0
        self.errors = []
        self.warnings = []

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def find_legacy_log_files(self) -> List[Path]:
        """Find legacy log files to migrate."""
        patterns = ["bark_detector*.log", "bark_detector.log.bak"]
        found_files = []

        # Search in current directory
        current_dir = Path(".")
        for pattern in patterns:
            found_files.extend(current_dir.glob(pattern))

        # Also check logs directory for any legacy files
        if self.logs_dir.exists():
            for pattern in patterns:
                found_files.extend(self.logs_dir.glob(pattern))

        return list(set(found_files))  # Remove duplicates

    def validate_input_file(self, input_file: Path) -> None:
        """Validate input file exists and is readable."""
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if not input_file.is_file():
            raise ValueError(f"Input path is not a file: {input_file}")

        try:
            with open(input_file, 'r') as f:
                f.read(1)  # Test readability
        except Exception as e:
            raise ValueError(f"Cannot read input file: {e}")

    def create_backup(self, input_file: Path) -> Path:
        """Create timestamped backup of input file."""
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        backup_filename = f"{input_file.name}.backup.{timestamp}"
        backup_path = self.backup_dir / backup_filename

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create backup
        shutil.copy2(input_file, backup_path)
        self.logger.info(f"Created backup: {backup_path}")

        return backup_path

    def parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """
        Parse individual log line into structured entry.

        Expected format: "YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE"
        """
        line = line.strip()
        if not line:
            return None

        # Regex pattern for standard Python logging format
        pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.*)$'

        match = re.match(pattern, line)
        if not match:
            self.malformed_lines += 1
            warning = f"Line {line_number}: Malformed timestamp format - skipped"
            self.warnings.append(warning)

            if not self.continue_on_error:
                raise ValueError(f"Malformed log line at {line_number}: {line}")

            return None

        timestamp_str, level, message = match.groups()

        try:
            # Parse timestamp - handle microseconds as milliseconds
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
        except ValueError as e:
            self.malformed_lines += 1
            warning = f"Line {line_number}: Invalid timestamp format - skipped"
            self.warnings.append(warning)

            if not self.continue_on_error:
                raise ValueError(f"Invalid timestamp at line {line_number}: {e}")

            return None

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            original_line=line
        )

    def classify_by_channel(self, log_entry: LogEntry) -> str:
        """
        Classify log entry by channel based on message content.

        Returns:
            str: 'detection' or 'analysis'
        """
        message_lower = log_entry.message.lower()

        # Check analysis keywords first (more specific)
        for keyword in self.ANALYSIS_KEYWORDS:
            if keyword in message_lower:
                return 'analysis'

        # Check detection keywords
        for keyword in self.DETECTION_KEYWORDS:
            if keyword in message_lower:
                return 'detection'

        # Default fallback to detection channel
        return 'detection'

    def parse_log_file(self, input_file: Path) -> List[LogEntry]:
        """Parse entire log file into structured entries."""
        entries = []

        self.logger.info(f"Parsing log file: {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                self.total_lines += 1

                entry = self.parse_log_line(line, line_number)
                if entry:
                    entries.append(entry)

                # Progress reporting for large files
                if self.total_lines % 1000 == 0:
                    self.logger.info(f"Processed {self.total_lines} lines...")

        self.logger.info(f"Parsed {len(entries)} valid entries from {self.total_lines} total lines")
        return entries

    def group_by_date_and_channel(self, entries: List[LogEntry]) -> Dict[str, Dict[str, List[LogEntry]]]:
        """Group entries by date and channel."""
        grouped = {}

        for entry in entries:
            date_str = entry.timestamp.strftime('%Y-%m-%d')
            channel = self.classify_by_channel(entry)

            if date_str not in grouped:
                grouped[date_str] = {'detection': [], 'analysis': []}

            grouped[date_str][channel].append(entry)

        return grouped

    def write_daily_channel_logs(self, date: str, entries_by_channel: Dict[str, List[LogEntry]]) -> List[str]:
        """Write daily channel log files."""
        output_files = []

        date_dir = self.logs_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)

        for channel, entries in entries_by_channel.items():
            if not entries:  # Skip empty channels
                continue

            log_file = date_dir / f"{date}_{channel}.log"

            with open(log_file, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(entry.original_line + '\n')

            output_files.append(str(log_file))
            self.logger.info(f"Created {log_file} with {len(entries)} entries")

        return output_files

    def generate_summary(self, backup_path: Path, grouped_entries: Dict[str, Dict[str, List[LogEntry]]],
                        output_files: List[str]) -> MigrationSummary:
        """Generate migration summary."""
        classification_stats = {
            'detection_entries': 0,
            'analysis_entries': 0,
            'unclassified_entries': 0
        }

        dates = list(grouped_entries.keys())
        date_range = {
            'earliest_date': min(dates) if dates else '',
            'latest_date': max(dates) if dates else ''
        }

        for date_entries in grouped_entries.values():
            classification_stats['detection_entries'] += len(date_entries['detection'])
            classification_stats['analysis_entries'] += len(date_entries['analysis'])

        return MigrationSummary(
            migration_timestamp=datetime.now(timezone.utc).isoformat(),
            input_file=str(backup_path.name),
            backup_file=str(backup_path),
            total_lines_processed=self.total_lines,
            malformed_lines=self.malformed_lines,
            classification_stats=classification_stats,
            date_range=date_range,
            output_files_created=output_files,
            errors=self.errors,
            warnings=self.warnings
        )

    def migrate_logs(self, input_file: Path, dry_run: bool = False) -> MigrationSummary:
        """
        Main migration algorithm.

        Args:
            input_file: Path to input log file
            dry_run: Preview changes without executing

        Returns:
            MigrationSummary: Migration statistics and results
        """
        self.logger.info(f"Starting migration of {input_file}")

        if dry_run:
            self.logger.info("DRY RUN MODE - no files will be modified")

        # 1. Input Validation
        self.validate_input_file(input_file)

        # 2. Parse and Classify
        log_entries = self.parse_log_file(input_file)
        grouped_entries = self.group_by_date_and_channel(log_entries)

        if dry_run:
            self.logger.info("DRY RUN: Migration preview:")
            for date, channels in grouped_entries.items():
                for channel, entries in channels.items():
                    if entries:
                        output_file = f"{self.logs_dir}/{date}/{date}_{channel}.log"
                        self.logger.info(f"  Would create: {output_file} ({len(entries)} entries)")

            # Return preview summary without creating files
            return self.generate_summary(input_file, grouped_entries, [])

        # 3. Create Backup
        backup_path = self.create_backup(input_file)

        # 4. Write Output Files
        output_files = []
        for date, channels in grouped_entries.items():
            files_for_date = self.write_daily_channel_logs(date, channels)
            output_files.extend(files_for_date)

        # 5. Generate Summary
        summary = self.generate_summary(backup_path, grouped_entries, output_files)

        # 6. Write Summary JSON
        summary_file = self.logs_dir / f"migration_summary_{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(asdict(summary), f, indent=2)

        self.logger.info(f"Migration summary written to: {summary_file}")
        self.logger.info(f"Migration completed successfully!")

        return summary


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Migrate legacy bark detector logs to channel-based daily structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration (RECOMMENDED FIRST STEP)
  python scripts/migrate_logs_by_date.py --dry-run

  # Execute migration with default settings
  python scripts/migrate_logs_by_date.py

  # Migrate specific log file
  python scripts/migrate_logs_by_date.py --input bark_detector_archive.log

  # Custom output directory
  python scripts/migrate_logs_by_date.py --logs-dir /custom/logs/path

  # Process with backup retention
  python scripts/migrate_logs_by_date.py --backup-dir ./migration_backups
        """
    )

    parser.add_argument('--input', type=str,
                        help='Input log file to migrate (default: search for bark_detector*.log)')
    parser.add_argument('--logs-dir', type=str, default='logs',
                        help='Output logs directory (default: logs)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without executing migration')
    parser.add_argument('--backup-dir', type=str,
                        help='Directory for backup files (default: logs/migration_backups)')
    parser.add_argument('--continue-on-error', action='store_true',
                        help='Continue processing despite individual line parsing errors')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Process log entries in batches (default: 1000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    return parser.parse_args()


def main():
    """Main entry point for migration script."""
    args = parse_arguments()

    # Initialize migrator
    migrator = LogMigrator(
        logs_dir=args.logs_dir,
        backup_dir=args.backup_dir,
        continue_on_error=args.continue_on_error,
        batch_size=args.batch_size,
        verbose=args.verbose
    )

    # Determine input file
    if args.input:
        input_file = Path(args.input)
    else:
        # Auto-discover legacy log files
        legacy_files = migrator.find_legacy_log_files()

        if not legacy_files:
            print("No legacy log files found. Use --input to specify a file.")
            return 1

        if len(legacy_files) == 1:
            input_file = legacy_files[0]
            print(f"Found legacy log file: {input_file}")
        else:
            print("Multiple legacy log files found:")
            for i, file in enumerate(legacy_files, 1):
                print(f"  {i}. {file}")
            print("Use --input to specify which file to migrate.")
            return 1

    try:
        # Execute migration
        summary = migrator.migrate_logs(input_file, dry_run=args.dry_run)

        # Print summary
        print(f"\nMigration Summary:")
        print(f"  Input file: {summary.input_file}")
        print(f"  Total lines processed: {summary.total_lines_processed}")
        print(f"  Malformed lines: {summary.malformed_lines}")
        print(f"  Detection entries: {summary.classification_stats['detection_entries']}")
        print(f"  Analysis entries: {summary.classification_stats['analysis_entries']}")

        if summary.date_range['earliest_date']:
            print(f"  Date range: {summary.date_range['earliest_date']} to {summary.date_range['latest_date']}")

        if not args.dry_run:
            print(f"  Backup file: {summary.backup_file}")
            print(f"  Output files created: {len(summary.output_files_created)}")

        if summary.warnings:
            print(f"  Warnings: {len(summary.warnings)}")

        if summary.errors:
            print(f"  Errors: {len(summary.errors)}")
            return 1

        return 0

    except Exception as e:
        print(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())