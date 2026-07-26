import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright

async def main():
    print("=" * 60)
    print("LIVE VISUAL VERIFICATION")
    print("=" * 60)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        page = await browser.new_page()
        
        print("\n[1/5] Navigating to http://localhost:3000 ...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        print("[2/5] Checking page content for MockAgent...")
        page_text = await page.inner_text("body")
        if "mock agent" in page_text.lower():
            print("  CRITICAL FAILURE: MockAgent detected on page!")
        else:
            print("  LiteLLMToolAgent is active (no MockAgent warning)")

        print("[3/5] Typing test prompt...")
        input_box = page.locator("textarea").first
        await input_box.wait_for(state="visible", timeout=5000)
        await input_box.fill("create a file called test.txt in Documents with Hello MOZA")
        await page.keyboard.press("Enter")
        print("  Enter pressed. Waiting for agent response...")

        print("[4/5] Monitoring for events (15 seconds)...")
        await page.wait_for_timeout(15000)
        
        # Read full conversation
        body_text = await page.inner_text("body")
        print("\n[4b] Page text after 15s:")
        print(body_text[:2000])
        
        print("[5/5] Capturing screenshot...")
        await page.screenshot(path="D:\\Moza\\verification_result.png", full_page=True)
        print("  Screenshot saved to D:\\Moza\\verification_result.png")
        
        await browser.close()
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
