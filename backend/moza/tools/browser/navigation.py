from moza.tools.browser.utils import SCROLL_TIMEOUT_MS, BACK_TIMEOUT_MS, FORWARD_TIMEOUT_MS


async def navigate(page, url: str) -> tuple[str, str, str]:
    await page.goto(url, wait_until="domcontentloaded")
    title = await page.title()
    current_url = page.url
    return title, current_url, f"Navigated to {url}\nTitle: {title}"


async def go_back(page) -> tuple[str, str, str]:
    await page.go_back()
    await page.wait_for_timeout(BACK_TIMEOUT_MS)
    title = await page.title()
    current_url = page.url
    return title, current_url, f"Navigated back to: {current_url}"


async def go_forward(page) -> tuple[str, str, str]:
    await page.go_forward()
    await page.wait_for_timeout(FORWARD_TIMEOUT_MS)
    title = await page.title()
    current_url = page.url
    return title, current_url, f"Navigated forward to: {current_url}"


async def scroll(page, direction: str, amount: int) -> tuple[str, str, str]:
    scroll_y = amount if direction == "down" else -amount
    await page.evaluate(f"window.scrollBy(0, {scroll_y})")
    await page.wait_for_timeout(SCROLL_TIMEOUT_MS)
    title = await page.title()
    current_url = page.url
    return title, current_url, f"Scrolled {direction} {amount}px"


async def get_current_url(page) -> tuple[str, str, str]:
    current_url = page.url
    title = await page.title()
    return title, current_url, f"URL: {current_url}\nTitle: {title}"
