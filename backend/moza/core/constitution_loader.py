"""
Constitution Loader for MOZA AI OS.

Loads constitution.yaml at startup and provides it to all components.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache


@lru_cache(maxsize=1)
def load_constitution(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the MOZA constitution from YAML file.
    
    Args:
        path: Optional path to constitution.yaml. Defaults to backend/constitution.yaml
        
    Returns:
        Parsed constitution dictionary
    """
    if path is None:
        # Default to root constitution.yaml (SSOT)
        path = Path(__file__).resolve().parent.parent.parent.parent / "constitution.yaml"
    else:
        path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Constitution not found at {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_constitution() -> Dict[str, Any]:
    """Get the loaded constitution (cached)."""
    return load_constitution()


def get_core_principles() -> list[Dict[str, Any]]:
    """Get the immutable core principles."""
    return get_constitution().get("core_principles", [])


def get_golden_rules() -> list[Dict[str, Any]]:
    """Get the golden rules for agent behavior."""
    return get_constitution().get("golden_rules", [])


def get_provider_ranking() -> list[Dict[str, Any]]:
    """Get the provider ranking for failover."""
    return get_constitution().get("provider_ranking", [])


def get_task_states() -> list[str]:
    """Get the authoritative task states."""
    return get_constitution().get("task_states", [])


def get_event_types() -> list[str]:
    """Get the authoritative event types."""
    return get_constitution().get("event_types", [])


def get_identity() -> Dict[str, Any]:
    """Get the MOZA identity information."""
    return get_constitution().get("identity", {})


# Convenience function for components that need constitution context
def get_constitution_context() -> Dict[str, Any]:
    """
    Get a condensed constitution context suitable for including in LLM prompts.
    """
    c = get_constitution()
    return {
        "identity": c.get("identity", {}),
        "core_principles": [p["title"] for p in c.get("core_principles", [])],
        "golden_rules": [r["title"] for r in c.get("golden_rules", [])],
        "task_states": c.get("task_states", []),
        "event_types": c.get("event_types", []),
    }