"""
Mock test script for X posting functionality without requiring real authentication
"""
import os
import sys
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def mock_post_to_twitter(text, media_files=None):
    """
    Mock function to simulate posting to Twitter
    
    Args:
        text: Text content to post
        media_files: Optional list of media files to upload
        
    Returns:
        dict: Simulated response with success status and tweet URL
    """
    logger.info(f"MOCK: Would post text: {text}")
    
    if media_files:
        logger.info(f"MOCK: Would upload {len(media_files)} media files:")
        for i, file in enumerate(media_files):
            logger.info(f"  {i+1}. {file}")
    
    mock_tweet_id = "1234567890123456789"
    mock_tweet_url = f"https://x.com/niijima_account/status/{mock_tweet_id}"
    
    return {
        "success": True,
        "tweet_id": mock_tweet_id,
        "tweet_url": mock_tweet_url
    }

def test_single_post():
    """Test single text post functionality"""
    test_message = f"""
🌟 メンエス出稼ぎ求人 🌟

【テスト投稿】
東京・大阪で高収入メンズエステ求人募集中！
日給3万円以上保証 💰
未経験者大歓迎 ✨

詳細はDMまで 📩

投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    logger.info("=== テスト: 単一テキスト投稿 ===")
    
    with patch('bot.services.twitter_client.poster.post_to_twitter', mock_post_to_twitter):
        result = mock_post_to_twitter(test_message)
        
        if result["success"]:
            logger.info(f"投稿成功: {result.get('tweet_url')}")
            return True
        else:
            logger.error(f"投稿失敗: {result.get('error', '不明なエラー')}")
            return False

def test_multiple_videos():
    """Test multiple video upload functionality"""
    test_message = f"""
🎥 Q&A動画シリーズ 🎥

メンズエステ求人に関するよくある質問にお答えします！
全4本の動画をまとめて投稿します。

投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    video_files = [
        "bot/videos/qa_video_1.mp4",
        "bot/videos/qa_video_2.mp4",
        "bot/videos/qa_video_3.mp4",
        "bot/videos/qa_video_4.mp4"
    ]
    
    logger.info("=== テスト: 複数動画投稿 ===")
    
    with patch('bot.services.twitter_client.poster.post_to_twitter', mock_post_to_twitter):
        result = mock_post_to_twitter(test_message, media_files=video_files)
        
        if result["success"]:
            logger.info(f"複数動画投稿成功: {result.get('tweet_url')}")
            return True
        else:
            logger.error(f"投稿失敗: {result.get('error', '不明なエラー')}")
            return False

def main():
    """Main function to run all tests"""
    logger.info("X投稿機能のモックテストを開始します")
    
    single_post_result = test_single_post()
    multiple_videos_result = test_multiple_videos()
    
    if single_post_result and multiple_videos_result:
        logger.info("すべてのテストが成功しました")
        return 0
    else:
        logger.error("一部のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())
