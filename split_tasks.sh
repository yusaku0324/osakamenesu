#!/usr/bin/env bash
# split_tasks.sh
# 自動で Taskfile.backup.yml をサブファイルへ振り分けるスクリプト
# 使い方: ./split_tasks.sh Taskfile.backup.yml
# 必要コマンド: yq (https://mikefarah.github.io/yq/)

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <backup_taskfile.yml>" >&2
  exit 1
fi

src="$1"

if [[ ! -f "$src" ]]; then
  echo "Error: file $src not found" >&2
  exit 1
fi

# 対象の prefix
prefixes=(core venv cursor tests flow)

echo "Splitting tasks from $src into tasks/*.yml ..."

for prefix in "${prefixes[@]}"; do
  dest="tasks/${prefix}.yml"
  tmp="${dest}.tmp"
  new="${dest}.new"

  # yq で prefix に一致するタスクだけ抽出して一時ファイルに保存
  yq eval ".tasks | with_entries(select(.key | test(\"^${prefix}:\")))" "$src" \
    | yq eval '{"version": "3", "tasks": .}' - \
    > "$tmp"

  # 既存ファイルが無い場合は空のテンプレを用意
  if [[ ! -f "$dest" ]]; then
    echo -e "---\nversion: \"3\"\n\ntasks: {}" > "$dest"
  fi

  # 既存とマージ (既存優先)
  yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' "$dest" "$tmp" > "$new"

  mv "$new" "$dest"
  rm "$tmp"
  echo "  -> updated $dest"

done

echo "Done. Remember to run 'yamllint .' and 'task --list-all' to verify." 