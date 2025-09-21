import os
import uuid
from datetime import date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app import models
from app.db import SessionLocal
from app.main import app
from app.meili import purge_all
from app.settings import settings


pytestmark = pytest.mark.integration


async def _reset_database() -> None:
    async with SessionLocal() as session:
        for table in (models.Availability, models.Outlink, models.Profile):
            await session.execute(delete(table))
        await session.commit()


async def _create_profile() -> models.Profile:
    profile = models.Profile(
        id=uuid.uuid4(),
        name="体験サロンA",
        area="難波/日本橋",
        price_min=11000,
        price_max=17000,
        bust_tag="D",
        service_type="store",
        height_cm=158,
        age=24,
        body_tags=["癒し", "丁寧"],
        photos=["https://example.com/photo1.jpg"],
        contact_json={
            "store_name": "リラクゼーションA",
            "ranking_reason": "編集部ピックアップ",
            "promotions": [
                {
                    "label": "朝割キャンペーン",
                    "description": "11時までのコースが1,000円OFF",
                }
            ],
            "reviews": {
                "average_score": 4.8,
                "review_count": 8,
                "highlighted": [
                    {
                        "title": "極上の癒し",
                        "body": "接客が非常に丁寧でリピート決定",
                        "score": 5,
                        "visited_at": date.today().isoformat(),
                        "author_alias": "匿名会員",
                    }
                ],
            },
        },
        discounts=[
            {
                "label": "WEB予約割",
                "description": "ネット予約で500円OFF",
            }
        ],
        ranking_badges=["人気No.1"],
        ranking_weight=90,
        status="published",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    availability = models.Availability(
        id=uuid.uuid4(),
        profile_id=profile.id,
        date=date.today(),
        slots_json={
            "slots": [
                {
                    "start_at": f"{date.today()}T10:00:00",
                    "end_at": f"{date.today()}T11:30:00",
                    "status": "open",
                }
            ]
        },
        is_today=True,
    )

    outlink = models.Outlink(
        id=uuid.uuid4(),
        profile_id=profile.id,
        kind="web",
        token="web-token",
        target_url="https://example.com",
        utm=None,
    )

    async with SessionLocal() as session:
        session.add(profile)
        session.add(availability)
        session.add(outlink)
        await session.commit()

    return profile


@pytest.mark.anyio
async def test_reindex_all_end_to_end() -> None:
    await _reset_database()
    purge_all()

    profile = await _create_profile()

    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/admin/reindex",
            headers={"X-Admin-Key": settings.admin_api_key},
        )
        assert resp.status_code == 200

        resp = await client.get("/api/v1/shops?page_size=5")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] >= 1
        first = payload["results"][0]
        assert first["id"] == str(profile.id)
        assert any(promo["label"] == "朝割キャンペーン" for promo in first.get("promotions", []))
        assert first.get("rating") == pytest.approx(4.8)
        assert first.get("ranking_reason") == "編集部ピックアップ"

    purge_all()
