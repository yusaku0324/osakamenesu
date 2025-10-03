#!/usr/bin/env bash
# Update the Cloud Run web service so that NEXT_PUBLIC_OSAKAMENESU_API_BASE / NEXT_PUBLIC_API_BASE
# automatically point to the currently deployed API service URL.

set -euo pipefail

PROJECT=${PROJECT:-gen-lang-client-0412098348}
REGION=${REGION:-asia-northeast1}
API_SERVICE=${API_SERVICE:-osakamenesu-api}
WEB_SERVICE=${WEB_SERVICE:-osakamenesu-web}

if ! command -v gcloud >/dev/null 2>&1; then
  echo "[update-api-base] gcloud CLI が見つかりません。先にインストール / 認証してください。" >&2
  exit 1
fi

API_URL=$(gcloud run services describe "$API_SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format='value(status.url)' || true)

if [[ -z "${API_URL}" ]]; then
  echo "[update-api-base] API サービス ($API_SERVICE) の URL を取得できませんでした。" >&2
  exit 1
fi

echo "[update-api-base] API base URL -> ${API_URL}"

gcloud run services update "$WEB_SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --set-env-vars=NEXT_PUBLIC_OSAKAMENESU_API_BASE="$API_URL",NEXT_PUBLIC_API_BASE="$API_URL"

echo "[update-api-base] Updated $WEB_SERVICE with NEXT_PUBLIC_* env vars"
