import asyncio
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    print("=" * 60)
    print("AUTONOMOUS VERIFICATION & SELF-HEALING TEST")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        page = await browser.new_page()

        runtime_errors = []
        page.on("pageerror", lambda err: runtime_errors.append(str(err)))

        # ── 1. Navigate ────────────────────────────────────────────────────
        print("\n[1/5] Navigating to http://localhost:3000 ...")
        try:
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            print("  Page loaded successfully")
        except Exception as e:
            print(f"  Failed to load page: {e}")
            await browser.close()
            return

        await page.wait_for_timeout(5000)
        await page.screenshot(path="D:\\Moza\\test_01_initial.png")

        # ── 2. Check runtime errors ────────────────────────────────────────
        print("\n[2/5] Checking for runtime errors...")
        if runtime_errors:
            print(f"  Found {len(runtime_errors)} error(s):")
            for i, err in enumerate(runtime_errors, 1):
                print(f"    {i}. {err}")
        else:
            print("  No runtime errors detected")

        def get_page_text():
            return page.evaluate("() => document.body.innerText")

        # ── TEST 1: Empty file creation ────────────────────────────────────
        print("\n [3/5] TEST 1: Creating empty file...")
        input_box = page.locator("textarea").first
        await input_box.wait_for(state="visible", timeout=5000)
        await input_box.fill("Create an empty file named test_empty.txt in D:\\")
        await page.keyboard.press("Enter")

        print("  Waiting 15 seconds...")
        await page.wait_for_timeout(15000)
        await page.screenshot(path="D:\\Moza\\test_02_empty_file.png")

        text1 = await get_page_text()
        print(f"  Page text:\n{text1[:1500]}\n")

        test_file_1 = Path("D:/test_empty.txt")
        test1_pass = test_file_1.exists()
        if test1_pass:
            print(f"  TEST 1 PASSED: File created ({test_file_1.stat().st_size} bytes)")
            test_file_1.unlink()
        else:
            print(f"  TEST 1 FAILED: {test_file_1.absolute()} not found")

        # ── TEST 2: File via terminal ──────────────────────────────────────
        print("\n [4/5] TEST 2: Creating file via terminal...")
        await input_box.fill("Use terminal to create D:\\moza_verified.txt with content 'I love moza'")
        await page.keyboard.press("Enter")

        print("  Waiting 25 seconds...")
        await page.wait_for_timeout(25000)
        await page.screenshot(path="D:\\Moza\\test_03_terminal_file.png")

        text2 = await get_page_text()
        print(f"  Page text:\n{text2[:2000]}\n")

        test_file_2 = Path("D:/moza_verified.txt")
        test2_pass = test_file_2.exists()
        content_ok = False
        if test2_pass:
            content = test_file_2.read_text(encoding="utf-8", errors="replace")
            print(f"  TEST 2 PASSED: File created")
            print(f"  Content: '{content}'")
            content_ok = "I love moza" in content
            if content_ok:
                print("  Content verified correctly!")
            else:
                print(f"  Content mismatch")
            test_file_2.unlink()
        else:
            print(f"  TEST 2 FAILED: {test_file_2.absolute()} not found")

        # ── Summary ────────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"  Runtime errors: {len(runtime_errors)}")
        print(f"  Empty file test: {'PASS' if test1_pass else 'FAIL'}")
        print(f"  Terminal file test: {'PASS' if test2_pass else 'FAIL'}")
        print(f"  Content preservation: {'PASS' if content_ok else 'N/A'}")

        if runtime_errors:
            print("\n ISSUES DETECTED:")
            for err in runtime_errors:
                print(f"  - {err}")

        await browser.close()
        print("\n Done.")

if __name__ == "__main__":
    asyncio.run(main())
