"""Headless screenshot to verify transparent logo against dark sidebar."""
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()
        await page.goto("http://localhost:3000", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path="D:\\Moza\\reports\\moza_headless.png", full_page=False)
        print("Screenshot saved: moza_headless.png")
        
        # Try to get logo info
        aside = page.locator("aside").first
        if await aside.is_visible():
            print("Sidebar is visible")
            logo = aside.locator("img").first
            if await logo.is_visible():
                box = await logo.bounding_box()
                print(f"Logo: x={box['x']:.0f} y={box['y']:.0f} w={box['width']:.0f} h={box['height']:.0f}")
            else:
                print("Logo img not found in sidebar")
                print(await aside.inner_html())
        else:
            print("Sidebar not found")
            body = page.locator("body").first
            txt = await body.inner_text()
            print(txt[:500])
        await b.close()

asyncio.run(run())
