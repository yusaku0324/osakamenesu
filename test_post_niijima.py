"""
Test script to post a single message using niijima account
"""
import os
import sys
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.services.twitter_client.driver_factory import create_driver
from bot.services.twitter_client.cookie_loader import load_cookies
from bot.services.twitter_client.poster import post_to_twitter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to post a test message"""
    try:
        test_message = f"""
🌟 メンエス出稼ぎ求人 🌟

【テスト投稿】
東京・大阪で高収入メンズエステ求人募集中！
日給3万円以上保証 💰
未経験者大歓迎 ✨

詳細はDMまで 📩

投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        logger.info("Starting test post...")
        
        driver = create_driver(headless=True)
        
        cookie_path = os.path.join(os.path.dirname(__file__), "bot", "niijima_cookies.json")
        if not load_cookies(driver, cookie_path):
            logger.error("Failed to load cookies")
            driver.quit()
            return 1
        
        result = post_to_twitter(driver, test_message)
        
        if result:
            logger.info(f"Successfully posted test message: {result}")
            driver.quit()
            return 0
        else:
            logger.error("Failed to post test message")
            driver.quit()
            return 1
    
    except Exception as e:
        logger.error(f"Error in test post: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
