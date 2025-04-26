#!/usr/bin/env python3
"""
募集ツイートを生成し、X（旧Twitter）に自動投稿するスクリプト
"""
import io
import json
import logging
import os
import random
import sys
from typing import Any, Dict, List, Optional

import openai
import tweepy
from dotenv import load_dotenv

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("recruit_posts.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("recruit_posts")

# 環境変数の読み込み
load_dotenv()

# OpenAI APIキーの設定
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEYが設定されていません")
    sys.exit(1)

# Twitter APIキーの設定
twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
if not twitter_bearer_token:
    logger.error("TWITTER_BEARER_TOKENが設定されていません")
    sys.exit(1)


def generate_recruit_post() -> str:
    """
    OpenAI APIを使用して募集ツイートを生成する

    Returns:
        str: 生成された募集ツイート
    """
    try:
        client = openai.OpenAI(api_key=openai_api_key)

        # プロンプトの設定
        prompt = """
        以下の条件を満たす、メンズエステの求人募集ツイートを1つ作成してください：
        
        - 140文字以内
        - 絵文字を2-3個含める
        - ハッシュタグを2-3個含める（#メンエス求人、#高収入、#日払いなど）
        - 都内または大阪の店舗という設定
        - 日給3万円以上という魅力的な条件を含める
        - 未経験歓迎という内容を含める
        - 応募方法（DMまたはLINE）を含める
        
        ツイート本文のみを出力してください。
        """

        # APIリクエスト
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはメンズエステサロンの求人担当者です。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        # レスポンスから生成されたテキストを取得
        generated_text = response.choices[0].message.content.strip()
        logger.info(f"生成されたツイート: {generated_text}")

        return generated_text

    except Exception as e:
        logger.error(f"ツイート生成中にエラーが発生しました: {e}")
        raise


def post_to_twitter(post_text: str) -> Dict[str, Any]:
    """
    X（旧Twitter）に投稿する

    Args:
        post_text: 投稿するテキスト

    Returns:
        Dict[str, Any]: 投稿結果
    """
    try:
        # Tweepy v2 クライアントの初期化
        client = tweepy.Client(bearer_token=twitter_bearer_token)

        # 投稿
        response = client.create_tweet(text=post_text)

        tweet_id = response.data["id"]
        logger.info(
            f"ツイートを投稿しました: https://twitter.com/user/status/{tweet_id}"
        )

        return {
            "success": True,
            "tweet_id": tweet_id,
            "tweet_url": f"https://twitter.com/user/status/{tweet_id}",
        }

    except Exception as e:
        logger.error(f"ツイート投稿中にエラーが発生しました: {e}")
        return {"success": False, "error": str(e)}


def add_emojis(text: str) -> str:
    """
    テキストにランダムな絵文字を追加する

    Args:
        text: 元のテキスト

    Returns:
        str: 絵文字が追加されたテキスト
    """
    emoji_list = [
        "✨",
        "💫",
        "💰",
        "💎",
        "🌟",
        "⭐",
        "🔥",
        "💯",
        "🎯",
        "🚀",
        "💪",
        "👑",
        "🌈",
        "🍀",
        "💝",
        "💖",
        "💕",
        "💓",
        "💘",
        "💞",
    ]

    # ランダムに2つの絵文字を選択
    selected_emojis = random.sample(emoji_list, 2)

    # テキストの先頭に絵文字を追加
    return f"{selected_emojis[0]} {text} {selected_emojis[1]}"


def ensure_utf8_encoding():
    """
    標準出力のエンコーディングをUTF-8に設定する

    Returns:
        bool: 設定に成功したかどうか
    """
    try:
        # 現在のstdoutを保存
        old_stdout = sys.stdout

        # 新しいUTF-8エンコーディングのTextIOWrapperを作成
        if hasattr(sys.stdout, "encoding") and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", line_buffering=True
            )
            logger.info(
                f"stdoutのエンコーディングを{old_stdout.encoding}からutf-8に変更しました"
            )

        return True
    except Exception as e:
        logger.error(f"stdoutのエンコーディング変更中にエラーが発生しました: {e}")
        return False


def main():
    """メイン関数"""
    try:
        # 標準出力のエンコーディングをUTF-8に設定
        ensure_utf8_encoding()

        logger.info("募集ツイートの生成を開始します")

        # 募集ツイートの生成
        post_text = generate_recruit_post()

        # 投稿
        result = post_to_twitter(post_text)

        if result["success"]:
            logger.info("処理が正常に完了しました")
            return 0
        else:
            logger.error("処理が失敗しました")
            return 1

    except UnicodeEncodeError as e:
        logger.error(f"UnicodeEncodeError: {e}")
        logger.info("エンコーディングを修正して再試行します")

        # エンコーディングを修正
        if ensure_utf8_encoding():
            # 再試行
            try:
                post_text = generate_recruit_post()
                result = post_to_twitter(post_text)

                if result["success"]:
                    logger.info("処理が正常に完了しました")
                    return 0
                else:
                    logger.error("処理が失敗しました")
                    return 1

            except Exception as e:
                logger.error(f"再試行中にエラーが発生しました: {e}")
                return 1
        else:
            logger.error("エンコーディングの修正に失敗しました")
            return 1

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
