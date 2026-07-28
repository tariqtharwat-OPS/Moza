"""
Use MOZA's own chat interface to perform the research task.
Watch the browser — this runs HEADED with slow_mo=1500.
"""

import asyncio, json, time
from pathlib import Path
from datetime import datetime

REPORTS = Path("D:/Moza/reports")
REPORTS.mkdir(parents=True, exist_ok=True)

async def run():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        # 1. Open MOZA frontend
        print("\n>>> Opening MOZA Chat UI at http://localhost:3000")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(REPORTS / "01_moza_loaded.png"))
        print("    Screenshot: MOZA loaded")

        # 2. Check what's visible
        body = await page.inner_text("body")
        print(f"    Page text: {body[:200]}...")

        # 3. Find and fill input
        textarea = page.locator("textarea").first
        input_visible = await textarea.is_visible()
        print(f"    Textarea visible: {input_visible}")

        if not input_visible:
            # Try other selectors
            textarea = page.locator("input[type='text'], div[contenteditable='true'], .input-area textarea").first
            input_visible = await textarea.is_visible(timeout=5000)
            print(f"    Alt input visible: {input_visible}")

        if input_visible:
            # Send the research task
            task_msg = (
                "Please research 'red snapper' frozen fish exporters and importers "
                "in Indonesia, Vietnam, and Malaysia. For each country, find real company names, "
                "websites, and any pricing information. After collecting the data, create: "
                "1) a CSV file at D:\\Moza\\reports\\red_snapper_importers.csv with columns: Country, Company Name, Website, Notes/Pricing "
                "2) a professional HTML report at D:\\Moza\\reports\\red_snapper_report.html with inline CSS styling ready for print"
            )
            print(f"\n>>> Sending task to MOZA...")
            print(f"    Task: {task_msg[:120]}...")
            await textarea.fill(task_msg)
            await page.wait_for_timeout(1000)

            # Take screenshot before submitting
            await page.screenshot(path=str(REPORTS / "02_before_submit.png"))

            # Submit
            await page.keyboard.press("Enter")
            print("    Submitted! Watching for response...")

            # Monitor for events and response
            start_time = time.time()
            max_wait = 180  # 3 minutes max
            last_response_len = 0
            stable_count = 0

            while time.time() - start_time < max_wait:
                await page.wait_for_timeout(2000)

                # Check for agent messages
                agent_bubbles = page.locator(".prose.prose-invert")
                bubble_count = await agent_bubbles.count()
                if bubble_count > 0:
                    last_text = await agent_bubbles.last.inner_text()
                    if len(last_text) > last_response_len:
                        last_response_len = len(last_text)
                        print(f"    Agent response growing ({len(last_text)} chars)...")

                # Check for tool calls in execution panel
                tool_names = page.locator("span.text-amber-400")
                tc_count = await tool_names.count()
                if tc_count > 0:
                    print(f"    Tool calls visible: {tc_count}")

                # Check for status
                status_els = page.locator("text=MOZA is thinking, Executing tool")
                for se in await status_els.all():
                    txt = await se.inner_text()
                    if txt.strip():
                        print(f"    Status: {txt.strip()}")

                # Check if response stabilized
                current_text = ""
                if bubble_count > 0:
                    current_text = await agent_bubbles.last.inner_text()
                if len(current_text) == last_response_len and len(current_text) > 20:
                    stable_count += 1
                else:
                    stable_count = 0

                # If stable for 5 checks (10s) and has content, done
                if stable_count >= 5 and len(current_text) > 20:
                    print(f"    Response stable. Final length: {len(current_text)} chars")
                    break

                if time.time() - start_time > max_wait:
                    print("    Max wait time reached")
                    break

            # Take final screenshot
            await page.screenshot(path=str(REPORTS / "03_final_response.png"), full_page=True)

            # Print final state
            agent_bubbles = page.locator(".prose.prose-invert")
            bc = await agent_bubbles.count()
            print(f"\n    Final agent bubble count: {bc}")
            for i in range(bc):
                txt = await agent_bubbles.nth(i).inner_text()
                print(f"    Bubble {i}: {txt[:200]}...")

            # Check tool calls
            tool_spans = page.locator("span.text-amber-400")
            tc = await tool_spans.count()
            print(f"    Tool calls executed: {tc}")

        else:
            print("    ERROR: Could not find input field!")
            await page.screenshot(path=str(REPORTS / "error_no_input.png"))

        await browser.close()

    # Check if files were created
    print(f"\n{'='*50}")
    print("CHECKING CREATED FILES:")
    csv_path = REPORTS / "red_snapper_importers.csv"
    html_path = REPORTS / "red_snapper_report.html"
    if csv_path.exists():
        print(f"  CSV: {csv_path} ({csv_path.stat().st_size} bytes) ✅")
    else:
        print(f"  CSV: NOT FOUND ❌")
    if html_path.exists():
        print(f"  HTML: {html_path} ({html_path.stat().st_size} bytes) ✅")
    else:
        print(f"  HTML: NOT FOUND ❌")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(run())
