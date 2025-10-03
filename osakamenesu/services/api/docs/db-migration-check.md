# External ID Migration Checklist

1. **起動**: 必要なら `docker-compose up -d osakamenesu-db` でローカル Postgres を起動。
2. **マイグレーション**: プロジェクトルートで `poetry run alembic upgrade head` または `docker-compose run --rm osakamenesu-api alembic upgrade head` を実行。
3. **重複チェック**: `poetry run python scripts/check_external_ids.py` を実行し、`[dup-check] reviews: OK` / `[dup-check] diaries: OK` が出ることを確認。重複があれば `scripts/check_external_ids.py` が該当レコードを列挙します。
4. **ステージング→本番**: 同じ手順を両環境で実行し、結果を記録します。

> 補足: `scripts/check_external_ids.py` は `app/settings.py` の `database_url` を利用するので、`.env` などで正しい接続情報をセットしてから実行してください。
