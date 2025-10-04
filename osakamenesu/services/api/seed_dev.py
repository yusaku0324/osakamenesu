#!/usr/bin/env python3
import argparse
import json
import os
import random
import sys
import time
from datetime import date
from typing import Optional
from urllib import request, parse, error


def make_client(api_base: str, admin_key: str, authorization: Optional[str]):
    def _execute(req: request.Request) -> dict:
        try:
            with request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"HTTPError {exc.code} for {req.full_url}: {detail or exc.reason}"
            ) from exc

    def post_json(path: str, payload: dict) -> dict:
        url = f"{api_base}{path}"
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Key": admin_key,
        }
        if authorization:
            headers["Authorization"] = authorization
        req = request.Request(url, data=data, headers=headers, method="POST")
        return _execute(req)

    def post_query(path: str, params: dict) -> dict:
        url = f"{api_base}{path}?{parse.urlencode(params)}"
        headers = {
            "X-Admin-Key": admin_key,
        }
        if authorization:
            headers["Authorization"] = authorization
        req = request.Request(url, headers=headers, method="POST")
        return _execute(req)

    return post_json, post_query


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Seed development data")
    parser.add_argument(
        "--api-base",
        default=os.environ.get("OSAKAMENESU_API_BASE")
        or os.environ.get("API_BASE", "http://localhost:8000"),
    )
    parser.add_argument("--count", type=int, default=8, help="number of profiles to create")
    parser.add_argument("--today-rate", type=float, default=0.5, help="ratio of profiles with availability today (0-1)")
    parser.add_argument("--diaries", type=int, default=0, help="diaries per profile (admin endpoint pending)")
    parser.add_argument(
        "--admin-key",
        default=os.environ.get("OSAKAMENESU_ADMIN_API_KEY")
        or os.environ.get("ADMIN_API_KEY", "dev_admin_key"),
        help="X-Admin-Key header",
    )
    parser.add_argument(
        "--authorization",
        default=os.environ.get("AUTHORIZATION"),
        help="Full Authorization header value (overrides --id-token if provided)",
    )
    parser.add_argument(
        "--id-token",
        default=os.environ.get("CLOUD_RUN_ID_TOKEN"),
        help="Identity token used as Bearer token for Cloud Run IAM auth",
    )
    args = parser.parse_args(argv)

    auth_header = args.authorization
    if not auth_header and args.id_token:
        auth_header = f"Bearer {args.id_token}"

    post_json, post_query = make_client(args.api_base, args.admin_key, auth_header)
    today = date.today().strftime("%Y-%m-%d")

    names = ["葵", "凛", "真央", "美月", "結衣", "楓", "ひなた", "さくら", "七海", "彩", "琴音", "乃愛", "花音", "心愛", "美咲", "陽菜"]
    areas = ["難波/日本橋", "梅田", "天王寺", "京橋", "堺", "北新地", "本町", "心斎橋"]
    busts = ["C", "D", "E", "F", "G", "H", "I", "J", "K_PLUS"]
    services = ["store", "dispatch"]
    body_pool = ["清楚", "スレンダー", "巨乳", "モデル", "ロリ", "可愛い", "セクシー", "黒髪", "お姉さん", "明るい", "グラマー"]

    rng = random.Random(42)
    created_ids: list[str] = []
    for i in range(args.count):
        name = names[i % len(names)] + (str((i // len(names)) + 1) if i >= len(names) else "")
        area = areas[i % len(areas)]
        bust = busts[i % len(busts)]
        base = 7000 + (i % 12) * 1000
        price_min = base
        price_max = base + 8000 + (i % 5) * 2000
        body_tags = rng.sample(body_pool, k=min(2, len(body_pool)))
        photos = [
            f"https://picsum.photos/seed/menesu{i+1}-1/800/600",
            f"https://picsum.photos/seed/menesu{i+1}-2/800/600",
            f"https://picsum.photos/seed/menesu{i+1}-3/800/600",
        ]

        base_store_name = f"{area}メンエス {chr(65 + (i % 3))}店"
        rating = 4.1 + (i % 4) * 0.2
        review_count = 35 + i * 3
        contact_json = {
            "line": f"line_{i:03}",
            "line_id": f"line_{i:03}",
            "tel": f"0900000{i:03}",
            "phone": f"0900000{i:03}",
            "web": "https://example.com",
            "store_name": base_store_name,
            "address": f"大阪市中央区{area}ビル{i % 7 + 1}F",
            "ranking_reason": "編集部が雰囲気・技術を取材してピックアップしています。",
            "service_tags": body_tags,
            "height_cm": 155 + (i % 15),
            "age": 20 + (i % 12),
            "menus": [
                {
                    "name": "アロマトリートメント90分",
                    "price": price_min + 3000,
                    "duration_minutes": 90,
                    "description": "全身リンパを丁寧に流す人気コースです。",
                    "tags": ["オイル", "リンパ"],
                },
                {
                    "name": "プレミアム120分",
                    "price": price_max,
                    "duration_minutes": 120,
                    "description": "VIPルームでの極上リラックスタイム。",
                    "tags": ["個室", "VIP"],
                },
            ],
            "staff": [
                {
                    "name": names[(i + 1) % len(names)],
                    "alias": "セラピスト",
                    "avatar_url": f"https://i.pravatar.cc/160?img={(i % 60) + 1}",
                    "headline": "繊細なハンドトリートメントが得意です。",
                    "specialties": ["ドライヘッド", "ディープリンパ"],
                    "rating": rating,
                    "review_count": review_count,
                },
                {
                    "name": names[(i + 2) % len(names)],
                    "alias": "新人",
                    "avatar_url": f"https://i.pravatar.cc/160?img={(i % 60) + 20}",
                    "headline": "笑顔が魅力のセラピスト。丁寧なカウンセリング付き。",
                    "specialties": ["ホットストーン", "ストレッチ"],
                },
            ],
            "promotions": [
                {
                    "label": "朝割キャンペーン",
                    "description": "11時までのご来店で1,000円OFF",
                    "expires_at": today,
                }
            ],
            "reviews": {
                "average_score": round(rating, 1),
                "review_count": review_count,
                "highlighted": [
                    {
                        "title": "技術も接客も大満足",
                        "body": "丁寧な施術で疲れが一気に取れました。会話も心地よくてリピート決定です。",
                        "score": 5,
                        "visited_at": today,
                        "author_alias": "匿名会員",
                    }
                ],
            },
        }

        discounts = [
            {
                "label": "新人割",
                "description": "入店30日以内の特別価格",
                "expires_at": None,
            }
        ] if i % 3 == 0 else [
            {
                "label": "早割",
                "description": "前日予約で1,000円OFF",
                "expires_at": None,
            }
        ] if i % 3 == 1 else []

        body = {
            "name": name,
            "area": area,
            "price_min": price_min,
            "price_max": price_max,
            "bust_tag": bust,
            "service_type": services[i % len(services)],
            "height_cm": 155 + (i % 15),
            "age": 20 + (i % 12),
            "body_tags": body_tags,
            "photos": photos,
            "contact_json": contact_json,
            "discounts": discounts,
            "ranking_badges": (["人気No.1"] if i % 5 == 0 else []) + (["本日注目"] if i % 4 == 0 else []),
            "ranking_weight": 100 - i,
            "status": "published",
        }
        res = post_json("/api/admin/profiles?skip_index=1", body)
        pid = res["id"]
        created_ids.append(pid)

        # Diary API は未実装のためスキップ

        # Availability for today by ratio
        if rng.random() < args.today_rate:
            post_query("/api/admin/availabilities", {"profile_id": pid, "date": today})

        # Outlinks (use pid-based unique tokens)
        token_suffix = pid.split("-")[-1]
        post_query("/api/admin/outlinks", {"profile_id": pid, "kind": "line", "token": f"line-{token_suffix}", "target_url": f"https://l.example/{pid}"})
        post_query("/api/admin/outlinks", {"profile_id": pid, "kind": "tel",  "token": f"tel-{token_suffix}",  "target_url": f"tel:0900000{i:03}"})
        post_query("/api/admin/outlinks", {"profile_id": pid, "kind": "web",  "token": f"web-{token_suffix}",  "target_url": f"https://example.com/{pid}"})

        time.sleep(0.05)

    # Reindex all
    post_query("/api/admin/reindex", {})

    print(json.dumps({"seeded": len(created_ids), "ids": created_ids}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
