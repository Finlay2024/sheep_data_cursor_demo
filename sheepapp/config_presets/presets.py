"""Configuration presets for different analysis scenarios."""

import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

from ..core.models import AnalysisConfig
from ..core.constants import DEFAULT_PRESETS

logger = logging.getLogger(__name__)

class ConfigPresets:
    """Manages configuration presets for different analysis scenarios."""
    
    def __init__(self, presets_dir: str = None):
        if presets_dir is None:
            presets_dir = Path(__file__).parent
        self.presets_dir = Path(presets_dir)
        self.presets = {}
        self._load_presets()
    
    def _load_presets(self):
        """Load all available presets."""
        # Load from YAML files
        for yaml_file in self.presets_dir.glob("*.yaml"):
            preset_name = yaml_file.stem
            try:
                with open(yaml_file, 'r') as f:
                    preset_data = yaml.safe_load(f)
                self.presets[preset_name] = preset_data
                logger.info(f"Loaded preset: {preset_name}")
            except Exception as e:
                logger.error(f"Error loading preset {preset_name}: {e}")
        
        # Add default presets if no YAML files found
        if not self.presets:
            self.presets = DEFAULT_PRESETS.copy()
            logger.info("Using default presets")
    
    def get_preset(self, name: str) -> Dict[str, Any]:
        """Get a specific preset configuration."""
        if name not in self.presets:
            available = list(self.presets.keys())
            raise ValueError(f"Preset '{name}' not found. Available: {available}")
        
        return self.presets[name]
    
    def get_available_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list(self.presets.keys())
    
    def create_config_from_preset(self, name: str) -> AnalysisConfig:
        """Create AnalysisConfig from a preset."""
        preset_data = self.get_preset(name)
        
        # Convert preset data to AnalysisConfig
        config_data = {
            'contemporary_group_window_days': preset_data.get('contemporary_group_window_days', 30),
            'normalization_method': preset_data.get('normalization_method', 'percentile'),
            'min_birth_weight': preset_data.get('min_birth_weight', 2.0),
            'max_footrot_score': preset_data.get('max_footrot_score', 4),
            'max_dag_score': preset_data.get('max_dag_score', 4),
            'min_weaning_weight': preset_data.get('min_weaning_weight', 20.0),
            'max_micron': preset_data.get('max_micron', 25.0),
            'bse_pass_required': preset_data.get('bse_pass_required', True),
            'weights': preset_data.get('weights', {}),
            'trait_weights': preset_data.get('trait_weights', {})
        }
        
        return AnalysisConfig(**config_data)
    
    def save_preset(self, name: str, config: AnalysisConfig, description: str = ""):
        """Save a configuration as a new preset."""
        preset_data = {
            'name': name,
            'description': description,
            'contemporary_group_window_days': config.contemporary_group_window_days,
            'normalization_method': config.normalization_method,
            'min_birth_weight': config.min_birth_weight,
            'max_footrot_score': config.max_footrot_score,
            'max_dag_score': config.max_dag_score,
            'min_weaning_weight': config.min_weaning_weight,
            'max_micron': config.max_micron,
            'bse_pass_required': config.bse_pass_required,
            'weights': config.weights,
            'trait_weights': config.trait_weights
        }
        
        # Save to YAML file
        yaml_file = self.presets_dir / f"{name}.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(preset_data, f, default_flow_style=False, indent=2)
        
        # Update in-memory presets
        self.presets[name] = preset_data
        logger.info(f"Saved preset: {name}")

def load_preset(name: str) -> AnalysisConfig:
    """Convenience function to load a preset configuration."""
    presets = ConfigPresets()
    return presets.create_config_from_preset(name)

def get_available_presets() -> List[str]:
    """Convenience function to get available preset names."""
    presets = ConfigPresets()
    return presets.get_available_presets()
