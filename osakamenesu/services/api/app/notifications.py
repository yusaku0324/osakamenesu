from __future__ import annotations

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

import httpx

from .settings import settings
from .utils.email import MailNotConfiguredError, send_email_async

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
    customer_email: Optional[str] = None
    shop_phone: Optional[str] = None
    shop_line_contact: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    slack_webhook_url: Optional[str] = None
    line_notify_token: Optional[str] = None


async def _post_json(url: str, payload: Dict[str, Any]) -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(url, json=payload)


async def send_reservation_notification(payload: ReservationNotification) -> None:
    message = (
        f"予約ID: {payload.reservation_id}\n"
        f"店舗: {payload.shop_name} ({payload.shop_id})\n"
        f"ステータス: {payload.status}\n"
        f"経路: {payload.channel or '-'}\n"
        f"来店希望: {payload.desired_start} 〜 {payload.desired_end}\n"
        f"顧客: {payload.customer_name} ({payload.customer_phone})\n"
        f"メモ: {payload.notes or '-'}"
    )

    tasks: List[asyncio.Future] = []

    slack_webhook = payload.slack_webhook_url or SLACK_WEBHOOK
    if slack_webhook:
        tasks.append(_send_slack_notification(slack_webhook, message, payload.status))

    if payload.email_recipients:
        tasks.append(_send_store_email(payload, message))
    elif EMAIL_ENDPOINT:
        email_payload = {
            "subject": f"予約更新: {payload.shop_name} ({payload.status})",
            "message": message,
            "reservation_id": payload.reservation_id,
            "shop_id": payload.shop_id,
        }
        tasks.append(_post_json(EMAIL_ENDPOINT, email_payload))

    line_token = payload.line_notify_token
    if line_token:
        tasks.append(_send_line_notify(line_token, message))
    elif LINE_ENDPOINT:
        line_payload = {
            "message": message,
            "reservation_id": payload.reservation_id,
            "shop_id": payload.shop_id,
        }
        tasks.append(_post_json(LINE_ENDPOINT, line_payload))

    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.info("reservation_notification", extra={"payload": json.dumps(message, ensure_ascii=False)})

    if payload.customer_email:
        await _send_customer_confirmation(payload)


def fire_and_forget(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)


def schedule_reservation_notification(payload: ReservationNotification) -> None:
    fire_and_forget(send_reservation_notification(payload))


async def _send_slack_notification(webhook: str, message: str, status: str) -> None:
    payload = {
        "text": f"*予約更新通知*: {status}",
        "attachments": [
            {
                "color": "#36a64f" if status == "confirmed" else "#f4c542",
                "text": message,
            }
        ],
    }
    try:
        await _post_json(webhook, payload)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("slack_notification_failed: %s", exc)


async def _send_store_email(payload: ReservationNotification, message: str) -> None:
    subject = f"予約更新: {payload.shop_name} ({payload.status})"
    body_html = "<br>".join(message.splitlines())
    try:
        await send_email_async(
            to=payload.email_recipients,
            subject=subject,
            html=f"<p>以下の内容で予約リクエストを受信しました。</p><p>{body_html}</p>",
            text=message,
            tags=["reservation", "alert"],
        )
    except MailNotConfiguredError:
        logger.info("store_email_skipped", extra={"reason": "mail_not_configured"})
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("store_email_failed: %s", exc)


async def _send_line_notify(token: str, message: str) -> None:
    headers = {"Authorization": f"Bearer {token.strip()}"}
    data = {"message": message[:900]}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
            response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("line_notify_failed: %s", exc)


def _format_datetime(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


async def _send_customer_confirmation(payload: ReservationNotification) -> None:
    desired_start = _format_datetime(payload.desired_start)
    desired_end = _format_datetime(payload.desired_end)

    contact_lines = []
    if payload.shop_phone:
        contact_lines.append(f"・お電話：{payload.shop_phone}")
    if payload.shop_line_contact:
        contact_lines.append(f"・LINE：{payload.shop_line_contact}")
    contact_block = "<br>".join(contact_lines) if contact_lines else "店舗からの折り返しをお待ちください。"

    html = f"""
<p>{payload.customer_name} 様</p>
<p>このたびは <strong>{payload.shop_name}</strong> へのご予約リクエストをいただきありがとうございます。</p>
<p>以下の内容で受け付けました。担当スタッフより折り返しご連絡いたしますので、今しばらくお待ちください。</p>
<ul>
  <li>受付番号: {payload.reservation_id}</li>
  <li>ステータス: {payload.status}</li>
  <li>希望日時: {desired_start} 〜 {desired_end}</li>
  <li>送信経路: {payload.channel or '-'} </li>
</ul>
<p>ご不明点がございましたら、下記の連絡先より店舗へお問い合わせください。</p>
<p>{contact_block}</p>
<p>※本メールは送信専用です。ご返信には対応しておりません。</p>
"""

    try:
        await send_email_async(
            to=payload.customer_email,
            subject=f"[{payload.shop_name}] ご予約リクエストを受け付けました",
            html=html,
            text=(
                f"{payload.customer_name} 様\n"
                f"{payload.shop_name} へのご予約リクエストを受け付けました。\n"
                f"受付番号: {payload.reservation_id}\n"
                f"ステータス: {payload.status}\n"
                f"希望日時: {desired_start} 〜 {desired_end}\n"
                f"送信経路: {payload.channel or '-'}\n"
                "店舗からの連絡をお待ちください。\n"
            ),
            tags=["reservation", "confirmation"],
        )
    except MailNotConfiguredError:
        logger.info("customer_confirmation_skipped", extra={"reason": "mail_not_configured"})
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("customer_confirmation_failed: %s", exc)
