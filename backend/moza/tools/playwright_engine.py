from playwright._impl._errors import Error as PlaywrightError
from playwright.async_api import TimeoutError
from pathlib import Path
from typing import Optional

from loguru import logger

from moza.tools.browser import forms, navigation, dom, screenshot as shot_mod
from moza.tools.browser_engine import BrowserEngine


class PlaywrightEngine(BrowserEngine):
    """BrowserEngine implementation backed by Playwright (headless Chromium)."""

    def __init__(self, headless: bool = True, screenshots_dir: str | Path | None = None) -> None:
        self._headless = headless
        self._screenshots_dir = Path(screenshots_dir) if screenshots_dir else None

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    # ── lifecycle ──────────────────────────────────────────────────────────

    async def ensure_browser(self) -> None:
        if self._page is not None:
            return
        import asyncio
        import sys

        # Ensure Windows proactor event loop for subprocess support
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except RuntimeError:
                pass  # Policy already set

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await asyncio.wait_for(
                self._playwright.chromium.launch(
                    headless=self._headless,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security",
                    ],
                ),
                timeout=30.0,
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            self._page = await self._context.new_page()
            logger.info(f"PlaywrightEngine: browser started (headless={self._headless})")
        except ImportError:
            raise RuntimeError(
                "playwright is not installed. Run: pip install playwright && playwright install"
            )
        except asyncio.TimeoutError:
            logger.error("PlaywrightEngine: browser launch timed out (30s)")
            await self.close()
            raise RuntimeError("Browser launch timed out after 30s. Check that Chromium is installed.")
        except Exception as e:
            logger.error(f"PlaywrightEngine: failed to start browser: {e}")
            await self.close()
            raise RuntimeError(f"Failed to start browser: {e}")

    async def close(self) -> None:
        for target, name in [
            (self._page, "page"),
            (self._context, "context"),
            (self._browser, "browser"),
            (self._playwright, "playwright"),
        ]:
            if target is None:
                continue
            try:
                if name == "page":
                    await target.close()
                elif name in ("context", "browser"):
                    await target.close()
                elif name == "playwright":
                    await target.stop()
            except Exception as e:
                logger.warning(f"Error closing {name}: {e}")
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        logger.info("PlaywrightEngine: browser closed")

    # ── helpers ────────────────────────────────────────────────────────────

    async def _capture(self) -> dict:
        meta = await shot_mod.take_screenshot(self._page, self._screenshots_dir)
        title = await dom.get_title(self._page)
        url = dom.get_url(self._page)
        meta.update({"title": title, "url": url})
        return meta

    # ── actions ────────────────────────────────────────────────────────────

    async def navigate(self, url: str) -> dict:
        await self.ensure_browser()
        try:
            title, current_url, stdout = await navigation.navigate(self._page, url)
            meta = await self._capture()
            return {"stdout": stdout, **meta}
        except TimeoutError as e:
            logger.error(f"PlaywrightEngine: navigation timeout: {e}")
            return {
                "stdout": f"Navigation to {url} timed out",
                "title": "",
                "url": url,
                "error": str(e),
            }
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: navigation failed: {e}")
            return {
                "stdout": f"Navigation to {url} failed: {e}",
                "title": "",
                "url": url,
                "error": str(e),
            }

    async def click(self, selector: str) -> dict:
        await self.ensure_browser()
        try:
            stdout = await forms.click(self._page, selector)
            meta = await self._capture()
            return {"stdout": stdout, **meta}
        except TimeoutError as e:
            logger.error(f"PlaywrightEngine: click timeout: {e}")
            return {"stdout": f"Click on {selector} timed out", "error": str(e)}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: click failed: {e}")
            return {"stdout": f"Click on {selector} failed: {e}", "error": str(e)}

    async def type_text(self, selector: str, text: str) -> dict:
        await self.ensure_browser()
        try:
            stdout = await forms.type_text(self._page, selector, text)
            meta = await self._capture()
            return {"stdout": stdout, **meta}
        except TimeoutError as e:
            logger.error(f"PlaywrightEngine: type timeout: {e}")
            return {"stdout": f"Type into {selector} timed out", "error": str(e)}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: type failed: {e}")
            return {"stdout": f"Type into {selector} failed: {e}", "error": str(e)}

    async def screenshot(self) -> dict:
        await self.ensure_browser()
        meta = await self._capture()
        return {"stdout": f"Screenshot saved: {meta.get('screenshot_path', 'unknown')}", **meta}

    async def extract_text(self, selector: str | None = None) -> dict:
        await self.ensure_browser()
        try:
            text = await dom.extract_text(self._page, selector)
            meta = await self._capture()
            return {"stdout": text, **meta}
        except TimeoutError as e:
            logger.error(f"PlaywrightEngine: extract_text timeout: {e}")
            return {"stdout": f"Extract text timed out", "error": str(e)}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: extract_text failed: {e}")
            return {"stdout": f"Extract text failed: {e}", "error": str(e)}

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> dict:
        await self.ensure_browser()
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return {"stdout": f"Selector {selector} appeared"}
        except TimeoutError as e:
            logger.error(f"PlaywrightEngine: wait_for_selector timeout: {e}")
            return {"stdout": f"Wait for {selector} timed out", "error": str(e)}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: wait_for_selector failed: {e}")
            return {"stdout": f"Wait for {selector} failed: {e}", "error": str(e)}

    async def scroll(self, direction: str, amount: int) -> dict:
        await self.ensure_browser()
        try:
            delta = amount if direction == "down" else -amount
            await self._page.mouse.wheel(0, delta)
            meta = await self._capture()
            return {"stdout": f"Scrolled {direction} by {amount}", **meta}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: scroll failed: {e}")
            return {"stdout": f"Scroll failed: {e}", "error": str(e)}

    async def go_back(self) -> dict:
        await self.ensure_browser()
        try:
            await self._page.go_back()
            meta = await self._capture()
            return {"stdout": "Navigated back", **meta}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: go_back failed: {e}")
            return {"stdout": f"Go back failed: {e}", "error": str(e)}

    async def go_forward(self) -> dict:
        await self.ensure_browser()
        try:
            await self._page.go_forward()
            meta = await self._capture()
            return {"stdout": "Navigated forward", **meta}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: go_forward failed: {e}")
            return {"stdout": f"Go forward failed: {e}", "error": str(e)}

    async def get_url(self) -> dict:
        await self.ensure_browser()
        try:
            url = self._page.url
            title = await self._page.title()
            return {"stdout": url, "url": url, "title": title}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: get_url failed: {e}")
            return {"stdout": f"Get URL failed: {e}", "error": str(e)}

    async def execute_js(self, script: str) -> dict:
        await self.ensure_browser()
        try:
            result = await self._page.evaluate(script)
            return {"stdout": str(result), "result": result}
        except PlaywrightError as e:
            logger.error(f"PlaywrightEngine: execute_js failed: {e}")
            return {"stdout": f"JS execution failed: {e}", "error": str(e)}