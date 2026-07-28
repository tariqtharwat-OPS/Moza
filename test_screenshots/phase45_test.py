"""Test Phase 4.5: Browser Preview & Tool Execution Log"""

import asyncio, json, uuid
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # Test browser preview
        await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        await page.screenshot(path="phase45_browser_preview.png", full_page=True)

        # Test tool execution log
        tool_log_visible = await page.is_visible("text=Tool Execution Log")
        print(f"Tool execution log visible: {tool_log_visible}")

        # Test browser preview
        browser_preview_visible = await page.is_visible("img[alt='Browser screenshot']")
        print(f"Browser preview visible: {browser_preview_visible}")

        # Test live badge
        live_badge_visible = await page.is_visible("text=LIVE")
        print(f"Live badge visible: {live_badge_visible}")

        # Test tool execution log collapsible
        tool_log_button = await page.query_selector("button:has-text('Tool Execution Log')")
        if tool_log_button:
            await tool_log_button.click()
            await asyncio.sleep(1)
            tool_log_collapsed = not await page.is_visible("div.flex.flex-col.gap-1")
            print(f"Tool execution log collapsible: {tool_log_collapsed}")
        else:
            print("Tool execution log button not found")

        await browser.close()

asyncio.run(main())
