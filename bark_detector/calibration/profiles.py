"""Calibration profile management"""

import logging
from pathlib import Path
from ..core.models import CalibrationProfile

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manage calibration profiles."""
    
    def __init__(self, profiles_dir: str = "profiles"):
        """Initialize profile manager."""
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
    
    def save_profile(self, profile: CalibrationProfile):
        """Save a calibration profile."""
        profile_path = self.profiles_dir / f"{profile.name}.json"
        profile.save(profile_path)
        logger.info(f"💾 Profile saved: {profile_path}")
    
    def load_profile(self, name: str) -> CalibrationProfile:
        """Load a calibration profile."""
        profile_path = self.profiles_dir / f"{name}.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")
            
        profile = CalibrationProfile.load(profile_path)
        logger.debug(f"📂 Loaded profile: {name}")
        return profile
    
    def list_profiles(self) -> list:
        """List all available profiles."""
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                profile = CalibrationProfile.load(profile_file)
                profiles.append({
                    'name': profile.name,
                    'created': profile.created_date,
                    'sensitivity': profile.sensitivity,
                    'notes': profile.notes
                })
            except Exception as e:
                logger.warning(f"Could not load profile {profile_file}: {e}")
        return profiles