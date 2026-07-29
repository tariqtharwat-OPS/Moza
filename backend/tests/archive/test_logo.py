"""Open MOZA UI in headed mode so user can see the transparent logo."""
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page(
            viewport={"width": 1400, "height": 900}
        )
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Take a close-up screenshot of the logo in the left sidebar
        logo = page.locator("aside img[alt='MOZA']").first
        if await logo.is_visible():
            await logo.screenshot(path="D:\\Moza\\reports\\logo_transparent_test.png")
            print("Logo screenshot saved for inspection")

        # Full page screenshot
        await page.screenshot(path="D:\\Moza\\reports\\moza_with_logo.png", full_page=True)
        print("Full page screenshot saved")

        print("\nBrowser is open — look at the screen!")
        print("Logo should appear without white background.")
        print("Close the browser window when done checking.")

        # Keep browser open for user to inspect
        await page.wait_for_timeout(60000)  # 1 minute for user to look

        await browser.close()
        print("Browser closed.")

asyncio.run(run())
