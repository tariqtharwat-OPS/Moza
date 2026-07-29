"""Open MOZA UI to verify transparent logo."""
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False, slow_mo=500)
        page = await b.new_page()
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Close-up of logo
        logo = page.locator("aside img[alt='MOZA']").first
        if await logo.is_visible():
            await logo.screenshot(path="D:\\Moza\\reports\\logo_final.png")
            print("Logo close-up saved")
        await page.screenshot(path="D:\\Moza\\reports\\moza_final.png", full_page=True)
        print("Full page saved")

        print("\nBrowser open - check the logo. Close when done.")
        await page.wait_for_timeout(30000)
        await b.close()

asyncio.run(run())
