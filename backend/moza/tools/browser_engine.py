from abc import ABC, abstractmethod


class BrowserEngine(ABC):
    """Abstract interface for browser engines.

    Each method returns a dict with keys relevant to the action.
    All methods raise ValueError on invalid parameters and
    RuntimeError on browser-level failures.
    """

    @abstractmethod
    async def ensure_browser(self) -> None:
        """Lazily start the browser if not already running."""

    @abstractmethod
    async def close(self) -> None:
        """Shut down the browser and release resources."""

    @abstractmethod
    async def navigate(self, url: str) -> dict:
        """Navigate to url. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def click(self, selector: str) -> dict:
        """Click an element. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def type_text(self, selector: str, text: str) -> dict:
        """Fill a form field. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def extract_text(self, selector: str | None) -> dict:
        """Extract text content. Returns {stdout, title, url}."""

    @abstractmethod
    async def screenshot(self) -> dict:
        """Capture a screenshot. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def scroll(self, direction: str, amount: int) -> dict:
        """Scroll the page. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def go_back(self) -> dict:
        """Navigate back. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def go_forward(self) -> dict:
        """Navigate forward. Returns {stdout, title, url, screenshot_meta}."""

    @abstractmethod
    async def get_url(self) -> dict:
        """Return current page info. Returns {stdout, url, title}."""

    @abstractmethod
    async def execute_js(self, script: str) -> dict:
        """Run JavaScript. Returns {stdout, result}."""
