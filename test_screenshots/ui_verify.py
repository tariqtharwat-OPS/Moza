import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        errors = []
        page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}"))

        await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        await page.screenshot(path="ui_verify.png", full_page=True)

        body = await page.inner_text("body")

        # Check key elements
        has_welcome = "Welcome" in body
        has_input = "Ask MOZA" in body or "textarea" in body.lower() or "input" in body.lower()
        has_error_500 = "500" in body and "Internal Server Error" in body

        logo = await page.query_selector('img[alt="MOZA"]')
        logo_ok = logo and await logo.evaluate("el => el.complete && el.naturalWidth > 0")

        print(f"Welcome text: {has_welcome}")
        print(f"Input area: {has_input}")
        print(f"500 error page: {has_error_500}")
        print(f"Logo loaded: {logo_ok}")

        if errors:
            print(f"\nConsole messages ({len(errors)}):")
            for e in errors:
                if "error" in e.lower() or "fail" in e.lower():
                    print(f"  ERROR: {e}")
        else:
            print("No console messages.")

        if has_error_500:
            print("\n!!! INTERFACE IS RUINED - 500 ERROR !!!")
        elif has_welcome and has_input and logo_ok:
            print("\nINTERFACE LOOKS GOOD!")
        else:
            print(f"\nPartial: welcome={has_welcome} input={has_input} logo={logo_ok}")

        await browser.close()

asyncio.run(main())
