"""Vision System Configuration Loader

Loads and manages Vision System configuration from various sources.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionSystemConfig:
    """Vision System configuration manager"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load Vision System configuration from file or environment"""
        if cls._config is not None:
            return cls._config
        
        # Default configuration
        default_config = cls._get_default_config()
        
        # Try to load from file
        file_config = {}
        if config_path is None:
            config_path = os.environ.get(
                "DHAFNCK_VISION_CONFIG_PATH",
                "./config/vision_system_config.yaml"
            )
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded Vision System config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Merge configurations (file config overrides defaults)
        config = cls._deep_merge(default_config, file_config)
        
        # Apply environment variable overrides
        config = cls._apply_env_overrides(config)
        
        cls._config = config
        return config
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get current configuration"""
        if cls._config is None:
            cls.load_config()
        return cls._config
    
    @classmethod
    def is_vision_enabled(cls) -> bool:
        """Check if Vision System is enabled"""
        config = cls.get_config()
        return config.get("vision_system", {}).get("enabled", True)
    
    @classmethod
    def is_phase_enabled(cls, phase: str) -> bool:
        """Check if a specific phase is enabled"""
        config = cls.get_config()
        vision_config = config.get("vision_system", {})
        
        # Check master switch first
        if not vision_config.get("enabled", True):
            return False
        
        # Check phase-specific config
        phase_config = vision_config.get(phase, {})
        return phase_config.get("enabled", True)
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default Vision System configuration"""
        return {
            "vision_system": {
                "enabled": True,
                "context_enforcement": {
                    "enabled": True,
                    "require_completion_summary": True,
                    "min_summary_length": 50
                },
                "progress_tracking": {
                    "enabled": True,
                    "auto_calculate_from_subtasks": True
                },
                "workflow_hints": {
                    "enabled": True,
                    "max_hints_per_response": 5
                },
                "agent_coordination": {
                    "enabled": True,
                    "work_distribution": {
                        "strategy": "skill_based"
                    }
                },
                "vision_enrichment": {
                    "enabled": True,
                    "include_in_all_responses": True
                }
            },
            "performance": {
                "cache_settings": {
                    "vision_cache_ttl": 3600,
                    "use_memory_cache": True
                },
                "overhead_limits": {
                    "max_enrichment_time_ms": 100,
                    "fail_gracefully": True
                }
            }
        }
    
    @staticmethod
    def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = VisionSystemConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        # Master switch
        if "DHAFNCK_ENABLE_VISION" in os.environ:
            enabled = os.environ["DHAFNCK_ENABLE_VISION"].lower() == "true"
            config["vision_system"]["enabled"] = enabled
        
        # Phase-specific switches
        phase_env_map = {
            "DHAFNCK_VISION_CONTEXT_ENFORCEMENT": "context_enforcement",
            "DHAFNCK_VISION_PROGRESS_TRACKING": "progress_tracking",
            "DHAFNCK_VISION_WORKFLOW_HINTS": "workflow_hints",
            "DHAFNCK_VISION_AGENT_COORDINATION": "agent_coordination",
            "DHAFNCK_VISION_ENRICHMENT": "vision_enrichment"
        }
        
        for env_var, phase_key in phase_env_map.items():
            if env_var in os.environ:
                enabled = os.environ[env_var].lower() == "true"
                if phase_key in config["vision_system"]:
                    config["vision_system"][phase_key]["enabled"] = enabled
        
        # Performance settings
        if "DHAFNCK_VISION_MAX_OVERHEAD_MS" in os.environ:
            try:
                max_overhead = int(os.environ["DHAFNCK_VISION_MAX_OVERHEAD_MS"])
                config["performance"]["overhead_limits"]["max_enrichment_time_ms"] = max_overhead
            except ValueError:
                pass
        
        return config


# Convenience functions
def get_vision_config() -> Dict[str, Any]:
    """Get Vision System configuration"""
    return VisionSystemConfig.get_config()


def is_vision_enabled() -> bool:
    """Check if Vision System is enabled"""
    return VisionSystemConfig.is_vision_enabled()


def is_phase_enabled(phase: str) -> bool:
    """Check if a specific Vision System phase is enabled"""
    return VisionSystemConfig.is_phase_enabled(phase)