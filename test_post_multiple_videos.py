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
from bot.services.twitter_client.media_uploader import upload_multiple_media, prepare_media
from bot.services.twitter_client.composer import type_tweet_text, click_tweet_button

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def post_with_multiple_videos(driver, text, video_paths):
    """
    Post a tweet with multiple videos
    
    Args:
        driver: WebDriver instance
        text: Tweet text
        video_paths: List of video file paths
        
    Returns:
        dict: Result of the post operation
    """
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        logger.info("投稿画面に移動します...")
        driver.get("https://x.com/compose/tweet")
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='textbox']"))
        )
        
        logger.info(f"{len(video_paths)}個の動画をアップロードします...")
        if not upload_multiple_media(driver, video_paths):
            logger.error("動画のアップロードに失敗しました")
            return {"success": False, "error": "Failed to upload videos"}
        
        logger.info(f"ツイートテキストを入力します: {text}")
        if not type_tweet_text(driver, text):
            logger.error("ツイートテキストの入力に失敗しました")
            return {"success": False, "error": "Failed to type tweet text"}
        
        if not click_tweet_button(driver):
            logger.error("ツイートボタンのクリックに失敗しました")
            return {"success": False, "error": "Failed to click tweet button"}
        
        import time
        time.sleep(10)
        
        tweet_url = driver.current_url
        if "/status/" in tweet_url:
            logger.info(f"ツイートに成功しました: {tweet_url}")
            return {"success": True, "tweet_url": tweet_url}
        else:
            logger.error("ツイートURLの取得に失敗しました")
            return {"success": False, "error": "Failed to get tweet URL"}
    
    except Exception as e:
        logger.error(f"ツイート投稿中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

def main():
    """Main function to post multiple videos"""
    try:
        test_message = f"""
🎥 メンエス求人動画集 🎥

【複数動画テスト投稿】
東京・大阪で高収入メンズエステ求人募集中！
日給3万円以上保証 💰
未経験者大歓迎 ✨

詳細はDMまで 📩

投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        video_paths = []
        for i in range(4):
            video_path = f"/tmp/test_video_{i+1}.mp4"
            with open(video_path, 'wb') as f:
                f.write(b'test video content')
            video_paths.append(video_path)
        
        logger.info("Starting test post with multiple videos...")
        
        driver = create_driver(headless=True)
        
        cookie_path = os.path.join(os.path.dirname(__file__), "bot", "niijima_cookies.json")
        if not load_cookies(driver, cookie_path):
            logger.error("Failed to load cookies")
            driver.quit()
            return 1
        
        result = post_with_multiple_videos(driver, test_message, video_paths)
        
        if result["success"]:
            logger.info(f"Successfully posted test message with videos: {result.get('tweet_url', 'No URL available')}")
        else:
            logger.error(f"Failed to post test message: {result.get('error', 'Unknown error')}")
        
        driver.quit()
        
        for video_path in video_paths:
            if os.path.exists(video_path):
                os.remove(video_path)
        
        return 0 if result["success"] else 1
    
    except Exception as e:
        logger.error(f"Error in test post: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
