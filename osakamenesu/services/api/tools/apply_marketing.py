#!/usr/bin/env python3
"""Bulk update profile marketing metadata via admin API.

Usage:
    python tools/apply_marketing.py marketing.json --api-base http://localhost:8000 --admin-key dev_admin_key

Input JSON format:
    [
      {
        "profile_id": "uuid",
        "ranking_badges": ["人気No.1"],
        "ranking_weight": 95,
        "discounts": [
          {"label": "新人割", "description": "初回1,000円OFF", "expires_at": "2024-12-31" }
        ]
      }
    ]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib import request, error


def load_entries(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("input must be a JSON list or object")
    out: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("each item must be an object")
        if "profile_id" not in item:
            raise ValueError("each item must include profile_id")
        payload = {
            k: v for k, v in item.items() if k in {"discounts", "ranking_badges", "ranking_weight"}
        }
        out.append({"profile_id": item["profile_id"], "payload": payload})
    return out


def post_json(url: str, payload: dict[str, Any], admin_key: str) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Key": admin_key,
    }
    req = request.Request(url, data=data, headers=headers, method="POST")
    with request.urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Apply marketing metadata to profiles")
    parser.add_argument("input", help="JSON file with marketing entries")
    parser.add_argument("--api-base", default="http://localhost:8000", help="Admin API base URL")
    parser.add_argument("--admin-key", default="dev_admin_key", help="X-Admin-Key for admin API")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between requests (seconds)")
    args = parser.parse_args(argv)

    entries = load_entries(Path(args.input))
    if not entries:
        print("No entries to apply", file=sys.stderr)
        return 0

    for entry in entries:
        profile_id = entry["profile_id"]
        payload = entry["payload"]
        if not payload:
            print(f"{profile_id}: skipped (no fields)")
            continue
        url = f"{args.api_base.rstrip('/')}/api/admin/profiles/{profile_id}/marketing"
        try:
            res = post_json(url, payload, args.admin_key)
            print(f"{profile_id}: {res}")
        except error.HTTPError as e:
            print(f"{profile_id}: HTTP {e.code} {e.reason}", file=sys.stderr)
        except Exception as exc:
            print(f"{profile_id}: failed ({exc})", file=sys.stderr)
        time.sleep(max(0.0, args.sleep))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
