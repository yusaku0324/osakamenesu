from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import (
    Reservation as ReservationSchema,
    ReservationCreateRequest,
    ReservationStatusEvent,
    ReservationUpdateRequest,
)
from ..deps import require_admin, audit_admin


router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])


def _reservation_to_schema(reservation: models.Reservation) -> ReservationSchema:
    history = [
        ReservationStatusEvent(
            status=event.status,  # type: ignore[arg-type]
            changed_at=event.changed_at,
            changed_by=event.changed_by,
            note=event.note,
        )
        for event in sorted(reservation.status_events, key=lambda e: e.changed_at)
    ]

    customer = {
        "name": reservation.customer_name,
        "phone": reservation.customer_phone,
        "email": reservation.customer_email,
        "line_id": reservation.customer_line_id,
        "remark": reservation.customer_remark,
        "id": None,
    }

    return ReservationSchema(
        id=reservation.id,
        status=reservation.status,  # type: ignore[arg-type]
        shop_id=reservation.shop_id,
        staff_id=reservation.staff_id,
        menu_id=reservation.menu_id,
        channel=reservation.channel,
        desired_start=reservation.desired_start,
        desired_end=reservation.desired_end,
        notes=reservation.notes,
        customer=customer,  # type: ignore[arg-type]
        status_history=history,
        marketing_opt_in=reservation.marketing_opt_in,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
    )


async def _ensure_shop(db: AsyncSession, shop_id: UUID) -> None:
    exists = await db.get(models.Profile, shop_id)
    if not exists:
        raise HTTPException(status_code=404, detail="shop not found")


async def _check_overlap(
    db: AsyncSession,
    shop_id: UUID,
    desired_start: datetime,
    desired_end: datetime,
    exclude_reservation_id: Optional[UUID] = None,
) -> bool:
    stmt = select(models.Reservation).where(
        models.Reservation.shop_id == shop_id,
        models.Reservation.status.in_(["pending", "confirmed"]),
        models.Reservation.desired_start < desired_end,
        models.Reservation.desired_end > desired_start,
    )
    if exclude_reservation_id:
        stmt = stmt.where(models.Reservation.id != exclude_reservation_id)
    res = await db.execute(stmt.limit(1))
    return res.scalar_one_or_none() is not None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_reservation(payload: ReservationCreateRequest, db: AsyncSession = Depends(get_session)):
    if payload.desired_end <= payload.desired_start:
        raise HTTPException(status_code=400, detail="desired_end must be after desired_start")

    await _ensure_shop(db, payload.shop_id)

    has_overlap = await _check_overlap(db, payload.shop_id, payload.desired_start, payload.desired_end)
    if has_overlap:
        raise HTTPException(status_code=409, detail="conflicting reservation slot")

    reservation = models.Reservation(
        shop_id=payload.shop_id,
        staff_id=payload.staff_id,
        menu_id=payload.menu_id,
        channel=payload.channel,
        desired_start=payload.desired_start,
        desired_end=payload.desired_end,
        notes=payload.notes,
        marketing_opt_in=bool(payload.marketing_opt_in),
        customer_name=payload.customer.name,
        customer_phone=payload.customer.phone,
        customer_email=payload.customer.email,
        customer_line_id=payload.customer.line_id,
        customer_remark=payload.customer.remark,
    )
    if not reservation.status:
        reservation.status = 'pending'
    initial_status = reservation.status
    status_event = models.ReservationStatusEvent(
        status=initial_status,
        changed_at=datetime.now(timezone.utc),
        changed_by="system",
        note=None,
    )
    reservation.status_events.append(status_event)

    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    await db.refresh(reservation, attribute_names=["status_events"])

    return _reservation_to_schema(reservation).model_dump()


@router.get("/{reservation_id}")
async def get_reservation(
    reservation_id: UUID,
    db: AsyncSession = Depends(get_session),
    _admin: None = Depends(require_admin),
    __audit: None = Depends(audit_admin),
):
    reservation = await db.get(models.Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="reservation not found")
    await db.refresh(reservation, attribute_names=["status_events"])
    return _reservation_to_schema(reservation).model_dump()


@router.patch("/{reservation_id}")
async def update_reservation(
    reservation_id: UUID,
    payload: ReservationUpdateRequest,
    db: AsyncSession = Depends(get_session),
    _admin: None = Depends(require_admin),
    __audit: None = Depends(audit_admin),
):
    if payload.status is None and payload.staff_id is None and payload.notes is None:
        raise HTTPException(status_code=400, detail="no updates provided")

    reservation = await db.get(models.Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="reservation not found")

    status_changed = False
    note: Optional[str] = None

    if payload.staff_id is not None:
        reservation.staff_id = payload.staff_id
    if payload.notes is not None:
        reservation.notes = payload.notes
        note = payload.notes
    if payload.status is not None and payload.status != reservation.status:
        if payload.status not in {"pending", "confirmed", "declined", "cancelled", "expired"}:
            raise HTTPException(status_code=400, detail="invalid status")
        reservation.status = payload.status
        status_changed = True

    if payload.response_message:
        note = (note or "") + (f"\n{payload.response_message}" if note else payload.response_message)

    if status_changed or note:
        event = models.ReservationStatusEvent(
            reservation_id=reservation.id,
            status=reservation.status,
            changed_at=datetime.now(timezone.utc),
            changed_by="admin",
            note=note,
        )
        db.add(event)

    await db.commit()
    await db.refresh(reservation)
    await db.refresh(reservation, attribute_names=["status_events"])

    return _reservation_to_schema(reservation).model_dump()
