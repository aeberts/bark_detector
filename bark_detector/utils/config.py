"""Configuration management for bark detector"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DetectionConfig:
    """Detection-related configuration."""
    sensitivity: float = 0.68
    analysis_sensitivity: float = 0.30
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    quiet_duration: float = 30.0
    session_gap_threshold: float = 10.0


@dataclass
class OutputConfig:
    """Output directory configuration."""
    recordings_dir: str = "recordings"
    reports_dir: str = "reports" 
    logs_dir: str = "logs"
    profiles_dir: str = "profiles"


@dataclass
class CalibrationConfig:
    """Calibration-related configuration."""
    default_profile: Optional[str] = None
    sensitivity_range: list = None
    calibration_steps: int = 20
    
    def __post_init__(self):
        if self.sensitivity_range is None:
            self.sensitivity_range = [0.01, 0.5]


@dataclass
class SchedulingConfig:
    """Scheduling and automation configuration."""
    auto_start: bool = False
    start_time: str = "06:00"
    stop_time: str = "19:00"
    timezone: str = "local"


@dataclass
class LegalConfig:
    """Legal violation detection configuration."""
    continuous_threshold: int = 300  # 5 minutes in seconds
    sporadic_threshold: int = 900    # 15 minutes in seconds  
    sporadic_gap_threshold: int = 300  # 5 minutes in seconds


@dataclass
class BarkDetectorConfig:
    """Complete bark detector configuration."""
    detection: DetectionConfig = None
    output: OutputConfig = None
    calibration: CalibrationConfig = None
    scheduling: SchedulingConfig = None
    legal: LegalConfig = None
    
    def __post_init__(self):
        if self.detection is None:
            self.detection = DetectionConfig()
        if self.output is None:
            self.output = OutputConfig()
        if self.calibration is None:
            self.calibration = CalibrationConfig()
        if self.scheduling is None:
            self.scheduling = SchedulingConfig()
        if self.legal is None:
            self.legal = LegalConfig()


class ConfigManager:
    """Manage configuration loading, validation, and saving."""
    
    DEFAULT_CONFIG_PATHS = [
        Path("config.json"),
        Path.home() / ".bark_detector" / "config.json",
        Path("/etc/bark_detector/config.json")
    ]
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = BarkDetectorConfig()
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> BarkDetectorConfig:
        """Load configuration from file with fallback to defaults."""
        if config_path:
            # Explicit path provided
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_file}")
            return self._load_from_file(config_file)
        
        # Search default locations
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                logger.info(f"Loading configuration from: {path}")
                return self._load_from_file(path)
        
        # No config file found, use defaults
        logger.info("No configuration file found, using defaults")
        return BarkDetectorConfig()
    
    def _load_from_file(self, config_path: Path) -> BarkDetectorConfig:
        """Load configuration from specific file."""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            # Validate and convert to config objects
            config = self._dict_to_config(data)
            logger.info(f"✅ Configuration loaded successfully from {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration from {config_path}: {e}")
    
    def _dict_to_config(self, data: Dict[str, Any]) -> BarkDetectorConfig:
        """Convert dictionary to configuration objects with validation."""
        config = BarkDetectorConfig()
        
        # Detection config
        if 'detection' in data:
            detection_data = data['detection']
            sensitivity = self._validate_float(detection_data.get('sensitivity', 0.68), 0.01, 1.0, 'sensitivity')
            # Backward compatibility: if analysis_sensitivity not specified or None, use sensitivity value
            analysis_sensitivity = detection_data.get('analysis_sensitivity', sensitivity)
            if analysis_sensitivity is None:
                analysis_sensitivity = sensitivity
            else:
                analysis_sensitivity = self._validate_float(analysis_sensitivity, 0.1, 1.0, 'analysis_sensitivity')

            config.detection = DetectionConfig(
                sensitivity=sensitivity,
                analysis_sensitivity=analysis_sensitivity,
                sample_rate=detection_data.get('sample_rate', 16000),
                chunk_size=detection_data.get('chunk_size', 1024),
                channels=detection_data.get('channels', 1),
                quiet_duration=self._validate_float(detection_data.get('quiet_duration', 30.0), 5.0, 300.0, 'quiet_duration'),
                session_gap_threshold=self._validate_float(detection_data.get('session_gap_threshold', 10.0), 1.0, 60.0, 'session_gap_threshold')
            )
        
        # Output config
        if 'output' in data:
            output_data = data['output']
            config.output = OutputConfig(
                recordings_dir=output_data.get('recordings_dir', 'recordings'),
                reports_dir=output_data.get('reports_dir', 'reports'),
                logs_dir=output_data.get('logs_dir', 'logs'),
                profiles_dir=output_data.get('profiles_dir', 'profiles')
            )
        
        # Calibration config
        if 'calibration' in data:
            calib_data = data['calibration']
            config.calibration = CalibrationConfig(
                default_profile=calib_data.get('default_profile'),
                sensitivity_range=calib_data.get('sensitivity_range', [0.01, 0.5]),
                calibration_steps=calib_data.get('calibration_steps', 20)
            )
        
        # Scheduling config
        if 'scheduling' in data:
            sched_data = data['scheduling']
            config.scheduling = SchedulingConfig(
                auto_start=sched_data.get('auto_start', False),
                start_time=sched_data.get('start_time', '06:00'),
                stop_time=sched_data.get('stop_time', '19:00'),
                timezone=sched_data.get('timezone', 'local')
            )
        
        # Legal config
        if 'legal' in data:
            legal_data = data['legal']
            config.legal = LegalConfig(
                continuous_threshold=legal_data.get('continuous_threshold', 300),
                sporadic_threshold=legal_data.get('sporadic_threshold', 900),
                sporadic_gap_threshold=legal_data.get('sporadic_gap_threshold', 300)
            )
        
        return config
    
    def _validate_float(self, value: float, min_val: float, max_val: float, name: str) -> float:
        """Validate float parameter is within range."""
        if not isinstance(value, (int, float)):
            raise ValueError(f"Configuration parameter '{name}' must be a number, got {type(value).__name__}")
        
        if not (min_val <= value <= max_val):
            raise ValueError(f"Configuration parameter '{name}' must be between {min_val} and {max_val}, got {value}")
        
        return float(value)
    
    def save_config(self, config: BarkDetectorConfig, config_path: Union[str, Path]):
        """Save configuration to file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary
        config_dict = asdict(config)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, sort_keys=True)
            logger.info(f"💾 Configuration saved to: {config_file}")
            
        except Exception as e:
            raise RuntimeError(f"Error saving configuration to {config_file}: {e}")
    
    def create_default_config(self, config_path: Union[str, Path]):
        """Create a default configuration file."""
        default_config = BarkDetectorConfig()
        self.save_config(default_config, config_path)
        logger.info(f"📝 Default configuration created: {config_path}")
    
    def merge_cli_args(self, config: BarkDetectorConfig, args: Any) -> BarkDetectorConfig:
        """Merge CLI arguments with configuration file settings (CLI takes precedence)."""
        # Create a copy to avoid mutating the original
        merged_config = BarkDetectorConfig(
            detection=DetectionConfig(**asdict(config.detection)),
            output=OutputConfig(**asdict(config.output)),
            calibration=CalibrationConfig(**asdict(config.calibration)),
            scheduling=SchedulingConfig(**asdict(config.scheduling)),
            legal=LegalConfig(**asdict(config.legal))
        )
        
        # Override with CLI arguments if provided
        if hasattr(args, 'sensitivity') and args.sensitivity is not None:
            merged_config.detection.sensitivity = args.sensitivity
        if hasattr(args, 'analysis_sensitivity') and args.analysis_sensitivity is not None:
            merged_config.detection.analysis_sensitivity = args.analysis_sensitivity
        if hasattr(args, 'output_dir') and args.output_dir is not None:
            merged_config.output.recordings_dir = args.output_dir
        if hasattr(args, 'profile') and args.profile is not None:
            merged_config.calibration.default_profile = args.profile
        
        return merged_config