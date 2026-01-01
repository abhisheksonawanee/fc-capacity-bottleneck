"""Utility functions for FC capacity planning project."""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file relative to project root
        
    Returns:
        Dictionary containing configuration
    """
    project_root = Path(__file__).parent.parent
    config_file = project_root / config_path
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def ensure_dir(path: Path) -> None:
    """Ensure directory exists, create if it doesn't.
    
    Args:
        path: Path to directory
    """
    path.mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """Get project root directory.
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent

