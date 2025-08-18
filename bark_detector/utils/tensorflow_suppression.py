"""TensorFlow logging suppression utilities"""

import os
import warnings

def suppress_tensorflow_logging():
    """
    Comprehensive TensorFlow logging suppression for all platforms.
    Must be called BEFORE importing TensorFlow for maximum effectiveness.
    """
    # Primary TensorFlow logging suppression
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 0=INFO, 1=WARN, 2=ERROR, 3=FATAL
    
    # Additional TensorFlow environment variables for Intel/CPU builds
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations logging
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'  # Prevent GPU memory allocation warnings
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Force CPU-only operation
    
    # Suppress specific TensorFlow warnings and deprecation messages
    warnings.filterwarnings('ignore', category=UserWarning, module='tensorflow_hub')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*pkg_resources.*')
    warnings.filterwarnings('ignore', category=FutureWarning, module='tensorflow')
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='tensorflow')
    
    # Suppress specific message patterns that appear in TensorFlow debug output
    warnings.filterwarnings('ignore', message='.*This TensorFlow binary is optimized.*')
    warnings.filterwarnings('ignore', message='.*DEBUG INFO.*')
    warnings.filterwarnings('ignore', message='.*Executor start aborting.*')

def configure_tensorflow_after_import():
    """
    Additional TensorFlow configuration that must be done after TensorFlow is imported.
    Call this after importing TensorFlow.
    """
    try:
        import tensorflow as tf
        
        # Set TensorFlow logging levels
        tf.get_logger().setLevel('ERROR')
        
        # Also set v1 logging if available
        if hasattr(tf, 'compat') and hasattr(tf.compat, 'v1'):
            tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
        
        # Disable TensorFlow debug output for specific operations
        try:
            tf.config.experimental.enable_op_determinism()
        except Exception:
            pass
            
        # Force CPU-only operation to avoid GPU-related warnings
        try:
            tf.config.set_visible_devices([], 'GPU')
        except Exception:
            pass
            
    except ImportError:
        # TensorFlow not available, nothing to configure
        pass

# Apply suppression immediately when this module is imported
suppress_tensorflow_logging()