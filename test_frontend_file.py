from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000', wait_until='networkidle')
    page.wait_for_timeout(2000)
    try:
        page.fill('textarea', 'Write a file named ui_test.txt with content: UI test successful')
        page.click('button[type="submit"]')
        page.wait_for_timeout(20000)
        page.screenshot(path=r'D:\Moza\frontend_file_write.png')
        print('File write screenshot saved')
    except Exception as e:
        print(f'Error: {e}')
    browser.close()