import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks


ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "services" / "api"))


from app import models  # type: ignore  # noqa: E402
from app.routers import reservations as reservations_router  # type: ignore  # noqa: E402
from app.schemas import ReservationCreateRequest, ReservationCustomerInput  # type: ignore  # noqa: E402
from app.settings import settings  # type: ignore  # noqa: E402


class DummyResult:
    def __init__(self, value=None) -> None:
        self._value = value

    def scalar_one_or_none(self):  # pragma: no cover - simple container
        return self._value


class FakeSession:
    def __init__(self, shop):
        self.shop = shop
        self.reservations = []

    async def get(self, model, key):  # pragma: no cover - simple router helper
        if model is models.Profile:
            return self.shop if key == self.shop.id else None
        if model is models.Reservation:
            for reservation in self.reservations:
                if reservation.id == key:
                    return reservation
        return None

    async def execute(self, stmt):  # pragma: no cover
        return DummyResult(None)

    def add(self, obj):  # pragma: no cover
        if isinstance(obj, models.Reservation):
            self.reservations.append(obj)

    async def commit(self):  # pragma: no cover
        return None

    async def refresh(self, obj, attribute_names=None):  # pragma: no cover
        return None


@pytest.mark.anyio
async def test_create_reservation_queues_notifications(monkeypatch):
    shop_id = uuid4()
    shop = SimpleNamespace(
        id=shop_id,
        name="テスト店",
        notification_emails=["store@example.com"],
    )
    session = FakeSession(shop)

    settings.admin_notification_emails = ["ops@example.com"]

    called = {}

    def fake_queue(reservation, shop_obj, background_tasks):
        called["reservation"] = reservation
        called["shop"] = shop_obj
        called["tasks_len"] = len(background_tasks.tasks)

    monkeypatch.setattr(reservations_router, "queue_reservation_notifications", fake_queue)

    start = datetime.now(timezone.utc) + timedelta(hours=1)
    end = start + timedelta(hours=2)
    payload = ReservationCreateRequest(
        shop_id=shop_id,
        desired_start=start,
        desired_end=end,
        notes="気になるお客様",
        channel="web",
        customer=ReservationCustomerInput(
            name="山田太郎",
            phone="09000000000",
            email="user@example.com",
            line_id=None,
            remark="よろしくお願いします",
        ),
        marketing_opt_in=True,
    )

    background_tasks = BackgroundTasks()

    await reservations_router.create_reservation(
        payload,
        background_tasks,
        db=session,
        user=None,
    )

    assert "reservation" in called, "queue_reservation_notifications was not invoked"
    assert called["reservation"].shop_id == shop_id
    assert called["shop"].id == shop_id
    # fake queue does not add tasks but should receive BackgroundTasks instance
    assert called["tasks_len"] == 0
