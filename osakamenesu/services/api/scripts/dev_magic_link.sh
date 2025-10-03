#!/usr/bin/env bash
set -euo pipefail

PROJECT=${PROJECT:-gen-lang-client-0412098348}
REGION=${REGION:-asia-northeast1}
SERVICE=${SERVICE:-osakamenesu-api}
API_HOST=${API_HOST:-https://osakamenesu-api-794815346083.asia-northeast1.run.app}
EMAIL=${1:-dashboard-test@example.com}
FRESHNESS=${FRESHNESS:-5m}

echo "[dev_magic_link] Requesting magic link for ${EMAIL}"
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\"}" \
  "${API_HOST}/api/auth/request-link" > /dev/null

# Give logging a moment to flush
sleep 2

echo "[dev_magic_link] Fetching latest link from Cloud Logging"
ENTRY=$(gcloud logging read \
  "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE}\" AND textPayload:\"MAGIC_LINK_DEBUG\"" \
  --freshness="${FRESHNESS}" \
  --limit=1 \
  --project="${PROJECT}" \
  --format="value(textPayload)" || true)

if [[ -z "${ENTRY}" ]]; then
  echo "[dev_magic_link] No magic link found in the last ${FRESHNESS}." >&2
  exit 1
fi

LINK=${ENTRY#MAGIC_LINK_DEBUG }

if [[ -z "${LINK}" || "${LINK}" == "${ENTRY}" ]]; then
  echo "[dev_magic_link] Unexpected log format: ${ENTRY}" >&2
  exit 1
fi

echo "[dev_magic_link] Magic link URL"
echo "${LINK}"

echo "[dev_magic_link] Tip: open the link in the same browser to establish the session." >&2

echo "[dev_magic_link] Done"
