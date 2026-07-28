"""Test Google via direct search URL."""
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        # Direct search URL
        await page.goto(
            "https://www.google.com/search?q=red+snapper+frozen+exporter+Indonesia",
            wait_until="domcontentloaded"
        )
        await page.wait_for_timeout(5000)

        # Check h3 elements
        h3s = page.locator("h3")
        count = await h3s.count()
        print(f"Found {count} h3 elements")
        for i in range(min(count, 10)):
            text = await h3s.nth(i).inner_text()
            print(f"  h3[{i}]: {text[:100]}")

        # Try to get links
        links = page.locator("a")
        lc = await links.count()
        print(f"Total links: {lc}")
        visible_links = 0
        for i in range(min(lc, 50)):
            try:
                if await links.nth(i).is_visible():
                    txt = await links.nth(i).inner_text()
                    if txt.strip():
                        visible_links += 1
                        if visible_links <= 10:
                            print(f"  visible link: {txt.strip()[:80]}")
            except:
                pass

        # Body text
        body = await page.inner_text("body")
        if "red snapper" in body.lower():
            print("Found 'red snapper' in body text")
        if "Indonesia" in body:
            print("Found 'Indonesia' in body text")
        print(f"Body length: {len(body)} chars")

        await page.screenshot(path="D:\\Moza\\reports\\google_debug2.png", full_page=True)
        print("Screenshot saved")
        await b.close()

asyncio.run(test())
