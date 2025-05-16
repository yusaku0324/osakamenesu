import asyncio
import csv
import os
from playwright.async_api import async_playwright

MARSHMALLOW_URL = os.getenv("MARSHMALLOW_URL", "https://marshmallow-qa.com/wiq4442uvh8iawe")
QUESTIONS_FILE = "questions.tsv"

async def post_question(page, question):
    await page.goto(MARSHMALLOW_URL)
    await page.wait_for_selector("#message_content", timeout=10000)
    await page.fill("#message_content", question)
    # 1st おくる
    await page.click("button:has-text('おくる')")
    # 優先表示モーダルが出た場合は閉じる
    try:
        await page.click("[data-bs-dismiss='modal']", timeout=3000)
    except Exception:
        pass
    # 2nd おくる（確認画面）
    try:
        await page.click("form#new_message button.btn-primary[type='submit']", timeout=5000)
    except Exception:
        pass
    await asyncio.sleep(2)

async def main():
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        questions = [row[0] for row in reader if row and row[0].strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        for idx, question in enumerate(questions):
            context = await browser.new_context()
            page = await context.new_page()
            print(f"[{idx+1}/{len(questions)}] 投稿: {question[:30]}...")
            try:
                await post_question(page, question)
                print("  -> 投稿完了")
            except Exception as e:
                print(f"  -> 投稿失敗: {e}")
            await context.close()
            await asyncio.sleep(3)  # Bot判定回避のため間隔を空ける
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 