#!/usr/bin/env bash
set -euo pipefail
PROJECT="${PROJECT:-gen-lang-client-0412098348}"
REGION="${REGION:-asia-northeast1}"
CLOUD_SQL_CONN="${CLOUD_SQL_CONN:-$PROJECT:$REGION:osakamenesu-pg}"
SERVICE="${SERVICE:-osakamenesu-api}"
MEILI_SERVICE="${MEILI_SERVICE:-osakamenesu-meili}"
SITE_BASE_URL="${SITE_BASE_URL:-https://gemini-stg-794815346083.asia-northeast1.run.app}"
MEILI_HOST="${MEILI_HOST:-https://osakamenesu-meili-794815346083.asia-northeast1.run.app}"
NOTIFY_SMTP_HOST="${NOTIFY_SMTP_HOST:-sandbox.smtp.mailtrap.io}"
NOTIFY_SMTP_PORT="${NOTIFY_SMTP_PORT:-2525}"
NOTIFY_SMTP_USERNAME="${NOTIFY_SMTP_USERNAME:-d7f28b27f7218e}"
NOTIFY_SMTP_PASSWORD="${NOTIFY_SMTP_PASSWORD:-e1705971ebda5b}"
NOTIFY_FROM_EMAIL="${NOTIFY_FROM_EMAIL:-no-reply@osakamenesu-stg.local}"
AUTH_MAGIC_LINK_DEBUG="${AUTH_MAGIC_LINK_DEBUG:-false}"

NEW_PASS=$(openssl rand -base64 24)
echo "Generated Cloud SQL password: $NEW_PASS"

gcloud sql users set-password app \
  --project="$PROJECT" \
  --instance=osakamenesu-pg \
  --password="$NEW_PASS"

ENCODED_PASS=$(python -c "import urllib.parse; print(urllib.parse.quote_plus('$NEW_PASS'))")

MEILI_MASTER_KEY=$(openssl rand -base64 32)
echo "Generated Meili master key: $MEILI_MASTER_KEY"

gcloud run services update "$MEILI_SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --set-env-vars=MEILI_MASTER_KEY="$MEILI_MASTER_KEY"

gcloud run services update "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --add-cloudsql-instances="$CLOUD_SQL_CONN" \
  --set-env-vars=DATABASE_URL="postgresql+asyncpg://app:${ENCODED_PASS}@/osaka_menesu?host=/cloudsql/${CLOUD_SQL_CONN}",\
SITE_BASE_URL="$SITE_BASE_URL",\
MEILI_HOST="$MEILI_HOST",\
MEILI_MASTER_KEY="$MEILI_MASTER_KEY",\
AUTH_MAGIC_LINK_DEBUG="$AUTH_MAGIC_LINK_DEBUG",\
NOTIFY_SMTP_HOST="$NOTIFY_SMTP_HOST",\
NOTIFY_SMTP_PORT="$NOTIFY_SMTP_PORT",\
NOTIFY_SMTP_USERNAME="$NOTIFY_SMTP_USERNAME",\
NOTIFY_SMTP_PASSWORD="$NOTIFY_SMTP_PASSWORD",\
NOTIFY_FROM_EMAIL="$NOTIFY_FROM_EMAIL"
