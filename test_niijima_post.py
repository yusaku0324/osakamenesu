"""
niijimaアカウントでメンエス出稼ぎについてのツイートをテストするスクリプト
"""
import os
import sys
import json
import logging
import openai
from generate_recruit_posts import post_to_twitter, ensure_utf8_encoding, create_driver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_niijima_post.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("test_niijima_post")

def test_niijima_post():
    """niijimaアカウントでメンエス出稼ぎについてのツイートをテスト"""
    try:
        ensure_utf8_encoding()
        
        test_tweet = "【メンエス出稼ぎ募集】✨ 都内高級店で日給3.5万円保証！未経験大歓迎、即日勤務OK！交通費全額支給、寮完備で地方からの出稼ぎも安心♪ 応募はDMまで！ #メンエス出稼ぎ #高収入 #日払い"
        
        logger.info(f"テストツイート: {test_tweet}")
        
        cookie_path = "niijima_cookies.json"
        
        if os.path.exists(cookie_path):
            logger.info(f"クッキーファイルを使用します: {cookie_path}")
        else:
            logger.error(f"クッキーファイルが見つかりません: {cookie_path}")
            return 1
        
        os.environ["X_COOKIE_PATH"] = cookie_path
        os.environ["CI"] = "true"  # ヘッドレスモードを強制
        
        result = post_to_twitter(test_tweet)
        
        if result["success"]:
            logger.info(f"テスト投稿が成功しました: {result.get('tweet_url', 'URL不明')}")
            return 0
        else:
            logger.error(f"テスト投稿が失敗しました: {result.get('error', '不明なエラー')}")
            return 1
    
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}")
        return 1
    
    finally:
        # if os.path.exists(cookie_path):
        #     os.remove(cookie_path)
        #     logger.info(f"{cookie_path}を削除しました")
        pass

if __name__ == "__main__":
    sys.exit(test_niijima_post())
