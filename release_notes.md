## 変更点
- リポジトリ全体のPythonランタイムを3.12に統一
- GitHub Actionsワークフローを全てPython 3.12に更新
- pyproject.tomlのrequires-pythonを"^3.12"に更新
- Blackのtarget-versionを["py312"]に更新
- READMEの必要条件を「Python 3.12以上」に更新
- テストカバレッジ 84% 以上を保証

## 破壊的変更
- Python 3.8/3.9のサポートを終了し、3.12以上が必須になりました

## CI
- 全テスト通過済み
