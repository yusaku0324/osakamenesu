import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List

import pytest
from fastapi import HTTPException

from app import models  # type: ignore
from app.routers import shops as shops_router  # type: ignore


class FakeScalarResult:
    def __init__(self, data: List[Any]):
        self._data = data

    def all(self) -> List[Any]:
        return self._data


class FakeResult:
    def __init__(self, *, scalars: List[Any] | None = None, scalar_one: Any | None = None) -> None:
        self._scalars = scalars or []
        self._scalar_one = scalar_one

    def scalars(self) -> FakeScalarResult:
        return FakeScalarResult(self._scalars)

    def scalar_one(self) -> Any:
        if self._scalar_one is None:
            raise AssertionError("scalar_one not set")
        return self._scalar_one


class FakeSession:
    def __init__(self, profile: models.Profile, diaries: List[models.Diary]) -> None:
        self._profile = profile
        self._diaries = diaries

    async def get(self, model: Any, pk: Any) -> Any:  # noqa: ANN401 - test double
        if model is models.Profile and pk == self._profile.id:
            return self._profile
        return None

    async def execute(self, query):  # type: ignore[override]
        desc = query.column_descriptions[0]
        entity = desc.get("entity")
        if entity is models.Diary:
            items = self._filtered_diaries()
            offset_clause = getattr(query, "_offset_clause", None)
            if offset_clause is not None and getattr(offset_clause, "value", None) is not None:
                items = items[int(offset_clause.value) :]
            limit_clause = getattr(query, "_limit_clause", None)
            if limit_clause is not None and getattr(limit_clause, "value", None) is not None:
                items = items[: int(limit_clause.value)]
            return FakeResult(scalars=items)

        if desc.get("name") == "count" and entity is None:
            items = self._filtered_diaries()
            return FakeResult(scalar_one=len(items))

        raise AssertionError(f"Unhandled query: {query}")

    def _filtered_diaries(self) -> List[models.Diary]:
        eligible = [
            diary
            for diary in self._diaries
            if diary.profile_id == self._profile.id and diary.status == 'published'
        ]
        return sorted(eligible, key=lambda d: d.created_at, reverse=True)


class MissingProfileSession(FakeSession):
    def __init__(self) -> None:
        pass

    async def get(self, model: Any, pk: Any) -> Any:  # noqa: ANN401 - test double
        return None

    async def execute(self, query):  # type: ignore[override]
        raise AssertionError("execute should not be called when profile is missing")


def _make_profile(**overrides: Any) -> models.Profile:
    now = datetime.now(timezone.utc)
    base = {
        "id": uuid.uuid4(),
        "name": "サロンA",
        "area": "難波/日本橋",
        "price_min": 10000,
        "price_max": 15000,
        "bust_tag": "C",
        "service_type": "store",
        "body_tags": [],
        "photos": [],
        "contact_json": {},
        "discounts": [],
        "ranking_badges": [],
        "ranking_weight": 10,
        "status": "published",
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    profile = models.Profile(**base)
    profile.diaries = []
    return profile


def _make_diary(profile_id: uuid.UUID, *, created_at: datetime, status: str = 'published', **overrides: Any) -> models.Diary:
    payload = {
        "id": uuid.uuid4(),
        "profile_id": profile_id,
        "title": overrides.pop("title", "写メ日記"),
        "text": overrides.pop("text", "テキスト"),
        "photos": overrides.pop("photos", ["https://example.com/photo.jpg"]),
        "hashtags": overrides.pop("hashtags", ["癒し"]),
        "status": status,
        "created_at": created_at,
    }
    payload.update(overrides)
    return models.Diary(**payload)


@pytest.mark.anyio
async def test_get_shop_diaries_returns_recent_entries() -> None:
    profile = _make_profile()
    base_time = datetime.now(timezone.utc)
    diaries = [
        _make_diary(profile.id, created_at=base_time - timedelta(hours=delta), title=f"日記{delta}")
        for delta in range(3)
    ]
    diaries.append(
        _make_diary(
            profile.id,
            created_at=base_time,
            status='hidden',
            title="非公開",
        )
    )
    session = FakeSession(profile, diaries)

    payload = await shops_router.get_shop_diaries(profile.id, page=1, page_size=2, db=session)

    assert payload["total"] == 3
    assert [item["title"] for item in payload["items"]] == ["日記0", "日記1"]
    assert payload["items"][0]["photos"]


@pytest.mark.anyio
async def test_get_shop_diaries_missing_profile_raises_404() -> None:
    session = MissingProfileSession()
    with pytest.raises(HTTPException) as exc:
        await shops_router.get_shop_diaries(uuid.uuid4(), db=session)
    assert exc.value.status_code == 404
