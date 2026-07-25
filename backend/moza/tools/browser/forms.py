from moza.tools.browser.utils import CLICK_TIMEOUT_MS


async def click_element(page, selector: str) -> None:
    await page.click(selector)
    await page.wait_for_timeout(CLICK_TIMEOUT_MS)


async def fill_field(page, selector: str, text: str) -> None:
    await page.fill(selector, text)
