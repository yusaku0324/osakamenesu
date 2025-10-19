#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $(basename "$0") <path>" >&2
  exit 1
fi

TARGET=$1
if [[ ! -e "$TARGET" ]]; then
  echo "[fix-quarantine] path not found: $TARGET" >&2
  exit 1
fi

sudo xattr -dr com.apple.quarantine "$TARGET"
sudo xattr -dr com.apple.provenance "$TARGET"

echo "[fix-quarantine] removed quarantine/provenance from $TARGET"
