import os
import asyncio
import subprocess # For running ffmpeg
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async
import requests

load_dotenv() 
INBOX_URL = "https://marshmallow-qa.com/messages"
IMAGE_SAVE_DIR = Path("images") # Renamed for clarity
VIDEO_SAVE_DIR = Path("videos") # Directory for saving videos
IMAGE_SAVE_DIR.mkdir(exist_ok=True)
VIDEO_SAVE_DIR.mkdir(exist_ok=True)
CUSTOM_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
COOKIE_FILE = "marshmallow_cookies.json"

async def get_image_urls(page):
    print(f"Navigating to inbox: {INBOX_URL}")
    await page.goto(INBOX_URL, wait_until="domcontentloaded")
    if "お詫びとして猫をご用意しました" in await page.content():
        print("Cat page detected when accessing inbox.")
        await page.screenshot(path="inbox_cat_page_cookie.png")
        raise PlaywrightTimeoutError("Cat page detected at inbox (cookie method)")
    
    print("Looking for image download links...")
    # Selector for <a> tags that are image download links
    download_link_selector = 'a[download][href*="media.marshmallow-qa.com/system/images/"]'
    
    try:
        await page.wait_for_selector(download_link_selector, timeout=15000)
    except PlaywrightTimeoutError:
        print(f"No image download links found with selector: {download_link_selector}. Saving screenshot: inbox_no_download_links_cookie.png")
        await page.screenshot(path="inbox_no_download_links_cookie.png")
        return []
        
    link_elements = await page.query_selector_all(download_link_selector)
    urls = set()
    print(f"Found {len(link_elements)} image download links.")
    for link in link_elements:
        href = await link.get_attribute("href")
        if href:
            # Ensure full URL if it's relative (though in this case it seems absolute)
            if href.startswith("//"): href = "https:" + href
            elif not href.startswith("http"): href = page.url + href # Basic relative URL handling, might need base_url logic
            urls.add(href)
            
    if not urls:
        print("No usable image URLs extracted from download links. Saving screenshot: inbox_no_usable_links_cookie.png")
        await page.screenshot(path="inbox_no_usable_links_cookie.png")
    return list(urls)

def download_image(url, save_dir):
    fname = Path(url).name.split("?")[0]
    if not fname:
        timestamp = asyncio.get_event_loop().time()
        fname = f"image_{timestamp}.png"
    path = save_dir / fname
    try:
        print(f"Downloading {url} to {path}")
        r = requests.get(url, timeout=15, headers={"User-Agent": CUSTOM_USER_AGENT})
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"Successfully downloaded: {fname}")
        return path # Return the path of the downloaded image
    except Exception as e:
        print(f"Failed to download: {url} ({e})")
        return None

def convert_image_to_video(image_path: Path, video_dir: Path, duration: int = 1):
    """Converts an image to a video of specified duration using ffmpeg."""
    if not image_path or not image_path.exists():
        print(f"Image not found for video conversion: {image_path}")
        return None

    video_filename = image_path.stem + ".mp4"
    output_video_path = video_dir / video_filename

    ffmpeg_command = [
        "ffmpeg",
        "-loop", "1",
        "-i", str(image_path),
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", # Ensure even dimensions
        str(output_video_path),
        "-y" # Overwrite output file if it exists
    ]

    try:
        print(f"Converting {image_path} to {output_video_path} ({duration}s video)...")
        process = subprocess.run(ffmpeg_command, capture_output=True, text=True, check=True)
        print(f"Successfully converted {image_path.name} to {video_filename}")
        return output_video_path
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error during conversion of {image_path.name}:")
        print(f"Stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH.")
        return None

async def main():
    if not Path(COOKIE_FILE).exists():
        print(f"Error: Cookie file '{COOKIE_FILE}' not found. Please create it first.")
        print("You can create it by manually logging into Marshmallow in a browser,")
        print("then using browser developer tools to export cookies for marshmallow-qa.com,")
        print(f"and saving them in the correct format as {COOKIE_FILE} in the root directory.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Set headless=True for background execution
        context = await browser.new_context(
            storage_state=COOKIE_FILE, 
            user_agent=CUSTOM_USER_AGENT
        )
        page = await context.new_page()
        await stealth_async(page)

        try:
            print(f"Attempting to fetch images using saved cookies from {COOKIE_FILE}...")
            urls = await get_image_urls(page)
            print(f"Image URLs found: {len(urls)}")

            if not urls:
                print("No images found in the inbox using the cookie method.")
            else:
                downloaded_image_paths = []
                for url in urls:
                    downloaded_path = download_image(url, IMAGE_SAVE_DIR)
                    if downloaded_path:
                        downloaded_image_paths.append(downloaded_path)
                
                if downloaded_image_paths:
                    print(f"\nStarting video conversion for {len(downloaded_image_paths)} images...")
                    for img_path in downloaded_image_paths:
                        convert_image_to_video(img_path, VIDEO_SAVE_DIR, duration=1)
                    print("Video conversion process complete.")
                else:
                    print("No images were successfully downloaded, skipping video conversion.")

        except PlaywrightTimeoutError as e:
            print(f"Timeout occurred (cookie method): {e}")
        except Exception as e:
            print(f"An unexpected error occurred (cookie method): {e}")
            await page.screenshot(path="unexpected_error_cookie_method.png")
        finally:
            print("Closing page, context, and browser (cookie method)...")
            await page.close()
            await context.close()
            try:
                await browser.close()
            except Exception as e:
                print(f"Error closing browser: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 