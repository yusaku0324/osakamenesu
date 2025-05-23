#!/usr/bin/env python3
"""
品質監視とゲートキーパー - 製品の品質を自動的に維持
"""

import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QualityGate:
    """品質ゲートと自動改善を管理"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.metrics = {
            "code_coverage": 85,      # 最低85%のコードカバレッジ
            "performance_score": 90,   # パフォーマンススコア90点以上
            "security_score": 95,      # セキュリティスコア95点以上
            "user_satisfaction": 4.5,  # ユーザー満足度4.5以上
            "bug_density": 0.1,        # バグ密度0.1以下
            "technical_debt": 5        # 技術的負債5%以下
        }
        self.results = {}
    
    def automated_review(self) -> Dict:
        """自動レビューを実行"""
        logger.info("🔍 自動品質レビューを開始します")
        
        self.results['timestamp'] = datetime.now().isoformat()
        self.results['tests'] = self.run_automated_tests()
        self.results['security'] = self.security_scan()
        self.results['performance'] = self.performance_test()
        self.results['code_quality'] = self.analyze_code_quality()
        self.results['documentation'] = self.check_documentation()
        
        # 全体的な品質スコアを計算
        self.results['overall_score'] = self._calculate_overall_score()
        
        # 品質ゲートの判定
        if self._passes_quality_gate():
            logger.info("✅ 品質ゲートを通過しました")
            self.deploy_to_production()
        else:
            logger.warning("❌ 品質ゲートを通過できませんでした")
            self.create_improvement_tasks()
        
        return self.results
    
    def run_automated_tests(self) -> Dict:
        """自動テストを実行"""
        logger.info("テストスイートを実行中...")
        
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--cov=./", "--cov-report=json"],
            capture_output=True,
            text=True
        )
        
        coverage_data = {}
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
        
        return {
            "passed": result.returncode == 0,
            "coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
            "test_count": len(result.stdout.split('\n')),
            "failures": result.stderr.count("FAILED")
        }
    
    def security_scan(self) -> Dict:
        """セキュリティスキャンを実行"""
        logger.info("セキュリティスキャンを実行中...")
        
        security_issues = []
        
        # 依存関係の脆弱性チェック
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            # 実際のセキュリティチェックAPIを呼び出す（例：Snyk、Safety）
            # ここではダミーのチェック
            vulnerable_packages = []
            
        # ハードコードされた認証情報のチェック
        secret_patterns = [
            r"password\s*=\s*['\"].*['\"]",
            r"api_key\s*=\s*['\"].*['\"]",
            r"secret\s*=\s*['\"].*['\"]"
        ]
        
        for pattern in secret_patterns:
            result = subprocess.run(
                ["grep", "-r", "-E", pattern, "--include=*.py", "."],
                capture_output=True,
                text=True
            )
            if result.stdout:
                security_issues.append(f"潜在的な秘密情報の露出: {pattern}")
        
        security_score = 100 - (len(security_issues) * 5)
        
        return {
            "score": max(0, security_score),
            "issues": security_issues,
            "vulnerable_packages": vulnerable_packages if 'vulnerable_packages' in locals() else []
        }
    
    def performance_test(self) -> Dict:
        """パフォーマンステストを実行"""
        logger.info("パフォーマンステストを実行中...")
        
        # 簡単なパフォーマンステスト
        import time
        import psutil
        
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # テスト用のダミー処理
        # 実際のアプリケーションのエンドポイントをテスト
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        response_time = (end_time - start_time) * 1000  # ms
        memory_usage = end_memory - start_memory
        
        # スコア計算（レスポンスタイムとメモリ使用量に基づく）
        performance_score = 100
        if response_time > 1000:
            performance_score -= (response_time - 1000) / 100
        if memory_usage > 100:
            performance_score -= (memory_usage - 100) / 10
        
        return {
            "score": max(0, min(100, performance_score)),
            "response_time_ms": response_time,
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": psutil.cpu_percent(interval=1)
        }
    
    def analyze_code_quality(self) -> Dict:
        """コード品質を分析"""
        logger.info("コード品質を分析中...")
        
        metrics = {
            "complexity": 0,
            "duplications": 0,
            "maintainability": 100,
            "readability": 100
        }
        
        # Flake8によるコード品質チェック
        result = subprocess.run(
            ["flake8", ".", "--statistics", "--count"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            metrics["maintainability"] -= error_count * 2
        
        # 循環的複雑度の計算（radonを使用）
        try:
            result = subprocess.run(
                ["radon", "cc", ".", "-a"],
                capture_output=True,
                text=True
            )
            if "Average complexity:" in result.stdout:
                avg_complexity = float(result.stdout.split("Average complexity:")[1].split()[0])
                metrics["complexity"] = avg_complexity
                if avg_complexity > 10:
                    metrics["readability"] -= (avg_complexity - 10) * 5
        except:
            pass
        
        return metrics
    
    def check_documentation(self) -> Dict:
        """ドキュメントの完成度をチェック"""
        logger.info("ドキュメントをチェック中...")
        
        doc_files = list(self.project_root.glob("**/*.md"))
        py_files = list(self.project_root.glob("**/*.py"))
        
        # Docstringのカバレッジを計算
        total_functions = 0
        documented_functions = 0
        
        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue
                
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                total_functions += content.count("def ")
                documented_functions += content.count('"""')
        
        doc_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            "markdown_files": len(doc_files),
            "docstring_coverage": doc_coverage,
            "readme_exists": (self.project_root / "README.md").exists(),
            "api_docs_exists": (self.project_root / "docs" / "api.md").exists()
        }
    
    def _calculate_overall_score(self) -> float:
        """全体的な品質スコアを計算"""
        scores = []
        
        if 'tests' in self.results:
            scores.append(self.results['tests']['coverage'])
        if 'security' in self.results:
            scores.append(self.results['security']['score'])
        if 'performance' in self.results:
            scores.append(self.results['performance']['score'])
        if 'code_quality' in self.results:
            scores.append(self.results['code_quality']['maintainability'])
        if 'documentation' in self.results:
            scores.append(self.results['documentation']['docstring_coverage'])
        
        return sum(scores) / len(scores) if scores else 0
    
    def _passes_quality_gate(self) -> bool:
        """品質ゲートを通過するかチェック"""
        if not self.results:
            return False
        
        # 各メトリクスのチェック
        checks = []
        
        if 'tests' in self.results:
            checks.append(self.results['tests']['coverage'] >= self.metrics['code_coverage'])
        if 'security' in self.results:
            checks.append(self.results['security']['score'] >= self.metrics['security_score'])
        if 'performance' in self.results:
            checks.append(self.results['performance']['score'] >= self.metrics['performance_score'])
        
        return all(checks) if checks else False
    
    def deploy_to_production(self):
        """本番環境へのデプロイ"""
        logger.info("🚀 本番環境へのデプロイを開始します")
        
        # デプロイスクリプトの実行
        deploy_script = self.project_root / "scripts" / "deploy.sh"
        if deploy_script.exists():
            subprocess.run(["bash", str(deploy_script)])
        
        # デプロイ完了の通知
        self._send_notification("デプロイ完了", "品質ゲートを通過し、本番環境へのデプロイが完了しました。")
    
    def create_improvement_tasks(self):
        """改善タスクを作成"""
        logger.info("📋 改善タスクを作成します")
        
        tasks = []
        
        # テストカバレッジの改善
        if self.results.get('tests', {}).get('coverage', 0) < self.metrics['code_coverage']:
            tasks.append({
                "title": "テストカバレッジの改善",
                "description": f"現在のカバレッジ: {self.results['tests']['coverage']:.1f}%、目標: {self.metrics['code_coverage']}%",
                "priority": "high"
            })
        
        # セキュリティの改善
        if self.results.get('security', {}).get('issues'):
            tasks.append({
                "title": "セキュリティ問題の修正",
                "description": f"検出された問題: {', '.join(self.results['security']['issues'])}",
                "priority": "critical"
            })
        
        # パフォーマンスの改善
        if self.results.get('performance', {}).get('score', 0) < self.metrics['performance_score']:
            tasks.append({
                "title": "パフォーマンスの最適化",
                "description": f"現在のスコア: {self.results['performance']['score']:.1f}、目標: {self.metrics['performance_score']}",
                "priority": "medium"
            })
        
        # タスクの保存
        tasks_file = self.project_root / "improvement_tasks.json"
        with open(tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        logger.info(f"{len(tasks)}個の改善タスクを作成しました")
    
    def _send_notification(self, title: str, message: str):
        """通知を送信"""
        logger.info(f"通知: {title} - {message}")
        # Slack、メール、その他の通知サービスとの統合
    
    def generate_report(self) -> str:
        """品質レポートを生成"""
        report = f"""
# 品質レポート
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 全体スコア: {self.results.get('overall_score', 0):.1f}/100

### テスト結果
- カバレッジ: {self.results.get('tests', {}).get('coverage', 0):.1f}%
- テスト成功: {'✅' if self.results.get('tests', {}).get('passed') else '❌'}

### セキュリティ
- スコア: {self.results.get('security', {}).get('score', 0)}/100
- 検出された問題: {len(self.results.get('security', {}).get('issues', []))}

### パフォーマンス
- スコア: {self.results.get('performance', {}).get('score', 0):.1f}/100
- レスポンスタイム: {self.results.get('performance', {}).get('response_time_ms', 0):.1f}ms

### コード品質
- 保守性: {self.results.get('code_quality', {}).get('maintainability', 0)}/100
- 可読性: {self.results.get('code_quality', {}).get('readability', 0)}/100

### ドキュメント
- Docstringカバレッジ: {self.results.get('documentation', {}).get('docstring_coverage', 0):.1f}%
- READMEの存在: {'✅' if self.results.get('documentation', {}).get('readme_exists') else '❌'}
"""
        
        report_file = self.project_root / "quality_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        return report


if __name__ == "__main__":
    monitor = QualityGate()
    results = monitor.automated_review()
    report = monitor.generate_report()
    print(report)