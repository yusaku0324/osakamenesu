# gui_app.py - X DM Bot GUI版
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
import threading
import queue
from datetime import datetime
import sys
from pathlib import Path
import subprocess
import webbrowser
from cryptography.fernet import Fernet
import base64

# メインボットのインポート（後で作成）
try:
    from main import XDMBot, Campaign
except ImportError:
    XDMBot = None
    Campaign = None


class ConfigManager:
    """設定ファイルと暗号化を管理"""
    
    def __init__(self):
        self.config_file = "config.json"
        self.encrypted_file = ".credentials.enc"
        self.key_file = ".secret.key"
        self._ensure_key()
    
    def _ensure_key(self):
        """暗号化キーを確保"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        
    def _get_cipher(self):
        """暗号化オブジェクトを取得"""
        with open(self.key_file, 'rb') as f:
            key = f.read()
        return Fernet(key)
    
    def save_credentials(self, username, password):
        """認証情報を暗号化して保存"""
        cipher = self._get_cipher()
        data = {
            'username': username,
            'password': password,
            'saved_at': datetime.now().isoformat()
        }
        encrypted = cipher.encrypt(json.dumps(data).encode())
        with open(self.encrypted_file, 'wb') as f:
            f.write(encrypted)
    
    def load_credentials(self):
        """暗号化された認証情報を読み込み"""
        if not os.path.exists(self.encrypted_file):
            return None, None
        
        try:
            cipher = self._get_cipher()
            with open(self.encrypted_file, 'rb') as f:
                encrypted = f.read()
            decrypted = cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            return data['username'], data['password']
        except:
            return None, None
    
    def save_config(self, config):
        """設定をJSONファイルに保存"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def load_config(self):
        """設定をJSONファイルから読み込み"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.get_default_config()
    
    def get_default_config(self):
        """デフォルト設定を返す"""
        return {
            "campaigns": [],
            "rate_limits": {
                "max_dms_per_hour": 20,
                "user_cooldown_hours": 24,
                "min_delay_between_dms": 10,
                "max_delay_between_dms": 30
            },
            "exclude_list": [],
            "settings": {
                "headless_mode": False,
                "use_proxy": False,
                "proxy_url": "",
                "save_screenshots_on_error": True,
                "max_retries": 3,
                "timeout_seconds": 30,
                "log_level": "INFO"
            }
        }


class XDMBotGUI:
    """X DM Bot のGUIアプリケーション"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("X DM Bot - 設定管理システム")
        self.root.geometry("1200x800")
        
        # スタイル設定
        self.setup_styles()
        
        # マネージャー
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # ボット関連
        self.bot_thread = None
        self.bot_instance = None
        self.log_queue = queue.Queue()
        self.is_running = False
        
        # GUI構築
        self.create_widgets()
        self.load_saved_data()
        
        # ログ更新を開始
        self.update_log_display()
    
    def setup_styles(self):
        """GUIスタイルを設定"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # カスタムカラー
        self.colors = {
            'primary': '#1DA1F2',
            'success': '#17BF63',
            'danger': '#E1306C',
            'warning': '#FFAD1F',
            'dark': '#14171A',
            'light': '#F7F9FA'
        }
    
    def create_widgets(self):
        """メインウィジェットを作成"""
        # メニューバー
        self.create_menu()
        
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 各タブ
        self.create_account_tab()
        self.create_campaigns_tab()
        self.create_settings_tab()
        self.create_monitor_tab()
        self.create_help_tab()
    
    def create_menu(self):
        """メニューバーを作成"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="設定をエクスポート", command=self.export_config)
        file_menu.add_command(label="設定をインポート", command=self.import_config)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit)
        
        # ツールメニュー
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="依存関係をインストール", command=self.install_dependencies)
        tools_menu.add_command(label="ログをクリア", command=self.clear_logs)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self.show_help)
        help_menu.add_command(label="バージョン情報", command=self.show_about)
    
    def create_account_tab(self):
        """アカウント設定タブを作成"""
        account_frame = ttk.Frame(self.notebook)
        self.notebook.add(account_frame, text="アカウント設定")
        
        # メインコンテナ
        main_container = ttk.Frame(account_frame, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title = ttk.Label(main_container, text="X (Twitter) アカウント設定", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 20))
        
        # 認証情報フレーム
        auth_frame = ttk.LabelFrame(main_container, text="認証情報", padding="20")
        auth_frame.pack(fill=tk.X, pady=(0, 20))
        
        # ユーザー名
        ttk.Label(auth_frame, text="ユーザー名/メールアドレス:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(auth_frame, textvariable=self.username_var, width=40)
        self.username_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # パスワード
        ttk.Label(auth_frame, text="パスワード:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, width=40, show="*")
        self.password_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # パスワード表示トグル
        self.show_password_var = tk.BooleanVar()
        show_password_cb = ttk.Checkbutton(auth_frame, text="パスワードを表示", 
                                          variable=self.show_password_var,
                                          command=self.toggle_password_visibility)
        show_password_cb.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # プロキシ設定フレーム
        proxy_frame = ttk.LabelFrame(main_container, text="プロキシ設定（オプション）", padding="20")
        proxy_frame.pack(fill=tk.X, pady=(0, 20))
        
        # プロキシ使用
        self.use_proxy_var = tk.BooleanVar()
        proxy_cb = ttk.Checkbutton(proxy_frame, text="プロキシを使用する", 
                                  variable=self.use_proxy_var,
                                  command=self.toggle_proxy_settings)
        proxy_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # プロキシURL
        ttk.Label(proxy_frame, text="プロキシURL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.proxy_url_var = tk.StringVar()
        self.proxy_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_url_var, width=40, state='disabled')
        self.proxy_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        ttk.Label(proxy_frame, text="例: http://user:pass@proxy.server:8080", 
                 font=('Arial', 9), foreground='gray').grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # 保存ボタン
        button_frame = ttk.Frame(main_container)
        button_frame.pack(pady=20)
        
        save_btn = ttk.Button(button_frame, text="認証情報を保存", command=self.save_credentials)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        test_btn = ttk.Button(button_frame, text="接続テスト", command=self.test_connection)
        test_btn.pack(side=tk.LEFT, padx=5)
        
        # ステータス表示
        self.account_status_var = tk.StringVar(value="認証情報が設定されていません")
        status_label = ttk.Label(main_container, textvariable=self.account_status_var,
                               font=('Arial', 10), foreground='gray')
        status_label.pack(pady=10)
    
    def create_campaigns_tab(self):
        """キャンペーン設定タブを作成"""
        campaigns_frame = ttk.Frame(self.notebook)
        self.notebook.add(campaigns_frame, text="キャンペーン管理")
        
        # 左右分割
        left_frame = ttk.Frame(campaigns_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        left_frame.pack_propagate(False)
        
        right_frame = ttk.Frame(campaigns_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)
        
        # 左側 - キャンペーンリスト
        ttk.Label(left_frame, text="キャンペーン一覧", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # リストボックス
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.campaigns_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.campaigns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.campaigns_listbox.yview)
        
        self.campaigns_listbox.bind('<<ListboxSelect>>', self.on_campaign_select)
        
        # ボタン
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="新規作成", command=self.new_campaign).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="削除", command=self.delete_campaign).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="複製", command=self.duplicate_campaign).pack(side=tk.LEFT, padx=2)
        
        # 右側 - キャンペーン詳細
        self.campaign_detail_frame = ttk.Frame(right_frame)
        self.campaign_detail_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_campaign_detail_widgets()
        self.refresh_campaigns_list()
    
    def create_campaign_detail_widgets(self):
        """キャンペーン詳細ウィジェットを作成"""
        # スクロール可能なフレーム
        canvas = tk.Canvas(self.campaign_detail_frame)
        scrollbar = ttk.Scrollbar(self.campaign_detail_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 詳細フォーム
        detail_container = ttk.Frame(scrollable_frame, padding="20")
        detail_container.pack(fill=tk.BOTH, expand=True)
        
        # キャンペーン名
        ttk.Label(detail_container, text="キャンペーン名:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.campaign_name_var = tk.StringVar()
        ttk.Entry(detail_container, textvariable=self.campaign_name_var, width=50).grid(row=0, column=1, pady=5, sticky=tk.W)
        
        # アクティブ状態
        self.campaign_active_var = tk.BooleanVar()
        ttk.Checkbutton(detail_container, text="このキャンペーンを有効にする", 
                       variable=self.campaign_active_var).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # キーワード
        ttk.Label(detail_container, text="検索キーワード:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.NW, pady=5)
        keywords_frame = ttk.Frame(detail_container)
        keywords_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.keywords_text = scrolledtext.ScrolledText(keywords_frame, height=3, width=50)
        self.keywords_text.pack(side=tk.LEFT)
        ttk.Label(keywords_frame, text="1行に1つずつ入力", font=('Arial', 9), foreground='gray').pack(side=tk.LEFT, padx=10)
        
        # メッセージテンプレート
        ttk.Label(detail_container, text="メッセージテンプレート:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.NW, pady=5)
        template_frame = ttk.Frame(detail_container)
        template_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        self.templates_text = scrolledtext.ScrolledText(template_frame, height=6, width=50)
        self.templates_text.pack()
        
        # 変数説明
        var_info = ttk.Frame(template_frame)
        var_info.pack(fill=tk.X, pady=5)
        ttk.Label(var_info, text="使用可能な変数:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(var_info, text="{username} - ユーザー名", font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(var_info, text="{keyword} - 検索キーワード", font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(var_info, text="{time_ago} - 経過秒数", font=('Arial', 9)).pack(anchor=tk.W)
        
        # レート設定
        rate_frame = ttk.LabelFrame(detail_container, text="レート設定", padding="10")
        rate_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(rate_frame, text="1時間あたりの最大DM数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_dms_var = tk.IntVar(value=15)
        ttk.Spinbox(rate_frame, from_=1, to=50, textvariable=self.max_dms_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(rate_frame, text="チェック間隔（秒）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.check_interval_var = tk.IntVar(value=30)
        ttk.Spinbox(rate_frame, from_=10, to=300, textvariable=self.check_interval_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 除外リスト
        ttk.Label(detail_container, text="除外ユーザー:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.NW, pady=5)
        exclude_frame = ttk.Frame(detail_container)
        exclude_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        self.exclude_text = scrolledtext.ScrolledText(exclude_frame, height=3, width=50)
        self.exclude_text.pack(side=tk.LEFT)
        ttk.Label(exclude_frame, text="1行に1ユーザー", font=('Arial', 9), foreground='gray').pack(side=tk.LEFT, padx=10)
        
        # 保存ボタン
        save_frame = ttk.Frame(detail_container)
        save_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(save_frame, text="キャンペーンを保存", command=self.save_campaign).pack()
    
    def create_settings_tab(self):
        """設定タブを作成"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="詳細設定")
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 設定コンテナ
        settings_container = ttk.Frame(scrollable_frame, padding="20")
        settings_container.pack(fill=tk.BOTH, expand=True)
        
        # レート制限設定
        rate_frame = ttk.LabelFrame(settings_container, text="グローバルレート制限", padding="15")
        rate_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(rate_frame, text="1時間あたりの最大DM数（全体）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.global_max_dms_var = tk.IntVar(value=20)
        ttk.Spinbox(rate_frame, from_=1, to=100, textvariable=self.global_max_dms_var, width=15).grid(row=0, column=1, pady=5)
        
        ttk.Label(rate_frame, text="ユーザークールダウン時間（時間）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cooldown_hours_var = tk.IntVar(value=24)
        ttk.Spinbox(rate_frame, from_=1, to=168, textvariable=self.cooldown_hours_var, width=15).grid(row=1, column=1, pady=5)
        
        ttk.Label(rate_frame, text="DM間の最小遅延（秒）:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.min_delay_var = tk.IntVar(value=10)
        ttk.Spinbox(rate_frame, from_=5, to=60, textvariable=self.min_delay_var, width=15).grid(row=2, column=1, pady=5)
        
        ttk.Label(rate_frame, text="DM間の最大遅延（秒）:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_delay_var = tk.IntVar(value=30)
        ttk.Spinbox(rate_frame, from_=10, to=300, textvariable=self.max_delay_var, width=15).grid(row=3, column=1, pady=5)
        
        # ブラウザ設定
        browser_frame = ttk.LabelFrame(settings_container, text="ブラウザ設定", padding="15")
        browser_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.headless_var = tk.BooleanVar()
        ttk.Checkbutton(browser_frame, text="ヘッドレスモード（バックグラウンド実行）", 
                       variable=self.headless_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.screenshot_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(browser_frame, text="エラー時にスクリーンショットを保存", 
                       variable=self.screenshot_var).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(browser_frame, text="タイムアウト時間（秒）:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.IntVar(value=30)
        ttk.Spinbox(browser_frame, from_=10, to=120, textvariable=self.timeout_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # ログ設定
        log_frame = ttk.LabelFrame(settings_container, text="ログ設定", padding="15")
        log_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(log_frame, text="ログレベル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                      state="readonly", width=15)
        log_level_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # グローバル除外リスト
        exclude_frame = ttk.LabelFrame(settings_container, text="グローバル除外リスト", padding="15")
        exclude_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(exclude_frame, text="以下のユーザーには絶対にDMを送信しない:").pack(anchor=tk.W)
        self.global_exclude_text = scrolledtext.ScrolledText(exclude_frame, height=5, width=60)
        self.global_exclude_text.pack(pady=10)
        
        # 保存ボタン
        save_btn = ttk.Button(settings_container, text="設定を保存", command=self.save_settings)
        save_btn.pack(pady=20)
    
    def create_monitor_tab(self):
        """モニタータブを作成"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="実行・モニター")
        
        # コントロールパネル
        control_panel = ttk.Frame(monitor_frame)
        control_panel.pack(fill=tk.X, padx=10, pady=10)
        
        # ボタン
        button_frame = ttk.Frame(control_panel)
        button_frame.pack(side=tk.LEFT)
        
        self.start_btn = ttk.Button(button_frame, text="ボットを開始", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="ボットを停止", command=self.stop_bot, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # ステータス
        self.status_var = tk.StringVar(value="停止中")
        status_label = ttk.Label(control_panel, textvariable=self.status_var, 
                               font=('Arial', 12, 'bold'))
        status_label.pack(side=tk.LEFT, padx=20)
        
        # 統計情報
        stats_frame = ttk.LabelFrame(monitor_frame, text="統計情報", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack()
        
        # 統計ラベル
        self.stats_vars = {
            'total_sent': tk.StringVar(value="0"),
            'success_rate': tk.StringVar(value="0%"),
            'active_time': tk.StringVar(value="00:00:00"),
            'tweets_found': tk.StringVar(value="0")
        }
        
        ttk.Label(stats_container, text="送信済みDM:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(stats_container, textvariable=self.stats_vars['total_sent'], font=('Arial', 11, 'bold')).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(stats_container, text="成功率:").grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        ttk.Label(stats_container, textvariable=self.stats_vars['success_rate'], font=('Arial', 11, 'bold')).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        ttk.Label(stats_container, text="実行時間:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(stats_container, textvariable=self.stats_vars['active_time'], font=('Arial', 11, 'bold')).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(stats_container, text="発見ツイート:").grid(row=1, column=2, sticky=tk.W, padx=10, pady=5)
        ttk.Label(stats_container, textvariable=self.stats_vars['tweets_found'], font=('Arial', 11, 'bold')).grid(row=1, column=3, sticky=tk.W, pady=5)
        
        # ログ表示
        log_frame = ttk.LabelFrame(monitor_frame, text="ログ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # ログテキスト
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ログコントロール
        log_control = ttk.Frame(log_frame)
        log_control.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_control, text="ログをクリア", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control, text="ログを保存", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control, text="自動スクロール", variable=self.auto_scroll_var).pack(side=tk.LEFT, padx=20)
    
    def create_help_tab(self):
        """ヘルプタブを作成"""
        help_frame = ttk.Frame(self.notebook)
        self.notebook.add(help_frame, text="ヘルプ")
        
        # スクロール可能なテキスト
        help_text = scrolledtext.ScrolledText(help_frame, wrap=tk.WORD, width=80, height=30)
        help_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ヘルプ内容
        help_content = """
X DM Bot - 使い方ガイド

【初期設定】
1. アカウント設定タブで、Xの認証情報を入力して保存
2. キャンペーン管理タブで、新規キャンペーンを作成
3. 詳細設定タブで、必要に応じて設定を調整

【キャンペーンの作成】
1. キャンペーン管理タブで「新規作成」をクリック
2. キャンペーン名を入力
3. 検索キーワードを入力（1行に1つ）
4. メッセージテンプレートを作成
   - {username}: 受信者のユーザー名
   - {keyword}: 検索キーワード
   - {time_ago}: ツイートからの経過秒数
5. レート設定を調整
6. 「キャンペーンを保存」をクリック

【ボットの実行】
1. 実行・モニタータブに移動
2. 「ボットを開始」をクリック
3. ログでリアルタイムの動作を確認
4. 停止する場合は「ボットを停止」をクリック

【安全な使用のために】
- 1時間あたりのDM数は控えめに設定
- ユーザークールダウンは24時間以上を推奨
- グローバル除外リストに公式アカウントを追加
- Xの利用規約を必ず遵守してください

【トラブルシューティング】
- ログイン失敗: 認証情報を確認、2段階認証の無効化
- DM送信失敗: レート制限を確認、除外リストを確認
- ツイートが見つからない: キーワードを調整、検索間隔を短く

【注意事項】
このツールは教育目的で作成されています。
スパム行為や迷惑行為は絶対に行わないでください。
使用は自己責任でお願いします。
        """
        
        help_text.insert(tk.END, help_content)
        help_text.config(state='disabled')
    
    # ===== ユーティリティメソッド =====
    
    def toggle_password_visibility(self):
        """パスワードの表示/非表示を切り替え"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def toggle_proxy_settings(self):
        """プロキシ設定の有効/無効を切り替え"""
        if self.use_proxy_var.get():
            self.proxy_entry.config(state='normal')
        else:
            self.proxy_entry.config(state='disabled')
    
    def save_credentials(self):
        """認証情報を保存"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("エラー", "ユーザー名とパスワードを入力してください")
            return
        
        # 暗号化して保存
        self.config_manager.save_credentials(username, password)
        
        # プロキシ設定も保存
        self.config['settings']['use_proxy'] = self.use_proxy_var.get()
        self.config['settings']['proxy_url'] = self.proxy_url_var.get()
        self.config_manager.save_config(self.config)
        
        self.account_status_var.set("認証情報を保存しました")
        messagebox.showinfo("成功", "認証情報を安全に保存しました")
    
    def test_connection(self):
        """接続テスト"""
        # TODO: 実際の接続テストを実装
        messagebox.showinfo("接続テスト", "この機能は準備中です")
    
    def refresh_campaigns_list(self):
        """キャンペーンリストを更新"""
        self.campaigns_listbox.delete(0, tk.END)
        for campaign in self.config.get('campaigns', []):
            status = "✓" if campaign.get('active', False) else "✗"
            self.campaigns_listbox.insert(tk.END, f"{status} {campaign['name']}")
    
    def on_campaign_select(self, event):
        """キャンペーン選択時の処理"""
        selection = self.campaigns_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        campaign = self.config['campaigns'][index]
        
        # フォームに値を設定
        self.campaign_name_var.set(campaign.get('name', ''))
        self.campaign_active_var.set(campaign.get('active', True))
        
        # キーワード
        self.keywords_text.delete(1.0, tk.END)
        keywords = campaign.get('keywords', [])
        self.keywords_text.insert(1.0, '\n'.join(keywords))
        
        # テンプレート
        self.templates_text.delete(1.0, tk.END)
        templates = campaign.get('message_templates', [])
        self.templates_text.insert(1.0, '\n\n'.join(templates))
        
        # レート設定
        self.max_dms_var.set(campaign.get('max_dms_per_hour', 15))
        self.check_interval_var.set(campaign.get('check_interval', 30))
        
        # 除外リスト
        self.exclude_text.delete(1.0, tk.END)
        exclude_list = campaign.get('exclude_list', [])
        self.exclude_text.insert(1.0, '\n'.join(exclude_list))
    
    def new_campaign(self):
        """新規キャンペーン作成"""
        # フォームをクリア
        self.campaign_name_var.set("新規キャンペーン")
        self.campaign_active_var.set(True)
        self.keywords_text.delete(1.0, tk.END)
        self.templates_text.delete(1.0, tk.END)
        self.max_dms_var.set(15)
        self.check_interval_var.set(30)
        self.exclude_text.delete(1.0, tk.END)
        
        # 新規キャンペーンをリストに追加
        new_campaign = {
            "name": "新規キャンペーン",
            "keywords": [],
            "message_templates": [],
            "max_dms_per_hour": 15,
            "check_interval": 30,
            "exclude_list": [],
            "active": True
        }
        self.config['campaigns'].append(new_campaign)
        self.refresh_campaigns_list()
        
        # 最後の項目を選択
        self.campaigns_listbox.selection_clear(0, tk.END)
        self.campaigns_listbox.selection_set(tk.END)
        self.campaigns_listbox.see(tk.END)
    
    def save_campaign(self):
        """キャンペーンを保存"""
        selection = self.campaigns_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "キャンペーンを選択してください")
            return
        
        index = selection[0]
        
        # フォームから値を取得
        campaign = {
            "name": self.campaign_name_var.get().strip(),
            "active": self.campaign_active_var.get(),
            "keywords": [k.strip() for k in self.keywords_text.get(1.0, tk.END).strip().split('\n') if k.strip()],
            "message_templates": [t.strip() for t in self.templates_text.get(1.0, tk.END).strip().split('\n\n') if t.strip()],
            "max_dms_per_hour": self.max_dms_var.get(),
            "check_interval": self.check_interval_var.get(),
            "exclude_list": [e.strip() for e in self.exclude_text.get(1.0, tk.END).strip().split('\n') if e.strip()],
            "recipient_list": None
        }
        
        # 検証
        if not campaign['name']:
            messagebox.showerror("エラー", "キャンペーン名を入力してください")
            return
        
        if not campaign['keywords']:
            messagebox.showerror("エラー", "少なくとも1つのキーワードを入力してください")
            return
        
        if not campaign['message_templates']:
            messagebox.showerror("エラー", "少なくとも1つのメッセージテンプレートを入力してください")
            return
        
        # 保存
        self.config['campaigns'][index] = campaign
        self.config_manager.save_config(self.config)
        self.refresh_campaigns_list()
        
        messagebox.showinfo("成功", "キャンペーンを保存しました")
    
    def delete_campaign(self):
        """キャンペーンを削除"""
        selection = self.campaigns_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除するキャンペーンを選択してください")
            return
        
        if messagebox.askyesno("確認", "選択したキャンペーンを削除しますか？"):
            index = selection[0]
            del self.config['campaigns'][index]
            self.config_manager.save_config(self.config)
            self.refresh_campaigns_list()
    
    def duplicate_campaign(self):
        """キャンペーンを複製"""
        selection = self.campaigns_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "複製するキャンペーンを選択してください")
            return
        
        index = selection[0]
        original = self.config['campaigns'][index].copy()
        original['name'] = f"{original['name']} (コピー)"
        
        self.config['campaigns'].append(original)
        self.config_manager.save_config(self.config)
        self.refresh_campaigns_list()
    
    def save_settings(self):
        """詳細設定を保存"""
        # レート制限
        self.config['rate_limits']['max_dms_per_hour'] = self.global_max_dms_var.get()
        self.config['rate_limits']['user_cooldown_hours'] = self.cooldown_hours_var.get()
        self.config['rate_limits']['min_delay_between_dms'] = self.min_delay_var.get()
        self.config['rate_limits']['max_delay_between_dms'] = self.max_delay_var.get()
        
        # ブラウザ設定
        self.config['settings']['headless_mode'] = self.headless_var.get()
        self.config['settings']['save_screenshots_on_error'] = self.screenshot_var.get()
        self.config['settings']['timeout_seconds'] = self.timeout_var.get()
        self.config['settings']['log_level'] = self.log_level_var.get()
        
        # グローバル除外リスト
        exclude_list = [e.strip() for e in self.global_exclude_text.get(1.0, tk.END).strip().split('\n') if e.strip()]
        self.config['exclude_list'] = exclude_list
        
        self.config_manager.save_config(self.config)
        messagebox.showinfo("成功", "設定を保存しました")
    
    def start_bot(self):
        """ボットを開始"""
        # 認証情報をチェック
        username, password = self.config_manager.load_credentials()
        if not username or not password:
            messagebox.showerror("エラー", "認証情報を設定してください")
            self.notebook.select(0)  # アカウントタブに移動
            return
        
        # アクティブなキャンペーンをチェック
        active_campaigns = [c for c in self.config.get('campaigns', []) if c.get('active', False)]
        if not active_campaigns:
            messagebox.showerror("エラー", "アクティブなキャンペーンがありません")
            self.notebook.select(1)  # キャンペーンタブに移動
            return
        
        # ボットを開始
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set("実行中")
        
        # ボットスレッドを開始
        self.bot_thread = threading.Thread(target=self.run_bot_thread, daemon=True)
        self.bot_thread.start()
        
        self.log_message("INFO", "ボットを開始しました")
    
    def stop_bot(self):
        """ボットを停止"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("停止中")
        
        self.log_message("INFO", "ボットを停止しました")
        
        # ボットインスタンスをクリーンアップ
        if self.bot_instance:
            try:
                self.bot_instance.cleanup()
            except:
                pass
    
    def run_bot_thread(self):
        """ボットを別スレッドで実行"""
        try:
            # 環境変数を設定
            username, password = self.config_manager.load_credentials()
            os.environ['X_USERNAME'] = username
            os.environ['X_PASSWORD'] = password
            
            if self.config['settings'].get('use_proxy') and self.config['settings'].get('proxy_url'):
                os.environ['PROXY_URL'] = self.config['settings']['proxy_url']
            
            # ボットインスタンスを作成
            if XDMBot:
                self.bot_instance = XDMBot()
                self.bot_instance.config = self.config
                
                # ログをGUIにリダイレクト
                # TODO: カスタムログハンドラーを実装
                
                # ボットを実行
                self.bot_instance.run()
            else:
                self.log_message("ERROR", "ボットモジュールが見つかりません")
                
        except Exception as e:
            self.log_message("ERROR", f"ボットエラー: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, self.stop_bot)
    
    def log_message(self, level, message):
        """ログメッセージをキューに追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] [{level}] {message}")
    
    def update_log_display(self):
        """ログ表示を更新"""
        # キューからメッセージを取得
        while not self.log_queue.empty():
            try:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                
                # 自動スクロール
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
            except:
                break
        
        # 定期的に更新
        self.root.after(100, self.update_log_display)
    
    def clear_logs(self):
        """ログをクリア"""
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """ログを保存"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("ログファイル", "*.log"), ("テキストファイル", "*.txt")]
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("成功", "ログを保存しました")
    
    def export_config(self):
        """設定をエクスポート"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json")]
        )
        
        if filename:
            # 認証情報を除外してエクスポート
            export_config = self.config.copy()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "設定をエクスポートしました")
    
    def import_config(self):
        """設定をインポート"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSONファイル", "*.json")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # 既存の設定とマージ
                self.config.update(imported_config)
                self.config_manager.save_config(self.config)
                
                # UIを更新
                self.load_saved_data()
                self.refresh_campaigns_list()
                
                messagebox.showinfo("成功", "設定をインポートしました")
            except Exception as e:
                messagebox.showerror("エラー", f"インポートに失敗しました: {str(e)}")
    
    def install_dependencies(self):
        """依存関係をインストール"""
        if messagebox.askyesno("確認", "必要なパッケージをインストールしますか？"):
            # 新しいウィンドウでインストール進行状況を表示
            install_window = tk.Toplevel(self.root)
            install_window.title("パッケージインストール")
            install_window.geometry("600x400")
            
            text = scrolledtext.ScrolledText(install_window)
            text.pack(fill=tk.BOTH, expand=True)
            
            def run_install():
                packages = [
                    'selenium',
                    'undetected-chromedriver',
                    'python-dotenv',
                    'cryptography',
                    'requests'
                ]
                
                for package in packages:
                    text.insert(tk.END, f"Installing {package}...\n")
                    text.see(tk.END)
                    install_window.update()
                    
                    result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                         capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        text.insert(tk.END, f"✓ {package} installed successfully\n")
                    else:
                        text.insert(tk.END, f"✗ Failed to install {package}\n")
                        text.insert(tk.END, result.stderr + "\n")
                    
                    text.see(tk.END)
                    install_window.update()
                
                text.insert(tk.END, "\nインストール完了！\n")
                messagebox.showinfo("完了", "パッケージのインストールが完了しました")
            
            threading.Thread(target=run_install, daemon=True).start()
    
    def show_help(self):
        """ヘルプを表示"""
        self.notebook.select(4)  # ヘルプタブに移動
    
    def show_about(self):
        """バージョン情報を表示"""
        about_text = """X DM Bot GUI
バージョン 1.0.0

キーワード検索に基づいて自動的にDMを送信するボット

作成者: Your Name
ライセンス: MIT

注意: このツールは教育目的で作成されています。
使用は自己責任でお願いします。"""
        
        messagebox.showinfo("バージョン情報", about_text)
    
    def load_saved_data(self):
        """保存されたデータを読み込み"""
        # 認証情報
        username, password = self.config_manager.load_credentials()
        if username:
            self.username_var.set(username)
            self.password_var.set(password)
            self.account_status_var.set("認証情報が設定されています")
        
        # プロキシ設定
        self.use_proxy_var.set(self.config['settings'].get('use_proxy', False))
        self.proxy_url_var.set(self.config['settings'].get('proxy_url', ''))
        self.toggle_proxy_settings()
        
        # 詳細設定
        self.global_max_dms_var.set(self.config['rate_limits'].get('max_dms_per_hour', 20))
        self.cooldown_hours_var.set(self.config['rate_limits'].get('user_cooldown_hours', 24))
        self.min_delay_var.set(self.config['rate_limits'].get('min_delay_between_dms', 10))
        self.max_delay_var.set(self.config['rate_limits'].get('max_delay_between_dms', 30))
        
        self.headless_var.set(self.config['settings'].get('headless_mode', False))
        self.screenshot_var.set(self.config['settings'].get('save_screenshots_on_error', True))
        self.timeout_var.set(self.config['settings'].get('timeout_seconds', 30))
        self.log_level_var.set(self.config['settings'].get('log_level', 'INFO'))
        
        # グローバル除外リスト
        exclude_list = self.config.get('exclude_list', [])
        self.global_exclude_text.delete(1.0, tk.END)
        self.global_exclude_text.insert(1.0, '\n'.join(exclude_list))


def main():
    """メイン関数"""
    root = tk.Tk()
    app = XDMBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()