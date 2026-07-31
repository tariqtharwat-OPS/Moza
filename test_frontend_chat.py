from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000', wait_until='networkidle')
    page.wait_for_timeout(2000)
    try:
        page.fill('textarea', '\u0645\u0631\u062d\u0628\u0627\u060b \u0645\u0627 \u0647\u0648 \u0627\u0633\u0645\u0643\u063f')
        page.click('button[type="submit"]')
        page.wait_for_timeout(20000)
        page.screenshot(path=r'D:\Moza\frontend_after_arabic.png')
        print('Arabic test screenshot saved')
    except Exception as e:
        print(f'Error: {e}')
        print(page.content()[:2000])
    browser.close()