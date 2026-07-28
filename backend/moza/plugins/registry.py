"""
Plugin Registry for MOZA

The PluginRegistry is responsible for:
1. Storing registered plugins
2. Allowing lookup by name/type
3. Integrating with existing ToolRegistry
4. Managing plugin capabilities
5. Providing plugin discovery

Design Principles:
- Compatible with existing ToolRegistry
- Plugins are optional - existing tools work without them
- Plugins are discoverable - the system can find and use them
- Capability-based discovery - plugins are found by what they can do
"""

from typing import Any, Type

from loguru import logger

from .interfaces import CapabilityInterface, ToolInterface, ProviderInterface
from ..tools.registry import ToolRegistry, BaseTool


class PluginRegistry:
    """
    Registry for MOZA plugins.
    
    The PluginRegistry stores and manages all registered plugins, allowing
    them to be discovered and used by the system.
    
    It integrates with the existing ToolRegistry to provide a unified
    interface for all tools and capabilities.
    """

    def __init__(self) -> None:
        """Initialize the PluginRegistry."""
        self._plugins: dict[str, dict[str, Any]] = {}
        self._capabilities: dict[str, list[str]] = {}
        self._tool_registry = ToolRegistry()

    async def register_plugin(self, plugin: Any) -> None:
        """
        Register a plugin with the registry.
        
        Args:
            plugin: Plugin instance to register
        
        Raises:
            ValueError: If the plugin is not a valid plugin type
        """
        if isinstance(plugin, CapabilityInterface):
            plugin_type = "capability"
        elif isinstance(plugin, ToolInterface):
            plugin_type = "tool"
        elif isinstance(plugin, ProviderInterface):
            plugin_type = "provider"
        else:
            raise ValueError(f"Unknown plugin type: {type(plugin)}")

        plugin_name = plugin.name
        self._plugins[plugin_name] = {
            "instance": plugin,
            "type": plugin_type,
        }

        # Register capabilities
        if plugin_type == "tool":
            for capability in plugin.capabilities:
                if capability not in self._capabilities:
                    self._capabilities[capability] = []
                self._capabilities[capability].append(plugin_name)

        # Register tools with the ToolRegistry
        if plugin_type == "tool":
            # Convert ToolInterface to BaseTool for compatibility
            class PluginToolAdapter(BaseTool):
                def __init__(self, plugin: ToolInterface):
                    self._plugin = plugin

                @property
                def name(self) -> str:
                    return self._plugin.name

                @property
                def description(self) -> str:
                    return self._plugin.description

                @property
                def version(self) -> str:
                    return self._plugin.version

                @property
                def parameters(self) -> list:
                    # Convert ToolInterface actions to ToolParameters
                    return [
                        {
                            "name": action,
                            "type": "string",
                            "description": f"Execute {action} action",
                            "required": True,
                        }
                        for action in self._plugin.actions
                    ]

                @property
                def capabilities(self) -> list[str]:
                    return self._plugin.capabilities

                @property
                def is_destructive(self) -> bool:
                    return self._plugin.is_destructive

                @property
                def requires_confirmation(self) -> bool:
                    return self._plugin.requires_confirmation

                async def execute(self, **kwargs: Any) -> Any:
                    action = kwargs.get("action")
                    if action not in self._plugin.actions:
                        raise ValueError(f"Invalid action: {action}")
                    return await self._plugin.execute(action, kwargs)

                async def on_load(self) -> None:
                    await self._plugin.on_load()

                async def on_unload(self) -> None:
                    await self._plugin.on_unload()

                async def cleanup(self) -> None:
                    await self._plugin.cleanup()

            # Register the adapter with the ToolRegistry
            await self._tool_registry.load(PluginToolAdapter(plugin))

        logger.info(f"Registered plugin: {plugin_name} ({plugin_type}) v{plugin.version}")

    async def unregister_plugin(self, plugin_name: str) -> None:
        """
        Unregister a plugin from the registry.
        
        Args:
            plugin_name: Name of the plugin to unregister
        
        Raises:
            KeyError: If the plugin is not found
        """
        plugin = self._plugins.pop(plugin_name, None)
        if plugin is None:
            raise KeyError(f"Plugin not found: {plugin_name}")

        # Unregister capabilities
        if plugin["type"] == "tool":
            for capability in plugin["instance"].capabilities:
                if capability in self._capabilities:
                    self._capabilities[capability].remove(plugin_name)
                    if not self._capabilities[capability]:
                        del self._capabilities[capability]

        # Unregister tools from the ToolRegistry
        if plugin["type"] == "tool":
            await self._tool_registry.unload(plugin_name)

        logger.info(f"Unregistered plugin: {plugin_name}")

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
        Get all registered plugins.
        
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

    def get_plugins_by_capability(self, capability: str) -> list[str]:
        """
        Get all plugins that provide a specific capability.
        
        Args:
            capability: Capability to search for
        
        Returns:
            List of plugin names that provide the capability
        """
        return self._capabilities.get(capability, [])

    def get_tool_registry(self) -> ToolRegistry:
        """
        Get the underlying ToolRegistry.
        
        Returns:
            The ToolRegistry instance used by this PluginRegistry
        """
        return self._tool_registry

    async def cleanup(self) -> None:
        """
        Clean up all plugins and the ToolRegistry.
        
        This method is called when the PluginRegistry is no longer needed.
        It unregisters all plugins and cleans up the ToolRegistry.
        """
        for plugin_name in list(self._plugins.keys()):
            try:
                await self.unregister_plugin(plugin_name)
            except Exception as e:
                logger.warning(f"Failed to unregister plugin {plugin_name}: {e}")

        await self._tool_registry.cleanup_all()

        logger.info("PluginRegistry cleanup complete")


_plugin_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """
    Get the global PluginRegistry instance.
    
    Returns:
        The global PluginRegistry instance
    """
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
    return _plugin_registry
