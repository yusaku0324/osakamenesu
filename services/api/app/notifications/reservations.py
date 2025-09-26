from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks

from .. import models
from ..settings import settings
from .email import send_email

logger = logging.getLogger(__name__)
JST = ZoneInfo("Asia/Tokyo")


def queue_reservation_notifications(
    reservation: models.Reservation,
    shop: models.Profile,
    background_tasks: BackgroundTasks,
) -> None:
    recipients = _collect_recipients(shop)
    if not recipients:
        logger.debug("No notification recipients configured for shop %s", shop.id)
        return

    subject, body = _render_reservation_email(reservation, shop)
    background_tasks.add_task(send_email, subject, body, recipients)


def _collect_recipients(shop: models.Profile) -> list[str]:
    recipients: list[str] = []
    if shop.notification_emails:
        recipients.extend([email for email in shop.notification_emails if email])
    admin_emails: Iterable[str] = (str(email) for email in settings.admin_notification_emails)
    recipients.extend([email for email in admin_emails if email])
    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for email in recipients:
        lowered = email.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(email)
    return unique


def _render_reservation_email(reservation: models.Reservation, shop: models.Profile) -> tuple[str, str]:
    start_local = _to_jst(reservation.desired_start)
    end_local = _to_jst(reservation.desired_end)
    subject = f"[予約リクエスト] {shop.name} {start_local:%m/%d %H:%M}"

    customer_lines = [
        f"お名前: {reservation.customer_name or '未入力'}",
        f"電話番号: {reservation.customer_phone or '未入力'}",
        f"メールアドレス: {reservation.customer_email or '未入力'}",
    ]
    if reservation.customer_line_id:
        customer_lines.append(f"LINE ID: {reservation.customer_line_id}")
    if reservation.customer_remark:
        customer_lines.append(f"備考: {reservation.customer_remark}")

    marketing = "はい" if reservation.marketing_opt_in else "いいえ"

    lines = [
        "予約リクエストが届きました。",
        "",
        f"店舗名: {shop.name}",
        f"希望日時: {start_local:%Y-%m-%d %H:%M} 〜 {end_local:%H:%M}",
        f"予約ID: {reservation.id}",
        f"予約ステータス: {reservation.status}",
        "",
        "【お客様情報】",
        *customer_lines,
        "",
        "【予約メモ】",
        f"チャンネル: {reservation.channel or 'web'}",
        f"メモ: {reservation.notes or '（なし）'}",
        f"マーケティング連絡可否: {marketing}",
    ]

    if settings.site_base_url:
        lines.extend(
            [
                "",
                f"管理画面で確認: {settings.site_base_url.rstrip('/')}/admin/reservations/{reservation.id}",
            ]
        )

    body = "\n".join(lines)
    return subject, body


def _to_jst(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=JST)
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo("UTC")).astimezone(JST)
    return value.astimezone(JST)
