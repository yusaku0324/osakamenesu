# multi_account_web_gui.py - 複数アカウント対応Web GUI
from flask import Flask, render_template, request, jsonify, redirect, url_for
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
from models import Campaign

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# マネージャーインスタンス
manager = MultiAccountManager()


# ルートページ
@app.route('/')
def index():
    return render_template('multi_account.html')


# アカウント一覧API
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts_data = []
    for account in manager.accounts.values():
        accounts_data.append({
            'id': account.id,
            'name': account.name,
            'username': account.username,
            'active': account.active,
            'has_credentials': bool(account.username and account.password),
            'proxy': account.proxy,
            'campaigns_count': len(account.campaigns),
            'status': manager.stats.get(account.id, {}).get('status', 'stopped')
        })
    return jsonify(accounts_data)


# アカウント追加API
@app.route('/api/accounts', methods=['POST'])
def add_account():
    data = request.json
    name = data.get('name', '新規アカウント')
    username = data.get('username', '')
    password = data.get('password', '')
    proxy = data.get('proxy', '')
    
    account_id = manager.add_account(name, username, password)
    
    if proxy:
        manager.accounts[account_id].proxy = proxy
    
    manager.save_config()
    
    return jsonify({
        'status': 'success',
        'account_id': account_id
    })


# アカウント詳細API
@app.route('/api/accounts/<account_id>', methods=['GET', 'PUT', 'DELETE'])
def account_detail(account_id):
    if account_id not in manager.accounts:
        return jsonify({'status': 'error', 'message': 'Account not found'}), 404
    
    if request.method == 'GET':
        account = manager.accounts[account_id]
        return jsonify({
            'id': account.id,
            'name': account.name,
            'username': account.username,
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
        })
    
    elif request.method == 'PUT':
        data = request.json
        account = manager.accounts[account_id]
        
        # アカウント情報を更新
        account.name = data.get('name', account.name)
        account.active = data.get('active', account.active)
        account.proxy = data.get('proxy', account.proxy)
        
        # 認証情報が提供された場合は保存
        if 'username' in data and 'password' in data:
            username = data['username']
            password = data['password']
            if username and password:
                manager.save_account_credentials(account_id, username, password)
        
        manager.save_config()
        return jsonify({'status': 'success'})
    
    else:  # DELETE
        manager.remove_account(account_id)
        return jsonify({'status': 'success'})


# キャンペーンAPI
@app.route('/api/accounts/<account_id>/campaigns', methods=['GET', 'POST'])
def account_campaigns(account_id):
    if account_id not in manager.accounts:
        return jsonify({'status': 'error', 'message': 'Account not found'}), 404
    
    account = manager.accounts[account_id]
    
    if request.method == 'GET':
        campaigns = [
            {
                'index': i,
                'name': c.name,
                'keywords': c.keywords,
                'message_templates': c.message_templates,
                'max_dms_per_hour': c.max_dms_per_hour,
                'check_interval': c.check_interval,
                'active': c.active
            } for i, c in enumerate(account.campaigns)
        ]
        return jsonify(campaigns)
    
    else:  # POST
        data = request.json
        campaign = Campaign(
            name=data.get('name', '新規キャンペーン'),
            keywords=data.get('keywords', []),
            message_templates=data.get('message_templates', []),
            max_dms_per_hour=data.get('max_dms_per_hour', 10),
            check_interval=data.get('check_interval', 300),
            active=data.get('active', True)
        )
        account.campaigns.append(campaign)
        manager.save_config()
        return jsonify({'status': 'success'})


@app.route('/api/accounts/<account_id>/campaigns/<int:campaign_index>', methods=['PUT', 'DELETE'])
def campaign_detail(account_id, campaign_index):
    if account_id not in manager.accounts:
        return jsonify({'status': 'error', 'message': 'Account not found'}), 404
    
    account = manager.accounts[account_id]
    
    if campaign_index >= len(account.campaigns):
        return jsonify({'status': 'error', 'message': 'Campaign not found'}), 404
    
    if request.method == 'PUT':
        data = request.json
        campaign = account.campaigns[campaign_index]
        
        campaign.name = data.get('name', campaign.name)
        campaign.keywords = data.get('keywords', campaign.keywords)
        campaign.message_templates = data.get('message_templates', campaign.message_templates)
        campaign.max_dms_per_hour = data.get('max_dms_per_hour', campaign.max_dms_per_hour)
        campaign.check_interval = data.get('check_interval', campaign.check_interval)
        campaign.active = data.get('active', campaign.active)
        
        manager.save_config()
        return jsonify({'status': 'success'})
    
    else:  # DELETE
        account.campaigns.pop(campaign_index)
        manager.save_config()
        return jsonify({'status': 'success'})


# ボット制御API
@app.route('/api/bot/<account_id>/start', methods=['POST'])
def start_bot(account_id):
    try:
        manager.start_bot(account_id)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/bot/<account_id>/stop', methods=['POST'])
def stop_bot(account_id):
    manager.stop_bot(account_id)
    return jsonify({'status': 'success'})


@app.route('/api/bot/start-all', methods=['POST'])
def start_all_bots():
    manager.start_all_active()
    return jsonify({'status': 'success'})


@app.route('/api/bot/stop-all', methods=['POST'])
def stop_all_bots():
    manager.stop_all()
    return jsonify({'status': 'success'})


# ステータスAPI
@app.route('/api/status', methods=['GET'])
def get_status():
    all_stats = manager.get_all_stats()
    
    # 各アカウントのログを取得
    logs = {}
    for account_id in manager.accounts:
        logs[account_id] = manager.get_account_logs(account_id, limit=50)
    
    return jsonify({
        'stats': all_stats,
        'logs': logs
    })


# HTMLテンプレートを作成
def create_templates():
    """HTMLテンプレートファイルを作成"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # multi_account.html
    multi_account_html = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X DM Bot - 複数アカウント管理</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .navbar { background-color: #1DA1F2 !important; }
        .navbar-brand { color: white !important; font-weight: bold; }
        .account-card { 
            border-left: 4px solid #1DA1F2;
            transition: transform 0.2s;
            cursor: pointer;
        }
        .account-card:hover { transform: translateY(-2px); }
        .account-card.active { border-left-color: #17BF63; }
        .account-card.inactive { border-left-color: #ccc; }
        .status-running { color: #17BF63; }
        .status-stopped { color: #E1306C; }
        .log-container { 
            height: 300px; 
            overflow-y: auto; 
            background: #1a1a1a; 
            color: #00ff00; 
            font-family: monospace;
            font-size: 12px;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-robot"></i> X DM Bot - 複数アカウント管理
            </a>
            <div class="navbar-text text-white">
                <button class="btn btn-success btn-sm me-2" onclick="startAllBots()">
                    <i class="bi bi-play-fill"></i> 全て開始
                </button>
                <button class="btn btn-danger btn-sm" onclick="stopAllBots()">
                    <i class="bi bi-stop-fill"></i> 全て停止
                </button>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <!-- アカウント一覧 -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">アカウント一覧</h5>
                        <button class="btn btn-primary btn-sm" onclick="showAddAccountModal()">
                            <i class="bi bi-plus"></i> 追加
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="accounts-list"></div>
                    </div>
                </div>
            </div>

            <!-- アカウント詳細 -->
            <div class="col-md-8">
                <div id="account-detail" style="display: none;">
                    <div class="card mb-3">
                        <div class="card-header">
                            <h5 id="account-name">アカウント詳細</h5>
                        </div>
                        <div class="card-body">
                            <!-- アカウント設定 -->
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <h6>認証情報</h6>
                                    <div class="mb-2">
                                        <input type="text" class="form-control" id="account-username" placeholder="ユーザー名">
                                    </div>
                                    <div class="mb-2">
                                        <input type="password" class="form-control" id="account-password" placeholder="パスワード">
                                    </div>
                                    <button class="btn btn-sm btn-primary" onclick="saveAccountCredentials()">認証情報を保存</button>
                                </div>
                                <div class="col-md-6">
                                    <h6>プロキシ設定</h6>
                                    <input type="text" class="form-control mb-2" id="account-proxy" placeholder="http://proxy:port">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="account-active">
                                        <label class="form-check-label">アクティブ</label>
                                    </div>
                                    <button class="btn btn-sm btn-success mt-2" onclick="toggleBot()">
                                        <i class="bi bi-play"></i> <span id="toggle-bot-text">開始</span>
                                    </button>
                                </div>
                            </div>

                            <!-- キャンペーン -->
                            <h6>キャンペーン 
                                <button class="btn btn-sm btn-success" onclick="showAddCampaignModal()">
                                    <i class="bi bi-plus"></i> 追加
                                </button>
                            </h6>
                            <div id="campaigns-list"></div>

                            <!-- ログ -->
                            <h6 class="mt-3">ログ</h6>
                            <div class="log-container" id="account-log"></div>
                        </div>
                    </div>
                </div>

                <!-- 統計ダッシュボード -->
                <div class="card">
                    <div class="card-header">
                        <h5>全体統計</h5>
                    </div>
                    <div class="card-body">
                        <div class="row" id="global-stats">
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h6 class="text-muted">アクティブアカウント</h6>
                                    <h3 id="stat-active-accounts">0</h3>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h6 class="text-muted">総DM送信数</h6>
                                    <h3 id="stat-total-dms">0</h3>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h6 class="text-muted">平均成功率</h6>
                                    <h3 id="stat-avg-success">0%</h3>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h6 class="text-muted">発見ツイート</h6>
                                    <h3 id="stat-total-tweets">0</h3>
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
                            <input type="text" class="form-control" id="new-account-proxy" placeholder="http://proxy:port">
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
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">1時間あたりの最大DM数</label>
                                <input type="number" class="form-control" id="campaign-max-dms" value="10">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">チェック間隔（秒）</label>
                                <input type="number" class="form-control" id="campaign-interval" value="300">
                            </div>
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
        let currentAccountId = null;
        let accounts = [];
        let statusInterval;

        // 初期化
        document.addEventListener('DOMContentLoaded', function() {
            loadAccounts();
            statusInterval = setInterval(updateStatus, 2000);
        });

        // アカウント一覧を読み込み
        async function loadAccounts() {
            const response = await fetch('/api/accounts');
            accounts = await response.json();
            displayAccounts();
        }

        // アカウント一覧を表示
        function displayAccounts() {
            const container = document.getElementById('accounts-list');
            container.innerHTML = '';
            
            accounts.forEach(account => {
                const card = document.createElement('div');
                card.className = `card account-card mb-2 ${account.active ? 'active' : 'inactive'}`;
                card.onclick = () => selectAccount(account.id);
                
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-0">${account.name}</h6>
                                <small class="text-muted">${account.username || '未設定'}</small>
                                <div class="mt-1">
                                    <span class="badge bg-secondary">${account.campaigns_count} キャンペーン</span>
                                    <span class="badge status-${account.status}">${account.status === 'running' ? '実行中' : '停止'}</span>
                                </div>
                            </div>
                            <div>
                                <button class="btn btn-sm btn-danger" onclick="deleteAccount('${account.id}', event)">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
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
            
            // アカウント詳細を読み込み
            const response = await fetch(`/api/accounts/${accountId}`);
            const account = await response.json();
            
            // 詳細を表示
            document.getElementById('account-name').textContent = account.name;
            document.getElementById('account-username').value = account.username || '';
            document.getElementById('account-password').value = '';
            document.getElementById('account-proxy').value = account.proxy || '';
            document.getElementById('account-active').checked = account.active;
            
            // キャンペーンを表示
            displayCampaigns(account.campaigns);
            
            // ボタンテキストを更新
            const isRunning = accounts.find(a => a.id === accountId)?.status === 'running';
            document.getElementById('toggle-bot-text').textContent = isRunning ? '停止' : '開始';
        }

        // キャンペーンを表示
        function displayCampaigns(campaigns) {
            const container = document.getElementById('campaigns-list');
            container.innerHTML = '';
            
            campaigns.forEach((campaign, index) => {
                const card = document.createElement('div');
                card.className = 'card mb-2';
                
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-0">${campaign.active ? '✓' : '✗'} ${campaign.name}</h6>
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
                    </div>
                `;
                
                container.appendChild(card);
            });
        }

        // アカウント追加モーダルを表示
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

        // アカウントを削除
        async function deleteAccount(accountId, event) {
            event.stopPropagation();
            
            if (!confirm('このアカウントを削除しますか？')) return;
            
            const response = await fetch(`/api/accounts/${accountId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                if (currentAccountId === accountId) {
                    document.getElementById('account-detail').style.display = 'none';
                    currentAccountId = null;
                }
                loadAccounts();
            }
        }

        // 認証情報を保存
        async function saveAccountCredentials() {
            const data = {
                username: document.getElementById('account-username').value,
                password: document.getElementById('account-password').value,
                proxy: document.getElementById('account-proxy').value,
                active: document.getElementById('account-active').checked
            };
            
            const response = await fetch(`/api/accounts/${currentAccountId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                alert('保存しました');
                loadAccounts();
            }
        }

        // ボットの開始/停止を切り替え
        async function toggleBot() {
            const account = accounts.find(a => a.id === currentAccountId);
            const isRunning = account?.status === 'running';
            
            const endpoint = isRunning ? 'stop' : 'start';
            const response = await fetch(`/api/bot/${currentAccountId}/${endpoint}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                loadAccounts();
            } else {
                const data = await response.json();
                alert(data.message);
            }
        }

        // キャンペーン編集
        async function editCampaign(index) {
            const response = await fetch(`/api/accounts/${currentAccountId}/campaigns`);
            const campaigns = await response.json();
            const campaign = campaigns[index];
            
            document.getElementById('campaign-index').value = index;
            document.getElementById('campaign-name').value = campaign.name;
            document.getElementById('campaign-active').checked = campaign.active;
            document.getElementById('campaign-keywords').value = campaign.keywords.join('\\n');
            document.getElementById('campaign-templates').value = campaign.message_templates.join('\\n\\n');
            document.getElementById('campaign-max-dms').value = campaign.max_dms_per_hour;
            document.getElementById('campaign-interval').value = campaign.check_interval;
            
            const modal = new bootstrap.Modal(document.getElementById('campaignModal'));
            modal.show();
        }

        // 新規キャンペーン
        function showAddCampaignModal() {
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
                max_dms_per_hour: parseInt(document.getElementById('campaign-max-dms').value),
                check_interval: parseInt(document.getElementById('campaign-interval').value)
            };
            
            let response;
            if (index === -1) {
                // 新規作成
                response = await fetch(`/api/accounts/${currentAccountId}/campaigns`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(campaign)
                });
            } else {
                // 更新
                response = await fetch(`/api/accounts/${currentAccountId}/campaigns/${index}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(campaign)
                });
            }
            
            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('campaignModal')).hide();
                selectAccount(currentAccountId);
            }
        }

        // キャンペーンを削除
        async function deleteCampaign(index) {
            if (!confirm('このキャンペーンを削除しますか？')) return;
            
            const response = await fetch(`/api/accounts/${currentAccountId}/campaigns/${index}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                selectAccount(currentAccountId);
            }
        }

        // 全ボット開始
        async function startAllBots() {
            const response = await fetch('/api/bot/start-all', { method: 'POST' });
            if (response.ok) {
                loadAccounts();
            }
        }

        // 全ボット停止
        async function stopAllBots() {
            const response = await fetch('/api/bot/stop-all', { method: 'POST' });
            if (response.ok) {
                loadAccounts();
            }
        }

        // ステータス更新
        async function updateStatus() {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // 統計を更新
            let activeCount = 0;
            let totalDMs = 0;
            let totalSuccess = 0;
            let totalTweets = 0;
            
            Object.entries(data.stats).forEach(([accountId, stats]) => {
                if (stats.status === 'running') activeCount++;
                totalDMs += stats.total_sent || 0;
                totalSuccess += stats.success_rate || 0;
                totalTweets += stats.tweets_found || 0;
            });
            
            document.getElementById('stat-active-accounts').textContent = activeCount;
            document.getElementById('stat-total-dms').textContent = totalDMs;
            document.getElementById('stat-avg-success').textContent = Math.round(totalSuccess / Math.max(1, Object.keys(data.stats).length)) + '%';
            document.getElementById('stat-total-tweets').textContent = totalTweets;
            
            // ログを更新
            if (currentAccountId && data.logs[currentAccountId]) {
                const logContainer = document.getElementById('account-log');
                data.logs[currentAccountId].forEach(log => {
                    const line = document.createElement('div');
                    line.textContent = log;
                    logContainer.appendChild(line);
                });
                logContainer.scrollTop = logContainer.scrollHeight;
            }
            
            // アカウントステータスを更新
            loadAccounts();
        }
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'multi_account.html', 'w', encoding='utf-8') as f:
        f.write(multi_account_html)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='X DM Bot Multi-Account Web GUI')
    parser.add_argument('--port', type=int, default=5002, help='Port to run the web server on (default: 5002)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the web server on (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    create_templates()
    print("X DM Bot 複数アカウント管理 Web GUI を起動しています...")
    print(f"ブラウザで http://localhost:{args.port} を開いてください")
    app.run(host=args.host, port=args.port, debug=args.debug)