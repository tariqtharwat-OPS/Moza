"""Headless screenshot of MOZA to check logo against dark sidebar."""
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="D:\\Moza\\reports\\moza_now.png", full_page=False)
        print("Screenshot saved")
        
        # Check sidebar color
        sidebar = page.locator("aside").first
        if await sidebar.is_visible():
            box = await sidebar.bounding_box()
            print(f"Sidebar visible at {box}")
        # Check logo
        logo = page.locator("aside img").first
        if await logo.is_visible():
            box2 = await logo.bounding_box()
            print(f"Logo visible at {box2}")
        else:
            print("Logo NOT found")
            # Debug: what's in the sidebar?
            html = await page.locator("aside").first.inner_html()
            print(f"Sidebar HTML (first 500 chars): {html[:500]}")
        await b.close()

asyncio.run(run())
