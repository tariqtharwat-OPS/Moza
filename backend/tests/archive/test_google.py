"""Test Google search selectors with screenshot."""
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto("https://www.google.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # Accept cookies
        for txt in ["Accept all", "Accept", "I agree", "Reject all"]:
            try:
                btn = page.locator(f'button:has-text("{txt}")').first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    print(f"Clicked: {txt}")
                    break
            except:
                pass

        # Search
        box = page.locator('textarea[name="q"], input[name="q"]').first
        await box.fill("red snapper frozen exporter Indonesia")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)

        # Debug HTML structure
        h3s = page.locator("h3")
        count = await h3s.count()
        print(f"Found {count} h3 elements")
        for i in range(min(count, 10)):
            text = await h3s.nth(i).inner_text()
            print(f"  h3[{i}]: {text[:100]}")

        # Check various selectors
        for sel in ["div.g", "div[data-sokoban-container]", "#center_col div", "div.yuRUbf", "div#rso div.g"]:
            els = page.locator(sel)
            c = await els.count()
            print(f'  "{sel}": {c} elements')

        # Try to extract from the whole page
        all_text = await page.inner_text("body")
        idx = all_text.find("red snapper")
        if idx >= 0:
            print(f"Found 'red snapper' at index {idx}")
            print(f"Context: ...{all_text[max(0,idx-50):idx+200]}...")
        
        await page.screenshot(path="D:\\Moza\\reports\\google_debug.png", full_page=True)
        print("Screenshot saved to D:\\Moza\\reports\\google_debug.png")
        await b.close()

asyncio.run(test())
