#!/usr/bin/env bash
# Source this script: `source tools/use-temp-gcloud-config.sh`
# It exports CLOUDSDK_CONFIG to a fresh temporary directory so gcloud commands
# can run without touching ~/.config/gcloud.

set -euo pipefail

TEMP_DIR=$(mktemp -d)
export CLOUDSDK_CONFIG="$TEMP_DIR"
echo "[gcloud-temp-config] using CLOUDSDK_CONFIG=$TEMP_DIR"
