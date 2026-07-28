"""
MOZA Plugin Architecture

This package provides the plugin system for MOZA, allowing new capabilities
to be added without modifying the core system.

Core Components:
- interfaces.py: CapabilityInterface, ToolInterface, ProviderInterface
- plugin_manager.py: PluginManager (lifecycle management)
- registry.py: PluginRegistry (plugin storage and lookup)

The plugin system is designed to be:
1. Optional - existing code works without it
2. Non-invasive - doesn't break existing functionality
3. Extensible - new plugin types can be added easily
4. Safe - plugins are isolated and can be disabled
"""

from .interfaces import CapabilityInterface, ToolInterface, ProviderInterface
from .plugin_manager import PluginManager
from .registry import PluginRegistry

__all__ = [
    "CapabilityInterface",
    "ToolInterface", 
    "ProviderInterface",
    "PluginManager",
    "PluginRegistry",
]
