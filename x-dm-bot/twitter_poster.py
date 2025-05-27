# twitter_poster.py - X (Twitter) 投稿機能
import os
import time
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)


@dataclass
class Post:
    """投稿情報を表すデータクラス"""
    content: str
    media_paths: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None
    reply_to_id: Optional[str] = None
    
    
@dataclass
class PostCampaign:
    """投稿キャンペーンを表すデータクラス"""
    name: str
    posts: List[Post]
    interval_minutes: int = 60
    randomize_interval: bool = True
    active: bool = True


class XPoster:
    """X (Twitter) 投稿自動化クラス"""
    
    def __init__(self, username: str, password: str, proxy: Optional[str] = None):
        self.username = username
        self.password = password
        self.proxy = proxy if proxy else None
        self.driver = None
        self.wait = None
        self.logged_in = False
        
    def _setup_driver(self):
        """Chrome ドライバーをセットアップ"""
        try:
            # 古いchromedriverをPATHから除外
            import os
            current_path = os.environ.get('PATH', '')
            path_dirs = current_path.split(':')
            # /usr/local/bin を除外
            filtered_dirs = [d for d in path_dirs if d != '/usr/local/bin']
            os.environ['PATH'] = ':'.join(filtered_dirs)
            
            options = uc.ChromeOptions()
            
            # アンチ検出オプション
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # プロキシ設定
            if self.proxy:
                options.add_argument(f'--proxy-server={self.proxy}')
            
            # ユーザーエージェント
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            # Chrome のバージョンを自動検出
            self.driver = uc.Chrome(options=options)
            
            # PATHを元に戻す
            os.environ['PATH'] = current_path
            self.wait = WebDriverWait(self.driver, 20)
            
            # アンチ検出対策
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("ドライバーのセットアップが完了しました")
            
        except Exception as e:
            logger.error(f"ドライバーセットアップエラー: {e}")
            raise
    
    def login(self) -> bool:
        """X にログイン"""
        try:
            logger.info("ログインを開始します...")
            self.driver.get("https://twitter.com/login")
            time.sleep(random.uniform(3, 5))
            
            # ユーザー名入力
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            self._human_type(username_input, self.username)
            username_input.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 4))
            
            # パスワード入力
            password_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
            )
            self._human_type(password_input, self.password)
            password_input.send_keys(Keys.RETURN)
            
            # ログイン完了を待機
            time.sleep(random.uniform(5, 7))
            
            # ログイン成功確認
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="primaryColumn"]'))
                )
                self.logged_in = True
                logger.info("ログインに成功しました")
                return True
            except TimeoutException:
                logger.error("ログインに失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            return False
    
    def _human_type(self, element, text: str):
        """人間らしい遅延でテキストを入力"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.3))
    
    def create_post(self, post: Post) -> bool:
        """投稿を作成"""
        try:
            logger.info(f"投稿を作成します: {post.content[:50]}...")
            
            # ホームページに移動
            self.driver.get("https://twitter.com/home")
            time.sleep(random.uniform(2, 4))
            
            # 投稿ボックスをクリック
            tweet_box = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
            )
            tweet_box.click()
            time.sleep(random.uniform(1, 2))
            
            # テキストを入力
            self._human_type(tweet_box, post.content)
            
            # メディアを追加（存在する場合）
            if post.media_paths:
                self._add_media(post.media_paths)
            
            # 投稿ボタンをクリック
            tweet_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]'))
            )
            tweet_button.click()
            
            time.sleep(random.uniform(3, 5))
            logger.info("投稿が成功しました")
            return True
            
        except Exception as e:
            logger.error(f"投稿エラー: {e}")
            return False
    
    def _add_media(self, media_paths: List[str]):
        """メディア（画像/動画）を追加"""
        try:
            # メディアボタンをクリック
            media_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="fileInput"]'))
            )
            
            for media_path in media_paths[:4]:  # 最大4つまで
                if os.path.exists(media_path):
                    media_button.send_keys(os.path.abspath(media_path))
                    time.sleep(random.uniform(2, 3))
                    logger.info(f"メディアを追加しました: {media_path}")
                else:
                    logger.warning(f"メディアファイルが見つかりません: {media_path}")
                    
        except Exception as e:
            logger.error(f"メディア追加エラー: {e}")
    
    def reply_to_tweet(self, tweet_url: str, reply_content: str) -> bool:
        """ツイートに返信"""
        try:
            logger.info(f"ツイートに返信します: {tweet_url}")
            
            # ツイートページに移動
            self.driver.get(tweet_url)
            time.sleep(random.uniform(3, 5))
            
            # 返信ボックスをクリック
            reply_box = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
            )
            reply_box.click()
            
            # 返信内容を入力
            self._human_type(reply_box, reply_content)
            
            # 返信ボタンをクリック
            reply_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButton"]'))
            )
            reply_button.click()
            
            time.sleep(random.uniform(3, 5))
            logger.info("返信が成功しました")
            return True
            
        except Exception as e:
            logger.error(f"返信エラー: {e}")
            return False
    
    def run_campaign(self, campaign: PostCampaign):
        """投稿キャンペーンを実行"""
        logger.info(f"投稿キャンペーンを開始: {campaign.name}")
        
        for i, post in enumerate(campaign.posts):
            if not campaign.active:
                logger.info("キャンペーンが停止されました")
                break
            
            # 投稿を実行
            success = self.create_post(post)
            
            if success:
                logger.info(f"投稿 {i+1}/{len(campaign.posts)} が完了しました")
            else:
                logger.error(f"投稿 {i+1}/{len(campaign.posts)} が失敗しました")
            
            # 次の投稿まで待機（最後の投稿以外）
            if i < len(campaign.posts) - 1:
                wait_time = campaign.interval_minutes * 60
                if campaign.randomize_interval:
                    wait_time = random.uniform(wait_time * 0.8, wait_time * 1.2)
                
                logger.info(f"次の投稿まで {wait_time/60:.1f} 分待機します...")
                time.sleep(wait_time)
        
        logger.info("キャンペーンが完了しました")
    
    def cleanup(self):
        """リソースをクリーンアップ"""
        if self.driver:
            logger.info("ブラウザを閉じています...")
            self.driver.quit()


# 統合マネージャー
class XAccountManager:
    """DM と投稿の両方を管理する統合マネージャー"""
    
    def __init__(self, account_id: str, username: str, password: str, proxy: Optional[str] = None):
        self.account_id = account_id
        self.username = username
        self.password = password
        self.proxy = proxy
        self.mode = "dm"  # "dm" or "post"
        self.dm_bot = None
        self.poster = None
        
    def set_mode(self, mode: str):
        """モードを設定（dm または post）"""
        if mode in ["dm", "post"]:
            self.mode = mode
            logger.info(f"モードを {mode} に設定しました")
        else:
            raise ValueError("モードは 'dm' または 'post' である必要があります")
    
    def start_dm_bot(self, config: dict):
        """DMボットを開始"""
        from main import XDMBot
        
        # 環境変数を設定
        os.environ['X_USERNAME'] = self.username
        os.environ['X_PASSWORD'] = self.password
        if self.proxy:
            os.environ['PROXY_URL'] = self.proxy
        
        self.dm_bot = XDMBot()
        self.dm_bot.config = config
        self.dm_bot.run()
    
    def start_poster(self, campaign: PostCampaign):
        """投稿ボットを開始"""
        self.poster = XPoster(self.username, self.password, self.proxy)
        self.poster._setup_driver()
        
        if self.poster.login():
            self.poster.run_campaign(campaign)
        
        self.poster.cleanup()
    
    def stop(self):
        """実行中のボットを停止"""
        if self.dm_bot:
            self.dm_bot.cleanup()
        if self.poster:
            self.poster.cleanup()