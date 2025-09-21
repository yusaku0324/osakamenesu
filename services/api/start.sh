#!/usr/bin/env bash
set -euo pipefail

echo "[migrate] upgrading DB..."
alembic upgrade head || true
echo "[start] uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

