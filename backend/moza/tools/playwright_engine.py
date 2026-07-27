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

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._context = await asyncio.wait_for(
                self._playwright.chromium.launch_persistent_context(
                    user_data_dir="./browser_data",
                    headless=self._headless,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                ),
                timeout=30.0,
            )
            self._page = await self._context.new_page()
            logger.info(f"PlaywrightEngine: browser started (headless={self._headless}, persistent_context)")
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
        # With launch_persistent_context, closing the context closes the browser too.
        for target, name in [
            (self._page, "page"),
            (self._context, "context"),
            (self._playwright, "playwright"),
        ]:
            if target is None:
                continue
            try:
                if name == "page":
                    await target.close()
                elif name == "context":
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
                "stdout": f"Navigation to {url} failed",
                "title": "",
                "url": url,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"PlaywrightEngine: unexpected error during navigation: {e}")
            return {
                "stdout": f"Unexpected error navigating to {url}",
                "title": "",
                "url": url,
                "error": str(e),
            }

        except Exception as e:
            logger.error(f"PlaywrightEngine: unexpected error during navigation: {e}")
            return {
                "stdout": f"Unexpected error navigating to {url}",
                "title": "",
                "url": url,
                "error": str(e),
            }

    async def click(self, selector: str) -> dict:
        await self.ensure_browser()
        await forms.click_element(self._page, selector)
        title = await dom.get_title(self._page)
        current_url = dom.get_url(self._page)
        meta = await self._capture()
        return {"stdout": f"Clicked element: {selector}", "title": title, "url": current_url, **meta}

    async def type_text(self, selector: str, text: str) -> dict:
        await self.ensure_browser()
        await forms.fill_field(self._page, selector, text)
        title = await dom.get_title(self._page)
        current_url = dom.get_url(self._page)
        meta = await self._capture()
        return {"stdout": f"Typed '{text}' into element: {selector}", "title": title, "url": current_url, **meta}

    async def extract_text(self, selector: str | None = None) -> dict:
        await self.ensure_browser()
        content = await dom.extract_text(self._page, selector)
        title = await dom.get_title(self._page)
        current_url = dom.get_url(self._page)
        return {"stdout": content, "title": title, "url": current_url}

    async def screenshot(self) -> dict:
        await self.ensure_browser()
        title = await dom.get_title(self._page)
        current_url = dom.get_url(self._page)
        meta = await self._capture()
        return {"stdout": f"Screenshot taken: {current_url}", "title": title, "url": current_url, **meta}

    async def scroll(self, direction: str, amount: int) -> dict:
        await self.ensure_browser()
        title, current_url, stdout = await navigation.scroll(self._page, direction, amount)
        meta = await self._capture()
        return {"stdout": stdout, **meta}

    async def go_back(self) -> dict:
        await self.ensure_browser()
        title, current_url, stdout = await navigation.go_back(self._page)
        meta = await self._capture()
        return {"stdout": stdout, **meta}

    async def go_forward(self) -> dict:
        await self.ensure_browser()
        title, current_url, stdout = await navigation.go_forward(self._page)
        meta = await self._capture()
        return {"stdout": stdout, **meta}

    async def get_url(self) -> dict:
        await self.ensure_browser()
        title, current_url, stdout = await navigation.get_current_url(self._page)
        return {"stdout": stdout, "url": current_url, "title": title}

    async def execute_js(self, script: str) -> dict:
        await self.ensure_browser()
        result_str = await dom.execute_js(self._page, script)
        return {"stdout": result_str, "result": result_str}
