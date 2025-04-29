"""
Poster module for X (Twitter) posts
"""
import time
import logging
import urllib.parse
from typing import Optional, Dict, Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDåriver

from bot.services.twitter_client.composer import type_tweet_text, click_tweet_button
from bot.services.twitter_client.media_uploader import prepare_media, upload_media, upload_multiple_media

logger = logging.getLogger(__name__)

def navigate_to_compose(driver: WebDriver, timeout: int = 10) -> bool:
    """
    投稿画面に移動する
    
    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        logger.info("投稿画面に移動します...")
        driver.get("https://x.com/home")
        time.sleep(3)
        
        COMPOSE_SELECTORS = [
            "[data-testid='SideNav_NewTweet_Button']",
            "[data-testid='FloatingActionButton_Tweet_Button']",
            "[aria-label='Tweet']",
            "[aria-label='ツイートする']",
            "[aria-label='投稿する']",
            "a[href='/compose/tweet']",
            "div[role='button'][data-testid*='tweet']",
            "div[role='button'][data-testid*='Tweet']"
        ]
        
        from bot.utils.safe_click import safe_click_by_selector
        
        for selector in COMPOSE_SELECTORS:
            logger.info(f"コンポーズボタンのセレクタを試しています: {selector}")
            try:
                if safe_click_by_selector(driver, selector, timeout=timeout, max_retries=5):
                    logger.info(f"コンポーズボタンをクリックしました: {selector}")
                    
                    # 投稿テキストボックスが表示されるのを待つ
                    try:
                        WebDriverWait(driver, timeout).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='textbox']"))
                        )
                        logger.info("投稿画面の読み込みが完了しました")
                        return True
                    except Exception as e:
                        logger.warning(f"テキストボックスの待機中にエラーが発生しました: {e}")
                        continue
            except Exception as e:
                logger.warning(f"セレクタ {selector} でのクリック中にエラーが発生しました: {e}")
                continue
        
        logger.info("直接URLに移動する方法を試します...")
        driver.get("https://x.com/compose/tweet")
        
        try:
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='textbox']"))
            )
            logger.info("投稿画面の読み込みが完了しました")
            return True
        except Exception as e:
            logger.error(f"投稿画面の読み込み待機中にエラーが発生しました: {e}")
            return False
    
    except Exception as e:
        logger.error(f"投稿画面への移動中にエラーが発生しました: {e}")
        return False

def wait_for_tweet_url(driver: WebDriver, timeout: int = 20) -> Optional[str]:
    """
    ツイートURLが表示されるのを待つ

    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）

    Returns:
        Optional[str]: ツイートURL、失敗した場合はNone
    """
    try:
        logger.info("ツイートURLが表示されるのを待っています...")

        try:
            WebDriverWait(driver, timeout).until(
                lambda d: "/status/" in d.current_url
            )
            tweet_url = driver.current_url
            logger.info(f"ツイートURLが見つかりました: {tweet_url}")
            return tweet_url
        except Exception:
            logger.warning("URLでのツイート確認がタイムアウトしました、代替方法を試します...")

        try:
            tweet_link = driver.find_element(By.CSS_SELECTOR, "a[href*='/status/']")
            tweet_url = tweet_link.get_attribute("href")
            logger.info(f"ツイートリンクが見つかりました: {tweet_url}")
            return tweet_url
        except Exception as e:
            logger.error(f"ツイートリンクが見つかりませんでした: {e}")
            return None

    except Exception as e:
        logger.error(f"ツイートURL待機中にエラーが発生しました: {e}")
        return None

def post_to_twitter(driver: WebDriver, post_text: str, media_url: Optional[str] = None,
                   media_files: Optional[List[str]] = None, logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    Xに投稿する（複数動画対応）

    Args:
        driver: WebDriverインスタンス
        post_text: 投稿するテキスト
        media_url: メディアURL（オプション、単一ファイル用）
        media_files: メディアファイルのパスリスト（オプション、複数ファイル用）
        logger: ロガーインスタンス（Noneの場合はモジュールロガーを使用）

    Returns:
        Optional[str]: ツイートURL、失敗した場合はNone
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        if not navigate_to_compose(driver):
            return None

        time.sleep(5)

        if media_files:
            logger.info(f"{len(media_files)}個のメディアファイルをアップロードします...")
            if not upload_multiple_media(driver, media_files):
                logger.warning("複数メディアのアップロードに失敗しました")
        elif media_url:
            media_path = prepare_media(media_url)
            if media_path:
                if not upload_media(driver, media_path):
                    logger.warning("メディアのアップロードに失敗しました")
            else:
                logger.warning(f"メディアの準備に失敗しました: {media_url}")

        logger.info(f"ツイートテキストを入力します: {post_text}")
        if not type_tweet_text(driver, post_text):
            logger.error("ツイートテキストの入力に失敗しました")
            return None

        if not click_tweet_button(driver):
            logger.error("ツイートボタンのクリックに失敗しました")
            return None

        tweet_url = wait_for_tweet_url(driver)
        if tweet_url:
            logger.info(f"ツイートに成功しました: {tweet_url}")
            return tweet_url
        else:
            logger.error("ツイートURLの取得に失敗しました")
            return None

    except Exception as e:
        logger.error(f"ツイート投稿中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def extract_tweet_id(tweet_url: str) -> Optional[str]:
    """
    ツイートURLからツイートIDを抽出する

    Args:
        tweet_url: ツイートURL

    Returns:
        Optional[str]: ツイートID、失敗した場合はNone
    """
    try:
        if not tweet_url:
            return None

        parsed_url = urllib.parse.urlparse(tweet_url)
        path_parts = parsed_url.path.split('/')

        for i, part in enumerate(path_parts):
            if part == 'status' and i + 1 < len(path_parts):
                return path_parts[i + 1]

        return None

    except Exception as e:
        logger.error(f"ツイートID抽出中にエラーが発生しました: {e}")
        return None

def navigate_to_tweet(driver: WebDriver, tweet_url: str, timeout: int = 10) -> bool:
    """
    特定のツイートに移動する

    Args:
        driver: WebDriverインスタンス
        tweet_url: ツイートURL
        timeout: タイムアウト（秒）

    Returns:
        bool: 成功したかどうか
    """
    try:
        logger.info(f"ツイートに移動します: {tweet_url}")
        driver.get(tweet_url)

        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']"))
            )
            logger.info("ツイートの読み込みが完了しました")
            return True
        except Exception as e:
            logger.error(f"ツイートの読み込み待機中にエラーが発生しました: {e}")
            return False

    except Exception as e:
        logger.error(f"ツイートへの移動中にエラーが発生しました: {e}")
        return False

def find_reply_button(driver: WebDriver, timeout: int = 10) -> bool:
    """
    返信ボタンを見つけてクリックする

    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）

    Returns:
        bool: 成功したかどうか
    """
    try:
        REPLY_BTN_SEL = "[data-testid='reply']"

        reply_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, REPLY_BTN_SEL))
        )

        logger.info("返信ボタンをクリックします...")
        reply_button.click()
        time.sleep(2)

        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']"))
            )
            logger.info("返信テキストボックスが表示されました")
            return True
        except Exception as e:
            logger.error(f"返信テキストボックスの表示待機中にエラーが発生しました: {e}")
            return False

    except Exception as e:
        logger.error(f"返信ボタンが見つかりませんでした: {e}")
        return False

def reply_to_tweet(driver: WebDriver, tweet_url: str, reply_text: str,
                  media_url: Optional[str] = None, logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    ツイートに返信する

    Args:
        driver: WebDriverインスタンス
        tweet_url: 返信先ツイートのURL
        reply_text: 返信テキスト
        media_url: メディアURL（オプション）
        logger: ロガーインスタンス（Noneの場合はモジュールロガーを使用）

    Returns:
        Optional[str]: 返信ツイートのURL、失敗した場合はNone
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        if not navigate_to_tweet(driver, tweet_url):
            return None

        time.sleep(3)

        if not find_reply_button(driver):
            return None

        if media_url:
            media_path = prepare_media(media_url)
            if media_path:
                if not upload_media(driver, media_path):
                    logger.warning("メディアのアップロードに失敗しました")
            else:
                logger.warning(f"メディアの準備に失敗しました: {media_url}")

        logger.info(f"返信テキストを入力します: {reply_text}")
        if not type_tweet_text(driver, reply_text):
            logger.error("返信テキストの入力に失敗しました")
            return None

        if not click_tweet_button(driver):
            logger.error("返信ボタンのクリックに失敗しました")
            return None

        reply_url = wait_for_tweet_url(driver)
        if reply_url:
            logger.info(f"返信に成功しました: {reply_url}")
            return reply_url
        else:
            logger.error("返信URLの取得に失敗しました")
            return None

    except Exception as e:
        logger.error(f"ツイート返信中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
