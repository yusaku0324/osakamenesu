# Claude Code CLI セットアップガイド（Self-Hosted Runner用）

このガイドでは、GitHub Actions self-hosted runnerにClaude Code CLIをインストールする手順を説明します。

## 前提条件

- GitHub Actions self-hosted runnerが設定済み
- runnerマシンへのSSHアクセス
- ANTHROPIC_API_KEY（Claude API キー）

## インストール手順

### 1. Runnerマシンにログイン

```bash
ssh your-runner-machine
```

### 2. インストールスクリプトをダウンロード

```bash
# GitHubリポジトリからスクリプトをダウンロード
curl -O https://raw.githubusercontent.com/yusaku0324/kakeru/main/install-claude-cli-runner.sh

# または、既にリポジトリがクローンされている場合
cd /path/to/kakeru
```

### 3. スクリプトを実行

```bash
# 実行権限を付与
chmod +x install-claude-cli-runner.sh

# インストール実行
./install-claude-cli-runner.sh
```

### 4. 環境変数の設定

#### 方法1: Runnerの環境変数として設定

```bash
# .envファイルに追加（runnerのホームディレクトリ）
echo "ANTHROPIC_API_KEY=your-api-key-here" >> ~/.env
```

#### 方法2: systemdサービスファイルに追加（推奨）

```bash
# GitHub Actions runnerのサービスファイルを編集
sudo systemctl edit actions.runner.yusaku0324-kakeru.your-runner-name

# 以下を追加
[Service]
Environment="ANTHROPIC_API_KEY=your-api-key-here"
```

#### 方法3: runnerの.bashrcに追加

```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 5. インストールの確認

```bash
# Claude Code CLIが使えることを確認
claude-code --version

# APIキーが設定されていることを確認
claude-code ask "Hello, Claude!"
```

## トラブルシューティング

### claude-codeコマンドが見つからない

```bash
# PATHを確認
echo $PATH

# .local/binがPATHに含まれているか確認
which claude-code

# 手動でPATHに追加
export PATH="$PATH:$HOME/.local/bin"
```

### APIキーエラー

```bash
# 環境変数が設定されているか確認
echo $ANTHROPIC_API_KEY

# 設定されていない場合は再設定
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Runnerサービスの再起動

```bash
# systemdを使用している場合
sudo systemctl restart actions.runner.yusaku0324-kakeru.your-runner-name

# または、手動で再起動
cd ~/actions-runner
./svc.sh stop
./svc.sh start
```

## セキュリティに関する注意事項

1. **APIキーの保護**
   - APIキーは環境変数として設定し、コードにハードコードしない
   - ファイルに保存する場合は適切な権限（600）を設定

2. **Runnerのアクセス制限**
   - Self-hosted runnerは信頼できる環境でのみ実行
   - 必要最小限の権限のみ付与

3. **定期的な更新**
   - Claude Code CLIとrunnerソフトウェアを定期的に更新

## 動作確認

インストール完了後、GitHubで以下をテスト：

1. Issueを作成し、本文に「@claude Hello!」と記載
2. PRにコメントで「@claude Please analyze this code」と記載
3. Actions タブから手動でワークフローを実行

## 関連ファイル

- `/install-claude-cli-runner.sh` - インストールスクリプト
- `/.github/workflows/claude-code-max-v2.yml` - Claude Code対応ワークフロー
- `/.github/actions/setup-claude-code/action.yml` - セットアップアクション