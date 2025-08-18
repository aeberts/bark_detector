#!/usr/bin/env python3
"""
Backwards-compatible entry point for bark detector.
This file maintains compatibility with existing scripts and usage patterns.

For new development, use: uv run python -m bark_detector
"""

import os
import warnings
import sys
from pathlib import Path

# Add the current directory to Python path to ensure package can be found
sys.path.insert(0, str(Path(__file__).parent))

# Apply comprehensive TensorFlow logging suppression early (critical for Intel Macs)
try:
    from bark_detector.utils.tensorflow_suppression import suppress_tensorflow_logging
    suppress_tensorflow_logging()
except ImportError:
    # Fallback configuration if utility not available
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    warnings.filterwarnings('ignore', category=UserWarning, module='tensorflow_hub')

try:
    from bark_detector.cli import main
    from bark_detector import *  # Re-export all main classes for backwards compatibility
    
    # Provide backwards compatibility warning
    warnings.warn(
        "Using bd.py directly is deprecated. Use 'uv run python -m bark_detector' instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
except ImportError as e:
    print(f"Error importing refactored modules: {e}")
    print("Falling back to original implementation...")
    
    # If the refactored modules fail to import, we could fall back to the original
    # For now, we'll just show an error
    print("Please use the original bd_original.py file if the refactored version has issues.")
    sys.exit(1)

if __name__ == '__main__':
    exit(main())