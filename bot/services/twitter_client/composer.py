"""
Twitter composer module for text input with CDP and fallback mechanisms
"""
import sys
import time
import random
import logging
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)

def find_textbox(driver: WebDriver, timeout: int = 10) -> Optional[WebElement]:
    """
    テキスト入力ボックスを見つける
    
    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）
        
    Returns:
        Optional[WebElement]: テキストボックス要素、見つからない場合はNone
    """
    TEXTBOX_SEL = "div[role='textbox'],[data-testid='tweetTextarea_0']"
    
    try:
        box = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, TEXTBOX_SEL))
        )
        return box
    except Exception as e:
        logger.error(f"テキストボックスが見つかりませんでした: {e}")
        return None

def type_text_cdp(driver: WebDriver, text: str) -> bool:
    """
    CDPを使用してテキストを入力する
    
    Args:
        driver: WebDriverインスタンス
        text: 入力するテキスト
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        driver.execute_cdp_cmd("Input.insertText", {"text": text})
        time.sleep(0.3)
        logger.info("CDPを使用してテキストを入力しました")
        return True
    except Exception as e:
        logger.warning(f"CDP入力に失敗しました: {e}")
        return False

def type_text_clipboard(driver: WebDriver, box: WebElement, text: str) -> bool:
    """
    クリップボードを使用してテキストを入力する
    
    Args:
        driver: WebDriverインスタンス
        box: テキストボックス要素
        text: 入力するテキスト
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        
        if sys.platform.startswith("darwin"):
            box.send_keys(driver.Keys.COMMAND, "v")
        else:
            box.send_keys(driver.Keys.CONTROL, "v")
        
        time.sleep(0.3)
        logger.info("クリップボードを使用してテキストを入力しました")
        return True
    except Exception as e:
        logger.warning(f"クリップボード入力に失敗しました: {e}")
        return False

def type_text_character(box: WebElement, text: str) -> bool:
    """
    1文字ずつテキストを入力する
    
    Args:
        box: テキストボックス要素
        text: 入力するテキスト
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        for ch in text:
            box.send_keys(ch)
            time.sleep(random.uniform(0.02, 0.05))
        
        logger.info("1文字ずつテキストを入力しました")
        return True
    except Exception as e:
        logger.error(f"1文字ずつの入力に失敗しました: {e}")
        return False

def type_tweet_text(driver: WebDriver, text: str, timeout: int = 10) -> bool:
    """
    3段階フォールバックを使用してツイートテキストを入力する
    ①CDP → ②クリップボード → ③1文字ずつ
    
    Args:
        driver: WebDriverインスタンス
        text: 入力するテキスト
        timeout: タイムアウト（秒）
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        box = find_textbox(driver, timeout)
        if not box:
            return False
        
        box.click()  # フォーカスだけ合わせる
        time.sleep(0.2)
        
        if type_text_cdp(driver, text):
            if box.text.strip():  # 成功確認
                logger.info("CDPを使用してテキストを入力しました")
                return True
        
        if type_text_clipboard(driver, box, text):
            if box.text.strip():
                logger.info("クリップボードを使用してテキストを入力しました")
                return True
        
        if type_text_character(box, text):
            logger.info("1文字ずつテキストを入力しました")
            return True
        
        logger.error("すべての入力方法が失敗しました")
        return False
    
    except Exception as e:
        logger.error(f"テキスト入力中にエラーが発生しました: {e}")
        return False

def find_tweet_button(driver: WebDriver, timeout: int = 15) -> Optional[WebElement]:
    """
    ツイートボタンを見つける
    
    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）
        
    Returns:
        Optional[WebElement]: ボタン要素、見つからない場合はNone
    """
    BTN_SEL = "[data-testid$='tweetButton'],[data-testid$='tweetButtonInline']"
    
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, BTN_SEL))
        )
        return button
    except Exception as e:
        logger.error(f"ツイートボタンが見つかりませんでした: {e}")
        return None

def click_tweet_button(driver: WebDriver, timeout: int = 15) -> bool:
    """
    ツイートボタンをクリックする
    
    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        from bot.utils.safe_click import safe_click_by_selector
        
        BTN_SEL = "[data-testid$='tweetButton'],[data-testid$='tweetButtonInline']"
        
        logger.info("ツイートボタンをクリックします...")
        if safe_click_by_selector(driver, BTN_SEL, timeout=timeout, max_retries=5):
            time.sleep(5)
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"ツイートボタンのクリック中にエラーが発生しました: {e}")
        return False
