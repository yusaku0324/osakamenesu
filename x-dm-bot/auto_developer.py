#!/usr/bin/env python3
"""
X DM Bot 自動開発マネージャー
継続的に機能を追加・改善する自立型開発システム
"""

import argparse
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import queue

from scripts.auto_enhance import AutoDeveloper
from scripts.quality_monitor import QualityGate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoDevelopmentManager:
    """自動開発プロセス全体を管理"""
    
    def __init__(self, mode: str = "development", target: str = "mvp"):
        self.mode = mode
        self.target = target
        self.project_root = Path.cwd()
        self.developer = AutoDeveloper()
        self.quality_gate = QualityGate()
        self.task_queue = queue.Queue()
        self.status = {
            "running": False,
            "current_task": None,
            "completed_features": [],
            "quality_score": 0,
            "last_update": None
        }
        
    def start(self):
        """自動開発プロセスを開始"""
        logger.info(f"🚀 自動開発を開始します - モード: {self.mode}, ターゲット: {self.target}")
        
        self.status["running"] = True
        self.status["last_update"] = datetime.now().isoformat()
        
        # 開発サイクルをバックグラウンドで実行
        development_thread = threading.Thread(target=self._development_loop, daemon=True)
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        
        development_thread.start()
        monitoring_thread.start()
        
        # Web ダッシュボードを起動
        if self.mode == "production":
            self._start_dashboard()
        
        try:
            # メインループ
            while self.status["running"]:
                time.sleep(60)  # 1分ごとにステータスチェック
                self._update_status()
                
        except KeyboardInterrupt:
            logger.info("🛑 自動開発を停止します")
            self.stop()
    
    def _development_loop(self):
        """開発ループ - 継続的に機能を追加"""
        while self.status["running"]:
            try:
                # 次のタスクを決定
                next_task = self._get_next_task()
                if next_task:
                    self.status["current_task"] = next_task
                    logger.info(f"📋 タスク開始: {next_task['name']}")
                    
                    # 機能を実装
                    self.developer.implement_feature(next_task)
                    
                    # 品質チェック
                    quality_results = self.quality_gate.automated_review()
                    self.status["quality_score"] = quality_results.get("overall_score", 0)
                    
                    # 成功した場合は完了リストに追加
                    if quality_results.get("overall_score", 0) >= 80:
                        self.status["completed_features"].append(next_task["id"])
                        logger.info(f"✅ タスク完了: {next_task['name']}")
                    else:
                        logger.warning(f"⚠️ 品質基準を満たしていません: {next_task['name']}")
                        self._create_improvement_task(next_task, quality_results)
                    
                    self.status["current_task"] = None
                    
                # 開発間隔
                if self.mode == "production":
                    time.sleep(3600)  # 本番モードでは1時間ごと
                else:
                    time.sleep(300)   # 開発モードでは5分ごと
                    
            except Exception as e:
                logger.error(f"開発ループエラー: {e}")
                time.sleep(60)
    
    def _monitoring_loop(self):
        """監視ループ - システムの健全性をチェック"""
        while self.status["running"]:
            try:
                # システムメトリクスを収集
                metrics = self._collect_metrics()
                
                # アラートチェック
                self._check_alerts(metrics)
                
                # レポート生成
                if datetime.now().hour == 9:  # 毎日9時にレポート
                    self._generate_daily_report()
                
                time.sleep(300)  # 5分ごとにチェック
                
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                time.sleep(60)
    
    def _get_next_task(self) -> Optional[Dict]:
        """次に実行すべきタスクを取得"""
        # タスクキューから取得
        if not self.task_queue.empty():
            return self.task_queue.get()
        
        # または開発者の機能キューから取得
        for feature in self.developer.features_queue:
            if feature["id"] not in self.status["completed_features"]:
                return feature
        
        return None
    
    def _create_improvement_task(self, original_task: Dict, quality_results: Dict):
        """改善タスクを作成"""
        improvement_task = {
            "id": f"{original_task['id']}_improvement",
            "name": f"{original_task['name']} - 品質改善",
            "priority": 0,  # 最高優先度
            "tasks": []
        }
        
        # 品質結果に基づいて改善タスクを追加
        if quality_results.get("tests", {}).get("coverage", 0) < 85:
            improvement_task["tasks"].append("テストカバレッジを85%以上に改善")
        
        if quality_results.get("security", {}).get("score", 0) < 95:
            improvement_task["tasks"].append("セキュリティ脆弱性の修正")
        
        self.task_queue.put(improvement_task)
    
    def _collect_metrics(self) -> Dict:
        """システムメトリクスを収集"""
        import psutil
        
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_threads": threading.active_count(),
            "queue_size": self.task_queue.qsize(),
            "quality_score": self.status["quality_score"],
            "completed_features": len(self.status["completed_features"])
        }
    
    def _check_alerts(self, metrics: Dict):
        """アラート条件をチェック"""
        alerts = []
        
        if metrics["cpu_usage"] > 80:
            alerts.append(f"⚠️ CPU使用率が高い: {metrics['cpu_usage']}%")
        
        if metrics["memory_usage"] > 90:
            alerts.append(f"⚠️ メモリ使用率が高い: {metrics['memory_usage']}%")
        
        if metrics["quality_score"] < 70:
            alerts.append(f"⚠️ 品質スコアが低い: {metrics['quality_score']}")
        
        for alert in alerts:
            logger.warning(alert)
            # 通知を送信（Slack、メールなど）
    
    def _generate_daily_report(self):
        """日次レポートを生成"""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "completed_features": self.status["completed_features"],
            "quality_score": self.status["quality_score"],
            "metrics": self._collect_metrics()
        }
        
        report_file = self.project_root / "reports" / f"daily_report_{report['date']}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 日次レポートを生成: {report_file}")
    
    def _start_dashboard(self):
        """監視ダッシュボードを起動"""
        logger.info("📊 監視ダッシュボードを起動中...")
        
        # Flask/Dash でダッシュボードを起動
        dashboard_thread = threading.Thread(
            target=self._run_dashboard,
            daemon=True
        )
        dashboard_thread.start()
    
    def _run_dashboard(self):
        """ダッシュボードサーバーを実行"""
        try:
            from monitor_dashboard import create_dashboard_app
            app = create_dashboard_app(self)
            app.run_server(host='0.0.0.0', port=9000, debug=False)
        except ImportError:
            logger.warning("ダッシュボードモジュールが見つかりません")
    
    def _update_status(self):
        """ステータスを更新"""
        self.status["last_update"] = datetime.now().isoformat()
        
        # ステータスファイルに保存
        status_file = self.project_root / "status.json"
        with open(status_file, 'w') as f:
            json.dump(self.status, f, indent=2)
    
    def stop(self):
        """自動開発を停止"""
        self.status["running"] = False
        logger.info("自動開発を停止しました")
    
    def add_custom_task(self, task: Dict):
        """カスタムタスクを追加"""
        self.task_queue.put(task)
        logger.info(f"カスタムタスクを追加: {task['name']}")


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="X DM Bot 自動開発マネージャー")
    parser.add_argument(
        "--mode",
        choices=["development", "production"],
        default="development",
        help="実行モード"
    )
    parser.add_argument(
        "--target",
        choices=["mvp", "full", "enterprise"],
        default="mvp",
        help="開発ターゲット"
    )
    parser.add_argument(
        "--task",
        type=str,
        help="特定のタスクを追加"
    )
    
    args = parser.parse_args()
    
    # マネージャーを初期化
    manager = AutoDevelopmentManager(mode=args.mode, target=args.target)
    
    # カスタムタスクがある場合は追加
    if args.task:
        custom_task = {
            "id": f"custom_{int(time.time())}",
            "name": args.task,
            "priority": 1,
            "tasks": [args.task]
        }
        manager.add_custom_task(custom_task)
    
    # 開発を開始
    try:
        manager.start()
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        manager.stop()


if __name__ == "__main__":
    main()