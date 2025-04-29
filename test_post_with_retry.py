"""
Test script for X posting with retry mechanism and better error handling
"""
import os
import sys
import logging
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.services.twitter_client.driver_factory import create_driver
from bot.services.twitter_client.cookie_loader import load_cookies
from bot.services.twitter_client.poster import post_to_twitter
from bot.utils.safe_click import safe_click_by_selector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_cookie_file():
    """Create a test cookie file if it doesn't exist or is empty"""
    cookie_path = os.path.join(os.path.dirname(__file__), "bot", "niijima_cookies.json")
    
    try:
        if not os.path.exists(cookie_path) or os.path.getsize(cookie_path) < 10:
            logger.warning(f"Cookie file is missing or empty: {cookie_path}")
            logger.info("Creating a basic test cookie structure")
            
            test_cookies = [
                {
                    "name": "test_cookie",
                    "value": "test_value",
                    "domain": "x.com",
                    "path": "/",
                    "secure": True
                }
            ]
            
            os.makedirs(os.path.dirname(cookie_path), exist_ok=True)
            
            import json
            with open(cookie_path, 'w', encoding='utf-8') as f:
                json.dump(test_cookies, f, indent=2)
            
            logger.info(f"Created test cookie file at {cookie_path}")
            return True
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating test cookie file: {e}")
        return False

def test_post_with_retry(max_retries=3):
    """Test posting with retry mechanism"""
    test_message = f"""
🌟 メンエス出稼ぎ求人 🌟

【テスト投稿】
東京・大阪で高収入メンズエステ求人募集中！
日給3万円以上保証 💰
未経験者大歓迎 ✨

詳細はDMまで 📩

投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    logger.info("Starting test post with retry mechanism...")
    
    create_test_cookie_file()
    
    for attempt in range(max_retries):
        try:
            driver = create_driver(headless=True)
            
            debug_dir = os.path.join(os.path.dirname(__file__), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            cookie_path = os.path.join(os.path.dirname(__file__), "bot", "niijima_cookies.json")
            if not load_cookies(driver, cookie_path):
                logger.warning("Failed to load cookies, but continuing with test")
                
            debug_html_path = os.path.join(debug_dir, f"page_before_compose_{attempt}.html")
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Saved page source to {debug_html_path}")
            
            debug_screenshot_path = os.path.join(debug_dir, f"screenshot_before_compose_{attempt}.png")
            driver.save_screenshot(debug_screenshot_path)
            logger.info(f"Saved screenshot to {debug_screenshot_path}")
            
            logger.info("Navigating to compose page using improved navigate_to_compose function")
            
            from bot.services.twitter_client.poster import navigate_to_compose
            
            debug_html_before_path = os.path.join(debug_dir, f"page_before_navigate_{attempt}.html")
            with open(debug_html_before_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Saved page source before navigation to {debug_html_before_path}")
            
            compose_page_loaded = navigate_to_compose(driver, timeout=15)
            
            debug_html_after_path = os.path.join(debug_dir, f"page_after_navigate_{attempt}.html")
            with open(debug_html_after_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Saved page source after navigation to {debug_html_after_path}")
            
            debug_screenshot_after_path = os.path.join(debug_dir, f"screenshot_after_navigate_{attempt}.png")
            driver.save_screenshot(debug_screenshot_after_path)
            logger.info(f"Saved screenshot after navigation to {debug_screenshot_after_path}")
            
            if compose_page_loaded:
                logger.info("Successfully navigated to compose page")
                
                time.sleep(3)
                
                try:
                    text_area = driver.find_element_by_css_selector("[data-testid='tweetTextarea_0']")
                    text_area.send_keys(test_message)
                    logger.info("Successfully entered text in compose area")
                    
                    tweet_button_clicked = safe_click_by_selector(
                        driver, 
                        "[data-testid='tweetButton']", 
                        timeout=10,
                        max_retries=5
                    )
                    
                    if tweet_button_clicked:
                        logger.info("Successfully clicked tweet button")
                        time.sleep(5)
                        logger.info("Test post completed successfully")
                        driver.quit()
                        return True
                    else:
                        logger.error("Failed to click tweet button")
                
                except Exception as e:
                    logger.error(f"Error finding or interacting with text area: {e}")
            
            else:
                logger.error("Failed to find or click compose button")
            
            driver.quit()
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries} attempts")
                return False
        
        except Exception as e:
            logger.error(f"Error in test post attempt {attempt + 1}: {e}")
            
            try:
                driver.quit()
            except:
                pass
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries} attempts")
                return False
    
    return False

def main():
    """Main function"""
    try:
        logger.info("Starting X posting test with retry mechanism")
        
        result = test_post_with_retry()
        
        if result:
            logger.info("Test completed successfully")
            return 0
        else:
            logger.error("Test failed")
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
