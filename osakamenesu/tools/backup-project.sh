#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $(basename "$0") <destination-dir> [--exclude pattern]" >&2
  exit 1
fi

DEST=$1
shift
EXCLUDES=("--exclude=.git" "--exclude=node_modules" "--exclude=.venv")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --exclude)
      EXCLUDES+=("--exclude=$2")
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$DEST"

ROOT=$(git rev-parse --show-toplevel)
rsync -a "${EXCLUDES[@]}" "$ROOT/" "$DEST/"

echo "[backup-project] synced $ROOT -> $DEST"
