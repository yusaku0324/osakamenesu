"""
Test script to post multiple videos using niijima account
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
    """Main function to post multiple videos"""
    try:
        video_dir = os.path.join(os.path.dirname(__file__), "bot", "videos")
        os.makedirs(video_dir, exist_ok=True)
        
        video_files = []
        for i in range(1, 5):
            video_path = os.path.join(video_dir, f"qa_video_{i}.mp4")
            if os.path.exists(video_path):
                video_files.append(video_path)
        
        if not video_files:
            logger.error("No video files found in bot/videos directory")
            return 1
        
        test_message = f"""
🎥 Q&A動画シリーズ 🎥

メンズエステ求人に関するよくある質問にお答えします！
全4本の動画をまとめて投稿します。


投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        logger.info(f"Starting test post with {len(video_files)} videos...")
        
        driver = create_driver(headless=True)
        
        cookie_path = os.path.join(os.path.dirname(__file__), "bot", "niijima_cookies.json")
        if not load_cookies(driver, cookie_path):
            logger.error("Failed to load cookies")
            driver.quit()
            return 1
        
        result = post_to_twitter(driver, test_message, media_files=video_files)
        
        if result:
            logger.info(f"Successfully posted multiple videos: {result}")
            driver.quit()
            return 0
        else:
            logger.error("Failed to post multiple videos")
            driver.quit()
            return 1
    
    except Exception as e:
        logger.error(f"Error in test post: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
