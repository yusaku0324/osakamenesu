# web_gui.py - X DM Bot Web GUI
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import json
import os
import threading
import queue
import logging
from datetime import datetime
from pathlib import Path
import secrets
from cryptography.fernet import Fernet
import base64

# メインボットのインポート
try:
    from main import XDMBot, Campaign
except ImportError:
    XDMBot = None
    Campaign = None

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# グローバル変数
config_manager = ConfigManager()
bot_instance = None
bot_thread = None
is_running = False
log_queue = queue.Queue()
stats = {
    'total_sent': 0,
    'success_rate': 0,
    'active_time': '00:00:00',
    'tweets_found': 0
}


# ルートページ
@app.route('/')
def index():
    return render_template('index.html')


# 設定API
@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'GET':
        config_data = config_manager.load_config()
        username, _ = config_manager.load_credentials()
        config_data['has_credentials'] = username is not None
        return jsonify(config_data)
    else:
        config_data = request.json
        config_manager.save_config(config_data)
        return jsonify({'status': 'success'})


# 認証情報API
@app.route('/api/credentials', methods=['POST'])
def save_credentials():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username and password:
        config_manager.save_credentials(username, password)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 400


# キャンペーンAPI
@app.route('/api/campaigns', methods=['GET', 'POST'])
def campaigns():
    config_data = config_manager.load_config()
    
    if request.method == 'GET':
        return jsonify(config_data.get('campaigns', []))
    else:
        config_data['campaigns'] = request.json
        config_manager.save_config(config_data)
        return jsonify({'status': 'success'})


@app.route('/api/campaigns/<int:index>', methods=['PUT', 'DELETE'])
def campaign_detail(index):
    config_data = config_manager.load_config()
    campaigns = config_data.get('campaigns', [])
    
    if index >= len(campaigns):
        return jsonify({'status': 'error', 'message': 'Campaign not found'}), 404
    
    if request.method == 'PUT':
        campaigns[index] = request.json
        config_data['campaigns'] = campaigns
        config_manager.save_config(config_data)
        return jsonify({'status': 'success'})
    else:  # DELETE
        campaigns.pop(index)
        config_data['campaigns'] = campaigns
        config_manager.save_config(config_data)
        return jsonify({'status': 'success'})


# ボット制御API
@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    global bot_instance, bot_thread, is_running
    
    if is_running:
        return jsonify({'status': 'error', 'message': 'Bot is already running'}), 400
    
    # 認証情報をチェック
    username, password = config_manager.load_credentials()
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'No credentials configured'}), 400
    
    # アクティブなキャンペーンをチェック
    config_data = config_manager.load_config()
    active_campaigns = [c for c in config_data.get('campaigns', []) if c.get('active', False)]
    if not active_campaigns:
        return jsonify({'status': 'error', 'message': 'No active campaigns'}), 400
    
    # ボットを開始
    is_running = True
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    return jsonify({'status': 'success', 'message': 'Bot started'})


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    global bot_instance, is_running
    
    if not is_running:
        return jsonify({'status': 'error', 'message': 'Bot is not running'}), 400
    
    is_running = False
    
    if bot_instance:
        try:
            bot_instance.cleanup()
        except:
            pass
    
    return jsonify({'status': 'success', 'message': 'Bot stopped'})


@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    global is_running, stats
    
    # ログメッセージを取得
    logs = []
    while not log_queue.empty():
        try:
            logs.append(log_queue.get_nowait())
        except:
            break
    
    return jsonify({
        'is_running': is_running,
        'stats': stats,
        'logs': logs
    })


def run_bot_thread():
    """ボットを別スレッドで実行"""
    global bot_instance, is_running
    
    try:
        # 環境変数を設定
        username, password = config_manager.load_credentials()
        os.environ['X_USERNAME'] = username
        os.environ['X_PASSWORD'] = password
        
        config_data = config_manager.load_config()
        if config_data['settings'].get('use_proxy') and config_data['settings'].get('proxy_url'):
            os.environ['PROXY_URL'] = config_data['settings']['proxy_url']
        
        # ボットインスタンスを作成
        if XDMBot:
            bot_instance = XDMBot()
            bot_instance.config = config_data
            
            # ボットを実行
            bot_instance.run()
        else:
            log_message("ERROR", "Bot module not found")
            
    except Exception as e:
        log_message("ERROR", f"Bot error: {str(e)}")
    finally:
        is_running = False


def log_message(level, message):
    """ログメッセージをキューに追加"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_queue.put(f"[{timestamp}] [{level}] {message}")


# HTMLテンプレートを作成
def create_templates():
    """HTMLテンプレートファイルを作成"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # index.html
    index_html = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X DM Bot - Web GUI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .nav-pills .nav-link.active { background-color: #1DA1F2; }
        .navbar { background-color: #1DA1F2 !important; }
        .navbar-brand { color: white !important; font-weight: bold; }
        .log-container { 
            height: 400px; 
            overflow-y: auto; 
            background: #1a1a1a; 
            color: #00ff00; 
            font-family: monospace;
            padding: 10px;
            border-radius: 5px;
        }
        .stats-card {
            border-left: 4px solid #1DA1F2;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-robot"></i> X DM Bot
            </a>
            <span class="navbar-text text-white">
                <span id="bot-status" class="badge bg-danger">停止中</span>
            </span>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2">
                <div class="nav flex-column nav-pills" id="v-pills-tab">
                    <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#account">
                        <i class="bi bi-person"></i> アカウント
                    </button>
                    <button class="nav-link" data-bs-toggle="pill" data-bs-target="#campaigns">
                        <i class="bi bi-megaphone"></i> キャンペーン
                    </button>
                    <button class="nav-link" data-bs-toggle="pill" data-bs-target="#settings">
                        <i class="bi bi-gear"></i> 設定
                    </button>
                    <button class="nav-link" data-bs-toggle="pill" data-bs-target="#monitor">
                        <i class="bi bi-speedometer2"></i> モニター
                    </button>
                </div>
            </div>
            
            <div class="col-md-10">
                <div class="tab-content" id="v-pills-tabContent">
                    <!-- アカウントタブ -->
                    <div class="tab-pane fade show active" id="account">
                        <div class="card">
                            <div class="card-header">
                                <h5>アカウント設定</h5>
                            </div>
                            <div class="card-body">
                                <form id="credentials-form">
                                    <div class="mb-3">
                                        <label class="form-label">ユーザー名/メールアドレス</label>
                                        <input type="text" class="form-control" id="username" required>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">パスワード</label>
                                        <div class="input-group">
                                            <input type="password" class="form-control" id="password" required>
                                            <button class="btn btn-outline-secondary" type="button" onclick="togglePassword()">
                                                <i class="bi bi-eye"></i>
                                            </button>
                                        </div>
                                    </div>
                                    <button type="submit" class="btn btn-primary">保存</button>
                                </form>
                            </div>
                        </div>
                    </div>

                    <!-- キャンペーンタブ -->
                    <div class="tab-pane fade" id="campaigns">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5>キャンペーン管理</h5>
                                <button class="btn btn-success btn-sm" onclick="newCampaign()">
                                    <i class="bi bi-plus"></i> 新規作成
                                </button>
                            </div>
                            <div class="card-body">
                                <div id="campaigns-list"></div>
                            </div>
                        </div>
                    </div>

                    <!-- 設定タブ -->
                    <div class="tab-pane fade" id="settings">
                        <div class="card">
                            <div class="card-header">
                                <h5>詳細設定</h5>
                            </div>
                            <div class="card-body">
                                <form id="settings-form">
                                    <h6>レート制限</h6>
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <label class="form-label">1時間あたりの最大DM数</label>
                                            <input type="number" class="form-control" id="max_dms_per_hour" value="20">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label">ユーザークールダウン（時間）</label>
                                            <input type="number" class="form-control" id="user_cooldown_hours" value="24">
                                        </div>
                                    </div>
                                    <hr>
                                    <h6>ブラウザ設定</h6>
                                    <div class="form-check mb-3">
                                        <input class="form-check-input" type="checkbox" id="headless_mode">
                                        <label class="form-check-label">ヘッドレスモード</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">設定を保存</button>
                                </form>
                            </div>
                        </div>
                    </div>

                    <!-- モニタータブ -->
                    <div class="tab-pane fade" id="monitor">
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <button class="btn btn-success" onclick="startBot()" id="start-btn">
                                            <i class="bi bi-play"></i> 開始
                                        </button>
                                        <button class="btn btn-danger" onclick="stopBot()" id="stop-btn" disabled>
                                            <i class="bi bi-stop"></i> 停止
                                        </button>
                                    </div>
                                    <div class="text-end">
                                        <button class="btn btn-sm btn-outline-secondary" onclick="clearLogs()">
                                            ログをクリア
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="card stats-card">
                                    <div class="card-body">
                                        <h6 class="text-muted">送信済みDM</h6>
                                        <h3 id="stat-sent">0</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card stats-card">
                                    <div class="card-body">
                                        <h6 class="text-muted">成功率</h6>
                                        <h3 id="stat-success">0%</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card stats-card">
                                    <div class="card-body">
                                        <h6 class="text-muted">実行時間</h6>
                                        <h3 id="stat-time">00:00:00</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card stats-card">
                                    <div class="card-body">
                                        <h6 class="text-muted">発見ツイート</h6>
                                        <h3 id="stat-tweets">0</h3>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card">
                            <div class="card-header">
                                <h6>ログ</h6>
                            </div>
                            <div class="card-body">
                                <div class="log-container" id="log-container"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- キャンペーン編集モーダル -->
    <div class="modal fade" id="campaignModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">キャンペーン編集</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="campaign-form">
                        <input type="hidden" id="campaign-index">
                        <div class="mb-3">
                            <label class="form-label">キャンペーン名</label>
                            <input type="text" class="form-control" id="campaign-name" required>
                        </div>
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="campaign-active">
                                <label class="form-check-label">有効</label>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">検索キーワード（1行に1つ）</label>
                            <textarea class="form-control" id="campaign-keywords" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">メッセージテンプレート（空行で区切る）</label>
                            <textarea class="form-control" id="campaign-templates" rows="6" required></textarea>
                            <small class="text-muted">
                                使用可能な変数: {username}, {keyword}, {time_ago}
                            </small>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">キャンセル</button>
                    <button type="button" class="btn btn-primary" onclick="saveCampaign()">保存</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let config = {};
        let statusInterval;

        // 初期化
        document.addEventListener('DOMContentLoaded', function() {
            loadConfig();
            statusInterval = setInterval(updateStatus, 1000);
        });

        // 設定を読み込み
        async function loadConfig() {
            const response = await fetch('/api/config');
            config = await response.json();
            
            // 認証情報の有無を表示
            if (config.has_credentials) {
                document.getElementById('username').placeholder = '保存済み';
                document.getElementById('password').placeholder = '保存済み';
            }
            
            // 設定を表示
            document.getElementById('max_dms_per_hour').value = config.rate_limits.max_dms_per_hour;
            document.getElementById('user_cooldown_hours').value = config.rate_limits.user_cooldown_hours;
            document.getElementById('headless_mode').checked = config.settings.headless_mode;
            
            // キャンペーンを表示
            displayCampaigns();
        }

        // キャンペーン一覧を表示
        function displayCampaigns() {
            const container = document.getElementById('campaigns-list');
            container.innerHTML = '';
            
            config.campaigns.forEach((campaign, index) => {
                const card = document.createElement('div');
                card.className = 'card mb-2';
                card.innerHTML = `
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div>
                            <h6>${campaign.active ? '✓' : '✗'} ${campaign.name}</h6>
                            <small class="text-muted">キーワード: ${campaign.keywords.join(', ')}</small>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-primary" onclick="editCampaign(${index})">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteCampaign(${index})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        // 認証情報を保存
        document.getElementById('credentials-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const response = await fetch('/api/credentials', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                alert('認証情報を保存しました');
                loadConfig();
            }
        });

        // 設定を保存
        document.getElementById('settings-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            config.rate_limits.max_dms_per_hour = parseInt(document.getElementById('max_dms_per_hour').value);
            config.rate_limits.user_cooldown_hours = parseInt(document.getElementById('user_cooldown_hours').value);
            config.settings.headless_mode = document.getElementById('headless_mode').checked;
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                alert('設定を保存しました');
            }
        });

        // キャンペーン編集
        function editCampaign(index) {
            const campaign = config.campaigns[index];
            document.getElementById('campaign-index').value = index;
            document.getElementById('campaign-name').value = campaign.name;
            document.getElementById('campaign-active').checked = campaign.active;
            document.getElementById('campaign-keywords').value = campaign.keywords.join('\\n');
            document.getElementById('campaign-templates').value = campaign.message_templates.join('\\n\\n');
            
            const modal = new bootstrap.Modal(document.getElementById('campaignModal'));
            modal.show();
        }

        // 新規キャンペーン
        function newCampaign() {
            document.getElementById('campaign-index').value = -1;
            document.getElementById('campaign-form').reset();
            document.getElementById('campaign-active').checked = true;
            
            const modal = new bootstrap.Modal(document.getElementById('campaignModal'));
            modal.show();
        }

        // キャンペーンを保存
        async function saveCampaign() {
            const index = parseInt(document.getElementById('campaign-index').value);
            const campaign = {
                name: document.getElementById('campaign-name').value,
                active: document.getElementById('campaign-active').checked,
                keywords: document.getElementById('campaign-keywords').value.split('\\n').filter(k => k.trim()),
                message_templates: document.getElementById('campaign-templates').value.split('\\n\\n').filter(t => t.trim()),
                max_dms_per_hour: 15,
                check_interval: 30,
                exclude_list: [],
                recipient_list: null
            };
            
            if (index === -1) {
                config.campaigns.push(campaign);
            } else {
                config.campaigns[index] = campaign;
            }
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('campaignModal')).hide();
                displayCampaigns();
            }
        }

        // キャンペーンを削除
        async function deleteCampaign(index) {
            if (!confirm('このキャンペーンを削除しますか？')) return;
            
            config.campaigns.splice(index, 1);
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                displayCampaigns();
            }
        }

        // ボット制御
        async function startBot() {
            const response = await fetch('/api/bot/start', { method: 'POST' });
            const data = await response.json();
            
            if (!response.ok) {
                alert(data.message);
            }
        }

        async function stopBot() {
            const response = await fetch('/api/bot/stop', { method: 'POST' });
            const data = await response.json();
            
            if (!response.ok) {
                alert(data.message);
            }
        }

        // ステータス更新
        async function updateStatus() {
            const response = await fetch('/api/bot/status');
            const data = await response.json();
            
            // ボタン状態を更新
            document.getElementById('start-btn').disabled = data.is_running;
            document.getElementById('stop-btn').disabled = !data.is_running;
            
            // ステータスバッジを更新
            const statusBadge = document.getElementById('bot-status');
            if (data.is_running) {
                statusBadge.textContent = '実行中';
                statusBadge.className = 'badge bg-success';
            } else {
                statusBadge.textContent = '停止中';
                statusBadge.className = 'badge bg-danger';
            }
            
            // 統計を更新
            document.getElementById('stat-sent').textContent = data.stats.total_sent;
            document.getElementById('stat-success').textContent = data.stats.success_rate + '%';
            document.getElementById('stat-time').textContent = data.stats.active_time;
            document.getElementById('stat-tweets').textContent = data.stats.tweets_found;
            
            // ログを追加
            if (data.logs.length > 0) {
                const logContainer = document.getElementById('log-container');
                data.logs.forEach(log => {
                    const line = document.createElement('div');
                    line.textContent = log;
                    logContainer.appendChild(line);
                });
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        }

        // ユーティリティ関数
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
        }

        function clearLogs() {
            document.getElementById('log-container').innerHTML = '';
        }
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='X DM Bot Web GUI')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the web server on (default: 5001)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the web server on (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    create_templates()
    print("X DM Bot Web GUI を起動しています...")
    print(f"ブラウザで http://localhost:{args.port} を開いてください")
    # コマンドライン引数から設定を使用
    app.run(host=args.host, port=args.port, debug=args.debug)