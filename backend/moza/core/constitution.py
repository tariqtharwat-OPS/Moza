"""
Constitution Loader for Moza AI OS.
Loads the system constitution from YAML at startup.
"""

import yaml
from pathlib import Path
from typing import Any


_constitution_cache: dict[str, Any] | None = None


def load_constitution(path: Path) -> dict[str, Any]:
    """
    Load the constitution from YAML file.
    
    Args:
        path: Path to constitution.yaml
        
    Returns:
        Parsed constitution dict
        
    Raises:
        FileNotFoundError: If constitution file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    global _constitution_cache
    
    if _constitution_cache is not None:
        return _constitution_cache
    
    if not path.exists():
        raise FileNotFoundError(f"Constitution file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        _constitution_cache = yaml.safe_load(f)
    
    return _constitution_cache


def get_constitution() -> dict[str, Any]:
    """Get the cached constitution. Loads if not already loaded."""
    global _constitution_cache
    if _constitution_cache is None:
        # Default to project root
        from pathlib import Path
        _constitution_cache = load_constitution(Path(__file__).parent.parent.parent.parent / "constitution.yaml")
    return _constitution_cache


def get_golden_rules() -> list[dict[str, str]]:
    """Extract golden rules from constitution for quick access."""
    const = get_constitution()
    return const.get('golden_rules', [])


def get_identity() -> dict[str, str]:
    """Get identity information from constitution."""
    const = get_constitution()
    return const.get('identity', {})


def get_principles() -> list[dict[str, str]]:
    """Get principles from constitution."""
    const = get_constitution()
    return const.get('principles', [])


def get_immutable_constraints() -> list[str]:
    """Get immutable constraints from constitution."""
    const = get_constitution()
    return const.get('immutable_constraints', [])