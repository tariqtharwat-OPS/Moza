import pytest

from moza.tools.browser_tool import BrowserTool
from moza.tools.registry import ToolRegistry


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register(BrowserTool(headless=True))
    return r


@pytest.mark.asyncio
async def test_browser_tool_registered(registry):
    tool = registry.get("browser")
    assert tool is not None
    assert tool.name == "browser"
    assert tool.version == "1.0.0"


@pytest.mark.asyncio
async def test_browser_tool_metadata():
    tool = BrowserTool(headless=True)
    assert tool.name == "browser"
    assert tool.requires_confirmation is True
    assert tool.is_destructive is False
    assert "navigate" in tool.capabilities
    assert "screenshot" in tool.capabilities
    assert "click" in tool.capabilities


@pytest.mark.asyncio
async def test_browser_tool_missing_action(registry):
    result = await registry.execute_tool("browser")
    assert result.get("success") is False
    assert "action" in result.get("stderr", "")


@pytest.mark.asyncio
async def test_browser_tool_unknown_action(registry):
    result = await registry.execute_tool("browser", action="nonexistent")
    assert result.get("success") is False
    assert "Unknown action" in result.get("stderr", "")


@pytest.mark.asyncio
async def test_browser_tool_missing_url(registry):
    result = await registry.execute_tool("browser", action="navigate")
    assert result.get("success") is False
    assert "url" in result.get("stderr", "")


@pytest.mark.asyncio
async def test_browser_tool_cleanup():
    tool = BrowserTool(headless=True)
    await tool.on_load()
    await tool.cleanup()


@pytest.mark.asyncio
async def test_browser_tool_lifecycle():
    tool = BrowserTool(headless=True)
    assert tool._browser is None
    await tool.on_load()
    await tool.on_unload()
    assert tool._browser is None
