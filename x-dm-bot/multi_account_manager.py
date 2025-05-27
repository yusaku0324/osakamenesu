# multi_account_manager.py - 複数アカウント管理機能
import os
import json
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from main import XDMBot
from models import Campaign
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


@dataclass
class Account:
    """アカウント情報を表すデータクラス"""
    id: str
    name: str
    username: str
    password: str
    active: bool
    proxy: Optional[str] = None
    campaigns: List[Campaign] = None
    
    def __post_init__(self):
        if self.campaigns is None:
            self.campaigns = []


class MultiAccountManager:
    """複数のX DMボットアカウントを管理するクラス"""
    
    def __init__(self, config_file: str = "multi_account_config.json"):
        self.config_file = config_file
        self.accounts: Dict[str, Account] = {}
        self.bot_instances: Dict[str, XDMBot] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.log_queues: Dict[str, queue.Queue] = {}
        self.stats: Dict[str, dict] = {}
        self.cipher = self._get_cipher()
        
        self.load_config()
    
    def _get_cipher(self):
        """暗号化オブジェクトを取得"""
        key_file = ".secret.key"
        if not os.path.exists(key_file):
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
        
        with open(key_file, 'rb') as f:
            key = f.read()
        return Fernet(key)
    
    def load_config(self):
        """設定ファイルからアカウント情報を読み込む"""
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file {self.config_file} not found")
            return
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # アカウント情報を読み込み
        for account_data in config.get('accounts', []):
            account_id = account_data['id']
            
            # 暗号化された認証情報を読み込み
            username, password = self._load_account_credentials(account_id)
            
            account = Account(
                id=account_id,
                name=account_data['name'],
                username=username or account_data.get('username', ''),
                password=password or '',
                active=account_data.get('active', False),
                proxy=account_data.get('proxy'),
                campaigns=[Campaign(**c) for c in account_data.get('campaigns', [])]
            )
            
            self.accounts[account_id] = account
            self.log_queues[account_id] = queue.Queue()
            self.stats[account_id] = {
                'total_sent': 0,
                'success_rate': 0,
                'active_time': '00:00:00',
                'tweets_found': 0,
                'status': 'stopped'
            }
    
    def _load_account_credentials(self, account_id: str) -> tuple:
        """アカウントの暗号化された認証情報を読み込む"""
        cred_file = f".credentials_{account_id}.enc"
        if not os.path.exists(cred_file):
            return None, None
        
        try:
            with open(cred_file, 'rb') as f:
                encrypted = f.read()
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            return data['username'], data['password']
        except Exception as e:
            logger.error(f"Failed to load credentials for {account_id}: {e}")
            return None, None
    
    def save_account_credentials(self, account_id: str, username: str, password: str):
        """アカウントの認証情報を暗号化して保存"""
        data = {
            'username': username,
            'password': password,
            'saved_at': datetime.now().isoformat()
        }
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        
        cred_file = f".credentials_{account_id}.enc"
        with open(cred_file, 'wb') as f:
            f.write(encrypted)
        
        # メモリ上のアカウント情報も更新
        if account_id in self.accounts:
            self.accounts[account_id].username = username
            self.accounts[account_id].password = password
    
    def add_account(self, name: str, username: str = "", password: str = "") -> str:
        """新しいアカウントを追加"""
        # 新しいIDを生成
        account_id = f"account_{len(self.accounts) + 1}"
        
        account = Account(
            id=account_id,
            name=name,
            username=username,
            password=password,
            active=False,
            campaigns=[]
        )
        
        self.accounts[account_id] = account
        self.log_queues[account_id] = queue.Queue()
        self.stats[account_id] = {
            'total_sent': 0,
            'success_rate': 0,
            'active_time': '00:00:00',
            'tweets_found': 0,
            'status': 'stopped'
        }
        
        # 認証情報を保存
        if username and password:
            self.save_account_credentials(account_id, username, password)
        
        self.save_config()
        return account_id
    
    def remove_account(self, account_id: str):
        """アカウントを削除"""
        if account_id in self.accounts:
            # 実行中の場合は停止
            if account_id in self.bot_instances:
                self.stop_bot(account_id)
            
            # アカウント情報を削除
            del self.accounts[account_id]
            del self.log_queues[account_id]
            del self.stats[account_id]
            
            # 認証情報ファイルを削除
            cred_file = f".credentials_{account_id}.enc"
            if os.path.exists(cred_file):
                os.remove(cred_file)
            
            self.save_config()
    
    def save_config(self):
        """設定をファイルに保存"""
        config = {
            'accounts': [],
            'global_settings': {
                'rate_limits': {
                    'max_dms_per_hour_per_account': 20,
                    'max_total_dms_per_hour': 50,
                    'user_cooldown_hours': 24
                },
                'browser_settings': {
                    'headless_mode': False,
                    'use_separate_profiles': True,
                    'profile_directory': './profiles'
                }
            }
        }
        
        for account in self.accounts.values():
            account_data = {
                'id': account.id,
                'name': account.name,
                'username': account.username,  # 実際の保存時は空にする
                'active': account.active,
                'proxy': account.proxy,
                'campaigns': [
                    {
                        'name': c.name,
                        'keywords': c.keywords,
                        'message_templates': c.message_templates,
                        'max_dms_per_hour': c.max_dms_per_hour,
                        'check_interval': c.check_interval,
                        'active': c.active
                    } for c in account.campaigns
                ]
            }
            config['accounts'].append(account_data)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def start_bot(self, account_id: str):
        """特定のアカウントのボットを開始"""
        if account_id not in self.accounts:
            raise ValueError(f"Account {account_id} not found")
        
        account = self.accounts[account_id]
        
        if not account.username or not account.password:
            raise ValueError(f"No credentials for account {account_id}")
        
        if account_id in self.bot_instances:
            logger.warning(f"Bot for account {account_id} is already running")
            return
        
        # 環境変数を設定
        env = os.environ.copy()
        env['X_USERNAME'] = account.username
        env['X_PASSWORD'] = account.password
        if account.proxy:
            env['PROXY_URL'] = account.proxy
        
        # ボットインスタンスを作成
        bot = XDMBot()
        bot.config = {
            'campaigns': [vars(c) for c in account.campaigns],
            'rate_limits': {
                'max_dms_per_hour': 20,
                'user_cooldown_hours': 24
            },
            'exclude_list': []
        }
        
        self.bot_instances[account_id] = bot
        self.stats[account_id]['status'] = 'running'
        
        # 別スレッドでボットを実行
        thread = threading.Thread(
            target=self._run_bot_thread,
            args=(account_id, bot, env),
            daemon=True
        )
        thread.start()
        self.threads[account_id] = thread
        
        logger.info(f"Started bot for account {account.name} ({account_id})")
    
    def _run_bot_thread(self, account_id: str, bot: XDMBot, env: dict):
        """ボットを別スレッドで実行"""
        try:
            # 環境変数を一時的に設定
            old_env = os.environ.copy()
            os.environ.update(env)
            
            # ボットを実行
            bot.run()
            
        except Exception as e:
            self.log_message(account_id, "ERROR", f"Bot error: {str(e)}")
        finally:
            # 環境変数を復元
            os.environ.clear()
            os.environ.update(old_env)
            
            # クリーンアップ
            self.stats[account_id]['status'] = 'stopped'
            if account_id in self.bot_instances:
                del self.bot_instances[account_id]
            if account_id in self.threads:
                del self.threads[account_id]
    
    def stop_bot(self, account_id: str):
        """特定のアカウントのボットを停止"""
        if account_id in self.bot_instances:
            bot = self.bot_instances[account_id]
            try:
                bot.cleanup()
            except:
                pass
            
            del self.bot_instances[account_id]
            self.stats[account_id]['status'] = 'stopped'
            logger.info(f"Stopped bot for account {account_id}")
    
    def start_all_active(self):
        """アクティブな全アカウントのボットを開始"""
        active_accounts = [acc for acc in self.accounts.values() if acc.active]
        
        with ThreadPoolExecutor(max_workers=len(active_accounts)) as executor:
            futures = []
            for account in active_accounts:
                future = executor.submit(self.start_bot, account.id)
                futures.append((account.id, future))
            
            for account_id, future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Failed to start bot for {account_id}: {e}")
    
    def stop_all(self):
        """全てのボットを停止"""
        for account_id in list(self.bot_instances.keys()):
            self.stop_bot(account_id)
    
    def log_message(self, account_id: str, level: str, message: str):
        """アカウント別のログメッセージを記録"""
        if account_id in self.log_queues:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_queues[account_id].put(f"[{timestamp}] [{level}] {message}")
    
    def get_account_logs(self, account_id: str, limit: int = 100) -> List[str]:
        """特定のアカウントのログを取得"""
        if account_id not in self.log_queues:
            return []
        
        logs = []
        log_queue = self.log_queues[account_id]
        
        while not log_queue.empty() and len(logs) < limit:
            try:
                logs.append(log_queue.get_nowait())
            except:
                break
        
        return logs
    
    def get_all_stats(self) -> Dict[str, dict]:
        """全アカウントの統計情報を取得"""
        return self.stats.copy()


# 使用例
if __name__ == "__main__":
    manager = MultiAccountManager()
    
    # アカウントを追加
    account_id = manager.add_account("テストアカウント", "test_user", "test_pass")
    
    # キャンペーンを追加
    campaign = Campaign(
        name="Test Campaign",
        keywords=["Python", "プログラミング"],
        message_templates=["こんにちは！"],
        max_dms_per_hour=10,
        check_interval=60,
        active=True
    )
    manager.accounts[account_id].campaigns.append(campaign)
    
    # ボットを開始
    # manager.start_bot(account_id)
    
    print(f"Added account: {account_id}")