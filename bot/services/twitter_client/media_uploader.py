"""
Media uploader module for X (Twitter) posts
"""
import os
import time
import logging
import tempfile
import urllib.request
from typing import Optional, List, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

def download_media(url: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    メディアファイルをダウンロードする
    
    Args:
        url: ダウンロードURL
        output_path: 保存先パス（Noneの場合は一時ファイルを作成）
        
    Returns:
        Optional[str]: ダウンロードされたファイルのパス、失敗した場合はNone
    """
    try:
        if not url.startswith(('http://', 'https://')):
            if os.path.exists(url):
                logger.info(f"ローカルファイルを使用します: {url}")
                return url
            else:
                logger.error(f"無効なURL: {url}")
                return None
        
        if output_path is None:
            _, ext = os.path.splitext(url)
            if not ext:
                ext = '.tmp'
            
            fd, output_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
        
        # output_pathが空文字列の場合も考慮
        if output_path and os.path.dirname(output_path):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"メディアをダウンロードしています: {url} → {output_path}")
        urllib.request.urlretrieve(url, output_path)
        
        if not os.path.exists(output_path):
            logger.error(f"メディアのダウンロードに失敗しました: {output_path}")
            return None
        
        logger.info(f"メディアのダウンロードに成功しました: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"メディアのダウンロード中にエラーが発生しました: {e}")
        return None

def find_media_button(driver: WebDriver, timeout: int = 10) -> bool:
    """
    メディアボタンを見つけてクリックする
    
    Args:
        driver: WebDriverインスタンス
        timeout: タイムアウト（秒）
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        MEDIA_BTN_SEL = "[data-testid='fileInput']"
        
        media_button = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, MEDIA_BTN_SEL))
        )
        
        logger.info("メディアボタンを見つけました")
        return True
    
    except Exception as e:
        logger.error(f"メディアボタンが見つかりませんでした: {e}")
        return False

def upload_media(driver: WebDriver, media_path: str, timeout: int = 30) -> bool:
    """
    メディアをアップロードする
    
    Args:
        driver: WebDriverインスタンス
        media_path: メディアファイルのパス
        timeout: タイムアウト（秒）
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        if not os.path.exists(media_path):
            logger.error(f"メディアファイルが見つかりません: {media_path}")
            return False
        
        if not find_media_button(driver, timeout):
            return False
        
        file_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='fileInput']")
        
        absolute_path = os.path.abspath(media_path)
        logger.info(f"メディアをアップロードしています: {absolute_path}")
        file_input.send_keys(absolute_path)
        
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='attachments']"))
            )
            logger.info("メディアのアップロードに成功しました")
            return True
        
        except Exception as e:
            logger.error(f"メディアのアップロード完了待機中にエラーが発生しました: {e}")
            return False
    
    except Exception as e:
        logger.error(f"メディアのアップロード中にエラーが発生しました: {e}")
        return False

def upload_multiple_media(driver: WebDriver, media_paths: List[str], timeout: int = 30) -> bool:
    """
    複数のメディアをアップロードする
    
    Args:
        driver: WebDriverインスタンス
        media_paths: メディアファイルのパスリスト
        timeout: タイムアウト（秒）
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        if not media_paths:
            logger.warning("アップロードするメディアがありません")
            return True
        
        success_count = 0
        
        for media_path in media_paths:
            if upload_media(driver, media_path, timeout):
                success_count += 1
                time.sleep(2)
            else:
                logger.error(f"メディア {media_path} のアップロードに失敗しました")
        
        logger.info(f"{success_count}/{len(media_paths)}個のメディアをアップロードしました")
        return success_count == len(media_paths)
    
    except Exception as e:
        logger.error(f"複数メディアのアップロード中にエラーが発生しました: {e}")
        return False

def prepare_media(media_url: Optional[str]) -> Optional[str]:
    """
    メディアURLを処理し、必要に応じてダウンロードする
    
    Args:
        media_url: メディアURL（ローカルパスまたはURL）
        
    Returns:
        Optional[str]: 処理されたメディアパス、失敗した場合はNone
    """
    try:
        if not media_url:
            logger.info("メディアURLが指定されていません")
            return None
        
        if os.path.exists(media_url):
            logger.info(f"ローカルメディアファイルを使用します: {media_url}")
            return media_url
        
        if media_url.startswith(('http://', 'https://')):
            return download_media(media_url)
        
        logger.warning(f"認識できないメディアURL形式です: {media_url}")
        return None
    
    except Exception as e:
        logger.error(f"メディアの準備中にエラーが発生しました: {e}")
        return None
