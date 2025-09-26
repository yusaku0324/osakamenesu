from __future__ import annotations

import asyncio
import logging
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

import httpx

from .settings import settings

logger = logging.getLogger("app.notifications")

SLACK_WEBHOOK = getattr(settings, "slack_webhook_url", None)
EMAIL_ENDPOINT = getattr(settings, "notify_email_endpoint", None)
LINE_ENDPOINT = getattr(settings, "notify_line_endpoint", None)


@dataclass
class ReservationNotification:
    reservation_id: str
    shop_id: str
    shop_name: str
    customer_name: str
    customer_phone: str
    desired_start: str
    desired_end: str
    status: str
    channel: Optional[str] = None
    notes: Optional[str] = None


async def _post_json(url: str, payload: Dict[str, Any]) -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(url, json=payload)


async def send_reservation_notification(payload: ReservationNotification) -> None:
    tasks = []
    message = (
        f"予約ID: {payload.reservation_id}\n"
        f"店舗: {payload.shop_name} ({payload.shop_id})\n"
        f"ステータス: {payload.status}\n"
        f"来店希望: {payload.desired_start} 〜 {payload.desired_end}\n"
        f"顧客: {payload.customer_name} ({payload.customer_phone})\n"
        f"メモ: {payload.notes or '-'}"
    )

    if SLACK_WEBHOOK:
        slack_payload = {
            "text": f"*予約更新通知*: {payload.status}",
            "attachments": [
                {
                    "color": "#36a64f" if payload.status == "confirmed" else "#f4c542",
                    "text": message,
                }
            ],
        }
        tasks.append(_post_json(SLACK_WEBHOOK, slack_payload))

    if EMAIL_ENDPOINT:
        email_payload = {
            "subject": f"予約更新: {payload.shop_name} ({payload.status})",
            "message": message,
            "reservation_id": payload.reservation_id,
            "shop_id": payload.shop_id,
        }
        tasks.append(_post_json(EMAIL_ENDPOINT, email_payload))

    if LINE_ENDPOINT:
        line_payload = {
            "message": message,
            "reservation_id": payload.reservation_id,
            "shop_id": payload.shop_id,
        }
        tasks.append(_post_json(LINE_ENDPOINT, line_payload))

    if not tasks:
        logger.info("reservation_notification", extra={"payload": json.dumps(message, ensure_ascii=False)})
        return

    try:
        await asyncio.gather(*tasks)
    except Exception as exc:
        logger.warning("notification dispatch failed: %s", exc)


def fire_and_forget(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
