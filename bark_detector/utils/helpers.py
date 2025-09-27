"""Utility functions and helpers"""

import logging
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def convert_numpy_types(obj):
    """
    Recursively convert NumPy data types to native Python types for JSON serialization.
    
    Args:
        obj: Object that may contain NumPy types
        
    Returns:
        Object with NumPy types converted to native Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        # Handle NaN and infinity
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(item) for item in obj.tolist()]
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj


def setup_logging(
    channel: str = 'detection',
    log_file: Optional[str] = None,
    use_date_folders: bool = True,
    logs_dir: Optional[str] = None,
    config: Optional[object] = None,
    minimal: bool = False
) -> logging.Logger:
    """
    Configure logging for specific functional channels with full configuration integration.

    Args:
        channel: Logging channel - 'detection' or 'analysis'
        log_file: Override base filename
        use_date_folders: Enable date-based organization (default: True)
        logs_dir: Override logs directory path
        config: Configuration object to read logs_dir from
        minimal: Minimal logging for early startup (no config)

    Returns:
        logging.Logger: Configured logger instance

    Creates files like:
        - logs/2025-09-27/2025-09-27_detection.log (detection channel)
        - logs/2025-09-27/2025-09-27_analysis.log (analysis channel)
    """
    if minimal:
        # Early startup logging without configuration
        return _setup_minimal_logging()

    # Priority resolution for logs directory
    resolved_logs_dir = _resolve_logs_directory(logs_dir, config)

    # Generate appropriate filename
    log_filename = _generate_log_filename(channel, log_file, use_date_folders)

    # Create full log file path
    if use_date_folders:
        today = datetime.now().strftime('%Y-%m-%d')
        log_dir = Path(resolved_logs_dir) / today
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / log_filename
    else:
        log_file_path = Path(resolved_logs_dir) / log_filename

    return _configure_logger(log_file_path)


def _setup_minimal_logging() -> logging.Logger:
    """Setup minimal logging for early startup."""
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
        force=True
    )
    return logging.getLogger(__name__)


def _resolve_logs_directory(explicit_logs_dir: Optional[str], config: Optional[object]) -> str:
    """
    Resolve logs directory with proper priority order.

    Priority:
    1. Explicit logs_dir parameter (highest)
    2. config.output.logs_dir (if config provided)
    3. Default 'logs/' directory (fallback)
    """
    if explicit_logs_dir:
        return _validate_directory_path(explicit_logs_dir)

    if config and hasattr(config, 'output') and config.output.logs_dir:
        return _validate_directory_path(config.output.logs_dir)

    return 'logs'  # Default fallback


def _validate_directory_path(path_str: str) -> str:
    """
    Validate and normalize directory path.

    Args:
        path_str: Directory path to validate

    Returns:
        str: Validated and normalized path

    Raises:
        ValueError: If path is invalid or inaccessible
    """
    try:
        path = Path(path_str)

        # Handle relative vs absolute paths
        if not path.is_absolute():
            # Relative paths are relative to current working directory
            path = Path.cwd() / path

        # Ensure directory exists or can be created
        path.mkdir(parents=True, exist_ok=True)

        # Verify write permissions
        test_file = path / '.write_test'
        test_file.touch()
        test_file.unlink()

        return str(path)

    except (OSError, PermissionError) as e:
        raise ValueError(f"Invalid logs directory '{path_str}': {e}")


def _generate_log_filename(channel: str, log_file_override: Optional[str], use_date_folders: bool) -> str:
    """
    Generate appropriate log filename based on channel and date settings.
    """
    if log_file_override:
        return log_file_override

    if use_date_folders:
        today = datetime.now().strftime('%Y-%m-%d')
        return f"{today}_{channel}.log"
    else:
        # Legacy flat file naming
        return f"bark_detector_{channel}.log" if channel != 'detection' else "bark_detector.log"


def _configure_logger(log_file_path: Path) -> logging.Logger:
    """Configure the actual logger with file and console handlers."""
    # Clear any existing handlers to avoid duplicates
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ],
        force=True  # Force reconfiguration
    )
    return logging.getLogger(__name__)


def get_detection_logger(config: Optional[object] = None, logs_dir: Optional[str] = None) -> logging.Logger:
    """Get logger for real-time detection activities (monitoring, calibration, recording)."""
    return setup_logging(
        channel='detection',
        config=config,
        logs_dir=logs_dir,
        use_date_folders=True
    )


def get_analysis_logger(config: Optional[object] = None, logs_dir: Optional[str] = None) -> logging.Logger:
    """Get logger for analysis and reporting activities (violations, reports)."""
    return setup_logging(
        channel='analysis',
        config=config,
        logs_dir=logs_dir,
        use_date_folders=True
    )