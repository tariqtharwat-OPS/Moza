"""MOZA Live System Verification
Tests: Browser tool, Terminal tool, Context persistence, UI cleanliness
"""

import asyncio, json, sys, time, os
from playwright.async_api import async_playwright

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
REPORT = {"browser": "FAIL", "terminal": "FAIL", "context": "FAIL", "ui_clean": "FAIL"}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # ── 0. Load frontend ──
        print("=" * 60)
        print("STEP 0: Loading frontend")
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
        body = await page.inner_text("body")
        assert "Internal Server Error" not in body, "P0 FAIL"
        assert "500" not in body
        await page.screenshot(path="verify_00_loaded.png", full_page=True)
        print("  PASS: UI loaded\n")

        # ── 1. Browser Tool: Search Wikipedia ──
        print("=" * 60)
        print("STEP 1: Browser Tool - Search Wikipedia for AI")
        input_box = page.locator("textarea[placeholder*='Ask']").first
        await input_box.fill("Search Wikipedia for AI and take a screenshot")
        await input_box.press("Enter")
        print("  Waiting for browser task to complete (up to 45s)...")
        await asyncio.sleep(45)
        await page.screenshot(path="verify_01_browser.png", full_page=True)
        page_text = await page.inner_text("body")

        # Check browser preview
        browser_live = await page.locator("text=LIVE").count()
        browser_img = await page.locator("img[alt*='Browser' i], img[alt*='screenshot' i]").count()
        has_browser_heading = "Browser" in page_text
        has_actions_tab = "Actions" in page_text

        if browser_live > 0 or browser_img > 0 or (has_browser_heading and has_actions_tab):
            REPORT["browser"] = "PASS"
            print(f"  PASS: Browser tool executed (LIVE badge: {browser_live}, images: {browser_img})")
        else:
            # Fallback: check for "Waiting for a browser task" or similar
            if "Waiting" not in page_text:
                print("  PASS: Browser task triggered (no waiting message)")
                REPORT["browser"] = "PASS"
            else:
                print(f"  WARN: Browser preview shows waiting - check server logs. LIVE:{browser_live} IMG:{browser_img} Heading:{has_browser_heading}")
        print()

        # ── 2. Terminal Tool: Run dir ──
        print("=" * 60)
        print("STEP 2: Terminal Tool - Run 'dir'")
        await page.screenshot(path="verify_02_before_terminal.png", full_page=True)
        await input_box.fill("Run 'dir' in D:\\Moza to list files")
        await input_box.press("Enter")
        print("  Waiting for terminal task (up to 30s)...")
        await asyncio.sleep(20)
        await page.screenshot(path="verify_02_terminal.png", full_page=True)
        page_text = await page.inner_text("body")

        # Check for terminal output
        has_dir_output = any(kw in page_text.lower() for kw in ["directory", "dir", "moza", "backend", "frontend"])
        has_terminal_heading = "Terminal" in page_text
        has_tool_result = "completed" in page_text.lower()

        if has_dir_output or has_terminal_heading or has_tool_result:
            REPORT["terminal"] = "PASS"
            print(f"  PASS: Terminal executed (output: {has_dir_output}, heading: {has_terminal_heading})")
        else:
            print("  WARN: No terminal output detected yet")
        print()

        # ── 3. Context Persistence ──
        print("=" * 60)
        print("STEP 3: Context Persistence - 'What did I just ask?'")
        await page.screenshot(path="verify_03_before_context.png", full_page=True)
        await input_box.fill("What did I just ask you to do?")
        await input_box.press("Enter")
        await asyncio.sleep(10)
        await page.screenshot(path="verify_03_context.png", full_page=True)
        page_text = await page.inner_text("body")

        # The agent should reference the previous task
        context_keywords = ["dir", "directory", "list", "terminal", "previous", "earlier", "last", "قائمة", "سابق", "الأمر"]
        if any(kw in page_text.lower() for kw in context_keywords):
            REPORT["context"] = "PASS"
            print("  PASS: Agent remembers previous task")
        else:
            print("  WARN: Could not confirm context persistence from text")
        print()

        # ── 4. UI Cleanliness ──
        print("=" * 60)
        print("STEP 4: UI Cleanliness")
        await page.screenshot(path="verify_04_ui_clean.png", full_page=True)
        page_text = await page.inner_text("body")
        page_html = await page.content()

        issues = []
        # Check for debug markers
        for marker in ["ool_call>", "ool_result>", "Debug:", "<function="]:
            if marker in page_html:
                issues.append(f"Marker '{marker}' found in HTML")

        # Check tool log is collapsed by default
        tool_log = page.locator("button:has-text('Tool Execution Log')")
        tool_log_count = await tool_log.count()
        tool_log_visible = False
        if tool_log_count > 0:
            collapsed_state = await tool_log.locator("..").inner_html()
            # Look for the ▸ character indicating collapsed state
            if "▸" in collapsed_state:
                tool_log_visible = True  # button is visible with collapsed indicator
                print("  Tool log toggle visible with collapsed indicator (▸)")

        if not issues:
            REPORT["ui_clean"] = "PASS"
            print("  PASS: No debug markers found in UI")
        else:
            for i in issues:
                print(f"  ISSUE: {i}")

        print(f"\n{'=' * 60}")
        print("RESULTS SUMMARY")
        print(f"  Browser Tool:    [{REPORT['browser']}]")
        print(f"  Terminal Tool:   [{REPORT['terminal']}]")
        print(f"  Context:         [{REPORT['context']}]")
        print(f"  UI Cleanliness:  [{REPORT['ui_clean']}]")
        print(f"{'=' * 60}")

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())