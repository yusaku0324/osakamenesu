from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..deps import get_dashboard_profile
from ..schemas import (
    DashboardNotificationSettingsResponse,
    DashboardNotificationSettingsUpdate,
    DashboardNotificationSettingsInput,
    DashboardNotificationChannels,
    DashboardNotificationChannelEmail,
    DashboardNotificationChannelLine,
    DashboardNotificationChannelSlack,
)

router = APIRouter(prefix="/api/dashboard/shops", tags=["dashboard-notifications"])


def _channels_from_profile(profile: models.Profile) -> DashboardNotificationChannels:
    enabled_flags = profile.notify_channels_enabled or {}
    return DashboardNotificationChannels(
        email=DashboardNotificationChannelEmail(
            enabled=bool(enabled_flags.get("email")),
            recipients=profile.notify_email_recipients or [],
        ),
        line=DashboardNotificationChannelLine(
            enabled=bool(enabled_flags.get("line")),
            token=profile.notify_line_token,
        ),
        slack=DashboardNotificationChannelSlack(
            enabled=bool(enabled_flags.get("slack")),
            webhook_url=profile.notify_slack_webhook,
        ),
    )


def _response_from_profile(profile: models.Profile) -> DashboardNotificationSettingsResponse:
    return DashboardNotificationSettingsResponse(
        profile_id=profile.id,
        updated_at=profile.updated_at,
        channels=_channels_from_profile(profile),
        trigger_status=profile.notify_trigger_status or [],
    )


@router.get("/{profile_id}/notifications", response_model=DashboardNotificationSettingsResponse)
async def get_notification_settings(
    profile: models.Profile = Depends(get_dashboard_profile),
) -> DashboardNotificationSettingsResponse:
    return _response_from_profile(profile)


@router.put("/{profile_id}/notifications", response_model=DashboardNotificationSettingsResponse)
async def update_notification_settings(
    payload: DashboardNotificationSettingsUpdate,
    profile: models.Profile = Depends(get_dashboard_profile),
    db: AsyncSession = Depends(get_session),
) -> DashboardNotificationSettingsResponse:
    if profile.updated_at != payload.updated_at:
        current = _response_from_profile(profile)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "notification_settings_conflict",
                "message": "Notification settings were updated by another user.",
                "current": current.model_dump(mode="json"),
            },
        )

    channels = payload.channels
    profile.notify_email_recipients = list(channels.email.recipients)
    profile.notify_line_token = channels.line.token
    profile.notify_slack_webhook = channels.slack.webhook_url
    profile.notify_trigger_status = list(payload.trigger_status)
    profile.notify_channels_enabled = {
        "email": channels.email.enabled,
        "line": channels.line.enabled,
        "slack": channels.slack.enabled,
    }

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return _response_from_profile(profile)


@router.post("/{profile_id}/notifications/test")
async def test_notification_settings(
    payload: DashboardNotificationSettingsInput,
    profile: models.Profile = Depends(get_dashboard_profile),
) -> Response:
    # ※ダッシュボードの UI が完成するまではテスト送信を行わず、値のバリデーションのみ実施。
    # 後続タスクで実際の配送処理を組み込む予定。
    _ = payload
    _ = profile
    return Response(status_code=status.HTTP_204_NO_CONTENT)
