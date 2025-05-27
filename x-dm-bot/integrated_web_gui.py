# integrated_web_gui.py - DM & 投稿機能統合Web GUI
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import threading
import queue
import logging
from datetime import datetime
from pathlib import Path
import secrets
from multi_account_manager import MultiAccountManager, Account
from twitter_poster import XPoster, Post, PostCampaign, XAccountManager
from models import Campaign

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# マネージャーインスタンス
manager = MultiAccountManager()
account_managers = {}  # account_id -> XAccountManager


# ルートページ
@app.route('/')
def index():
    return render_template('integrated.html')


# アカウント一覧API（モード情報を含む）
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts_data = []
    for account in manager.accounts.values():
        account_data = {
            'id': account.id,
            'name': account.name,
            'username': account.username,
            'active': account.active,
            'has_credentials': bool(account.username and account.password),
            'proxy': account.proxy,
            'campaigns_count': len(account.campaigns),
            'status': manager.stats.get(account.id, {}).get('status', 'stopped'),
            'mode': account_managers.get(account.id, {}).get('mode', 'dm') if account.id in account_managers else 'dm'
        }
        accounts_data.append(account_data)
    return jsonify(accounts_data)


# モード切り替えAPI
@app.route('/api/accounts/<account_id>/mode', methods=['PUT'])
def set_account_mode(account_id):
    data = request.json
    mode = data.get('mode', 'dm')
    
    if account_id not in manager.accounts:
        return jsonify({'status': 'error', 'message': 'Account not found'}), 404
    
    # アカウントマネージャーを作成または更新
    account = manager.accounts[account_id]
    if account_id not in account_managers:
        # プロキシが空文字列の場合はNoneに変換
        proxy = account.proxy if account.proxy else None
        account_managers[account_id] = {
            'manager': XAccountManager(account_id, account.username, account.password, proxy),
            'mode': mode
        }
    else:
        account_managers[account_id]['mode'] = mode
        account_managers[account_id]['manager'].set_mode(mode)
    
    return jsonify({'status': 'success', 'mode': mode})


# 投稿キャンペーンAPI
@app.route('/api/accounts/<account_id>/post-campaigns', methods=['GET', 'POST'])
def post_campaigns(account_id):
    if account_id not in manager.accounts:
        return jsonify({'status': 'error', 'message': 'Account not found'}), 404
    
    # 投稿キャンペーンをファイルから読み込み/保存
    campaigns_file = f'post_campaigns_{account_id}.json'
    
    if request.method == 'GET':
        if os.path.exists(campaigns_file):
            with open(campaigns_file, 'r', encoding='utf-8') as f:
                campaigns = json.load(f)
        else:
            campaigns = []
        return jsonify(campaigns)
    
    else:  # POST
        campaigns = request.json
        with open(campaigns_file, 'w', encoding='utf-8') as f:
            json.dump(campaigns, f, indent=2, ensure_ascii=False)
        return jsonify({'status': 'success'})


# 投稿作成API
@app.route('/api/accounts/<account_id>/posts', methods=['POST'])
def create_post(account_id):
    if account_id not in manager.accounts:
        return jsonify({'status': 'error', 'message': 'Account not found'}), 404
    
    data = request.json
    post = Post(
        content=data.get('content', ''),
        media_paths=data.get('media_paths', []),
        scheduled_time=datetime.fromisoformat(data['scheduled_time']) if data.get('scheduled_time') else None
    )
    
    # 即座に投稿するか、キャンペーンに追加するか
    if data.get('immediate', False):
        # 即座に投稿
        account = manager.accounts[account_id]
        proxy = account.proxy if account.proxy else None
        poster = XPoster(account.username, account.password, proxy)
        
        try:
            poster._setup_driver()
            if poster.login():
                success = poster.create_post(post)
                poster.cleanup()
                
                if success:
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'status': 'error', 'message': 'Failed to create post'}), 500
            else:
                return jsonify({'status': 'error', 'message': 'Login failed'}), 401
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    else:
        # キャンペーンに追加
        campaign_name = data.get('campaign_name', 'Default Campaign')
        campaigns_file = f'post_campaigns_{account_id}.json'
        
        if os.path.exists(campaigns_file):
            with open(campaigns_file, 'r', encoding='utf-8') as f:
                campaigns = json.load(f)
        else:
            campaigns = []
        
        # キャンペーンを探すか作成
        campaign = None
        for c in campaigns:
            if c['name'] == campaign_name:
                campaign = c
                break
        
        if not campaign:
            campaign = {
                'name': campaign_name,
                'posts': [],
                'interval_minutes': 60,
                'randomize_interval': True,
                'active': True
            }
            campaigns.append(campaign)
        
        # 投稿を追加
        campaign['posts'].append({
            'content': post.content,
            'media_paths': post.media_paths,
            'scheduled_time': post.scheduled_time.isoformat() if post.scheduled_time else None
        })
        
        # 保存
        with open(campaigns_file, 'w', encoding='utf-8') as f:
            json.dump(campaigns, f, indent=2, ensure_ascii=False)
        
        return jsonify({'status': 'success'})


# ボット開始API（モードに応じて）
@app.route('/api/bot/<account_id>/start', methods=['POST'])
def start_bot(account_id):
    try:
        if account_id not in manager.accounts:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404
        
        account = manager.accounts[account_id]
        mode = account_managers.get(account_id, {}).get('mode', 'dm')
        
        if mode == 'dm':
            # DMモードで開始
            manager.start_bot(account_id)
        else:
            # 投稿モードで開始
            campaigns_file = f'post_campaigns_{account_id}.json'
            if os.path.exists(campaigns_file):
                with open(campaigns_file, 'r', encoding='utf-8') as f:
                    campaigns_data = json.load(f)
                
                # アクティブなキャンペーンを探す
                active_campaign = None
                for c in campaigns_data:
                    if c.get('active', False):
                        active_campaign = c
                        break
                
                if active_campaign:
                    # 投稿キャンペーンを実行
                    posts = [Post(
                        content=p['content'],
                        media_paths=p.get('media_paths', []),
                        scheduled_time=datetime.fromisoformat(p['scheduled_time']) if p.get('scheduled_time') else None
                    ) for p in active_campaign['posts']]
                    
                    campaign = PostCampaign(
                        name=active_campaign['name'],
                        posts=posts,
                        interval_minutes=active_campaign.get('interval_minutes', 60),
                        randomize_interval=active_campaign.get('randomize_interval', True),
                        active=True
                    )
                    
                    # 別スレッドで実行
                    thread = threading.Thread(
                        target=run_post_campaign,
                        args=(account_id, account, campaign),
                        daemon=True
                    )
                    thread.start()
                    
                    manager.stats[account_id]['status'] = 'running'
                    
                else:
                    return jsonify({'status': 'error', 'message': 'No active post campaign'}), 400
            else:
                return jsonify({'status': 'error', 'message': 'No post campaigns found'}), 400
        
        return jsonify({'status': 'success', 'mode': mode})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


def run_post_campaign(account_id: str, account: Account, campaign: PostCampaign):
    """投稿キャンペーンを実行"""
    try:
        proxy = account.proxy if account.proxy else None
        poster = XPoster(account.username, account.password, proxy)
        poster._setup_driver()
        
        if poster.login():
            poster.run_campaign(campaign)
        else:
            logger.error(f"Failed to login for account {account_id}")
        
        poster.cleanup()
        
    except Exception as e:
        logger.error(f"Post campaign error for {account_id}: {e}")
    finally:
        manager.stats[account_id]['status'] = 'stopped'


# メディアアップロードAPI
@app.route('/api/upload', methods=['POST'])
def upload_media():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    # メディアディレクトリを作成
    media_dir = Path('media')
    media_dir.mkdir(exist_ok=True)
    
    # ファイルを保存
    filename = f"{datetime.now().timestamp()}_{file.filename}"
    filepath = media_dir / filename
    file.save(filepath)
    
    return jsonify({
        'status': 'success',
        'path': str(filepath),
        'filename': filename
    })


# HTMLテンプレートを作成
def create_templates():
    """統合版HTMLテンプレートを作成"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    integrated_html = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Bot - 統合管理システム</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .navbar { background-color: #1DA1F2 !important; }
        .navbar-brand { color: white !important; font-weight: bold; }
        .mode-switch { 
            background: #e9ecef;
            border-radius: 20px;
            padding: 4px;
        }
        .mode-switch button {
            border-radius: 16px;
            border: none;
            padding: 4px 16px;
            transition: all 0.3s;
        }
        .mode-switch button.active {
            background: #1DA1F2;
            color: white;
        }
        .account-card { 
            border-left: 4px solid #1DA1F2;
            transition: transform 0.2s;
            cursor: pointer;
        }
        .account-card:hover { transform: translateY(-2px); }
        .post-composer {
            border: 2px dashed #1DA1F2;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .media-preview {
            display: inline-block;
            margin: 5px;
            position: relative;
        }
        .media-preview img {
            max-width: 100px;
            max-height: 100px;
            border-radius: 8px;
        }
        .media-preview .remove-btn {
            position: absolute;
            top: -5px;
            right: -5px;
            background: red;
            color: white;
            border: none;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 12px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-robot"></i> X Bot - 統合管理システム
            </a>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <!-- アカウント一覧 -->
            <div class="col-md-3">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">アカウント</h5>
                        <button class="btn btn-primary btn-sm" onclick="showAddAccountModal()">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="accounts-list"></div>
                    </div>
                </div>
            </div>

            <!-- メインコンテンツ -->
            <div class="col-md-9">
                <div id="account-detail" style="display: none;">
                    <!-- モード切り替え -->
                    <div class="text-center mb-3">
                        <div class="mode-switch d-inline-flex">
                            <button id="dm-mode-btn" class="active" onclick="switchMode('dm')">
                                <i class="bi bi-envelope"></i> DM モード
                            </button>
                            <button id="post-mode-btn" onclick="switchMode('post')">
                                <i class="bi bi-megaphone"></i> 投稿モード
                            </button>
                        </div>
                    </div>

                    <!-- DMモード -->
                    <div id="dm-mode-content">
                        <div class="card mb-3">
                            <div class="card-header">
                                <h5>DMキャンペーン</h5>
                            </div>
                            <div class="card-body">
                                <button class="btn btn-success mb-3" onclick="showAddCampaignModal()">
                                    <i class="bi bi-plus"></i> 新規キャンペーン
                                </button>
                                <div id="dm-campaigns-list"></div>
                            </div>
                        </div>
                    </div>

                    <!-- 投稿モード -->
                    <div id="post-mode-content" style="display: none;">
                        <!-- 投稿作成 -->
                        <div class="post-composer">
                            <h5>新規投稿</h5>
                            <textarea id="post-content" class="form-control mb-3" rows="4" 
                                     placeholder="いまどうしてる？"></textarea>
                            
                            <div class="mb-3">
                                <label class="btn btn-outline-primary btn-sm">
                                    <i class="bi bi-image"></i> メディアを追加
                                    <input type="file" id="media-input" multiple accept="image/*,video/*" 
                                           style="display: none;" onchange="handleMediaSelect(event)">
                                </label>
                                <div id="media-preview" class="mt-2"></div>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <div>
                                    <select id="post-campaign-select" class="form-select form-select-sm" style="width: 200px;">
                                        <option value="">即座に投稿</option>
                                        <option value="campaign">キャンペーンに追加</option>
                                    </select>
                                </div>
                                <button class="btn btn-primary" onclick="createPost()">
                                    <i class="bi bi-send"></i> 投稿
                                </button>
                            </div>
                        </div>

                        <!-- 投稿キャンペーン -->
                        <div class="card">
                            <div class="card-header">
                                <h5>投稿キャンペーン</h5>
                            </div>
                            <div class="card-body">
                                <div id="post-campaigns-list"></div>
                            </div>
                        </div>
                    </div>

                    <!-- コントロールパネル -->
                    <div class="card mt-3">
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
                                <div>
                                    <span id="status-badge" class="badge bg-secondary">停止中</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- アカウント追加モーダル -->
    <div class="modal fade" id="addAccountModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">新規アカウント追加</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="add-account-form">
                        <div class="mb-3">
                            <label class="form-label">アカウント名</label>
                            <input type="text" class="form-control" id="new-account-name" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">ユーザー名</label>
                            <input type="text" class="form-control" id="new-account-username">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">パスワード</label>
                            <input type="password" class="form-control" id="new-account-password">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">プロキシ（オプション）</label>
                            <input type="text" class="form-control" id="new-account-proxy">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">キャンセル</button>
                    <button type="button" class="btn btn-primary" onclick="addAccount()">追加</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentAccountId = null;
        let currentMode = 'dm';
        let selectedMedia = [];

        // 初期化
        document.addEventListener('DOMContentLoaded', function() {
            loadAccounts();
            setInterval(updateStatus, 2000);
        });

        // アカウント一覧を読み込み
        async function loadAccounts() {
            const response = await fetch('/api/accounts');
            const accounts = await response.json();
            
            const container = document.getElementById('accounts-list');
            container.innerHTML = '';
            
            accounts.forEach(account => {
                const card = document.createElement('div');
                card.className = 'card account-card mb-2';
                card.onclick = () => selectAccount(account.id);
                
                const modeIcon = account.mode === 'post' ? 'bi-megaphone' : 'bi-envelope';
                const statusColor = account.status === 'running' ? 'success' : 'secondary';
                
                card.innerHTML = `
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-0">${account.name}</h6>
                                <small><i class="bi ${modeIcon}"></i> ${account.mode === 'post' ? '投稿' : 'DM'}</small>
                            </div>
                            <span class="badge bg-${statusColor}">${account.status}</span>
                        </div>
                    </div>
                `;
                
                container.appendChild(card);
            });
        }

        // アカウントを選択
        async function selectAccount(accountId) {
            currentAccountId = accountId;
            document.getElementById('account-detail').style.display = 'block';
            
            // モードを取得
            const response = await fetch('/api/accounts');
            const accounts = await response.json();
            const account = accounts.find(a => a.id === accountId);
            
            if (account) {
                currentMode = account.mode || 'dm';
                updateModeUI();
                
                if (currentMode === 'dm') {
                    loadDMCampaigns();
                } else {
                    loadPostCampaigns();
                }
            }
        }

        // モード切り替え
        async function switchMode(mode) {
            currentMode = mode;
            
            // サーバーに保存
            await fetch(`/api/accounts/${currentAccountId}/mode`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            
            updateModeUI();
            loadAccounts();
            
            if (mode === 'dm') {
                loadDMCampaigns();
            } else {
                loadPostCampaigns();
            }
        }

        // モードUIを更新
        function updateModeUI() {
            if (currentMode === 'dm') {
                document.getElementById('dm-mode-btn').classList.add('active');
                document.getElementById('post-mode-btn').classList.remove('active');
                document.getElementById('dm-mode-content').style.display = 'block';
                document.getElementById('post-mode-content').style.display = 'none';
            } else {
                document.getElementById('dm-mode-btn').classList.remove('active');
                document.getElementById('post-mode-btn').classList.add('active');
                document.getElementById('dm-mode-content').style.display = 'none';
                document.getElementById('post-mode-content').style.display = 'block';
            }
        }

        // DMキャンペーンを読み込み
        async function loadDMCampaigns() {
            const response = await fetch(`/api/accounts/${currentAccountId}/campaigns`);
            const campaigns = await response.json();
            
            const container = document.getElementById('dm-campaigns-list');
            container.innerHTML = '';
            
            campaigns.forEach((campaign, index) => {
                const card = document.createElement('div');
                card.className = 'card mb-2';
                
                card.innerHTML = `
                    <div class="card-body">
                        <h6>${campaign.active ? '✓' : '✗'} ${campaign.name}</h6>
                        <small class="text-muted">キーワード: ${campaign.keywords.join(', ')}</small>
                    </div>
                `;
                
                container.appendChild(card);
            });
        }

        // 投稿キャンペーンを読み込み
        async function loadPostCampaigns() {
            const response = await fetch(`/api/accounts/${currentAccountId}/post-campaigns`);
            const campaigns = await response.json();
            
            const container = document.getElementById('post-campaigns-list');
            container.innerHTML = '';
            
            campaigns.forEach(campaign => {
                const card = document.createElement('div');
                card.className = 'card mb-2';
                
                card.innerHTML = `
                    <div class="card-body">
                        <h6>${campaign.active ? '✓' : '✗'} ${campaign.name}</h6>
                        <small class="text-muted">${campaign.posts.length} 件の投稿</small>
                    </div>
                `;
                
                container.appendChild(card);
            });
        }

        // メディア選択
        async function handleMediaSelect(event) {
            const files = event.target.files;
            
            for (let file of files) {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    selectedMedia.push(data.path);
                    
                    // プレビュー表示
                    const preview = document.createElement('div');
                    preview.className = 'media-preview';
                    preview.innerHTML = `
                        <img src="${URL.createObjectURL(file)}" alt="${file.name}">
                        <button class="remove-btn" onclick="removeMedia(${selectedMedia.length - 1})">×</button>
                    `;
                    document.getElementById('media-preview').appendChild(preview);
                }
            }
        }

        // メディアを削除
        function removeMedia(index) {
            selectedMedia.splice(index, 1);
            updateMediaPreview();
        }

        // 投稿を作成
        async function createPost() {
            const content = document.getElementById('post-content').value;
            const immediate = document.getElementById('post-campaign-select').value === '';
            
            if (!content.trim()) {
                alert('投稿内容を入力してください');
                return;
            }
            
            const data = {
                content,
                media_paths: selectedMedia,
                immediate,
                campaign_name: immediate ? null : 'Default Campaign'
            };
            
            const response = await fetch(`/api/accounts/${currentAccountId}/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                alert(immediate ? '投稿しました！' : 'キャンペーンに追加しました！');
                document.getElementById('post-content').value = '';
                selectedMedia = [];
                document.getElementById('media-preview').innerHTML = '';
                loadPostCampaigns();
            } else {
                alert('投稿に失敗しました');
            }
        }

        // ボットを開始
        async function startBot() {
            const response = await fetch(`/api/bot/${currentAccountId}/start`, {
                method: 'POST'
            });
            
            if (response.ok) {
                document.getElementById('start-btn').disabled = true;
                document.getElementById('stop-btn').disabled = false;
            } else {
                const data = await response.json();
                alert(data.message);
            }
        }

        // ボットを停止
        async function stopBot() {
            const response = await fetch(`/api/bot/${currentAccountId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
            }
        }

        // ステータス更新
        async function updateStatus() {
            if (!currentAccountId) return;
            
            const response = await fetch('/api/accounts');
            const accounts = await response.json();
            const account = accounts.find(a => a.id === currentAccountId);
            
            if (account) {
                const statusBadge = document.getElementById('status-badge');
                if (account.status === 'running') {
                    statusBadge.textContent = '実行中';
                    statusBadge.className = 'badge bg-success';
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                } else {
                    statusBadge.textContent = '停止中';
                    statusBadge.className = 'badge bg-secondary';
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                }
            }
        }

        // アカウント追加モーダル
        function showAddAccountModal() {
            document.getElementById('add-account-form').reset();
            const modal = new bootstrap.Modal(document.getElementById('addAccountModal'));
            modal.show();
        }

        // アカウントを追加
        async function addAccount() {
            const data = {
                name: document.getElementById('new-account-name').value,
                username: document.getElementById('new-account-username').value,
                password: document.getElementById('new-account-password').value,
                proxy: document.getElementById('new-account-proxy').value
            };
            
            const response = await fetch('/api/accounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('addAccountModal')).hide();
                loadAccounts();
            }
        }

        // DMキャンペーン追加モーダル
        function showAddCampaignModal() {
            // 実装省略（既存のDMキャンペーン追加機能を使用）
            alert('DMキャンペーン追加機能は既存の実装を使用してください');
        }
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'integrated.html', 'w', encoding='utf-8') as f:
        f.write(integrated_html)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='X Bot Integrated Web GUI')
    parser.add_argument('--port', type=int, default=5003, help='Port to run the web server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the web server on')
    args = parser.parse_args()
    
    create_templates()
    print("X Bot 統合管理システムを起動しています...")
    print(f"ブラウザで http://localhost:{args.port} を開いてください")
    app.run(host=args.host, port=args.port, debug=False)