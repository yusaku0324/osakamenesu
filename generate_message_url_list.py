import os
import asyncio
import csv
import json # For potential JSON output
from pathlib import Path
from urllib.parse import urljoin # For joining base URL and relative paths
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async

load_dotenv()
BASE_URL = "https://marshmallow-qa.com"
INBOX_URL = urljoin(BASE_URL, "/messages")
CUSTOM_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
COOKIE_FILE = "marshmallow_cookies.json"
QUESTIONS_TSV_PATH = Path("questions.tsv")
OUTPUT_CSV_PATH = Path("message_urls.csv")
OUTPUT_JSON_PATH = Path("message_urls.json") # Optional JSON output

async def get_all_message_links_from_inbox(page):
    """Fetches message links from all pages of the inbox by clicking 'もっとみる'."""
    all_extracted_messages = []
    current_page_url = INBOX_URL
    page_count = 1

    while current_page_url:
        print(f"Navigating to inbox page {page_count}: {current_page_url}")
        await page.goto(current_page_url, wait_until="domcontentloaded")

        if "お詫びとして猫をご用意しました" in await page.content():
            print(f"Cat page detected on page {page_count}. Stopping pagination.")
            await page.screenshot(path=f"inbox_cat_page_pagination_p{page_count}.png")
            break # Stop if cat page is encountered

        message_link_selector = 'a[data-obscene-word-target="content"][href^="/messages/"]'
        print(f"  Looking for message links with selector: {message_link_selector}")
        
        # Wait for at least one message link to appear, or timeout if page is empty/different
        try:
            await page.wait_for_selector(message_link_selector, timeout=10000) # Short timeout for content check
        except PlaywrightTimeoutError:
            print(f"  No message links found on page {page_count}. This might be the end or an empty page.")
            # It could be an empty page or the end of pagination, check for 'もっとみる' anyway
            pass # Continue to check for 'もっとみる' button

        link_elements = await page.query_selector_all(message_link_selector)
        print(f"  Found {len(link_elements)} potential message links on page {page_count}.")

        for link in link_elements:
            text_content = await link.text_content()
            href = await link.get_attribute("href")
            if text_content and href:
                question_text = text_content.strip()
                full_url = urljoin(BASE_URL, href.strip())
                all_extracted_messages.append({"question_preview": question_text, "url": full_url})
        
        # Check for "もっとみる" button
        load_more_button_selector = 'a.btn.btn-secondary[rel="next"][data-action="pagination-loader#load"]:has-text("もっとみる")'
        print(f"  Checking for 'もっとみる' button with selector: {load_more_button_selector}")
        load_more_button = await page.query_selector(load_more_button_selector)

        if load_more_button:
            next_page_relative_href = await load_more_button.get_attribute("href")
            if next_page_relative_href:
                current_page_url = urljoin(BASE_URL, next_page_relative_href.strip())
                print(f"  'もっとみる' button found. Next page URL: {current_page_url}")
                page_count += 1
                await asyncio.sleep(1) # Small delay before loading next page
            else:
                print("  'もっとみる' button found but no href. Stopping pagination.")
                current_page_url = None # Stop pagination
        else:
            print("  'もっとみる' button not found. Assuming end of messages.")
            current_page_url = None # Stop pagination
            
    return all_extracted_messages

async def main():
    if not Path(COOKIE_FILE).exists():
        print(f"Error: Cookie file '{COOKIE_FILE}' not found. Please ensure it exists.")
        return
    if not QUESTIONS_TSV_PATH.exists():
        print(f"Error: Questions file '{QUESTIONS_TSV_PATH}' not found.")
        return

    questions_from_file = []
    with open(QUESTIONS_TSV_PATH, mode='r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        for row in reader:
            if row:
                questions_from_file.append(row[0].strip())
    print(f"Loaded {len(questions_from_file)} questions from {QUESTIONS_TSV_PATH}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            storage_state=COOKIE_FILE,
            user_agent=CUSTOM_USER_AGENT,
            base_url=BASE_URL
        )
        page = await context.new_page()
        # await stealth_async(page) # Stealth might not be necessary with cookie auth, and can sometimes interfere

        matched_pairs = []
        try:
            print(f"Attempting to fetch all message URLs using cookies from {COOKIE_FILE}...")
            # Call the new function that handles pagination
            all_messages_from_inbox = await get_all_message_links_from_inbox(page)
            
            print(f"\nTotal messages fetched from all inbox pages: {len(all_messages_from_inbox)}")
            print(f"Matching {len(all_messages_from_inbox)} fetched messages against {len(questions_from_file)} questions from TSV...")
            
            # Create a dictionary of fetched messages for faster lookup if needed, though for a few hundred, direct iteration is fine.
            # fetched_message_dict = {msg["question_preview"]: msg["url"] for msg in all_messages_from_inbox}

            for q_file in questions_from_file:
                found_match = False
                for msg_page in all_messages_from_inbox:
                    if q_file in msg_page["question_preview"]:
                        matched_pairs.append({"question": q_file, "url": msg_page["url"]})
                        print(f"  MATCH: '{q_file[:50]}...' -> {msg_page['url']}")
                        # To avoid duplicate matches for the same TSV question if it appears multiple times in inbox with slight variations
                        # (though less likely for question previews from links)
                        # We could remove msg_page from all_messages_from_inbox here, but that complicates iteration.
                        # For now, first match wins for a given q_file.
                        found_match = True
                        break 
                if not found_match:
                    print(f"  NO MATCH for: '{q_file[:50]}...'")
            
            print(f"\nFound {len(matched_pairs)} matching question-URL pairs.")

            if matched_pairs:
                with open(OUTPUT_CSV_PATH, mode='w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ["question", "url"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(matched_pairs)
                print(f"Saved matched pairs to {OUTPUT_CSV_PATH}")

                with open(OUTPUT_JSON_PATH, mode='w', encoding='utf-8') as jsonfile:
                    json.dump(matched_pairs, jsonfile, ensure_ascii=False, indent=2)
                print(f"Saved matched pairs to {OUTPUT_JSON_PATH}")
            else:
                print("No matches found to save.")

        except PlaywrightTimeoutError as e:
            print(f"Timeout occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            await page.screenshot(path="unexpected_error_url_fetch_pagination.png")
        finally:
            print("Closing resources...")
            await page.close()
            await context.close()
            try: await browser.close()
            except Exception: pass

if __name__ == "__main__":
    asyncio.run(main()) 