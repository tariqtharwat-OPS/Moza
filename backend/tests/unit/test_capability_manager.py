import pytest
from moza.tools.registry import ToolRegistry, BaseTool


class _TestTool(BaseTool):
    name = "test_tool"
    description = "A generic test tool"

    async def execute(self, **kwargs):
        return {"success": True}


class _FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Filesystem operations"

    async def execute(self, **kwargs):
        return {"success": True, "stdout": "file read"}


class _TerminalTool(BaseTool):
    name = "terminal"
    description = "Terminal operations"
    is_destructive = True

    async def execute(self, **kwargs):
        return {"success": True, "stdout": "command output"}


class TestCapabilityCheck:
    def test_no_restrictions_allows_all(self):
        registry = ToolRegistry()
        registry.set_agent_capabilities("MockAgent", [])
        assert registry.check_capability("MockAgent", "any_tool") is True

    def test_no_config_allows_all(self):
        registry = ToolRegistry()
        assert registry.check_capability("UnknownAgent", "any_tool") is True

    def test_allowed_tool_passes(self):
        registry = ToolRegistry()
        registry.set_agent_capabilities("MockAgent", ["filesystem"])
        assert registry.check_capability("MockAgent", "filesystem") is True

    def test_disallowed_tool_raises_permission_error(self):
        registry = ToolRegistry()
        registry.set_agent_capabilities("MockAgent", ["filesystem"])
        with pytest.raises(PermissionError, match="not allowed"):
            registry.check_capability("MockAgent", "terminal")

    def test_multiple_allowed_tools(self):
        registry = ToolRegistry()
        registry.set_agent_capabilities("MockAgent", ["filesystem", "terminal"])
        assert registry.check_capability("MockAgent", "filesystem") is True
        assert registry.check_capability("MockAgent", "terminal") is True

    def test_per_agent_configs_independent(self):
        registry = ToolRegistry()
        registry.set_agent_capabilities("AgentA", ["filesystem"])
        registry.set_agent_capabilities("AgentB", ["terminal"])
        assert registry.check_capability("AgentA", "filesystem") is True
        with pytest.raises(PermissionError):
            registry.check_capability("AgentA", "terminal")
        assert registry.check_capability("AgentB", "terminal") is True
        with pytest.raises(PermissionError):
            registry.check_capability("AgentB", "filesystem")

    def test_error_message_contains_tool_name_and_allowed_list(self):
        registry = ToolRegistry()
        registry.set_agent_capabilities("Agent", ["filesystem"])
        with pytest.raises(PermissionError) as exc:
            registry.check_capability("Agent", "browser")
        assert "browser" in str(exc.value)
        assert "filesystem" in str(exc.value)
        assert "Agent" in str(exc.value)


class TestCapabilityWithToolExecution:
    async def test_execute_allowed_tool(self):
        registry = ToolRegistry()
        await registry.load(_FilesystemTool())
        registry.set_agent_capabilities("MockAgent", ["filesystem"])
        assert registry.check_capability("MockAgent", "filesystem") is True
        result = await registry.execute_tool("filesystem")
        assert result["success"] is True

    async def test_execute_disallowed_tool_raises(self):
        registry = ToolRegistry()
        await registry.load(_TerminalTool())
        registry.set_agent_capabilities("MockAgent", ["filesystem"])
        with pytest.raises(PermissionError):
            registry.check_capability("MockAgent", "terminal")
