"""Utility functions and helpers"""

import logging
import numpy as np
import os
from datetime import datetime
from pathlib import Path


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


def setup_logging(log_file='bark_detector.log', use_date_folders=True):
    """
    Configure logging for the bark detector system with optional date-based organization.
    
    Args:
        log_file: Path to the log file (used as base name if use_date_folders=True)
        use_date_folders: If True, organize logs in logs/YYYY-MM-DD/ folders
    """
    if use_date_folders:
        # Create date-based log organization
        today = datetime.now().strftime('%Y-%m-%d')
        logs_dir = Path('logs') / today
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract base filename without extension for date-based naming
        base_name = Path(log_file).stem
        log_file_path = logs_dir / f"{base_name}-{today}.log"
    else:
        # Use original behavior for backward compatibility
        log_file_path = log_file
    
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