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
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
import pyperclip
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

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

# X（旧Twitter）の設定
X_COOKIE_PATH = os.getenv("X_COOKIE_PATH", "x_cookies.json")
X_BASE_URL = "https://x.com"


def random_delay(min_sec=1.0, max_sec=3.0):
    """ランダムな待機時間を返す（秒）"""
    return random.uniform(min_sec, max_sec)


def get_random_emojis(n=2):
    """UTF-8で使える多くの絵文字からランダムにn個選んで連結して返す"""
    emoji_list = [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
        "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
        "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩",
        "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣",
        "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", "🤬",
        "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗",
        "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯",
        "😦", "😧", "😮", "😲", "😴", "🤤", "😪", "😵", "🤐", "🥴",
        "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑", "🤠", "😈", "👿",
        "👹", "👺", "🤡", "💩", "👻", "💀", "☠️", "👽", "👾", "🤖",
        "🎃", "✨", "💫", "💰", "💎", "🌟", "⭐", "🔥", "💯", "🎯",
        "🚀", "💪", "👑", "🌈", "🍀", "💝", "💖", "💕", "💓", "💘",
        "💞"
    ]
    return ''.join(random.sample(emoji_list, n))


def create_driver(headless=False):
    """Seleniumドライバーを作成する"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(10)
    return driver


def load_cookies(driver, cookie_path, base_url):
    """クッキーを読み込む"""
    if not os.path.exists(cookie_path):
        logger.info(f"Cookieファイルが見つかりません: {cookie_path}")
        return False
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        logger.info(f"クッキーを適用します: {cookie_path}")
        driver.get(base_url)
        time.sleep(random_delay(2, 4))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
                logger.debug(f"Cookie 追加成功: {cookie.get('name')}")
            except Exception as e:
                logger.debug(f"Cookie 追加失敗: {cookie.get('name')} エラー: {e}")
                time.sleep(random_delay(0.5, 1.5))
        driver.refresh()
        time.sleep(random_delay(3, 5))
        logger.info(f"クッキーを適用しました: {cookie_path}")
        return True
    except Exception as e:
        logger.error(f"クッキー読み込み中にエラー: {e}")
        return False


def manual_login_flow(driver, cookie_path, base_url):
    """手動ログインフロー"""
    logger.info("クッキーがないまたはログイン状態が確認できません。手動ログインが必要です。")
    driver.get(base_url + "/i/flow/login")
    time.sleep(random_delay(3, 6))
    
    if os.getenv("CI"):
        logger.error("CI環境では手動ログインができません。X_COOKIE_PATHを設定してください。")
        return False
    
    input("ログイン完了後、Enterキーを押してください...")
    cookies = driver.get_cookies()
    try:
        os.makedirs(os.path.dirname(os.path.abspath(cookie_path)), exist_ok=True)
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"クッキーを保存しました: {cookie_path}")
    except Exception as e:
        logger.error(f"クッキー保存中にエラー: {e}")
    driver.get(base_url)
    time.sleep(random_delay(3, 6))
    return True


def is_logged_in(driver):
    """ログイン状態を確認する"""
    try:
        driver.find_element(By.CSS_SELECTOR, "a[data-testid='SideNav_NewTweet_Button']")
        return True
    except Exception:
        return False


def click_element(driver, element):
    """要素をクリックする"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(random_delay(1, 2))
        element.click()
    except ElementClickInterceptedException:
        logger.info("通常クリックが要素被りで失敗したため、JSクリックを試します。")
        driver.execute_script("arguments[0].click();", element)


def paste_text(driver, element, text):
    """テキストを貼り付ける"""
    pyperclip.copy(text)
    if sys.platform.startswith('darwin'):
        paste_keys = (Keys.COMMAND, 'v')
    else:
        paste_keys = (Keys.CONTROL, 'v')
    element.send_keys(*paste_keys)


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
    driver = None
    try:
        driver = create_driver(headless=os.getenv("CI") == "true")
        
        cookie_loaded = load_cookies(driver, X_COOKIE_PATH, X_BASE_URL)
        
        if not cookie_loaded or not is_logged_in(driver):
            if not manual_login_flow(driver, X_COOKIE_PATH, X_BASE_URL):
                raise Exception("ログインに失敗しました")
        
        driver.get(X_BASE_URL + "/home")
        time.sleep(random_delay(2, 4))
        
        try:
            tweet_button = driver.find_element(By.CSS_SELECTOR, "a[data-testid='SideNav_NewTweet_Button']")
            click_element(driver, tweet_button)
        except NoSuchElementException:
            try:
                tweet_button = driver.find_element(By.CSS_SELECTOR, "a[href='/compose/tweet']")
                click_element(driver, tweet_button)
            except NoSuchElementException:
                raise Exception("ツイート投稿ボタンが見つかりませんでした")
        
        time.sleep(random_delay(2, 3))
        
        try:
            tweet_box = driver.find_element(By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']")
        except NoSuchElementException:
            raise Exception("ツイート入力欄が見つかりませんでした")
        
        click_element(driver, tweet_box)
        time.sleep(random_delay(1, 2))
        
        final_text = f"{post_text}\n{get_random_emojis(2)}"
        paste_text(driver, tweet_box, final_text)
        time.sleep(random_delay(1, 2))
        
        try:
            post_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='tweetButton']"))
            )
            logger.info("tweetButton で投稿ボタンを取得しました")
        except TimeoutException:
            logger.info("tweetButton が見つからないため、tweetButtonInline を試みます")
            try:
                post_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='tweetButtonInline']"))
                )
                logger.info("tweetButtonInline で投稿ボタンを取得しました")
            except TimeoutException:
                raise Exception("投稿ボタンが見つかりませんでした")
        
        click_element(driver, post_button)
        time.sleep(random_delay(3, 5))
        
        try:
            success_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'ツイートを送信しました')]"))
            )
            logger.info("ツイートを投稿しました")
            
            tweet_url = f"{X_BASE_URL}/status/dummy_id"
            logger.info(f"ツイートURL: {tweet_url}")
            
            return {
                "success": True,
                "tweet_id": "dummy_id",
                "tweet_url": tweet_url
            }
        except TimeoutException:
            raise Exception("ツイート投稿の確認ができませんでした")

    except Exception as e:
        logger.error(f"ツイート投稿中にエラーが発生しました: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        if driver:
            driver.quit()


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
