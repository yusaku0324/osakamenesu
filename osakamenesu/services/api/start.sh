#!/usr/bin/env bash
set -euo pipefail

cd /app

echo "[migrate] upgrading DB..."
alembic upgrade head || true
PORT=${PORT:-8080}
echo "[start] uvicorn on port ${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
