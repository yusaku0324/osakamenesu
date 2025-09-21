#!/usr/bin/env python3
"""Import shop data from a YAML file via admin endpoints."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib import request, parse

import yaml
from datetime import datetime, date


VALID_SERVICE_TYPES = {"store", "dispatch"}


def normalize_key(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None


def _as_date_string(value: Any) -> str | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return None


def validate_shop(shop: dict[str, Any], seen_keys: set[str]) -> list[str]:
    errors: list[str] = []
    name = shop.get("name")
    area = shop.get("area")
    if not name:
        errors.append("name is required")
    if not area:
        errors.append("area is required")

    key = f"{normalize_key(name)}::{normalize_key(area)}"
    if key in seen_keys:
        errors.append(f"duplicate shop for name+area ({name}/{area})")
    else:
        seen_keys.add(key)

    price_min = shop.get("price_min")
    price_max = shop.get("price_max")
    try:
        price_min = int(price_min)
    except Exception:
        errors.append("price_min must be integer")
        price_min = None
    try:
        price_max = int(price_max)
    except Exception:
        price_max = price_min
    if price_min is not None and price_max is not None and price_min > price_max:
        errors.append("price_min must be <= price_max")

    service_type = shop.get("service_type", "store")
    if service_type not in VALID_SERVICE_TYPES:
        errors.append(f"service_type must be one of {sorted(VALID_SERVICE_TYPES)}")

    availability = shop.get("availability")
    if availability:
        if not isinstance(availability, dict):
            errors.append("availability must be a mapping of date -> slots")
        else:
            for raw_date, slots in availability.items():
                date_str = _as_date_string(raw_date)
                if not date_str:
                    errors.append(f"availability date '{raw_date}' is not ISO format (YYYY-MM-DD)")
                    continue
                if slots is None:
                    continue
                if not isinstance(slots, list):
                    errors.append(f"availability for {date_str} must be a list of slots")
                    continue
                for slot in slots:
                    if not isinstance(slot, dict):
                        errors.append(f"slot in {date_str} must be an object")
                        continue
                    start_val = slot.get("start_at") or slot.get("start")
                    end_val = slot.get("end_at") or slot.get("end")
                    if not (start_val and end_val):
                        errors.append(f"slot in {date_str} missing start_at/end_at")
                        continue
                    start_dt = _as_datetime(start_val)
                    end_dt = _as_datetime(end_val)
                    if not start_dt or not end_dt:
                        errors.append(f"slot datetime invalid in {date_str}: {start_val} - {end_val}")
                        continue
                    if start_dt >= end_dt:
                        errors.append(f"slot in {date_str} has start >= end ({start_dt.isoformat()} >= {end_dt.isoformat()})")

    return errors


def post_json(api_base: str, path: str, payload: Any, admin_key: str) -> Any:
    url = f"{api_base}{path}"
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Key": admin_key,
    }
    req = request.Request(url, data=data, headers=headers, method="POST")
    with request.urlopen(req) as resp:
        text = resp.read().decode("utf-8")
        return json.loads(text) if text else None


def post_query(api_base: str, path: str, params: dict[str, Any], admin_key: str) -> Any:
    url = f"{api_base}{path}?{parse.urlencode(params)}"
    headers = {"X-Admin-Key": admin_key}
    req = request.Request(url, headers=headers, method="POST")
    with request.urlopen(req) as resp:
        text = resp.read().decode("utf-8")
        return json.loads(text) if text else None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Import shops from YAML file")
    parser.add_argument("file", help="Path to YAML file")
    parser.add_argument("--api-base", default=os.environ.get("API_BASE", "http://localhost:8000"))
    parser.add_argument("--admin-key", default=os.environ.get("ADMIN_API_KEY", "dev_admin_key"))
    args = parser.parse_args(argv)

    data = yaml.safe_load(Path(args.file).read_text(encoding="utf-8")) or {}
    shops = data.get("shops")
    if not isinstance(shops, list):
        print("YAML must contain a list under 'shops'", file=sys.stderr)
        return 1

    created: list[str] = []
    seen_keys: set[str] = set()

    validation_errors: list[str] = []
    for idx, shop in enumerate(shops):
        if not isinstance(shop, dict):
            validation_errors.append(f"entry #{idx + 1} is not an object")
            continue
        errs = validate_shop(shop, seen_keys)
        if errs:
            validation_errors.extend([f"[{shop.get('name','unknown')}]: {msg}" for msg in errs])

    if validation_errors:
        for msg in validation_errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    for shop in shops:
        name = shop.get("name")
        area = shop.get("area")

        price_min = int(shop.get("price_min", 0))
        price_max = int(shop.get("price_max", price_min))
        body_tags = shop.get("tags") or shop.get("body_tags") or []
        photos = shop.get("photos") or []
        discounts = shop.get("discounts") or []
        ranking_badges = shop.get("badges") or []
        contact_input = shop.get("contact") or {}

        contact_json = {
            "phone": contact_input.get("phone"),
            "line_id": contact_input.get("line"),
            "website_url": contact_input.get("website"),
            "reservation_form_url": contact_input.get("reservation_form_url"),
            "sns": contact_input.get("sns"),
            "address": shop.get("address"),
            "description": shop.get("description"),
            "catch_copy": shop.get("catch_copy"),
            "menus": shop.get("menus"),
            "staff": shop.get("staff"),
            "service_tags": shop.get("service_tags"),
        }

        payload = {
            "name": name,
            "area": area,
            "price_min": price_min,
            "price_max": price_max,
            "bust_tag": shop.get("bust_tag", ""),
            "service_type": shop.get("service_type", "store"),
            "height_cm": shop.get("height_cm"),
            "age": shop.get("age"),
            "body_tags": body_tags,
            "photos": photos,
            "contact_json": contact_json,
            "discounts": discounts,
            "ranking_badges": ranking_badges,
            "ranking_weight": shop.get("ranking_weight"),
            "status": shop.get("status", "published"),
        }

        res = post_json(args.api_base, "/api/admin/profiles", payload, args.admin_key)
        profile_id = res.get("id")
        if not profile_id:
            print(f"Failed to create profile for {name}", file=sys.stderr)
            continue
        created.append(profile_id)

        availability = shop.get("availability") or {}
        bulk_payload = []
        if isinstance(availability, dict):
            for raw_date, slots in availability.items():
                date_str = _as_date_string(raw_date)
                if not date_str:
                    continue
                slot_items = []
                if isinstance(slots, list):
                    for slot in slots:
                        if not isinstance(slot, dict):
                            continue
                        start_val = slot.get("start_at") or slot.get("start")
                        end_val = slot.get("end_at") or slot.get("end")
                        start_at = _as_datetime(start_val)
                        end_at = _as_datetime(end_val)
                        if not start_at or not end_at:
                            continue
                        slot_items.append({
                            "start_at": start_at.isoformat(),
                            "end_at": end_at.isoformat(),
                            "status": slot.get("status", "open"),
                        })
                bulk_payload.append({
                    "profile_id": profile_id,
                    "date": date_str,
                    "slots": slot_items or None,
                })
        if bulk_payload:
            post_json(args.api_base, "/api/admin/availabilities/bulk", bulk_payload, args.admin_key)

        # Optional outlinks for redirect tracking
        if contact_input.get("line"):
            token = f"line-{profile_id.split('-')[-1]}"
            post_query(args.api_base, "/api/admin/outlinks", {
                "profile_id": profile_id,
                "kind": "line",
                "token": token,
                "target_url": contact_input["line"],
            }, args.admin_key)
        if contact_input.get("phone"):
            token = f"tel-{profile_id.split('-')[-1]}"
            post_query(args.api_base, "/api/admin/outlinks", {
                "profile_id": profile_id,
                "kind": "tel",
                "token": token,
                "target_url": f"tel:{contact_input['phone']}",
            }, args.admin_key)
        if contact_input.get("website"):
            token = f"web-{profile_id.split('-')[-1]}"
            post_query(args.api_base, "/api/admin/outlinks", {
                "profile_id": profile_id,
                "kind": "web",
                "token": token,
                "target_url": contact_input["website"],
            }, args.admin_key)

    if created:
        post_json(args.api_base, "/api/admin/reindex", {"purge": False}, args.admin_key)

    print(json.dumps({"created": created}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
