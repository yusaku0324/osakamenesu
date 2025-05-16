# test_playwright.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting Playwright test script...")
    try:
        async with async_playwright() as p:
            print("  async_playwright context started.")
            # 必ずヘッドフルモードで起動、ブラウザの起動ログを確認するため verbose=True も試す価値あり
            browser = await p.chromium.launch(headless=False) 
            print(f"  Browser launched: {type(browser)}")
            page = await browser.new_page()
            print(f"  New page created: {type(page)}")
            
            target_url = "https://example.com"
            print(f"  Navigating to: {target_url}")
            try:
                # タイムアウトを30秒に設定、wait_untilでDOMの準備完了を待つ
                await page.goto(target_url, timeout=30000, wait_until="domcontentloaded") 
                print(f"  Successfully navigated to: {target_url}")
                page_title = await page.title()
                print(f"  Page title: {page_title}")
                await page.screenshot(path="example_test.png")
                print("  Screenshot saved as example_test.png")
            except Exception as e:
                print(f"  ERROR during navigation or page interaction: {e}")
            finally:
                if browser:
                    print("  Closing browser...")
                    await browser.close()
                    print("  Browser closed.")
    except Exception as e:
        print(f"ERROR during Playwright script execution: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 