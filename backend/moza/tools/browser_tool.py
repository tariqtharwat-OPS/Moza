import time
from typing import Any

from loguru import logger

from moza.core.models import ToolResultPayload
from moza.tools.browser.utils import VALID_ACTIONS, ACTION_HELP
from moza.tools.playwright_engine import PlaywrightEngine
from moza.tools.registry import BaseTool, ToolParameter


class BrowserTool(BaseTool):
    name: str = "browser"
    description: str = (
        "Control a web browser: navigate to URLs, click elements, type text, "
        "extract content, take screenshots, scroll, and execute JavaScript."
    )
    version: str = "1.0.0"
    parameters: list[ToolParameter] = [
        ToolParameter(name="action", type="enum",
                      description=f"One of: {' | '.join(sorted(VALID_ACTIONS))}", required=True),
        ToolParameter(name="url", type="string",
                      description="URL to navigate to (required for 'navigate' action)", required=False),
        ToolParameter(name="selector", type="string",
                      description="CSS selector for click/type/extract_text actions", required=False),
        ToolParameter(name="text", type="string",
                      description="Text to type into element (required for 'type' action)", required=False),
        ToolParameter(name="direction", type="string",
                      description="Scroll direction: 'up' or 'down' (default: down)", required=False),
        ToolParameter(name="amount", type="integer",
                      description="Scroll amount in pixels (default: 300)", required=False),
        ToolParameter(name="script", type="string",
                      description="JavaScript to execute (required for 'execute_js' action)", required=False),
    ]
    returns: str = "Page content, current URL, page title, and optional screenshot."
    requires_confirmation: bool = True
    is_destructive: bool = False
    capabilities: list[str] = [
        "navigate", "click", "type", "extract_text", "screenshot",
        "scroll", "navigate_history", "execute_js", "close",
    ]

    def __init__(self, headless: bool = True, screenshots_dir: str | None = None) -> None:
        super().__init__()
        self._engine = PlaywrightEngine(headless=headless, screenshots_dir=screenshots_dir)
        # Test compatibility: expose internal state at tool level
        self._browser: Any = None
        self._page: Any = None

    @property
    def _playwright(self) -> Any:
        return self._engine._playwright if hasattr(self._engine, "_playwright") else None

    @property
    def _context(self) -> Any:
        return self._engine._context if hasattr(self._engine, "_context") else None

    async def on_load(self) -> None:
        logger.info("BrowserTool loaded (browser not started yet)")

    async def on_unload(self) -> None:
        await self._engine.close()
        self._browser = None
        self._page = None

    async def cleanup(self) -> None:
        await self._engine.close()
        self._browser = None
        self._page = None

    # ── dispatch ───────────────────────────────────────────────────────────

    async def execute(self, **kwargs: Any) -> Any:
        start = time.monotonic()
        action = kwargs.get("action")

        if not action:
            return ToolResultPayload.error(
                "'action' is required.", duration_ms=(time.monotonic() - start) * 1000,
            ).model_dump()

        if action not in VALID_ACTIONS:
            return ToolResultPayload.error(
                f"Unknown action: {action}. {ACTION_HELP}",
                duration_ms=(time.monotonic() - start) * 1000,
            ).model_dump()

        # Validate action-specific required params
        param_err = self._validate_params(action, kwargs)
        if param_err:
            return ToolResultPayload.error(
                param_err, duration_ms=(time.monotonic() - start) * 1000,
            ).model_dump()

        try:
            engine = self._engine
            result = await self._dispatch(engine, action, kwargs)
            self._sync_state()
            elapsed = (time.monotonic() - start) * 1000
            return ToolResultPayload.ok(
                stdout=result.get("stdout", ""),
                duration_ms=elapsed,
                metadata={k: v for k, v in result.items() if k != "stdout"},
            ).model_dump()
        except RuntimeError as e:
            # Browser may have been closed — try restarting once
            err_msg = str(e)
            logger.warning(f"BrowserTool: {action} failed ({err_msg}), attempting restart...")
            try:
                await self._engine.close()
                self._browser = None
                self._page = None
                result = await self._dispatch(self._engine, action, kwargs)
                self._sync_state()
                elapsed = (time.monotonic() - start) * 1000
                return ToolResultPayload.ok(
                    stdout=result.get("stdout", ""),
                    duration_ms=elapsed,
                    metadata={k: v for k, v in result.items() if k != "stdout"},
                ).model_dump()
            except Exception as e2:
                elapsed = (time.monotonic() - start) * 1000
                logger.error(f"BrowserTool: restart also failed: {e2}")
                return ToolResultPayload.error(
                    f"Browser {action} failed after restart: {e2}",
                    duration_ms=elapsed, exit_code=1,
                ).model_dump()
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(f"BrowserTool: {action} failed: {e}")
            return ToolResultPayload.error(
                f"Browser {action} failed: {e}",
                duration_ms=elapsed, exit_code=1,
            ).model_dump()

    # ── internal ───────────────────────────────────────────────────────────

    def _validate_params(self, action: str, kwargs: dict) -> str | None:
        if action in ("navigate",) and not kwargs.get("url"):
            return "'url' is required for navigate action."
        if action in ("click", "type", "extract_text") and action == "type" and kwargs.get("text") is None:
            return "'selector' and 'text' are required for type action."
        if action == "execute_js" and not kwargs.get("script"):
            return "'script' is required for execute_js action."
        return None

    async def _dispatch(self, engine, action: str, kwargs: dict) -> dict:
        dispatch = {
            "navigate": lambda: engine.navigate(kwargs["url"]),
            "click": lambda: engine.click(kwargs["selector"]),
            "type": lambda: engine.type_text(kwargs["selector"], kwargs["text"]),
            "extract_text": lambda: engine.extract_text(kwargs.get("selector")),
            "screenshot": lambda: engine.screenshot(),
            "scroll": lambda: engine.scroll(kwargs.get("direction", "down"), kwargs.get("amount", 300)),
            "back": lambda: engine.go_back(),
            "forward": lambda: engine.go_forward(),
            "get_url": lambda: engine.get_url(),
            "execute_js": lambda: engine.execute_js(kwargs["script"]),
            "close": lambda: self._handle_close(),
        }
        return await dispatch[action]()

    async def _handle_close(self) -> dict:
        await self._engine.close()
        self._browser = None
        self._page = None
        return {"stdout": "Browser closed."}

    def _sync_state(self) -> None:
        eng = self._engine
        self._browser = eng._context.browser if eng._context else None
        self._page = eng._page if hasattr(eng, "_page") else None
