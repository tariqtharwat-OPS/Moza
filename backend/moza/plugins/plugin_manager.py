"""
Plugin Manager for MOZA

The PluginManager is responsible for:
1. Discovering available plugins
2. Managing plugin lifecycle (load/unload/activate/deactivate)
3. Providing plugin discovery and registration
4. Handling plugin dependencies
5. Managing plugin configuration

Design Principles:
- Plugins are optional - the system works without them
- Plugins are isolated - one plugin's failure doesn't affect others
- Plugins are discoverable - the system can find and load them
- Plugins are configurable - their behavior can be adjusted
"""

import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Type

from loguru import logger

from .interfaces import CapabilityInterface, ToolInterface, ProviderInterface


class PluginManager:
    """
    Manages the lifecycle of MOZA plugins.
    
    The PluginManager is responsible for:
    - Discovering available plugins
    - Loading and unloading plugins
    - Managing plugin dependencies
    - Providing plugin discovery and registration
    - Handling plugin configuration
    """

    def __init__(self, plugin_dirs: list[str] | None = None) -> None:
        """
        Initialize the PluginManager.
        
        Args:
            plugin_dirs: List of directories to search for plugins.
                       If None, uses the default plugin directory.
        """
        self._plugins: dict[str, dict[str, Any]] = {}
        self._plugin_dirs = plugin_dirs or ["plugins"]
        self._loaded_modules: dict[str, Any] = {}

    async def discover_plugins(self) -> list[dict[str, Any]]:
        """
        Discover available plugins in the plugin directories.
        
        Returns:
            List of plugin metadata dictionaries, each containing:
            - 'name': plugin name
            - 'version': plugin version
            - 'description': plugin description
            - 'author': plugin author
            - 'entry_point': module path
            - 'type': plugin type ('capability', 'tool', 'provider')
        """
        plugins: list[dict[str, Any]] = []

        for dir_name in self._plugin_dirs:
            plugin_dir = Path(dir_name)
            if not plugin_dir.exists():
                continue

            # Search for Python files in the plugin directory
            for py_file in plugin_dir.glob("*.py"):
                if py_file.stem == "__init__":
                    continue

                module_name = py_file.stem
                module_path = f"{plugin_dir.name}.{module_name}"

                try:
                    module = importlib.import_module(module_path)
                    self._loaded_modules[module_path] = module

                    # Check for plugin classes
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj):
                            if issubclass(obj, CapabilityInterface) and obj is not CapabilityInterface:
                                plugins.append({
                                    "name": obj.name,
                                    "version": obj.version,
                                    "description": obj.description,
                                    "author": obj.author,
                                    "entry_point": module_path,
                                    "type": "capability",
                                    "class": obj,
                                })
                            elif issubclass(obj, ToolInterface) and obj is not ToolInterface:
                                plugins.append({
                                    "name": obj.name,
                                    "version": obj.version,
                                    "description": obj.description,
                                    "author": "",
                                    "entry_point": module_path,
                                    "type": "tool",
                                    "class": obj,
                                })
                            elif issubclass(obj, ProviderInterface) and obj is not ProviderInterface:
                                plugins.append({
                                    "name": obj.name,
                                    "version": obj.model,
                                    "description": f"Provider for {obj.name}",
                                    "author": "",
                                    "entry_point": module_path,
                                    "type": "provider",
                                    "class": obj,
                                })
                except Exception as e:
                    logger.warning(f"Failed to load plugin {module_path}: {e}")

        return plugins

    async def load_plugin(self, plugin_info: dict[str, Any]) -> Any:
        """
        Load a plugin by its metadata.
        
        Args:
            plugin_info: Plugin metadata dictionary from discover_plugins()
        
        Returns:
            The loaded plugin instance
        
        Raises:
            ImportError: If the plugin cannot be imported
            ValueError: If the plugin type is unknown
        """
        plugin_class = plugin_info["class"]
        plugin_type = plugin_info["type"]

        # Create an instance of the plugin class
        try:
            plugin_instance = plugin_class()
        except Exception as e:
            raise ImportError(f"Failed to instantiate plugin {plugin_info['name']}: {e}") from e

        # Store the plugin instance
        self._plugins[plugin_info["name"]] = {
            "instance": plugin_instance,
            "type": plugin_type,
            "info": plugin_info,
        }

        logger.info(f"Loaded plugin: {plugin_info['name']} ({plugin_type}) v{plugin_info['version']}")
        return plugin_instance

    async def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin by its name.
        
        Args:
            plugin_name: Name of the plugin to unload
        
        Raises:
            KeyError: If the plugin is not found
        """
        plugin = self._plugins.pop(plugin_name, None)
        if plugin is None:
            raise KeyError(f"Plugin not found: {plugin_name}")

        # Call the plugin's on_unload method
        try:
            await plugin["instance"].on_unload()
        except Exception as e:
            logger.warning(f"Failed to unload plugin {plugin_name}: {e}")

        logger.info(f"Unloaded plugin: {plugin_name}")

    async def activate_plugin(self, plugin_name: str) -> None:
        """
        Activate a plugin by its name.
        
        Args:
            plugin_name: Name of the plugin to activate
        
        Raises:
            KeyError: If the plugin is not found
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {plugin_name}")

        # Call the plugin's on_load method
        try:
            await plugin["instance"].on_load()
        except Exception as e:
            logger.warning(f"Failed to activate plugin {plugin_name}: {e}")

        logger.info(f"Activated plugin: {plugin_name}")

    async def deactivate_plugin(self, plugin_name: str) -> None:
        """
        Deactivate a plugin by its name.
        
        Args:
            plugin_name: Name of the plugin to deactivate
        
        Raises:
            KeyError: If the plugin is not found
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {plugin_name}")

        # Call the plugin's on_unload method
        try:
            await plugin["instance"].on_unload()
        except Exception as e:
            logger.warning(f"Failed to deactivate plugin {plugin_name}: {e}")

        logger.info(f"Deactivated plugin: {plugin_name}")

    def get_plugin(self, plugin_name: str) -> dict[str, Any]:
        """
        Get a plugin by its name.
        
        Args:
            plugin_name: Name of the plugin to get
        
        Returns:
            Dictionary containing the plugin instance and metadata
        
        Raises:
            KeyError: If the plugin is not found
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {plugin_name}")
        return plugin

    def get_all_plugins(self) -> list[dict[str, Any]]:
        """
        Get all loaded plugins.
        
        Returns:
            List of dictionaries containing plugin instances and metadata
        """
        return list(self._plugins.values())

    def get_plugins_by_type(self, plugin_type: str) -> list[dict[str, Any]]:
        """
        Get all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to get ('capability', 'tool', 'provider')
        
        Returns:
            List of dictionaries containing plugin instances and metadata
        """
        return [
            plugin
            for plugin in self._plugins.values()
            if plugin["type"] == plugin_type
        ]

    async def reload_plugin(self, plugin_name: str) -> None:
        """
        Reload a plugin by its name.
        
        Args:
            plugin_name: Name of the plugin to reload
        
        Raises:
            KeyError: If the plugin is not found
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"Plugin not found: {plugin_name}")

        # Unload the plugin
        await self.unload_plugin(plugin_name)

        # Reload the module
        module_path = plugin["info"]["entry_point"]
        if module_path in self._loaded_modules:
            module = self._loaded_modules[module_path]
            importlib.reload(module)

        # Load the plugin again
        await self.load_plugin(plugin["info"])

        logger.info(f"Reloaded plugin: {plugin_name}")

    async def cleanup(self) -> None:
        """
        Clean up all plugins.
        
        This method is called when the PluginManager is no longer needed.
        It unloads all plugins and clears the plugin cache.
        """
        for plugin_name in list(self._plugins.keys()):
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                logger.warning(f"Failed to unload plugin {plugin_name}: {e}")

        self._plugins.clear()
        self._loaded_modules.clear()

        logger.info("PluginManager cleanup complete")
