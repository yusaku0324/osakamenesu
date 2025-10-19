#!/usr/bin/env bash
# Runs `gcloud auth login --no-launch-browser`, copies the URL to the clipboard,
# and prompts to paste the verification code back.

set -euo pipefail

: "${CLOUDSDK_CONFIG:=$(mktemp -d)}"

# Use a fifo to capture the authentication URL
FIFO=$(mktemp -u)
mkfifo "$FIFO"

echo "[gcloud-login] using CLOUDSDK_CONFIG=$CLOUDSDK_CONFIG"

gcloud auth login --no-launch-browser --format='value()' > "$FIFO" 2>/tmp/gcloud-login.log &
PID=$!

# The URL is the first line from gcloud
read -r URL < "$FIFO"
rm "$FIFO"

if command -v pbcopy >/dev/null 2>&1; then
  printf '%s' "$URL" | pbcopy
  echo "[gcloud-login] authentication URL copied to clipboard"
else
  echo "[gcloud-login] authentication URL:" >&2
  echo "$URL"
fi

echo "[gcloud-login] paste the verification code below:" >&2
read -r CODE
echo "$CODE" | gcloud auth login --remote-bootstrap="$URL" --quiet >/dev/null

wait "$PID" || true

echo "[gcloud-login] authentication complete"
