"""
Live UI E2E Test Script for Level A Closure Audit
Opens Chrome, runs 3 scenarios, captures observations.
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

RESULTS = {}

async def debug_page(page, label=""):
    """Debug: capture page state."""
    html = await page.content()
    # Save full HTML for inspection
    with open(f"backend/tests/archive/ui_debug_{label}.html", "w", encoding="utf-8") as f:
        f.write(html)
    # Get all interactive elements
    interactives = await page.evaluate("""
        () => {
            const els = document.querySelectorAll('input, textarea, [contenteditable], button, [role="textbox"]');
            return Array.from(els).map(e => ({
                tag: e.tagName,
                type: e.type || '',
                placeholder: e.placeholder || '',
                role: e.role || '',
                id: e.id || '',
                class: e.className?.slice(0, 80) || '',
                rect: e.getBoundingClientRect ? 
                    `${e.getBoundingClientRect().x},${e.getBoundingClientRect().y}` : ''
            }));
        }
    """)
    print(f"  Found {len(interactives)} interactive elements:")
    for el in interactives[:10]:
        print(f"    <{el['tag']} type={el['type']} placeholder='{el['placeholder']}' class='{el['class']}'>")

async def get_page_text(page):
    return await page.evaluate("() => document.body.innerText")

async def check_raw_tags(page):
    body = await page.evaluate("() => document.body.innerHTML")
    raw_patterns = ["<filesystem", "<browser", "<terminal", "function_call", "tool_call"]
    found = []
    for pat in raw_patterns:
        if pat in body:
            found.append(pat)
    return found

async def test_scenario_a(page):
    print("\n=== Scenario A: Basic Chat ===")
    await debug_page(page, "a_initial")
    
    # Try to find and use the input area
    input_area = page.locator('[contenteditable="true"], textarea, [role="textbox"], input[type="text"]').first
    try:
        await input_area.fill("Hello MOZA, are you ready?", timeout=5000)
        await page.keyboard.press("Enter")
    except:
        # Try clicking a button first
        btns = page.locator('button')
        count = await btns.count()
        print(f"  Found {count} buttons")
        
        # Try typing via keyboard
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type("Hello MOZA, are you ready?", delay=50)
        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
    
    await asyncio.sleep(5)
    text = await get_page_text(page)
    has_reply = any(greet in text.lower() for greet in ["hello", "hi there", "hey", "moza", "how can i help"])
    raw_tags = await check_raw_tags(page)
    
    result = {"has_reply": has_reply, "text_preview": text[:500], "raw_tags_found": raw_tags}
    RESULTS["scenario_a"] = result
    print(f"  Reply received: {has_reply}")
    print(f"  Raw tags: {raw_tags if raw_tags else 'None'}")
    return result

async def test_scenario_b(page):
    print("\n=== Scenario B: File Tool ===")
    await debug_page(page, "b_initial")
    
    input_area = page.locator('[contenteditable="true"], textarea, [role="textbox"], input[type="text"]').first
    try:
        await input_area.fill("Create a file named test_ui.txt in D:\\Moza with content 'UI Test'.", timeout=5000)
        await page.keyboard.press("Enter")
    except:
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type("Create a file named test_ui.txt in D:\\Moza with content 'UI Test'.", delay=30)
        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
    
    await asyncio.sleep(10)
    text = await get_page_text(page)
    raw_tags = await check_raw_tags(page)
    
    has_tool_card = any(phrase in text.lower() for phrase in [
        "running filesystem", "filesystem completed", "filesystem.write",
        "filesystem failed", "tool execution", "tool_call", "tool_result"
    ])
    file_created = os.path.exists("D:\\Moza\\test_ui.txt")
    file_content = ""
    if file_created:
        with open("D:\\Moza\\test_ui.txt", "r") as f:
            file_content = f.read()
    
    result = {"has_tool_card": has_tool_card, "raw_tags_found": raw_tags,
              "file_created": file_created, "file_content": file_content, "text_preview": text[:500]}
    RESULTS["scenario_b"] = result
    print(f"  Tool UI card: {has_tool_card}")
    print(f"  Raw tags: {raw_tags if raw_tags else 'None'}")
    print(f"  File created: {file_created} content='{file_content}'")
    return result

async def test_scenario_c(page):
    print("\n=== Scenario C: Browser Tool ===")
    input_area = page.locator('[contenteditable="true"], textarea, [role="textbox"], input[type="text"]').first
    try:
        await input_area.fill("Search Wikipedia for 'Artificial Intelligence'.", timeout=5000)
        await page.keyboard.press("Enter")
    except:
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)
        await page.keyboard.type("Search Wikipedia for 'Artificial Intelligence'.", delay=30)
        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
    
    await asyncio.sleep(15)
    text = await get_page_text(page)
    raw_tags = await check_raw_tags(page)
    
    has_browser_panel = any(phrase in text.lower() for phrase in [
        "browser", "url:", "screenshot", "view", "actions", "live"
    ])
    still_waiting = "waiting for a browser task" in text.lower()
    
    result = {"has_browser_panel": has_browser_panel, "still_waiting": still_waiting,
              "raw_tags_found": raw_tags, "text_preview": text[:500]}
    RESULTS["scenario_c"] = result
    print(f"  Browser panel active: {has_browser_panel}")
    print(f"  Still 'Waiting...': {still_waiting}")
    print(f"  Raw tags: {raw_tags if raw_tags else 'None'}")
    return result

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        print("Loading http://localhost:3001...")
        await page.goto("http://localhost:3001", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        await page.screenshot(path="backend/tests/archive/ui_initial.png")
        
        await test_scenario_a(page)
        await page.screenshot(path="backend/tests/archive/ui_scenario_a.png")
        
        page2 = await context.new_page()
        await page2.goto("http://localhost:3001", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        await test_scenario_b(page2)
        await page2.screenshot(path="backend/tests/archive/ui_scenario_b.png")
        
        page3 = await context.new_page()
        await page3.goto("http://localhost:3001", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        await test_scenario_c(page3)
        await page3.screenshot(path="backend/tests/archive/ui_scenario_c.png")
        
        await browser.close()
    
    print("\n" + "="*60)
    print("UI TEST RESULTS")
    print("="*60)
    print(json.dumps(RESULTS, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
