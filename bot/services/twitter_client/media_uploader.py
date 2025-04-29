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
            EC.element_to_be_clickable((By.CSS_SELECTOR, MEDIA_BTN_SEL))
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
    複数のメディアをアップロードする（最大4つまで）
    
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
        
        if len(media_paths) > 4:
            logger.warning(f"メディアファイルが4つを超えています。最初の4つのみアップロードします。")
            media_paths = media_paths[:4]
        
        try:
            file_input = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='fileInput']"))
            )
        except Exception as e:
            logger.error(f"メディアアップロードボタンが見つかりません: {e}")
            return False
        
        file_paths = []
        for media_path in media_paths:
            if not os.path.exists(media_path):
                logger.error(f"メディアファイルが見つかりません: {media_path}")
                continue
            file_paths.append(os.path.abspath(media_path))
        
        if not file_paths:
            logger.error("有効なメディアファイルがありません")
            return False
        
        logger.info(f"{len(file_paths)}個のメディアファイルを一度にアップロードします")
        file_input.send_keys("\n".join(file_paths))
        
        try:
            for i in range(len(file_paths)):
                WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='attachments'] > div:nth-child({i+1})"))
                )
                logger.info(f"メディアファイル {i+1}/{len(file_paths)} のアップロードが完了しました")
        except Exception as e:
            logger.error(f"メディアファイルのアップロードがタイムアウトしました: {e}")
            return False
        
        logger.info("すべてのメディアファイルのアップロードが完了しました")
        return True
    
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
