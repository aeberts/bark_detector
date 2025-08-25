#!/usr/bin/env python3
"""
Rollback bark recording filename migrations.

This script reverses the changes made by rename_recordings_to_start_timestamps.py
by reading the migration log and restoring all files to their original names.

Usage:
    python scripts/rollback_recording_renames.py --log-file 2025-08-23-recording-rename.log
    
    # Dry run to preview rollback actions
    python scripts/rollback_recording_renames.py --log-file migration.log --dry-run
    
    # Rollback only successful renames (skip errors)
    python scripts/rollback_recording_renames.py --log-file migration.log --only-successful

Safety Features:
- Dry-run mode for safe testing
- Verification of file existence before rollback
- Comprehensive logging of rollback operations
- Selective rollback options
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class RenameRollback:
    """Handles rollback of bark recording filename migrations."""
    
    def __init__(self, log_file: str, dry_run: bool = False, only_successful: bool = False):
        """Initialize the rollback processor."""
        self.log_file = Path(log_file)
        self.dry_run = dry_run
        self.only_successful = only_successful
        
        # Rollback tracking
        self.rollback_stats = {
            "timestamp": datetime.now().isoformat(),
            "log_file": str(self.log_file),
            "dry_run": dry_run,
            "total_operations": 0,
            "successful_rollbacks": 0,
            "failed_rollbacks": 0,
            "skipped": 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def load_migration_log(self) -> Dict:
        """Load the migration log file."""
        try:
            with open(self.log_file, 'r') as f:
                migration_log = json.load(f)
            
            self.logger.info(f"Loaded migration log from {self.log_file}")
            
            # Validate log structure
            if "renames" not in migration_log:
                raise ValueError("Invalid migration log: missing 'renames' section")
            
            return migration_log
            
        except FileNotFoundError:
            self.logger.error(f"Migration log file not found: {self.log_file}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in migration log: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load migration log: {e}")
            raise
    
    def validate_rollback_operation(self, rename_entry: Dict) -> bool:
        """Validate that a rollback operation can be performed."""
        new_path = Path(rename_entry["new_path"])
        original_path = Path(rename_entry["original_path"])
        
        # Check if the renamed file exists
        if not new_path.exists():
            self.logger.warning(f"File to rollback not found: {new_path}")
            return False
        
        # Check if reverting would create a conflict
        if original_path.exists() and original_path != new_path:
            self.logger.warning(f"Rollback conflict: {original_path} already exists")
            return False
        
        # Check if we have write permission to the directory
        try:
            if not os.access(new_path.parent, os.W_OK):
                self.logger.error(f"No write permission to directory: {new_path.parent}")
                return False
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
        
        return True
    
    def perform_rollback(self, rename_entry: Dict) -> bool:
        """Perform a single rollback operation."""
        new_path = Path(rename_entry["new_path"])
        original_path = Path(rename_entry["original_path"])
        
        try:
            if self.dry_run:
                self.logger.info(f"DRY-RUN: Would rollback {new_path.name} -> {original_path.name}")
            else:
                # Perform atomic rename back to original name
                new_path.rename(original_path)
                self.logger.info(f"Rolled back: {new_path.name} -> {original_path.name}")
            
            self.rollback_stats["successful_rollbacks"] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback {new_path}: {e}")
            self.rollback_stats["failed_rollbacks"] += 1
            return False
    
    def run_rollback(self):
        """Run the complete rollback process."""
        self.logger.info("Starting bark recording filename rollback")
        self.logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        self.logger.info(f"Migration log: {self.log_file}")
        
        # Load migration log
        try:
            migration_log = self.load_migration_log()
        except Exception:
            return False
        
        # Get migration info
        migration_info = migration_log.get("migration_info", {})
        renames = migration_log.get("renames", [])
        
        self.logger.info("Original Migration Summary:")
        self.logger.info(f"  Migration date: {migration_info.get('timestamp', 'unknown')}")
        self.logger.info(f"  Total files processed: {migration_info.get('total_files', 0)}")
        self.logger.info(f"  Successful renames: {migration_info.get('successful_renames', 0)}")
        self.logger.info(f"  Errors: {migration_info.get('errors', 0)}")
        
        # Filter operations if requested
        operations_to_rollback = []
        
        for rename_entry in renames:
            status = rename_entry.get("status", "")
            
            # Skip dry-run entries unless specifically requested
            if status == "dry_run_success" and not self.dry_run:
                continue
            
            # Skip failed operations if only_successful is True
            if self.only_successful and status != "success":
                self.rollback_stats["skipped"] += 1
                continue
            
            operations_to_rollback.append(rename_entry)
        
        self.rollback_stats["total_operations"] = len(operations_to_rollback)
        
        if not operations_to_rollback:
            self.logger.info("No operations to rollback")
            return True
        
        self.logger.info(f"Rolling back {len(operations_to_rollback)} operations")
        
        # Process rollback operations
        successful_count = 0
        
        for i, rename_entry in enumerate(operations_to_rollback):
            # Validate the rollback operation
            if not self.validate_rollback_operation(rename_entry):
                self.rollback_stats["failed_rollbacks"] += 1
                continue
            
            # Perform the rollback
            if self.perform_rollback(rename_entry):
                successful_count += 1
            
            # Progress update every 50 operations
            if (i + 1) % 50 == 0:
                self.logger.info(f"Progress: {i + 1}/{len(operations_to_rollback)} operations processed")
        
        # Final summary
        self.logger.info("Rollback Summary:")
        self.logger.info(f"  Total operations: {self.rollback_stats['total_operations']}")
        self.logger.info(f"  Successful rollbacks: {self.rollback_stats['successful_rollbacks']}")
        self.logger.info(f"  Failed rollbacks: {self.rollback_stats['failed_rollbacks']}")
        self.logger.info(f"  Skipped: {self.rollback_stats['skipped']}")
        
        if self.dry_run:
            self.logger.info("DRY-RUN completed. No files were actually rolled back.")
        else:
            self.logger.info("Rollback completed!")
        
        return self.rollback_stats["failed_rollbacks"] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rollback bark recording filename migrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the migration log file to rollback"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview rollback actions without executing them"
    )
    
    parser.add_argument(
        "--only-successful",
        action="store_true",
        help="Only rollback operations that were marked as successful"
    )
    
    args = parser.parse_args()
    
    # Validate log file exists
    if not os.path.exists(args.log_file):
        print(f"Error: Migration log file '{args.log_file}' does not exist")
        sys.exit(1)
    
    # Create rollback processor and run
    rollback = RenameRollback(
        log_file=args.log_file,
        dry_run=args.dry_run,
        only_successful=args.only_successful
    )
    
    try:
        success = rollback.run_rollback()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nRollback interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Rollback failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()